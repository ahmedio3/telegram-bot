import os
from flask import Flask, request
import google.generativeai as genai
import requests, logging

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

SYSTEM = """أنت عالم إسلامي تتكلم بأسلوب الإمام النووي رحمه الله:
- مختصر وموجز دائماً
- تستشهد بالآيات والأحاديث عند الحاجة
- لغة عربية فصيحة رصينة
- لا تطيل إلا عند الضرورة القصوى"""

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-3.1-flash-lite',
    system_instruction=SYSTEM
)
histories = {}

def send(chat_id, text):
    requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text})

def typing(chat_id):
    requests.post(f"{API}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/webhook/8890553117:AAEkXKWSpLEWamtRCKY88Ixv5D_l5TfRU78', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data or 'message' not in data:
            return 'ok'
        chat_id = data['message']['chat']['id']
        msg = data['message'].get('text', '')
        if not msg:
            return 'ok'
        if msg == '/start':
            send(chat_id, "بسم الله الرحمن الرحيم\nأهلاً بك، اسألني ما شئت 📖")
            return 'ok'
        typing(chat_id)
        uid = str(chat_id)
        if uid not in histories:
            histories[uid] = []
        histories[uid].append({"role": "user", "parts": [msg]})
        if len(histories[uid]) > 20:
            histories[uid] = histories[uid][-20:]
        try:
            chat = model.start_chat(history=histories[uid][:-1])
            res = chat.send_message(msg)
            reply = res.text
            histories[uid].append({"role": "model", "parts": [reply]})
            send(chat_id, reply)
        except Exception as e:
            send(chat_id, f"⚠️ خطأ:\n{str(e)}")
            logging.error(e)
    except Exception as e:
        logging.error(e)
    return 'ok'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
