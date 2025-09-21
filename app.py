import os
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import gitlab
from github import Github
from github import Auth
from ai_reviewer import review_diff

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Access tokens
github_token = os.getenv("GITHUB_TOKEN")
gitlab_token = os.getenv("GITLAB_TOKEN")
webhook_secret = os.getenv("WEBHOOK_SECRET", "mysecret")

# Initialize API clients
auth = Auth.Token(github_token) if github_token else None
g = Github(auth=auth) if github_token else None
gl = gitlab.Gitlab("https://gitlab.com", private_token=gitlab_token) if gitlab_token else None


def verify_github_signature(request):
    """Verify GitHub webhook signature (HMAC)."""
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return False
    sha_name, signature = signature.split("=")
    mac = hmac.new(webhook_secret.encode(), msg=request.data, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)


def get_github_diff(repo_name, pr_number):
    """Fetch the diff from a GitHub pull request."""
    try:
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Get the patch content directly from the PR
        diff = pr.patch
        
        return diff
    except Exception as e:
        print(f"Error fetching GitHub diff: {e}")
        return None


def get_gitlab_diff(project_id, mr_iid):
    """Fetch the diff from a GitLab merge request."""
    try:
        project = gl.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)
        diffs = mr.diffs.list()
        diff_text = "\n".join([d.get("diff", "") for d in diffs])
        return diff_text
    except Exception as e:
        print(f"Error fetching GitLab diff: {e}")
        return None


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    payload = request.json or {}

    # Identify the platform
    if "X-GitHub-Event" in request.headers:
        # GitHub Handling
        if not verify_github_signature(request):
            return jsonify({"status": "error", "message": "Invalid GitHub signature"}), 403

        event_type = request.headers.get("X-GitHub-Event")
        action = payload.get("action")
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name")

        if event_type == "pull_request" and action in ["opened", "synchronize", "reopened"]:
            # Fetch diff
            diff = get_github_diff(repo_name, pr_number)
            
            if not diff:
                return jsonify({"status": "error", "message": "Failed to fetch diff"}), 500

            # Review with AI
            ai_feedback = review_diff(diff)

            # Post feedback as PR comment
            try:
                repo = g.get_repo(repo_name)
                pr = repo.get_pull(pr_number)
                pr.create_issue_comment(ai_feedback)
                
                print(f"[GitHub] PR #{pr_number} in {repo_name}, Action={action}")
                print("AI Review posted to GitHub PR.")
                
                return jsonify({"status": "success", "ai_feedback": ai_feedback}), 200
            except Exception as e:
                print(f"Error posting comment to GitHub PR: {e}")
                return jsonify({"status": "error", "message": "Failed to post review"}), 500

    elif "X-Gitlab-Event" in request.headers:
        # GitLab Handling
        event_type = request.headers.get("X-Gitlab-Event")
        
        if event_type == "Merge Request Hook":
            action = payload.get("object_attributes", {}).get("action")
            mr_iid = payload.get("object_attributes", {}).get("iid")
            project_id = payload.get("project", {}).get("id")

            if action in ["open", "update"]:
                # Fetch diff
                diff = get_gitlab_diff(project_id, mr_iid)
                
                if not diff:
                    return jsonify({"status": "error", "message": "Failed to fetch diff"}), 500

                # Review with AI
                ai_feedback = review_diff(diff)

                # Post feedback as MR note
                try:
                    project = gl.projects.get(project_id)
                    mr = project.mergerequests.get(mr_iid)
                    mr.notes.create({"body": ai_feedback})
                    
                    print(f"[GitLab] MR !{mr_iid} in project {project_id}, Action={action}")
                    print("AI Review posted to GitLab MR.")
                    
                    return jsonify({"status": "success", "ai_feedback": ai_feedback}), 200
                except Exception as e:
                    print(f"Error posting note to GitLab MR: {e}")
                    return jsonify({"status": "error", "message": "Failed to post review"}), 500

    # Unknown Source
    else:
        print("Unknown webhook source.")
        return jsonify({"status": "ignored", "message": "Unknown webhook source"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
# Test PR to trigger webhook
