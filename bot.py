import os
import tweepy
import threading
from fastapi import FastAPI
import uvicorn
import time

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
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# ========================
#   CONFIG DEL BOT
# ========================

USERS_TO_MONITOR = [
    "IvanCepedaCast", "RedPlanetaCol", "Ruzzarin", "petrogustavo"
]

KEYWORDS = [
    "comunismo", "capitalismo", "socialismo", "china",
    "colombia", "venezuela", "cuba", "stalin", "lenin"
]

last_seen = {}

# ========================
#       BOT LOOP SEGURO
# ========================

def bot_loop():
    print(">>> Bot estable iniciado…")

    while True:
        try:
            for user in USERS_TO_MONITOR:

                try:
                    u = client.get_user(username=user)
                    if not u or not u.data:
                        continue
                except:
                    continue

                try:
                    tweets = client.get_users_tweets(
                        id=u.data.id,
                        max_results=5
                    )
                except:
                    continue

                if not tweets or not tweets.data:
                    continue

                for tweet in tweets.data:

                    # evitar duplicados
                    if last_seen.get(user) == tweet.id:
                        continue

                    last_seen[user] = tweet.id

                    text = tweet.text.lower()

                    # verificar keywords
                    if any(k in text for k in KEYWORDS):
                        try:
                            client.retweet(tweet.id)
                            print(f"RT a @{user}: {tweet.id}")
                        except:
                            pass

            time.sleep(90)  # más seguro, evita 429

        except Exception:
            time.sleep(5)
            continue

# Hilo seguro
threading.Thread(target=bot_loop, daemon=True).start()

# ========================
#       SERVIDOR WEB
# ========================

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running", "message": "Bot retweeter activo"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
