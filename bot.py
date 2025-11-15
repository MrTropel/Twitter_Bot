import os
import tweepy
import threading
from fastapi import FastAPI
import uvicorn
import time
import telebot

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

USERS = [
    "IvanCepedaCast", "RedPlanetaCol", "Ruzzarin", "petrogustavo"
]

KEYWORDS = [
    "comunismo", "socialismo", "marx", "marxismo", "clase",
    "capitalismo", "imperialismo", "cuba", "venezuela", "china",
    "uribismo", "neoliberalismo", "burguesía", "proletariado"
]

last_seen = {}

def analyze(text):
    t = text.lower()
    if any(k in t for k in ["anticomunista", "antimarx", "antimarxista", "dictadura comunista"]):
        return "contra"
    if any(k in t for k in KEYWORDS):
        return "pro"
    return None

def bot_loop():
    while True:
        try:
            for username in USERS:
                u = client.get_user(username=username)
                if not u or not u.data:
                    continue

                tweets = client.get_users_tweets(id=u.data.id, max_results=5)
                if not tweets or not tweets.data:
                    continue

                for tw in tweets.data:
                    if last_seen.get(username) == tw.id:
                        continue

                    last_seen[username] = tw.id
                    txt = tw.text
                    tag = analyze(txt)

                    if not tag:
                        continue

                    if tag == "pro":
                        decision = "Tweet marxista detectado. ¿Hacer retweet?"
                    else:
                        decision = "Tweet anticomunista detectado. ¿Responder desmontando propaganda?"

                    bot.send_message(
                        TELEGRAM_CHAT_ID,
                        f"De @{username}:\n\n{txt}\n\n{decision}\n\nID: {tw.id}"
                    )

            time.sleep(600)

        except Exception:
            time.sleep(600)

# ============================
#   FIX: INICIAR BOT EN RENDER
# ============================

app = FastAPI()

@app.on_event("startup")
def start_background_tasks():
    threading.Thread(target=bot_loop, daemon=True).start()

@app.get("/")
def root():
    return {"status": "running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
