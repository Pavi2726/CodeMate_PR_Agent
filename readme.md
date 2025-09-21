# PR Review Agent (Problem Statement 2)

## 🚀 Overview
A Flask-based webhook server that:
- Listens to GitHub/GitLab pull/merge request events
- Fetches the PR/MR diffs
- Sends diffs to an AI reviewer (CodeMate Build/Extension)
- Returns automated code review feedback

## ⚡ Features
- Supports both **GitHub** and **GitLab** webhooks
- Secure GitHub signature verification
- Fetches diffs automatically
- Pluggable AI module (`ai_reviewer.py`) for feedback
- Ready to deploy on Replit/Render/Railway

## 🛠 Setup
1. Clone repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
