import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Access your tokens securely
github_token = os.getenv("GITHUB_TOKEN")
gitlab_token = os.getenv("GITLAB_TOKEN")
bitbucket_token = os.getenv("BITBUCKET_TOKEN")

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # The payload contains the data sent by the webhook
    payload = request.json
    print("Received webhook payload:", payload)

    # You will add logic here to determine the platform and process the request
    # For example, you can check headers like "X-GitHub-Event" or "X-GitLab-Event"

    # Return a success message
    return jsonify({"status": "success", "message": "Webhook received"}), 200

if __name__ == '__main__':
    # Run the server on a port that you will expose with ngrok
    app.run(port=5000, debug=True)