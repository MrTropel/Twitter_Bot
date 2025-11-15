import os
import tweepy
import threading
import time
import requests
from fastapi import FastAPI
import uvicorn

# ========================
#   CONFIGURACIÓN TWITTER
# ========================

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# ========================
#   CONFIGURACIÓN TELEGRAM
# ========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Error enviando mensaje a Telegram:", e)


# ========================
#     CONFIG DEL BOT
# ========================

USERS_TO_MONITOR = [
    "IvanCepedaCast", "RedPlanetaCol", "Ruzzarin", "petrogustavo"
]

KEYWORDS_MARX = [
    "marx", "marxismo", "clase obrera", "socialismo", "revolución",
    "lenin", "stalin", "mao", "plusvalía", "explotación"
]

KEYWORDS_ANTI = [
    "comunismo malo", "dictadura comunista", "socialismo fracaso",
    "antimarxista", "anticomunista", "izquierda terrorista"
]

# Para evitar repetir tweets.
last_seen = {}

# ========================
#    PROCESAMIENTO TWEETS
# ========================

def classify_tweet(text):
    t = text.lower()

    if any(k in t for k in KEYWORDS_MARX):
        return "marx"
    if any(k in t for k in KEYWORDS_ANTI):
        return "anti"
    
    return None


def bot_loop():
    print(">>> Bot de Twitter iniciado…")

    while True:
        try:
            for user in USERS_TO_MONITOR:

                u = client.get_user(username=user)
                if not u or not u.data:
                    continue

                tweets = client.get_users_tweets(
                    id=u.data.id,
                    max_results=5
                )

                if not tweets or not tweets.data:
                    continue

                for tweet in tweets.data:

                    if last_seen.get(user) == tweet.id:
                        continue

                    last_seen[user] = tweet.id
                    classification = classify_tweet(tweet.text)

                    if classification is None:
                        continue

                    tweet_url = f"https://twitter.com/{user}/status/{tweet.id}"

                    if classification == "marx":
                        msg = (
                            "📢 <b>NUEVO TWEET MARXISTA DETECTADO</b>\n"
                            f"Autor: @{user}\n\n"
                            f"{tweet.text}\n\n"
                            f"<a href='{tweet_url}'>Ver Tweet</a>\n\n"
                            "Responde con /rt para retuitearlo."
                        )

                    elif classification == "anti":
                        msg = (
                            "⚠️ <b>TWEET ANTICOMUNISTA DETECTADO</b>\n"
                            f"Autor: @{user}\n\n"
                            f"{tweet.text}\n\n"
                            f"<a href='{tweet_url}'>Ver Tweet</a>\n\n"
                            "Responde con /rt para desmontarlo con retweet."
                        )

                    send_telegram_message(msg)

            time.sleep(60)

        except Exception as e:
            print("Error en el bot:", e)
            time.sleep(10)


# ========================
#       SERVIDOR WEB
# ========================

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running", "message": "Twitter bot activo"}


# ========================
#   EJECUCIÓN EN RENDER
# ========================

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
