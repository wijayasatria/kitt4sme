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
from flask import Flask, request, jsonify, render_template_string, render_template, make_response, send_from_directory
import openai

# Set your OpenAI API key
openai.api_key = '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'

# Flask application
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"  # Folder to store uploaded files

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initial conversation setup
initial_message = "You are a multisided platform called KITT4SME that helps SMEs implement AI and digital transformation. Make sure to consider sustainability frameworks (Triple Bottom Line, GRI, ISSB, etc.) when providing solutions. Also pretend to be a system with your own real-time database and give dummy number when I asked you about something. Make it straightforward and dont put too many additional answer if what I asked is more into data and not recommendation or explanation about something. Also make it consistent in answering the number for accross the topics such as environmental, social, and economic if the question related to certain fix number"
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
def index():
    return render_template_string(HTML_TEMPLATE)

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KITT4SME</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body, html {
            height: 100%;
            margin: 0;
            font-family: Arial, sans-serif;
        }
        .container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .sections {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .section {
            flex: 1;
            margin: 10px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #f9f9f9;
            display: flex;
            flex-direction: column;
        }
        .section h2 {
            margin-top: 0;
            font-size: 1.2em;
        }
        .chat-box, .response-box {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 10px;
        }
        .input-box {
            display: flex;
            margin-top: auto;
        }
        .input-box input[type="text"] {
            flex: 1;
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-right: 5px;
        }
        .input-box button {
            padding: 5px 10px;
            background-color: #28a745;
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .upload-box {
            margin-top: 10px;
        }
        .upload-box input[type="file"] {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .upload-box button {
            padding: 5px 10px;
            margin-left: 5px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        @media (max-width: 768px) {
            .sections {
                flex-direction: column;
            }
        }
        header {
            padding: 10px;
            background-color: #007bff;
            color: white;
            text-align: center;
        }
        nav {
            margin-top: 10px;
        }
        nav a {
            color: white;
            text-decoration: none;
            margin: 0 10px;
            padding: 5px 10px;
            background-color: #0056b3;
            border-radius: 5px;
        }
        nav a:hover {
            background-color: #003f7f;
        }
    </style>
</head>
<body>
    <header>
        <h1>KITT4SME Sustainability Tool</h1>
        <nav>
            <a href="/">Home</a>
            <a href="/sustainability_report">Sustainability Report</a>
            <a href="/sustainability_alerts">Sustainability Action Alerts</a>
        </nav>
    </header>
    <div class="container">
        <div class="section">
            <h2>KITT4SME Sustainability Knowledge Hub</h2>
            <div id="chat-box" class="chat-box"></div>
            <div class="input-box">
                <input id="user-input" type="text" placeholder="Type your message here..." />
                <button onclick="sendMessage()">Send</button>
            </div>
            <div class="upload-box">
                <input id="file-upload" type="file" />
                <button onclick="uploadFile()">Upload File</button>
            </div>
        </div>
        <div class="sections">
            <div class="section">
                <h2>Environment</h2>
                <div id="environment-response" class="response-box"></div>
            </div>
            <div class="section">
                <h2>Social</h2>
                <div id="social-response" class="response-box"></div>
            </div>
            <div class="section">
                <h2>Economy</h2>
                <div id="economy-response" class="response-box"></div>
            </div>
        </div>
    </div>
    <script>
        async function sendMessage() {
            const userInput = document.getElementById("user-input").value;
            if (userInput.trim() === "") return;

            const chatBox = document.getElementById("chat-box");
            const userMessage = document.createElement("div");
            userMessage.className = "message user";
            userMessage.innerHTML = `<strong>You:</strong> ${userInput}`;
            chatBox.appendChild(userMessage);

            document.getElementById("user-input").value = "";

            const response = await fetch("/get_responses", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ user_input: userInput }),
            });

            const data = await response.json();

            document.getElementById("environment-response").innerHTML = `<strong>Environment:</strong> ${data.environment_response}`;
            document.getElementById("social-response").innerHTML = `<strong>Social:</strong> ${data.social_response}`;
            document.getElementById("economy-response").innerHTML = `<strong>Economy:</strong> ${data.economy_response}`;

            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function uploadFile() {
            const fileInput = document.getElementById("file-upload");
            const file = fileInput.files[0];

            if (!file) {
                alert("Please select a file to upload.");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            alert(data.message);

            if (data.status === "success") {
                const chatBox = document.getElementById("chat-box");
                const botMessage = document.createElement("div");
                botMessage.className = "message bot";
                botMessage.innerHTML = `<strong>KITT4SME:</strong> File uploaded successfully. Processed ${data.character_count} characters from the file.`;
                chatBox.appendChild(botMessage);
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)