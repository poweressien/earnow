from flask import Flask, render_template_string, request, jsonify, session
import json, os, uuid, random
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "earnnow-secret-key-2024"

# ════════════════════════════════════════════════════════
#  IN-MEMORY DATABASE  (swap with SQLite for production)
# ════════════════════════════════════════════════════════
users_db    = {}   # email → user dict
responses_db = {}  # "email_taskid" → answers

MIN_WITHDRAW_KOBO = 100000   # ₦1,000

# ════════════════════════════════════════════════════════
#  TASK CATALOGUE
#  type: "survey" | "quiz" | "poll" | "challenge"
# ════════════════════════════════════════════════════════
TASKS = [

    # ── SURVEYS ──────────────────────────────────────────
    {
        "id": "s1", "type": "survey",
        "title": "Daily Lifestyle Survey",
        "desc": "Share your daily habits and routines",
        "reward": 150, "xp": 10,
        "category": "Lifestyle", "duration": "2 min", "icon": "📋",
        "questions": [
            {"q": "How many hours do you sleep daily?",
             "options": ["Less than 5hrs","5–6 hrs","7–8 hrs","More than 8hrs"]},
            {"q": "How often do you exercise?",
             "options": ["Never","1–2x/week","3–4x/week","Daily"]},
            {"q": "What do you spend most time on?",
             "options": ["Work","Social Media","Family","Hobbies"]},
            {"q": "How would you rate your current happiness?",
             "options": ["Very Low","Low","High","Very High"]},
            {"q": "Do you use mobile banking?",
             "options": ["Yes, daily","Sometimes","Rarely","Never"]},
        ]
    },
    {
        "id": "s2", "type": "survey",
        "title": "Shopping Habits Quiz",
        "desc": "Tell us how you shop in Nigeria",
        "reward": 200, "xp": 15,
        "category": "Commerce", "duration": "3 min", "icon": "🛒",
        "questions": [
            {"q": "How often do you shop online?",
             "options": ["Daily","Weekly","Monthly","Rarely"]},
            {"q": "Which platform do you use most?",
             "options": ["Jumia","Konga","Instagram","WhatsApp"]},
            {"q": "What influences your purchase?",
             "options": ["Price","Reviews","Brand","Friends"]},
            {"q": "How do you usually pay?",
             "options": ["Transfer","USSD","POS","Cash"]},
            {"q": "Monthly spend on shopping?",
             "options": ["< ₦5k","₦5k–₦20k","₦20k–₦50k","> ₦50k"]},
        ]
    },
    {
        "id": "s3", "type": "survey",
        "title": "Food & Dining Trends",
        "desc": "Your Nigerian food preferences",
        "reward": 180, "xp": 12,
        "category": "Food", "duration": "2 min", "icon": "🍲",
        "questions": [
            {"q": "How often do you order food online?",
             "options": ["Daily","Weekly","Monthly","Rarely"]},
            {"q": "Preferred food delivery app?",
             "options": ["Chowdeck","Glovo","Bolt Food","None"]},
            {"q": "How much do you spend on food weekly?",
             "options": ["< ₦2k","₦2k–₦5k","₦5k–₦15k","> ₦15k"]},
            {"q": "Favourite Nigerian dish?",
             "options": ["Jollof Rice","Pounded Yam","Egusi Soup","Suya"]},
        ]
    },

    # ── QUIZZES (Learning) ────────────────────────────────
    {
        "id": "q1", "type": "quiz",
        "title": "Nigeria General Knowledge",
        "desc": "Test what you know about Nigeria! Earn bonus for high scores",
        "reward": 250, "xp": 25,
        "category": "Learning", "duration": "3 min", "icon": "🧠",
        "pass_score": 3,
        "questions": [
            {"q": "What is the capital of Nigeria?",
             "options": ["Lagos","Kano","Abuja","Port Harcourt"],
             "answer": "Abuja",
             "fact": "Abuja became Nigeria's capital in 1991, replacing Lagos."},
            {"q": "How many states are in Nigeria?",
             "options": ["30","36","40","42"],
             "answer": "36",
             "fact": "Nigeria has 36 states plus the Federal Capital Territory."},
            {"q": "What year did Nigeria gain independence?",
             "options": ["1955","1960","1963","1970"],
             "answer": "1960",
             "fact": "Nigeria gained independence from Britain on October 1, 1960."},
            {"q": "What is Nigeria's currency?",
             "options": ["Cedi","Naira","Shilling","Franc"],
             "answer": "Naira",
             "fact": "The Naira was introduced in 1973, replacing the Nigerian pound."},
            {"q": "Which river is the longest in Nigeria?",
             "options": ["Niger","Benue","Kaduna","Osun"],
             "answer": "Niger",
             "fact": "The Niger River is West Africa's largest river and runs through Nigeria."},
        ]
    },
    {
        "id": "q2", "type": "quiz",
        "title": "Tech & Finance Trivia",
        "desc": "How sharp are you on tech and money matters?",
        "reward": 300, "xp": 30,
        "category": "Learning", "duration": "3 min", "icon": "💡",
        "pass_score": 3,
        "questions": [
            {"q": "What does ATM stand for?",
             "options": ["Automated Teller Machine","Automatic Transfer Mode","Automated Transaction Monitor","All Transaction Methods"],
             "answer": "Automated Teller Machine",
             "fact": "ATMs were invented in 1967 by John Shepherd-Barron in London."},
            {"q": "What is cryptocurrency?",
             "options": ["A type of credit card","Digital money secured by encryption","A bank savings account","Government-issued bond"],
             "answer": "Digital money secured by encryption",
             "fact": "Bitcoin was the first cryptocurrency, created in 2009 by the anonymous Satoshi Nakamoto."},
            {"q": "What does BVN stand for in Nigerian banking?",
             "options": ["Bank Verification Number","Basic Value Note","Balance Verification Node","Bank Value Network"],
             "answer": "Bank Verification Number",
             "fact": "BVN was introduced by the CBN in 2014 to reduce banking fraud in Nigeria."},
            {"q": "What is inflation?",
             "options": ["When money gains value","When prices rise and money buys less","When banks give out loans","When stocks increase"],
             "answer": "When prices rise and money buys less",
             "fact": "Nigeria's inflation rate has been a major economic challenge in recent years."},
            {"q": "Which company owns Instagram?",
             "options": ["Google","Apple","Meta","Twitter"],
             "answer": "Meta",
             "fact": "Meta (formerly Facebook) acquired Instagram in 2012 for $1 billion."},
        ]
    },
    {
        "id": "q3", "type": "quiz",
        "title": "Health & Body Quiz",
        "desc": "How much do you know about your own health?",
        "reward": 200, "xp": 20,
        "category": "Learning", "duration": "2 min", "icon": "🏥",
        "pass_score": 2,
        "questions": [
            {"q": "How many litres of water should you drink daily?",
             "options": ["1 litre","2 litres","3 litres","5 litres"],
             "answer": "2 litres",
             "fact": "The average adult needs about 2 litres of water daily to stay hydrated."},
            {"q": "Which vitamin do you get from sunlight?",
             "options": ["Vitamin A","Vitamin B12","Vitamin C","Vitamin D"],
             "answer": "Vitamin D",
             "fact": "Nigeria's abundant sunshine makes Vitamin D deficiency less common here."},
            {"q": "What is a normal resting heart rate for adults?",
             "options": ["40–50 bpm","60–100 bpm","110–130 bpm","130–160 bpm"],
             "answer": "60–100 bpm",
             "fact": "Athletes often have lower resting heart rates of around 40–60 bpm."},
        ]
    },

    # ── POLLS (Expression) ────────────────────────────────
    {
        "id": "p1", "type": "poll",
        "title": "Nigeria Hot Takes 🌶️",
        "desc": "Share your real opinion — see what others think instantly",
        "reward": 80, "xp": 8,
        "category": "Expression", "duration": "1 min", "icon": "🗣️",
        "questions": [
            {"q": "Be honest — is Jollof Rice better from Ghana or Nigeria?",
             "options": ["Nigeria, no contest 🇳🇬","Ghana, let's be real 🇬🇭","They're equal","I don't eat jollof"],
             "poll": True},
            {"q": "Which is more important right now?",
             "options": ["Cheaper fuel","Stable electricity","Better internet","Affordable food"],
             "poll": True},
            {"q": "Would you move abroad if you had the chance?",
             "options": ["Yes, immediately","Yes, but come back later","No, I love Nigeria","Still deciding"],
             "poll": True},
        ]
    },
    {
        "id": "p2", "type": "poll",
        "title": "Pop Culture Pulse ⚡",
        "desc": "Your takes on music, movies, and culture",
        "reward": 80, "xp": 8,
        "category": "Expression", "duration": "1 min", "icon": "🎭",
        "questions": [
            {"q": "Best Nigerian artist right now?",
             "options": ["Burna Boy","Wizkid","Davido","Asake"],
             "poll": True},
            {"q": "Best Nollywood streaming platform?",
             "options": ["Netflix","Prime Video","Showmax","YouTube"],
             "poll": True},
            {"q": "Which sport do Nigerians love most?",
             "options": ["Football","Boxing","Athletics","Basketball"],
             "poll": True},
        ]
    },
    {
        "id": "p3", "type": "poll",
        "title": "Work & Money Opinions 💸",
        "desc": "What do you really think about work and money?",
        "reward": 100, "xp": 10,
        "category": "Expression", "duration": "1 min", "icon": "💼",
        "questions": [
            {"q": "Remote work or office work?",
             "options": ["Remote, always","Office is better","Hybrid is best","Depends on the job"],
             "poll": True},
            {"q": "What would you do with an extra ₦100,000?",
             "options": ["Save it","Invest it","Start a business","Enjoy it"],
             "poll": True},
            {"q": "Side hustle or one salary?",
             "options": ["Multiple income streams","One solid job","Business owner life","Still figuring out"],
             "poll": True},
        ]
    },

    # ── CHALLENGES (Gaming) ───────────────────────────────
    {
        "id": "c1", "type": "challenge",
        "title": "Word Scramble Sprint 🎮",
        "desc": "Unscramble 5 words as fast as you can! Speed = bonus coins",
        "reward": 200, "xp": 20,
        "category": "Gaming", "duration": "2 min", "icon": "🔤",
        "words": [
            {"scrambled": "AGOLS",   "answer": "LAGOS",   "hint": "Nigeria's biggest city"},
            {"scrambled": "YENOM",   "answer": "MONEY",   "hint": "What everyone wants"},
            {"scrambled": "NRYAAI", "answer": "NAIRA",  "hint": "Nigerian currency... almost"},
            {"scrambled": "ANKB",    "answer": "BANK",    "hint": "Where you keep your money"},
            {"scrambled": "NOEPH",   "answer": "PHONE",   "hint": "You're using one right now"},
        ]
    },
    {
        "id": "c2", "type": "challenge",
        "title": "True or False Blitz ⚡",
        "desc": "Answer 6 rapid-fire true/false questions about Nigeria",
        "reward": 180, "xp": 18,
        "category": "Gaming", "duration": "2 min", "icon": "⚡",
        "pass_score": 4,
        "questions": [
            {"q": "Nigeria is the most populous country in Africa",
             "answer": "True",
             "fact": "With 220+ million people, Nigeria is Africa's most populous nation."},
            {"q": "The Naira symbol is ₦",
             "answer": "True",
             "fact": "The Naira sign ₦ was designed specifically for Nigerian currency."},
            {"q": "Abuja has always been Nigeria's capital",
             "answer": "False",
             "fact": "Lagos was the capital until 1991 when Abuja took over."},
            {"q": "Nigeria produces oil",
             "answer": "True",
             "fact": "Nigeria is one of Africa's top oil producers, mainly from the Niger Delta."},
            {"q": "Igbo, Yoruba and Hausa are Nigeria's three main languages",
             "answer": "True",
             "fact": "Nigeria has over 500 languages but these three are the most widely spoken."},
            {"q": "MTN is a Nigerian company",
             "answer": "False",
             "fact": "MTN was founded in South Africa in 1994, though it operates widely in Nigeria."},
        ]
    },
    {
        "id": "c3", "type": "challenge",
        "title": "Emoji Decode Challenge 😂",
        "desc": "What Nigerian phrase or thing does this emoji combo represent?",
        "reward": 150, "xp": 15,
        "category": "Gaming", "duration": "2 min", "icon": "😎",
        "questions": [
            {"q": "🍚🔥 = ?",
             "options": ["Jollof Rice","Fried Rice","Porridge","Rice and Stew"],
             "answer": "Jollof Rice",
             "fact": "Jollof Rice cooked on open fire is called 'Party Jollof' and is legendary!"},
            {"q": "🤑📱 = ?",
             "options": ["Mobile Banking","Buying a phone","Online Shopping","Airtime top-up"],
             "answer": "Mobile Banking",
             "fact": "Nigeria has one of Africa's fastest-growing mobile banking markets."},
            {"q": "🚌😅💨 = ?",
             "options": ["Lagos Traffic","Road Trip","Bus Station","Running late"],
             "answer": "Lagos Traffic",
             "fact": "Lagos traffic (Third Mainland Bridge especially) is legendary across Africa."},
            {"q": "⚽🇳🇬😍 = ?",
             "options": ["Super Eagles","AFCON","World Cup","Premier League"],
             "answer": "Super Eagles",
             "fact": "Nigeria's Super Eagles have won the Africa Cup of Nations three times."},
            {"q": "💃🥁🌙 = ?",
             "options": ["Afrobeats","Owambe Party","Church Service","Wedding"],
             "answer": "Owambe Party",
             "fact": "Owambe is a classic Nigerian party — loud music, aso-ebi, and lots of food!"},
        ]
    },
]

# ════════════════════════════════════════════════════════
#  LEVELS SYSTEM
# ════════════════════════════════════════════════════════
LEVELS = [
    {"level": 1, "name": "Starter",     "min_xp": 0,   "badge": "🌱"},
    {"level": 2, "name": "Explorer",    "min_xp": 50,  "badge": "🔍"},
    {"level": 3, "name": "Earner",      "min_xp": 120, "badge": "💰"},
    {"level": 4, "name": "Hustler",     "min_xp": 250, "badge": "🔥"},
    {"level": 5, "name": "Champion",    "min_xp": 450, "badge": "🏆"},
    {"level": 6, "name": "Legend",      "min_xp": 700, "badge": "⭐"},
]

def get_level(xp):
    for lv in reversed(LEVELS):
        if xp >= lv["min_xp"]:
            return lv
    return LEVELS[0]

def next_level(xp):
    current = get_level(xp)
    for lv in LEVELS:
        if lv["min_xp"] > xp:
            return lv
    return None  # max level

# ════════════════════════════════════════════════════════
#  AIRTIME REWARD TIERS  (for display)
# ════════════════════════════════════════════════════════
AIRTIME_TIERS = [
    {"amount": "₦50",  "kobo": 5000,  "icon": "📱"},
    {"amount": "₦100", "kobo": 10000, "icon": "📲"},
    {"amount": "₦200", "kobo": 20000, "icon": "🔋"},
    {"amount": "₦500", "kobo": 50000, "icon": "💎"},
]

# ════════════════════════════════════════════════════════
#  HTML TEMPLATE  (all pages in one file for beginners)
# ════════════════════════════════════════════════════════
HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>EarnNow – Play, Learn & Earn Real Money</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --gold:#F5C518;--gold2:#c9910a;--bg:#0d0d0d;--surface:#161616;
  --s2:#1e1e1e;--border:#272727;--text:#f0f0f0;--muted:#777;
  --green:#4ade80;--red:#f87171;--blue:#60a5fa;--purple:#a78bfa;--pink:#f472b6;
  --r:14px;
}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh}

/* ── NAV ── */
nav{position:sticky;top:0;z-index:200;background:rgba(13,13,13,.96);backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);padding:12px 20px;
  display:flex;justify-content:space-between;align-items:center;gap:12px}
.logo{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:var(--gold);cursor:pointer;white-space:nowrap}
.logo span{color:var(--text)}
.nav-right{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.bal-chip{background:var(--s2);border:1px solid var(--gold);color:var(--gold);
  font-weight:700;font-size:13px;padding:7px 14px;border-radius:30px;cursor:pointer}
.xp-chip{background:var(--s2);border:1px solid var(--purple);color:var(--purple);
  font-size:12px;padding:7px 12px;border-radius:30px}
.btn-sm{background:transparent;border:1px solid var(--border);color:var(--muted);
  padding:7px 14px;border-radius:8px;font-size:13px;cursor:pointer;transition:.2s}
.btn-sm:hover{color:var(--text);border-color:#444}

/* ── PAGES ── */
.page{display:none}.page.active{display:block}
.wrap{max-width:960px;margin:0 auto;padding:28px 16px}
.wrap-sm{max-width:540px;margin:0 auto;padding:28px 16px}

/* ── HERO ── */
.hero{background:linear-gradient(135deg,#1a1300 0%,#0d0d0d 55%);
  border:1px solid #2a1f00;border-radius:20px;padding:36px 24px;
  text-align:center;margin-bottom:32px;position:relative;overflow:hidden}
.hero::after{content:'';position:absolute;bottom:-40px;left:-40px;
  width:160px;height:160px;
  background:radial-gradient(circle,rgba(245,197,24,.08) 0%,transparent 70%);border-radius:50%}
.hero h1{font-family:'Syne',sans-serif;font-size:clamp(24px,5vw,38px);font-weight:800;line-height:1.15;margin-bottom:10px}
.hero h1 span{color:var(--gold)}
.hero p{color:var(--muted);font-size:15px;max-width:380px;margin:0 auto 24px}
.stats-row{display:flex;justify-content:center;gap:24px;flex-wrap:wrap}
.stat{text-align:center}
.stat-n{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;color:var(--gold);display:block}
.stat-l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px}

/* ── LEVEL BAR ── */
.level-row{display:flex;align-items:center;gap:12px;
  background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:14px 18px;margin-bottom:24px}
.level-badge{font-size:26px}
.level-info{flex:1}
.level-name{font-family:'Syne',sans-serif;font-weight:700;font-size:15px}
.level-sub{font-size:12px;color:var(--muted)}
.xp-bar{height:6px;background:#222;border-radius:10px;margin-top:6px}
.xp-fill{height:100%;background:linear-gradient(90deg,var(--purple),var(--blue));border-radius:10px;transition:width .5s ease}

/* ── TABS ── */
.tabs{display:flex;gap:8px;margin-bottom:24px;overflow-x:auto;padding-bottom:4px}
.tab-btn{flex-shrink:0;background:var(--surface);border:1px solid var(--border);
  color:var(--muted);padding:9px 16px;border-radius:30px;font-size:13px;
  font-weight:600;cursor:pointer;transition:.2s;white-space:nowrap}
.tab-btn.active{background:var(--gold);color:#111;border-color:var(--gold)}

/* ── CARDS ── */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  padding:20px;transition:.2s;position:relative;overflow:hidden}
.card:not(.done):hover{border-color:#3a2f00;transform:translateY(-2px)}
.card.done{opacity:.45;pointer-events:none}
.card-icon{font-size:28px;margin-bottom:10px;display:block}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.type-badge{font-size:10px;text-transform:uppercase;letter-spacing:1px;
  padding:3px 9px;border-radius:20px;font-weight:700}
.badge-survey{background:#1a2a1a;color:#4ade80}
.badge-quiz{background:#1a1a3a;color:#60a5fa}
.badge-poll{background:#2a1a2a;color:#f472b6}
.badge-challenge{background:#2a1a0a;color:#fb923c}
.reward-tag{font-family:'Syne',sans-serif;font-size:17px;font-weight:800;color:var(--gold)}
.card h3{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;margin-bottom:4px}
.card-desc{font-size:12px;color:var(--muted);margin-bottom:14px}
.card-meta{font-size:11px;color:#555;margin-bottom:14px}
.card-xp{font-size:11px;color:var(--purple);font-weight:600;margin-bottom:10px}
.btn-go{width:100%;background:var(--gold);color:#111;border:none;border-radius:10px;
  padding:11px;font-weight:700;font-size:14px;cursor:pointer;
  font-family:'Syne',sans-serif;transition:.2s}
.btn-go:hover{background:var(--gold2)}
.btn-done{background:#222;color:#555;cursor:default}

/* ── STREAK BANNER ── */
.streak-banner{background:linear-gradient(90deg,#2a1a00,#1a0a00);
  border:1px solid #3a2000;border-radius:12px;padding:14px 20px;
  display:flex;align-items:center;gap:12px;margin-bottom:24px}
.streak-fire{font-size:32px}
.streak-text{flex:1}
.streak-title{font-weight:700;font-size:15px;color:var(--gold)}
.streak-sub{font-size:12px;color:var(--muted);margin-top:2px}

/* ── TASK SCREEN ── */
.task-header{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.btn-back{background:var(--surface);border:1px solid var(--border);
  color:var(--muted);padding:8px 14px;border-radius:8px;cursor:pointer;font-size:13px}
.btn-back:hover{color:var(--text)}
.task-title-h{font-family:'Syne',sans-serif;font-size:15px;font-weight:700}
.prog-bar{height:5px;background:#1e1e1e;border-radius:10px;margin-bottom:6px}
.prog-fill{height:100%;background:var(--gold);border-radius:10px;transition:width .4s}
.prog-txt{font-size:11px;color:var(--muted);margin-bottom:24px}
.q-card{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:28px 24px}
.q-badge{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.q-text{font-family:'Syne',sans-serif;font-size:19px;font-weight:700;margin-bottom:20px;line-height:1.4}
.options{display:flex;flex-direction:column;gap:9px}
.opt-btn{background:var(--bg);border:1px solid var(--border);color:var(--text);
  padding:13px 18px;border-radius:10px;text-align:left;font-size:14px;
  cursor:pointer;transition:.15s;font-family:'Inter',sans-serif}
.opt-btn:hover{border-color:var(--gold);color:var(--gold);background:#1a1500}
.opt-btn.correct{border-color:var(--green);background:#0a1f0a;color:var(--green)}
.opt-btn.wrong{border-color:var(--red);background:#1f0a0a;color:var(--red)}
.opt-btn.revealed{border-color:#333}
.fact-box{background:#111;border:1px solid #222;border-radius:10px;
  padding:14px;margin-top:14px;font-size:13px;color:#aaa;line-height:1.5}
.fact-box strong{color:var(--blue)}
.btn-next{width:100%;background:var(--gold);color:#111;border:none;border-radius:10px;
  padding:13px;font-weight:700;font-size:15px;cursor:pointer;
  font-family:'Syne',sans-serif;margin-top:16px}
.reward-hint-bar{text-align:center;margin-top:16px;font-size:13px;color:var(--muted)}
.reward-hint-bar strong{color:var(--gold)}

/* ── WORD SCRAMBLE ── */
.scramble-word{font-family:'Syne',sans-serif;font-size:36px;font-weight:800;
  color:var(--gold);text-align:center;letter-spacing:8px;margin:20px 0}
.scramble-hint{text-align:center;font-size:13px;color:var(--muted);margin-bottom:20px}
.scramble-input{width:100%;background:var(--bg);border:2px solid var(--border);
  color:var(--text);padding:14px;border-radius:10px;font-size:18px;
  text-align:center;font-family:'Syne',sans-serif;letter-spacing:4px;
  text-transform:uppercase;outline:none;transition:.2s}
.scramble-input:focus{border-color:var(--gold)}
.scramble-input.right{border-color:var(--green);background:#0a1f0a}
.scramble-input.wrong{border-color:var(--red);background:#1f0a0a}

/* ── TRUE/FALSE ── */
.tf-btns{display:flex;gap:12px;margin-top:16px}
.tf-btn{flex:1;padding:18px;border:2px solid var(--border);border-radius:12px;
  background:var(--bg);color:var(--text);font-size:18px;font-weight:700;
  cursor:pointer;transition:.2s;font-family:'Syne',sans-serif}
.tf-btn:hover{transform:scale(1.02)}
.tf-btn.correct{border-color:var(--green);background:#0a1f0a;color:var(--green)}
.tf-btn.wrong{border-color:var(--red);background:#1f0a0a;color:var(--red)}

/* ── POLL RESULT BAR ── */
.poll-results{margin-top:14px}
.poll-opt-row{margin-bottom:10px}
.poll-opt-label{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px}
.poll-bar-track{height:8px;background:#1e1e1e;border-radius:10px}
.poll-bar-fill{height:100%;border-radius:10px;background:linear-gradient(90deg,var(--pink),var(--purple));transition:width .7s ease}
.poll-chosen{font-size:11px;color:var(--pink);font-weight:600;margin-top:2px}

/* ── RESULT SCREEN ── */
.result-box{text-align:center;background:var(--surface);border:1px solid var(--border);
  border-radius:20px;padding:44px 28px;margin-top:32px}
.result-emoji{font-size:56px;margin-bottom:16px}
.result-title{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;margin-bottom:8px}
.result-amount{font-family:'Syne',sans-serif;font-size:48px;font-weight:800;color:var(--gold);margin:10px 0}
.result-xp{color:var(--purple);font-weight:600;font-size:15px;margin-bottom:6px}
.result-score{font-size:14px;color:var(--muted);margin-bottom:20px}
.unlock-wrap{max-width:280px;margin:0 auto 20px}
.unlock-bar{height:6px;background:#222;border-radius:10px;margin:8px 0}
.unlock-fill{height:100%;background:var(--gold);border-radius:10px}
.unlock-note{font-size:12px;color:var(--muted)}
.result-btns{display:flex;flex-direction:column;gap:10px;max-width:280px;margin:0 auto}
.btn-gold{background:var(--gold);color:#111;border:none;border-radius:10px;
  padding:14px;font-weight:700;font-size:15px;cursor:pointer;
  font-family:'Syne',sans-serif;width:100%}
.btn-dark{background:var(--s2);color:var(--muted);border:1px solid var(--border);
  border-radius:10px;padding:14px;font-size:14px;font-weight:600;
  cursor:pointer;width:100%}
.level-up-banner{background:linear-gradient(90deg,#1a0a3a,#0a0a2a);
  border:1px solid var(--purple);border-radius:12px;padding:16px;
  text-align:center;margin-bottom:16px}
.level-up-banner h3{font-family:'Syne',sans-serif;color:var(--purple);font-size:18px;margin-bottom:4px}

/* ── WALLET ── */
.wallet-card{background:linear-gradient(135deg,#1a1300,#2a1f00);
  border:1px solid #3a2f00;border-radius:20px;padding:32px 24px;
  text-align:center;margin-bottom:20px}
.w-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:2px;margin-bottom:8px}
.w-balance{font-family:'Syne',sans-serif;font-size:44px;font-weight:800;color:var(--gold)}
.w-kobo{font-size:13px;color:#444;margin-top:4px}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  padding:22px;margin-bottom:14px}
.panel h3{font-family:'Syne',sans-serif;font-size:16px;margin-bottom:6px}
.panel-sub{font-size:12px;color:var(--muted);margin-bottom:16px}
.input-lbl{font-size:11px;color:var(--muted);text-transform:uppercase;
  letter-spacing:1px;margin-bottom:6px;display:block;margin-top:12px}
.inp{width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);
  padding:13px 15px;border-radius:10px;font-size:15px;outline:none;transition:.2s;
  font-family:'Inter',sans-serif}
.inp:focus{border-color:var(--gold)}
.withdraw-msg{font-size:13px;text-align:center;margin-top:10px;padding:10px;border-radius:8px}
.withdraw-msg.ok{color:var(--green);background:rgba(74,222,128,.07)}
.withdraw-msg.err{color:var(--red);background:rgba(248,113,113,.07)}
.airtime-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px}
.airtime-btn{background:var(--bg);border:1px solid var(--border);border-radius:10px;
  padding:14px;text-align:center;cursor:pointer;transition:.2s}
.airtime-btn:hover{border-color:var(--gold)}
.airtime-btn .a-icon{font-size:24px}
.airtime-btn .a-amt{font-family:'Syne',sans-serif;font-size:16px;font-weight:700;color:var(--gold)}
.airtime-btn .a-cost{font-size:11px;color:var(--muted);margin-top:2px}
.history-item{display:flex;justify-content:space-between;align-items:center;
  padding:11px 0;border-bottom:1px solid #1a1a1a;font-size:13px}
.history-item:last-child{border-bottom:none}
.h-earn{color:var(--green);font-weight:600}
.h-withdraw{color:var(--red);font-weight:600}
.h-airtime{color:var(--blue);font-weight:600}
.empty-state{text-align:center;color:#333;padding:20px 0;font-size:13px}

/* ── AUTH ── */
.auth-wrap{background:var(--surface);border:1px solid var(--border);
  border-radius:20px;padding:36px 28px;margin-top:48px}
.auth-wrap h2{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;margin-bottom:6px}
.auth-wrap p{color:var(--muted);font-size:14px;margin-bottom:22px}
.auth-tabs{display:flex;background:var(--bg);border-radius:10px;padding:4px;margin-bottom:22px}
.auth-tab{flex:1;padding:9px;border:none;background:transparent;
  color:var(--muted);border-radius:8px;cursor:pointer;font-size:14px;font-weight:600}
.auth-tab.active{background:var(--gold);color:#111}
.auth-err{color:var(--red);font-size:13px;margin-bottom:10px}

/* ── TOAST ── */
.toast{position:fixed;bottom:20px;right:20px;z-index:999;
  background:var(--s2);border:1px solid var(--border);color:var(--text);
  padding:13px 18px;border-radius:12px;font-size:14px;
  box-shadow:0 8px 32px rgba(0,0,0,.5);
  transform:translateY(80px);opacity:0;transition:.3s;max-width:290px}
.toast.show{transform:translateY(0);opacity:1}

/* ── LEADERBOARD ── */
.lb-item{display:flex;align-items:center;gap:12px;
  padding:12px 0;border-bottom:1px solid #1a1a1a;font-size:14px}
.lb-item:last-child{border-bottom:none}
.lb-rank{font-family:'Syne',sans-serif;font-weight:800;font-size:16px;
  color:var(--muted);width:28px;text-align:center}
.lb-rank.gold{color:var(--gold)}
.lb-rank.silver{color:#aaa}
.lb-rank.bronze{color:#cd7f32}
.lb-name{flex:1;font-weight:600}
.lb-score{color:var(--gold);font-weight:700}
.lb-badge{font-size:16px}

@media(max-width:540px){
  .hero{padding:26px 16px}
  .q-card{padding:22px 16px}
  .auth-wrap{padding:24px 18px}
  .result-box{padding:32px 18px}
}
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="logo" onclick="goHome()">Earn<span>Now</span></div>
  <div class="nav-right">
    <span class="xp-chip" id="nav-xp" style="display:none">⚡ 0 XP</span>
    <span class="bal-chip" id="nav-bal" onclick="showPage('wallet')" style="display:none">💰 ₦0.00</span>
    <button class="btn-sm" id="btn-signin" onclick="showPage('auth')">Sign In</button>
    <button class="btn-sm" id="btn-logout" onclick="logout()" style="display:none">Logout</button>
  </div>
</nav>

<div class="toast" id="toast"></div>

<!-- ══════════════ AUTH PAGE ══════════════ -->
<div class="page active" id="page-auth">
  <div class="wrap-sm">
    <div class="auth-wrap">
      <h2>🟡 EarnNow</h2>
      <p>Play quizzes, share opinions & earn real money.</p>
      <div class="auth-tabs">
        <button class="auth-tab active" id="tab-li" onclick="swTab('li')">Sign In</button>
        <button class="auth-tab" id="tab-reg" onclick="swTab('reg')">Register</button>
      </div>
      <div class="auth-err" id="auth-err" style="display:none"></div>
      <!-- Login -->
      <div id="form-li">
        <label class="input-lbl">Email</label>
        <input class="inp" id="li-email" type="email" placeholder="you@email.com"/>
        <label class="input-lbl">Password</label>
        <input class="inp" id="li-pass" type="password" placeholder="••••••••"/>
        <button class="btn-go" style="margin-top:18px" onclick="doLogin()">Sign In →</button>
      </div>
      <!-- Register -->
      <div id="form-reg" style="display:none">
        <label class="input-lbl">Full Name</label>
        <input class="inp" id="reg-name" type="text" placeholder="Your full name"/>
        <label class="input-lbl">Email</label>
        <input class="inp" id="reg-email" type="email" placeholder="you@email.com"/>
        <label class="input-lbl">Password</label>
        <input class="inp" id="reg-pass" type="password" placeholder="Min 6 characters"/>
        <button class="btn-go" style="margin-top:18px" onclick="doRegister()">Create Account →</button>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════ HOME PAGE ══════════════ -->
<div class="page" id="page-home">
  <div class="wrap">
    <!-- HERO -->
    <div class="hero">
      <h1>Play. Learn. Express.<br/><span>Earn Real Money.</span></h1>
      <p>Quizzes, polls, challenges & surveys — get paid in naira for every task you complete.</p>
      <div class="stats-row">
        <div class="stat"><span class="stat-n" id="h-bal">₦0.00</span><span class="stat-l">Balance</span></div>
        <div class="stat"><span class="stat-n" id="h-done">0</span><span class="stat-l">Completed</span></div>
        <div class="stat"><span class="stat-n" id="h-streak">0🔥</span><span class="stat-l">Day Streak</span></div>
        <div class="stat"><span class="stat-n" id="h-xp">0</span><span class="stat-l">XP</span></div>
      </div>
    </div>

    <!-- LEVEL BAR -->
    <div class="level-row" id="level-row">
      <div class="level-badge" id="lv-badge">🌱</div>
      <div class="level-info">
        <div class="level-name" id="lv-name">Level 1 — Starter</div>
        <div class="level-sub" id="lv-sub">Keep earning XP to level up!</div>
        <div class="xp-bar"><div class="xp-fill" id="xp-fill" style="width:0%"></div></div>
      </div>
    </div>

    <!-- STREAK BANNER -->
    <div class="streak-banner" id="streak-banner" style="display:none">
      <div class="streak-fire">🔥</div>
      <div class="streak-text">
        <div class="streak-title" id="streak-title">3-Day Streak!</div>
        <div class="streak-sub">Keep going — log in and complete a task tomorrow to keep it alive</div>
      </div>
    </div>

    <!-- FILTER TABS -->
    <div class="tabs">
      <button class="tab-btn active" onclick="filterTasks('all',this)">All Tasks</button>
      <button class="tab-btn" onclick="filterTasks('survey',this)">📋 Surveys</button>
      <button class="tab-btn" onclick="filterTasks('quiz',this)">🧠 Learn</button>
      <button class="tab-btn" onclick="filterTasks('challenge',this)">🎮 Games</button>
      <button class="tab-btn" onclick="filterTasks('poll',this)">🗣️ Express</button>
    </div>

    <div class="cards" id="cards-grid"></div>

    <!-- LEADERBOARD -->
    <div class="panel" style="margin-top:28px">
      <h3>🏆 Top Earners This Week</h3>
      <div id="leaderboard"></div>
    </div>
  </div>
</div>

<!-- ══════════════ TASK PAGE ══════════════ -->
<div class="page" id="page-task">
  <div class="wrap-sm">
    <div class="task-header">
      <button class="btn-back" onclick="goHome()">← Back</button>
      <span class="task-title-h" id="task-name-lbl"></span>
    </div>
    <div class="prog-bar"><div class="prog-fill" id="prog-fill"></div></div>
    <p class="prog-txt" id="prog-txt"></p>

    <!-- STANDARD Q (survey/quiz/poll) -->
    <div id="standard-task">
      <div class="q-card">
        <div class="q-badge" id="q-badge">Question</div>
        <p class="q-text" id="q-text"></p>
        <div class="options" id="opts"></div>
        <div class="fact-box" id="fact-box" style="display:none"></div>
        <button class="btn-next" id="btn-next" onclick="nextStep()" style="display:none">Next →</button>
      </div>
      <p class="reward-hint-bar">Reward: <strong id="task-reward-lbl"></strong></p>
    </div>

    <!-- SCRAMBLE TASK -->
    <div id="scramble-task" style="display:none">
      <div class="q-card">
        <div class="q-badge">Word Scramble</div>
        <p class="q-text" id="scr-badge"></p>
        <div class="scramble-word" id="scr-word"></div>
        <div class="scramble-hint" id="scr-hint"></div>
        <input class="scramble-input" id="scr-input" type="text" placeholder="TYPE YOUR ANSWER"
               oninput="this.value=this.value.toUpperCase()" onkeydown="if(event.key==='Enter')checkScramble()"/>
        <button class="btn-next" onclick="checkScramble()" style="margin-top:12px">Check Answer</button>
        <div class="fact-box" id="scr-fact" style="display:none"></div>
        <button class="btn-next" id="scr-next" onclick="nextStep()" style="display:none">Next Word →</button>
      </div>
      <p class="reward-hint-bar">Reward: <strong id="scr-reward-lbl"></strong></p>
    </div>

    <!-- TRUE/FALSE TASK -->
    <div id="tf-task" style="display:none">
      <div class="q-card">
        <div class="q-badge">True or False ⚡</div>
        <p class="q-text" id="tf-q"></p>
        <div class="tf-btns">
          <button class="tf-btn" id="tf-true"  onclick="checkTF('True')">✅ True</button>
          <button class="tf-btn" id="tf-false" onclick="checkTF('False')">❌ False</button>
        </div>
        <div class="fact-box" id="tf-fact" style="display:none"></div>
        <button class="btn-next" id="tf-next" onclick="nextStep()" style="display:none">Next →</button>
      </div>
      <p class="reward-hint-bar">Reward: <strong id="tf-reward-lbl"></strong></p>
    </div>
  </div>
</div>

<!-- ══════════════ RESULT PAGE ══════════════ -->
<div class="page" id="page-result">
  <div class="wrap-sm">
    <div class="result-box">
      <div id="level-up-banner" class="level-up-banner" style="display:none">
        <h3 id="lup-text">🎉 Level Up!</h3>
        <p id="lup-sub" style="color:var(--muted);font-size:13px"></p>
      </div>
      <div class="result-emoji" id="res-emoji">🎉</div>
      <h2 class="result-title" id="res-title">Task Complete!</h2>
      <div class="result-xp" id="res-xp">+10 XP</div>
      <p style="color:var(--muted);font-size:14px">You earned</p>
      <div class="result-amount" id="res-amount">₦0.00</div>
      <div class="result-score" id="res-score"></div>
      <div class="unlock-wrap">
        <div class="unlock-bar"><div class="unlock-fill" id="unlock-fill" style="width:0%"></div></div>
        <p class="unlock-note" id="unlock-note"></p>
      </div>
      <div class="result-btns">
        <button class="btn-gold" id="res-withdraw" onclick="showPage('wallet')" style="display:none">💸 Withdraw Now</button>
        <button class="btn-dark" onclick="goHome()">← More Tasks</button>
      </div>
    </div>
  </div>
</div>

<!-- ══════════════ WALLET PAGE ══════════════ -->
<div class="page" id="page-wallet">
  <div class="wrap-sm">
    <button class="btn-back" onclick="goHome()" style="margin-bottom:18px">← Back</button>

    <div class="wallet-card">
      <p class="w-label">Available Balance</p>
      <div class="w-balance" id="w-bal">₦0.00</div>
      <p class="w-kobo" id="w-kobo">0 kobo</p>
    </div>

    <!-- AIRTIME PANEL -->
    <div class="panel">
      <h3>📱 Redeem Airtime</h3>
      <p class="panel-sub">Swap your earnings for airtime top-up on any network</p>
      <div class="airtime-grid" id="airtime-grid"></div>
      <label class="input-lbl">Your Phone Number</label>
      <input class="inp" id="airtime-phone" type="tel" placeholder="08012345678"/>
      <label class="input-lbl">Select Network</label>
      <select class="inp" id="airtime-network">
        <option value="MTN">MTN</option>
        <option value="Airtel">Airtel</option>
        <option value="Glo">Glo</option>
        <option value="9mobile">9mobile</option>
      </select>
      <button class="btn-go" style="margin-top:14px" onclick="redeemAirtime()">Redeem Airtime →</button>
      <div id="airtime-msg"></div>
    </div>

    <!-- BANK WITHDRAWAL PANEL -->
    <div class="panel">
      <h3>🏦 Withdraw to Bank</h3>
      <p class="panel-sub">Minimum ₦1,000 · Sent within 24hrs via Paystack</p>
      <label class="input-lbl">Account Number</label>
      <input class="inp" id="w-acct" type="text" placeholder="0123456789"/>
      <label class="input-lbl">Bank Name</label>
      <input class="inp" id="w-bank" type="text" placeholder="e.g. GTBank, Access, Zenith"/>
      <label class="input-lbl">Amount (₦)</label>
      <input class="inp" id="w-amt" type="number" placeholder="1000"/>
      <button class="btn-go" style="margin-top:14px" onclick="doWithdraw()">Withdraw →</button>
      <div id="withdraw-msg"></div>
    </div>

    <!-- HISTORY -->
    <div class="panel">
      <h3>📜 Transaction History</h3>
      <div id="history-list"></div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════
     JAVASCRIPT
══════════════════════════════════════════ -->
<script>
const TASKS    = {{ tasks_json|safe }};
const LEVELS   = {{ levels_json|safe }};
const AIRTIME  = {{ airtime_json|safe }};
const MIN_W    = 100000; // kobo

// ── STATE ──
let S = {
  user:null, balance:0, completed:[], history:[],
  xp:0, streak:0, last_active:null
};
let active = null;   // current task
let step   = 0;
let score  = 0;
let answers= {};
let selectedAirtime = null;

// ── UTILS ──
const toN = k => '₦' + (k/100).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g,',');
const $ = id => document.getElementById(id);
function toast(msg){
  const t=$('toast'); t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),3000);
}
function showPage(name){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  $('page-'+name).classList.add('active');
  if(name==='home') renderHome();
  if(name==='wallet') renderWallet();
}
function goHome(){ showPage('home'); }

// ── AUTH ──
function swTab(t){
  $('form-li').style.display  = t==='li'?'block':'none';
  $('form-reg').style.display = t==='reg'?'block':'none';
  $('tab-li').className  = 'auth-tab'+(t==='li'?' active':'');
  $('tab-reg').className = 'auth-tab'+(t==='reg'?' active':'');
  $('auth-err').style.display='none';
}
async function doLogin(){
  const r = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({email:$('li-email').value.trim(),password:$('li-pass').value})});
  const d = await r.json();
  if(d.error){showErr(d.error);return;}
  applyUser(d); showPage('home');
}
async function doRegister(){
  const r = await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:$('reg-name').value.trim(),
      email:$('reg-email').value.trim(),password:$('reg-pass').value})});
  const d = await r.json();
  if(d.error){showErr(d.error);return;}
  applyUser(d); showPage('home'); toast('Welcome to EarnNow! 🎉');
}
function applyUser(d){
  S = {user:d, balance:d.balance, completed:d.completed||[],
       history:d.history||[], xp:d.xp||0, streak:d.streak||0, last_active:d.last_active};
  $('btn-signin').style.display='none';
  $('btn-logout').style.display='block';
  $('nav-bal').style.display='flex';
  $('nav-xp').style.display='flex';
  updateNav();
}
function updateNav(){
  $('nav-bal').textContent = '💰 ' + toN(S.balance);
  $('nav-xp').textContent  = '⚡ ' + S.xp + ' XP';
}
async function logout(){
  await fetch('/api/logout',{method:'POST'});
  S={user:null,balance:0,completed:[],history:[],xp:0,streak:0};
  $('btn-signin').style.display='block';
  $('btn-logout').style.display='none';
  $('nav-bal').style.display='none';
  $('nav-xp').style.display='none';
  showPage('auth');
}
function showErr(msg){$('auth-err').textContent=msg;$('auth-err').style.display='block';}

// ── HOME ──
function getLevelInfo(xp){
  let cur=LEVELS[0];
  for(const lv of LEVELS) if(xp>=lv.min_xp) cur=lv;
  return cur;
}
function getNextLevel(xp){
  for(const lv of LEVELS) if(lv.min_xp>xp) return lv;
  return null;
}
function renderHome(){
  $('h-bal').textContent   = toN(S.balance);
  $('h-done').textContent  = S.completed.length;
  $('h-streak').textContent= S.streak+'🔥';
  $('h-xp').textContent    = S.xp;

  // level bar
  const lv   = getLevelInfo(S.xp);
  const nxt  = getNextLevel(S.xp);
  $('lv-badge').textContent = lv.badge;
  $('lv-name').textContent  = `Level ${lv.level} — ${lv.name}`;
  if(nxt){
    const pct = Math.round(((S.xp - lv.min_xp)/(nxt.min_xp - lv.min_xp))*100);
    $('lv-sub').textContent  = `${S.xp} / ${nxt.min_xp} XP to ${nxt.name}`;
    $('xp-fill').style.width = pct+'%';
  } else {
    $('lv-sub').textContent='Maximum level reached! 🏆';
    $('xp-fill').style.width='100%';
  }

  // streak banner
  if(S.streak>=2){
    $('streak-banner').style.display='flex';
    $('streak-title').textContent = S.streak+'-Day Streak! 🔥';
  }

  renderCards('all');
  renderLeaderboard();
  renderAirtimeGrid();
}
function filterTasks(type, btn){
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderCards(type);
}
function renderCards(filter){
  const grid = $('cards-grid');
  const tasks = filter==='all' ? TASKS : TASKS.filter(t=>t.type===filter);
  const typeLabel = {survey:'📋 Survey',quiz:'🧠 Learning',poll:'🗣️ Express',challenge:'🎮 Game'};
  const typeCls   = {survey:'badge-survey',quiz:'badge-quiz',poll:'badge-poll',challenge:'badge-challenge'};
  grid.innerHTML = tasks.map(t=>{
    const done = S.completed.includes(t.id);
    return `<div class="card ${done?'done':''}">
      <div class="card-top">
        <span class="type-badge ${typeCls[t.type]}">${typeLabel[t.type]}</span>
        <span class="reward-tag">${toN(t.reward)}</span>
      </div>
      <span class="card-icon">${t.icon}</span>
      <h3>${t.title}</h3>
      <p class="card-desc">${t.desc}</p>
      <p class="card-meta">⏱ ${t.duration}</p>
      <p class="card-xp">+${t.xp} XP</p>
      <button class="btn-go ${done?'btn-done':''}" onclick="startTask('${t.id}')">
        ${done?'✓ Completed':'Start →'}
      </button>
    </div>`;
  }).join('');
}
function renderLeaderboard(){
  const entries = [
    {name:'Chioma O.',  score:4800, badge:'🏆'},
    {name:'Emeka D.',   score:3650, badge:'🔥'},
    {name:'Fatima A.',  score:2900, badge:'⭐'},
    {name:'Tunde B.',   score:2100, badge:'💰'},
    {name:'Ngozi K.',   score:1750, badge:'🌟'},
  ];
  if(S.user) entries.push({name:'You 👤', score:S.balance, badge:'🟡'});
  entries.sort((a,b)=>b.score-a.score);
  $('leaderboard').innerHTML = entries.slice(0,6).map((e,i)=>{
    const cls = i===0?'gold':i===1?'silver':i===2?'bronze':'';
    return `<div class="lb-item">
      <span class="lb-rank ${cls}">${i+1}</span>
      <span class="lb-badge">${e.badge}</span>
      <span class="lb-name">${e.name}</span>
      <span class="lb-score">${toN(e.score)}</span>
    </div>`;
  }).join('');
}
function renderAirtimeGrid(){
  $('airtime-grid').innerHTML = AIRTIME.map((a,i)=>`
    <div class="airtime-btn" id="at-${i}" onclick="selectAirtime(${i})">
      <div class="a-icon">${a.icon}</div>
      <div class="a-amt">${a.amount}</div>
      <div class="a-cost">Costs ${toN(a.kobo)}</div>
    </div>`).join('');
}
function selectAirtime(i){
  document.querySelectorAll('.airtime-btn').forEach(b=>b.style.borderColor='');
  $('at-'+i).style.borderColor='var(--gold)';
  selectedAirtime = AIRTIME[i];
}

// ── START TASK ──
function startTask(id){
  if(!S.user){showPage('auth');return;}
  active = TASKS.find(t=>t.id===id);
  if(!active||S.completed.includes(id)) return;
  step=0; score=0; answers={};
  showPage('task');
  renderStep();
}

function renderStep(){
  $('task-name-lbl').textContent = active.title;
  const total = active.type==='challenge'&&active.words
    ? active.words.length : active.questions.length;
  $('prog-fill').style.width = Math.round((step/total)*100)+'%';
  $('prog-txt').textContent  = `Step ${step+1} of ${total}`;

  // hide all sub-tasks
  $('standard-task').style.display='none';
  $('scramble-task').style.display='none';
  $('tf-task').style.display='none';

  if(active.type==='challenge'&&active.words){
    renderScramble();
  } else if(active.id==='c2'){
    renderTF();
  } else {
    renderStandardQ();
  }
}

// ── STANDARD Q (survey / quiz / poll) ──
function renderStandardQ(){
  $('standard-task').style.display='block';
  const q = active.questions[step];
  const isPoll = active.type==='poll';
  const isQuiz = active.type==='quiz';
  $('q-badge').textContent = isPoll?'🗣️ Vote Now':isQuiz?'🧠 Question':'📋 Question';
  $('q-text').textContent  = q.q;
  $('task-reward-lbl').textContent = toN(active.reward);
  $('fact-box').style.display='none';
  $('btn-next').style.display='none';
  $('opts').innerHTML = q.options.map(o=>`
    <button class="opt-btn" onclick="pickOpt(this,'${o.replace(/'/g,"\\'")}')">
      ${isPoll?'→ ':''}${o}
    </button>`).join('');
}
function pickOpt(btn, val){
  const q = active.questions[step];
  if(active.type==='quiz'&&q.answer){
    // reveal correct/wrong
    document.querySelectorAll('#opts .opt-btn').forEach(b=>{
      b.classList.add('revealed'); b.disabled=true;
    });
    if(val===q.answer){ btn.classList.add('correct'); score++; }
    else              { btn.classList.add('wrong');
      document.querySelectorAll('#opts .opt-btn')
        .forEach(b=>{ if(b.textContent.trim()===q.answer) b.classList.add('correct'); });
    }
    if(q.fact){
      $('fact-box').innerHTML=`<strong>💡 Fun Fact:</strong> ${q.fact}`;
      $('fact-box').style.display='block';
    }
    $('btn-next').style.display='block';
  } else if(active.type==='poll'){
    // show simulated poll results
    document.querySelectorAll('#opts .opt-btn').forEach(b=>b.disabled=true);
    const fakePcts = simulatePoll(q.options, val);
    $('opts').innerHTML = q.options.map((o,i)=>`
      <div class="poll-opt-row">
        <div class="poll-opt-label">
          <span>${o}</span><span>${fakePcts[i]}%</span>
        </div>
        <div class="poll-bar-track">
          <div class="poll-bar-fill" style="width:${fakePcts[i]}%"></div>
        </div>
        ${o===val?'<div class="poll-chosen">← Your vote</div>':''}
      </div>`).join('');
    $('btn-next').textContent='Next →';
    $('btn-next').style.display='block';
  } else {
    // plain survey — just move on
    answers[step]=val;
    nextStep();
    return;
  }
  answers[step]=val;
}
function simulatePoll(opts, chosen){
  const rands = opts.map(()=>Math.floor(Math.random()*40)+10);
  const chosenIdx = opts.indexOf(chosen);
  rands[chosenIdx] += 30;
  const total = rands.reduce((a,b)=>a+b,0);
  return rands.map(r=>Math.round((r/total)*100));
}

// ── SCRAMBLE ──
function renderScramble(){
  $('scramble-task').style.display='block';
  const w = active.words[step];
  $('scr-badge').textContent = `Word ${step+1} of ${active.words.length}`;
  $('scr-word').textContent  = w.scrambled;
  $('scr-hint').textContent  = '💬 Hint: ' + w.hint;
  $('scr-reward-lbl').textContent = toN(active.reward);
  $('scr-input').value=''; $('scr-input').className='scramble-input';
  $('scr-fact').style.display='none'; $('scr-next').style.display='none';
  setTimeout(()=>$('scr-input').focus(),100);
}
function checkScramble(){
  const w = active.words[step];
  const val = $('scr-input').value.trim().toUpperCase();
  if(val===w.answer){
    $('scr-input').className='scramble-input right'; score++;
    $('scr-fact').innerHTML='<strong>✅ Correct!</strong>';
  } else {
    $('scr-input').className='scramble-input wrong';
    $('scr-fact').innerHTML=`<strong>❌ Answer was: ${w.answer}</strong>`;
  }
  $('scr-fact').style.display='block';
  $('scr-input').disabled=true;
  $('scr-next').textContent = step+1<active.words.length ? 'Next Word →' : 'See Results →';
  $('scr-next').style.display='block';
}

// ── TRUE/FALSE ──
function renderTF(){
  $('tf-task').style.display='block';
  const q = active.questions[step];
  $('tf-q').textContent = q.q;
  $('tf-reward-lbl').textContent = toN(active.reward);
  $('tf-true').className='tf-btn'; $('tf-false').className='tf-btn';
  $('tf-true').disabled=false; $('tf-false').disabled=false;
  $('tf-fact').style.display='none'; $('tf-next').style.display='none';
}
function checkTF(val){
  const q = active.questions[step];
  $('tf-true').disabled=true; $('tf-false').disabled=true;
  if(val===q.answer){
    (val==='True'?$('tf-true'):$('tf-false')).classList.add('correct'); score++;
  } else {
    (val==='True'?$('tf-true'):$('tf-false')).classList.add('wrong');
    (q.answer==='True'?$('tf-true'):$('tf-false')).classList.add('correct');
  }
  if(q.fact){$('tf-fact').innerHTML=`<strong>💡</strong> ${q.fact}`;$('tf-fact').style.display='block';}
  answers[step]=val;
  $('tf-next').textContent = step+1<active.questions.length?'Next →':'See Results →';
  $('tf-next').style.display='block';
}

// ── NEXT STEP / SUBMIT ──
function nextStep(){
  const total = active.words ? active.words.length : active.questions.length;
  step++;
  if(step < total){ renderStep(); }
  else             { submitTask(); }
}
async function submitTask(){
  const res = await fetch('/api/complete',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({task_id:active.id,answers,score})});
  const d = await res.json();
  if(d.error){toast('Error: '+d.error);return;}
  const oldXP = S.xp;
  S.balance=d.balance; S.completed=d.completed; S.history=d.history;
  S.xp=d.xp; S.streak=d.streak;
  updateNav();
  showResult(oldXP);
}

// ── RESULT ──
function showResult(oldXP){
  const isQuiz = active.type==='quiz'||active.id==='c2';
  const isGame = active.type==='challenge';
  const total  = active.words?active.words.length:active.questions?active.questions.length:1;
  const emoji  = score===total?'🏆':isGame?'🎮':active.type==='poll'?'🗣️':active.type==='quiz'?'🧠':'🎉';
  $('res-emoji').textContent = emoji;
  $('res-title').textContent = score===total&&isQuiz?'Perfect Score!':'Task Complete!';
  $('res-xp').textContent    = '+'+active.xp+' XP earned';
  $('res-amount').textContent= toN(active.reward);
  if(isQuiz||isGame){
    $('res-score').textContent = `Score: ${score}/${total}`;
  } else { $('res-score').textContent=''; }

  // level up check
  const prevLv = getLevelInfo(oldXP);
  const newLv  = getLevelInfo(S.xp);
  if(newLv.level > prevLv.level){
    $('level-up-banner').style.display='block';
    $('lup-text').textContent = newLv.badge+' Level Up! → '+newLv.name;
    $('lup-sub').textContent  = 'You reached Level '+newLv.level;
  } else { $('level-up-banner').style.display='none'; }

  const pct = Math.min(100,Math.round((S.balance/MIN_W)*100));
  $('unlock-fill').style.width = pct+'%';
  if(S.balance>=MIN_W){
    $('unlock-note').textContent='🎉 Withdrawal unlocked!';
    $('res-withdraw').style.display='block';
  } else {
    $('unlock-note').textContent='Earn '+toN(MIN_W-S.balance)+' more to unlock withdrawal';
    $('res-withdraw').style.display='none';
  }
  showPage('result');
}

// ── WALLET ──
function renderWallet(){
  $('w-bal').textContent  = toN(S.balance);
  $('w-kobo').textContent = S.balance+' kobo';
  renderAirtimeGrid();
  const hist = $('history-list');
  if(!S.history||S.history.length===0){
    hist.innerHTML='<p class="empty-state">No transactions yet.</p>';
  } else {
    hist.innerHTML = [...S.history].reverse().map(h=>`
      <div class="history-item">
        <div>
          <div style="font-weight:600">${h.title}</div>
          <div style="font-size:11px;color:var(--muted)">${h.date}</div>
        </div>
        <span class="${h.type==='earn'?'h-earn':h.type==='airtime'?'h-airtime':'h-withdraw'}">
          ${h.type==='earn'?'+':'−'}${toN(h.amount)}
        </span>
      </div>`).join('');
  }
}
async function redeemAirtime(){
  if(!selectedAirtime){toast('Please select an airtime amount first');return;}
  const phone   = $('airtime-phone').value.trim();
  const network = $('airtime-network').value;
  if(!phone||phone.length<10){showAirtimeMsg('Please enter a valid phone number','err');return;}
  if(selectedAirtime.kobo>S.balance){showAirtimeMsg('Insufficient balance','err');return;}
  const r = await fetch('/api/airtime',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({amount_kobo:selectedAirtime.kobo,phone,network})});
  const d = await r.json();
  if(d.error){showAirtimeMsg(d.error,'err');return;}
  S.balance=d.balance; S.history=d.history;
  updateNav(); renderWallet();
  showAirtimeMsg(`✅ ${selectedAirtime.amount} airtime sent to ${phone} (${network})!`,'ok');
  toast('Airtime sent! 📱');
}
function showAirtimeMsg(msg,cls){
  const el=$('airtime-msg');
  el.className='withdraw-msg '+cls; el.textContent=msg;
}
async function doWithdraw(){
  const acct = $('w-acct').value.trim();
  const bank = $('w-bank').value.trim();
  const amt  = parseFloat($('w-amt').value);
  if(!acct||!bank||!amt){showWMsg('Please fill all fields','err');return;}
  if(amt<1000){showWMsg('Minimum withdrawal is ₦1,000','err');return;}
  const amtK = Math.round(amt*100);
  if(amtK>S.balance){showWMsg('Insufficient balance','err');return;}
  const r = await fetch('/api/withdraw',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({amount_kobo:amtK,account:acct,bank})});
  const d = await r.json();
  if(d.error){showWMsg(d.error,'err');return;}
  S.balance=d.balance; S.history=d.history;
  updateNav(); renderWallet(); $('w-amt').value='';
  showWMsg(`✅ ₦${amt.toFixed(2)} withdrawal sent to ${bank} – ${acct}`,'ok');
  toast('Withdrawal submitted! 💸');
}
function showWMsg(msg,cls){
  const el=$('withdraw-msg');
  el.className='withdraw-msg '+cls; el.textContent=msg;
}

// ── INIT ──
(async function init(){
  const r = await fetch('/api/me');
  const d = await r.json();
  if(d.user){ applyUser(d.user); showPage('home'); }
})();
</script>
</body>
</html>
"""

# ════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template_string(
        HTML,
        tasks_json=json.dumps(TASKS),
        levels_json=json.dumps(LEVELS),
        airtime_json=json.dumps(AIRTIME_TIERS)
    )

@app.route("/api/register", methods=["POST"])
def api_register():
    d = request.json
    email = d.get("email","").lower().strip()
    if not email or not d.get("password") or not d.get("name"):
        return jsonify({"error": "All fields required"}), 400
    if email in users_db:
        return jsonify({"error": "Email already registered"}), 400
    users_db[email] = {
        "id": str(uuid.uuid4()), "name": d["name"],
        "email": email, "password": d["password"],
        "balance": 0, "xp": 0, "streak": 0,
        "last_active": str(date.today()),
        "completed": [], "history": []
    }
    session["ue"] = email
    return jsonify(_pub(users_db[email]))

@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.json
    email = d.get("email","").lower().strip()
    u = users_db.get(email)
    if not u or u["password"] != d.get("password"):
        return jsonify({"error": "Wrong email or password"}), 401
    _update_streak(u)
    session["ue"] = email
    return jsonify(_pub(u))

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/me")
def api_me():
    u = users_db.get(session.get("ue"))
    return jsonify({"user": _pub(u) if u else None})

@app.route("/api/complete", methods=["POST"])
def api_complete():
    u = users_db.get(session.get("ue"))
    if not u: return jsonify({"error": "Not logged in"}), 401
    d = request.json
    tid = d.get("task_id")
    if tid in u["completed"]: return jsonify({"error": "Already completed"}), 400
    task = next((t for t in TASKS if t["id"] == tid), None)
    if not task: return jsonify({"error": "Task not found"}), 404

    u["balance"]  += task["reward"]
    u["xp"]       += task["xp"]
    u["completed"].append(tid)
    u["history"].append({
        "title":  task["title"],
        "amount": task["reward"],
        "type":   "earn",
        "date":   datetime.now().strftime("%d %b %Y, %I:%M %p")
    })
    responses_db[f"{u['email']}_{tid}"] = d.get("answers", {})
    _update_streak(u)
    return jsonify({**_pub(u)})

@app.route("/api/airtime", methods=["POST"])
def api_airtime():
    u = users_db.get(session.get("ue"))
    if not u: return jsonify({"error": "Not logged in"}), 401
    d = request.json
    amt = d.get("amount_kobo", 0)
    if amt > u["balance"]: return jsonify({"error": "Insufficient balance"}), 400
    u["balance"] -= amt
    u["history"].append({
        "title":  f"Airtime — {d.get('network','?')} {d.get('phone','')}",
        "amount": amt,
        "type":   "airtime",
        "date":   datetime.now().strftime("%d %b %Y, %I:%M %p")
    })
    # In production: call VTPass / Nellobytes airtime API here
    return jsonify({**_pub(u)})

@app.route("/api/withdraw", methods=["POST"])
def api_withdraw():
    u = users_db.get(session.get("ue"))
    if not u: return jsonify({"error": "Not logged in"}), 401
    d = request.json
    amt = d.get("amount_kobo", 0)
    if amt < MIN_WITHDRAW_KOBO:
        return jsonify({"error": f"Minimum withdrawal is ₦{MIN_WITHDRAW_KOBO//100:,}"}), 400
    if amt > u["balance"]:
        return jsonify({"error": "Insufficient balance"}), 400
    u["balance"] -= amt
    u["history"].append({
        "title":  f"Withdrawal → {d.get('bank','?')} {d.get('account','')}",
        "amount": amt,
        "type":   "withdraw",
        "date":   datetime.now().strftime("%d %b %Y, %I:%M %p")
    })
    # In production: call Paystack /transfer API here
    return jsonify({**_pub(u)})

# ── HELPERS ──
def _pub(u):
    return {
        "id": u["id"], "name": u["name"], "email": u["email"],
        "balance": u["balance"], "xp": u["xp"], "streak": u["streak"],
        "last_active": u["last_active"],
        "completed": u["completed"], "history": u["history"]
    }

def _update_streak(u):
    today = str(date.today())
    last  = u.get("last_active")
    if last == today:
        return
    from datetime import timedelta
    yesterday = str(date.today() - timedelta(days=1))
    if last == yesterday:
        u["streak"] = u.get("streak", 0) + 1
    else:
        u["streak"] = 1
    u["last_active"] = today

if __name__ == "__main__":
    app.run(debug=True, port=5000)