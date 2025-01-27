import subprocess
import sys
import os

# Install required libraries if not already installed
def install_packages():
    required_packages = ["openai", "flask", "pandas", "PyPDF2", "python-docx"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"{package} not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

import pandas as pd
import PyPDF2
from docx import Document
from flask import Flask, request, jsonify, render_template_string, render_template, make_response, send_from_directory, redirect
import openai


# Set your OpenAI API key
keyA = 'sk-proj-8w3LqTH6-mE5I0iOz-PuwTa4iyc7N6PWXP4cN'
keyB = '-OS5sHQQHl7RfuWzLormnRamx_hBqhiBdAlFuT3BlbkFJ'
keyC = '6lJchqvvfq5qGWHVSb9Z8-NZIjjdyL58gM3G'
keyD = '-ySnWA3gXzUm1hvuhAb2H67W9H-sTMd343cX0A'
openai.api_key = keyA + keyB + keyC + keyD

# Flask application
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"  # Folder to store uploaded files

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initial conversation setup
initial_message = "You are a multisided platform called KITT4SME that helps SMEs implement AI and digital transformation. Make sure to consider sustainability frameworks (Triple Bottom Line, GRI, ISSB, etc.) when providing solutions. Also pretend to be a system with your own real-time database and give dummy number when I asked you about something. Make it straightforward and dont put too many additional answer if what I asked is more into data and not recommendation or explanation about something. Also make it consistent in answering the number for accross the topics such as environmental, social, and economic if the question related to certain fix number or something happened in certain part of the operations. The numbers provided as answer should relate and not contradict with each other topics"
conversation = [{"role": "system", "content": initial_message}]

# Function to extract text from various file types
def extract_text_from_file(filepath):
    file_extension = filepath.split(".")[-1].lower()
    try:
        if file_extension == "csv":
            df = pd.read_csv(filepath)
            return df.to_string()
        elif file_extension == "xlsx":
            df = pd.read_excel(filepath)
            return df.to_string()
        elif file_extension == "pdf":
            text = ""
            with open(filepath, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        elif file_extension == "docx":
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            return "Unsupported file format."
    except Exception as e:
        return f"Error extracting text from file: {str(e)}"

# Function to get responses from GPT model for different focuses
def get_gpt_response(user_input, focus):
    global conversation

    # Add user input and focus to the conversation
    conversation.append({"role": "user", "content": f"{user_input} Please focus on {focus} aspects."})

    try:
        response = openai.chat.completions.create(
        messages = conversation,
        model  =  "gpt-3.5-turbo"
        )
        conversation.append(response.choices[0].message)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Route for the main page
@app.route("/")
def home():
    return redirect("/knowledge_hub")

# Route for knowledge hub
@app.route("/knowledge_hub")
def index():
    return render_template("knowledge_hub.html")

# Route to get responses for different sections
@app.route("/get_responses", methods=["POST"])
def get_responses():
    user_input = request.json.get("user_input")
    if user_input:
        environment_response = get_gpt_response(user_input, "environmental")
        social_response = get_gpt_response(user_input, "social")
        economy_response = get_gpt_response(user_input, "economic")
        return jsonify({
            "environment_response": environment_response,
            "social_response": social_response,
            "economy_response": economy_response
        })
    return jsonify({"response": "No input received"})

# Route to handle file uploads
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "fail", "message": "No file part in the request"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "fail", "message": "No selected file"})

    try:
        # Save the file locally
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        # Extract text from the file
        extracted_text = extract_text_from_file(filepath)
        if extracted_text.startswith("Error"):
            return jsonify({"status": "fail", "message": extracted_text})

        # Add the extracted text to the conversation as context
        conversation.append({"role": "system", "content": f"Context from uploaded file: {extracted_text}"})

        return jsonify({
            "status": "success",
            "message": f"File uploaded successfully. Processed {len(extracted_text)} characters from the file.",
            "character_count": len(extracted_text)
        })

    except Exception as e:
        return jsonify({"status": "fail", "message": f"An error occurred: {str(e)}"})
    
# Route to serve the sustainability report
@app.route("/sustainability_report")
def sustainability_report():
    return render_template("sustainability_report.html")

# New route for the Sustainable Action Alerts page
@app.route('/sustainability_alerts')
def alerts():
    return render_template('sustainability_alerts.html')  # Renders the new alerts page

@app.route('/templates/<path:filename>')
def serve_template_file(filename):
    return send_from_directory('templates', filename)

if __name__ == "__main__":
    app.run(debug=True)
