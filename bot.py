import os
import tweepy
import threading
from fastapi import FastAPI
import uvicorn
from telegram import Bot as TelegramBot
from telegram.ext import Updater, MessageHandler, Filters
import logging

# ===========================
# ENVIRONMENT VARIABLES
# ===========================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===========================
# TWITTER CLIENT (API v2)
# ===========================
twitter_client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
)

# ===========================
# TELEGRAM BOT
# ===========================
telegram_bot = TelegramBot(token=TELEGRAM_TOKEN)

pending_tweet_id = None  # almacena el tweet esperando aprobación

# Palabras para filtrar tweets políticos relevantes
KEYWORDS = [
    "marx", "marxismo", "socialismo", "comunismo", "socialista", "comunista",
    "capitalismo", "imperialismo", "clase obrera", "lucha de clases",
    "dictadura del proletariado", "neoliberalismo", "antiimperialista",
    "CIA", "OTAN", "economía política", "gringo", "yanqui"
]


# ===========================
# FUNCIÓN: ENVIAR A TELEGRAM
# ===========================
def send_to_telegram(tweet_text, tweet_id):
    global pending_tweet_id
    pending_tweet_id = tweet_id

    telegram_bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=f"¿Quieres retuitear esto?\n\n{tweet_text}\n\nResponde: SI o NO"
    )


# ===========================
# TELEGRAM HANDLER
# ===========================
def handle_telegram(update, context):
    global pending_tweet_id

    text = update.message.text.strip().lower()

    if pending_tweet_id is None:
        return

    if text == "si":
        try:
            twitter_client.retweet(pending_tweet_id)
            telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="Retweet realizado 👍"
            )
        except Exception as e:
            telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=f"Error al retuitear: {e}"
            )

        pending_tweet_id = None

    elif text == "no":
        telegram_bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text="Entendido, no se retuitea."
        )
        pending_tweet_id = None


# ===========================
# INICIAR ESCUCHA EN TELEGRAM
# ===========================
def start_telegram_listener():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text, handle_telegram))
    updater.start_polling()
    updater.idle()


# ===========================
# TWITTER STREAM
# ===========================
class PoliticalStream(tweepy.StreamingClient):
    def on_tweet(self, tweet):

        if any(keyword in tweet.text.lower() for keyword in KEYWORDS):
            send_to_telegram(tweet.text, tweet.id)

    def on_connection_error(self):
        self.disconnect()


# ===========================
# INICIAR STREAM
# ===========================
def start_stream():
    stream = PoliticalStream(BEARER_TOKEN)

    # Limpiar reglas anteriores
    rules = stream.get_rules().data
    if rules:
        rule_ids = [rule.id for rule in rules]
        stream.delete_rules(rule_ids)

    # Regla general para recibir tweets públicos
    stream.add_rules(tweepy.StreamRule("lang:es -is:retweet"))

    stream.filter(
        expansions=["author_id"],
        tweet_fields=["created_at", "text", "id"]
    )


# ===========================
# FASTAPI (mantener vivo en Render)
# ===========================
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Twitter Bot Running"}


# ===========================
# MAIN
# ===========================
if __name__ == "__main__":
    # Telegram listener en hilo separado
    threading.Thread(target=start_telegram_listener, daemon=True).start()

    # Twitter stream en hilo separado
    threading.Thread(target=start_stream, daemon=True).start()

    print("Bot iniciado correctamente…")

    # Mantener servidor vivo en Render
    uvicorn.run(app, host="0.0.0.0", port=10000)
