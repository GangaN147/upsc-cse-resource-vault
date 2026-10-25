import os
import time
import pandas as pd
import requests

# Fetch credentials securely from GitHub Actions Secrets
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# Load local CSV from the repository
CSV_FILE = "upsc_polity_pyqs_1991_2026_master.csv"
df = pd.read_csv(CSV_FILE)

current_topic = None
total_questions = len(df)
topic_links = {}

print(
    f"🚀 GitHub Action started: Syncing {total_questions} Polity PYQs to"
    f" Telegram...\n"
)

for index, row in df.iterrows():
  q_num = index + 1
  q_id = str(row["Q_ID"]).strip()
  year = str(row["Year"]).strip()
  subject = str(row["Subject"]).strip()
  topic = str(row["Topic"]).strip()
  day_target = str(row["Day_Target"]).strip()
  raw_question = str(row["Question"]).strip()

  clean_question = raw_question.replace(f"[UPSC {year}]", "").strip()
  correct_id = int(row["Correct_Option"])
  explanation = str(row["Explanation"]).strip()[:195]

  options = [
      str(row["Option_A"]).strip(),
      str(row["Option_B"]).strip(),
      str(row["Option_C"]).strip(),
      str(row["Option_D"]).strip(),
  ]

  # Post Topic Divider Banner when a new Sub-Topic begins
  if topic != current_topic:
    current_topic = topic
    header_banner = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ SUBJECT: {subject}\n"
        f"📂 TOPIC: {topic}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    banner_res = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHANNEL_ID, "text": header_banner},
    ).json()

    if banner_res.get("ok"):
      msg_id = banner_res["result"]["message_id"]
      topic_links[topic] = msg_id
    time.sleep(2.5)

  # Premium Web Card Formatting (Continuous Numbering + Year Badge)
  card_header = (
      f"┌─────────────────────────────────┐\n"
      f"│ 🎯 UPSC PRELIMS MASTER VAULT    │\n"
      f"└─────────────────────────────────┘\n"
      f"🔢 **Question {q_num} of {total_questions}** | 📅 **UPSC {year}** ({q_id})\n"
      f"🎯 **Target:** {day_target}\n"
      f"───────────────────────────────────\n\n"
      f"{clean_question}"
  )

  # Smart Length Handling (>300 chars splits into text stem + poll)
  if len(clean_question) > 295:
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHANNEL_ID, "text": card_header},
    )
    time.sleep(1.5)
    poll_question = f"[{q_id} | UPSC {year}] Select correct option for question above ⬆️:"
  else:
    poll_question = f"[UPSC {year} | {q_id}] {clean_question}"

  # Send the Interactive Quiz Poll
  res = requests.post(
      f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll",
      json={
          "chat_id": CHANNEL_ID,
          "question": poll_question,
          "options": options,
          "type": "quiz",
          "correct_option_id": correct_id,
          "explanation": explanation,
          "is_anonymous": True,
      },
  )

  if res.status_code != 200:
    print(f"❌ Error on {q_id}: {res.text}")

  time.sleep(3.6)

# Automatically Generate & Post the Polity Sub-Topics Menu
if str(CHANNEL_ID).startswith("@"):
  base_url = f"https://t.me/{str(CHANNEL_ID).replace('@', '')}"
else:
  clean_priv_id = str(CHANNEL_ID).replace("-100", "")
  base_url = f"https://t.me/c/{clean_priv_id}"

polity_index_lines = [
    "⚖️ *INDIAN POLITY — TOPIC-WISE PRELIMS PYQs (1991–2026)*",
    "_Click any sub-topic below to jump directly to its PYQ quizzes:_\n",
]

for t_name, m_id in topic_links.items():
  polity_index_lines.append(f"👉 [{t_name}]({base_url}/{m_id})")

polity_index_lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━")
polity_index_lines.append(
    "🏠 _Use the Pinned Message at the top to switch Subjects or Categories_"
)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHANNEL_ID,
        "text": "\n".join(polity_index_lines),
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    },
)

print(
    "🎉 GitHub Action Complete! All questions and Sub-Topics Menu synced"
    " successfully."
)

