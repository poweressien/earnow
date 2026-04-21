# 🟡 EarnNow — Play, Learn & Earn Real Money

A Nigerian survey & earning platform with quizzes, games, polls, and airtime rewards.

---

## 🚀 Quick Start (Run on Your Computer)

1. Make sure Python is installed: https://python.org/downloads
2. Open a terminal inside this folder
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate it:
   - Windows:  venv\Scripts\activate
   - Mac/Linux: source venv/bin/activate
5. Install packages:
   ```
   pip install -r requirements.txt
   ```
6. Run the app:
   ```
   python app.py
   ```
7. Open your browser and go to: http://localhost:5000

---

## 📁 Files in This Folder

| File             | What it does                                      |
|------------------|---------------------------------------------------|
| app.py           | The entire website — Python + HTML + CSS + JS     |
| requirements.txt | Python packages needed                            |
| .env             | Your secret keys — EDIT THIS before running      |
| .gitignore       | Tells GitHub what not to upload                   |
| Procfile         | Tells Render.com how to start the app             |
| runtime.txt      | Tells Render which Python version to use          |

---

## ⚙️ Before You Run — Edit .env

Open the `.env` file and replace the placeholder values:

- `SECRET_KEY` — make up any long random phrase
- `PAYSTACK_SECRET_KEY` — get from https://dashboard.paystack.com
- `VTPASS_API_KEY` — get from https://vtpass.com (for airtime)
- `ADMIN_PASSWORD` — choose any password for your admin access

---

## 🌍 Deploy to Internet (Free)

1. Push this folder to GitHub
2. Go to https://render.com
3. New > Web Service > connect your GitHub repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Add your .env values under Environment Variables
7. Done — your site will be live in 3 minutes!

---

## 🎮 Task Types

- 📋 Surveys — answer questions, earn naira
- 🧠 Quizzes — learn facts, earn bonus XP
- 🎮 Games — word scramble, true/false, emoji decode
- 🗣️ Polls — vote and see live results

## 💰 Rewards

- Earn kobo on every task
- Redeem as airtime (MTN, Airtel, Glo, 9mobile)
- Withdraw to any Nigerian bank account (min ₦1,000)
- Level up with XP: Starter → Explorer → Earner → Hustler → Champion → Legend

---

Built with Python (Flask) 🐍
