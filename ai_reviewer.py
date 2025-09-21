"""
ai_reviewer.py
AI review logic — integrated with CodeMate Build/Extension.
"""

import os
import requests

# Get CodeMate API key from environment variable (set it in your terminal/VS Code)
CODEMATE_API_KEY = os.getenv("CODEMATE_API_KEY")

# Base URL for CodeMate — check hackathon docs for the exact endpoint
CODEMATE_URL = "https://api.codemate.ai/v1/code-review"  # <-- replace with actual

def call_ai_model(diff_text: str) -> str:
    """
    Calls CodeMate Build/Extension to review a code diff.
    """
    if not CODEMATE_API_KEY:
        raise ValueError("CODEMATE_API_KEY is not set in environment variables.")

    headers = {
        "Authorization": f"Bearer {CODEMATE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "agent": "code-review",    # or "pr-review" depending on the hackathon tool
        "input": diff_text         # may also require language or repo context
    }

    response = requests.post(CODEMATE_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"CodeMate API call failed: {response.status_code}, {response.text}"
        )

    data = response.json()
    # Adjust parsing depending on CodeMate's response schema
    return data.get("review", "No feedback returned from CodeMate.")

def review_diff(diff_text: str) -> str:
    return call_ai_model(diff_text)
