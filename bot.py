import os
import tweepy
import threading
from fastapi import FastAPI
import uvicorn
import time
import telebot

# =======================
#   CARGA DE CREDENCIALES
# =======================

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =======================
#   CLIENTES
# =======================

client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# =======================
#   CONFIGURACIÓN BOT
# =======================

USERS = [
    "IvanCepedaCast", "RedPlanetaCol", "Ruzzarin", "petrogustavo"
]

KEYWORDS = [
    "comunismo", "socialismo", "marx", "marxismo", "clase",
    "capitalismo", "imperialismo", "cuba", "venezuela", "china",
    "uribismo", "neoliberalismo", "burguesía", "proletariado"
]

last_seen = {}

# =======================
#   ANALIZADOR
# =======================

def analyze(text):
    t = text.lower()
    if any(k in t for k in ["anticomunista", "antimarx", "antimarxista", "dictadura comunista"]):
        return "contra"
    if any(k in t for k in KEYWORDS):
        return "pro"
    return None

# =======================
#   HILO PRINCIPAL TWITTER
# =======================

def bot_loop():
    print(">>> HILO DEL BOT INICIADO")

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

                    print(f">>> NUEVO TWEET DETECTADO: {tw.id}")

                    bot.send_message(
                        TELEGRAM_CHAT_ID,
                        f"De @{username}:\n\n{txt}\n\n{decision}\n\nID: {tw.id}"
                    )

            time.sleep(600)

        except Exception as e:
            print("ERROR EN LOOP:", e)
            time.sleep(600)

# =======================
#   BOT DE TELEGRAM
# =======================

@bot.message_handler(commands=["retweet"])
def retweet_cmd(message):
    try:
        tweet_id = message.text.split()[1]
        client.retweet(tweet_id)
        bot.reply_to(message, "Retweet realizado.")
    except:
        bot.reply_to(message, "Error procesando el retweet.")

@bot.message_handler(commands=["responder"])
def responder_cmd(message):
    try:
        parts = message.text.split(" ", 2)
        tweet_id = parts[1]
        respuesta = parts[2]
        client.create_tweet(text=respuesta, in_reply_to_tweet_id=tweet_id)
        bot.reply_to(message, "Respuesta enviada.")
    except:
        bot.reply_to(message, "Error enviando respuesta.")

def telegram_loop():
    print(">>> HILO TELEGRAM INICIADO")
    bot.infinity_polling()

# =======================
#   FASTAPI + HILOS
# =======================

app = FastAPI()

@app.on_event("startup")
def start_background_tasks():
    print(">>> APP INICIANDO HILOS")

    threading.Thread(target=bot_loop, daemon=True).start()
    threading.Thread(target=telegram_loop, daemon=True).start()

@app.get("/")
def root():
    return {"status": "running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
