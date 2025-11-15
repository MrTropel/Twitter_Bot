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
    access_token_secret=ACCESS_TOKEN_SECRET
)

# ========================
#   LISTAS Y CLASIFICADOR
# ========================

USERS_TO_MONITOR = [
    "IvanCepedaCast", "RedPlanetaCol", "Ruzzarin", "petrogustavo"
]

MARXISTA = [
    "marx", "lenin", "stalin", "gramsci", "proletariado",
    "burguesía", "imperialismo", "socialismo", "materialismo",
    "comunista", "comunismo científico"
]

ANTICOMUNISTA = [
    "comunismo asesino", "castrochavismo", "dictadura socialista",
    "socialismo fracaso", "venezuela hambre", "cuba dictadura",
    "antisocialista", "antimarxista", "marxismo cultural"
]

GEOPOLITICA = [
    "china", "brics", "otan", "geopolítica", "sanciones",
    "nacionalización", "privatización", "ee.uu", "pib", "inflación"
]

def clasificar_tweet(texto):
    t = texto.lower()

    if any(p in t for p in MARXISTA):
        return "marxista"
    if any(p in t for p in ANTICOMUNISTA):
        return "propaganda"
    if any(p in t for p in GEOPOLITICA):
        return "geopolítica"

    return "otro"

def mensaje_analisis(tweet, autor):
    categoria = clasificar_tweet(tweet.text)

    if categoria == "marxista":
        analisis = "🟥 *Contenido marxista / de izquierda*"
    elif categoria == "propaganda":
        analisis = "🟦 *Propaganda o ataque anti-socialista*"
    elif categoria == "geopolítica":
        analisis = "🟩 *Contenido geopolítico relevante*"
    else:
        analisis = "⚪ *Política general*"

    enlace = f"https://twitter.com/{autor}/status/{tweet.id}"

    return f"{analisis}\n\n📝 {tweet.text}\n\n🔗 {enlace}"

# =================================================
#   DEBES DEFINIR ESTA FUNCIÓN CON TU TOKEN TELEGRAM
# =================================================
def enviar_a_telegram(mensaje):
    import requests
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    if not TOKEN or not CHAT_ID:
        print("Telegram no configurado.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    requests.post(url, data=data)


# ========================
#       BOT LOOP
# ========================

def bot_loop():
    print(">>> Bot de Twitter iniciado…")
    last_seen = {}

    while True:
        try:
            for user in USERS_TO_MONITOR:

                u = client.get_user(username=user)
                if not u or not u.data:
                    continue

                tweets = client.get_users_tweets(id=u.data.id, max_results=5)
                if not tweets or not tweets.data:
                    continue

                for tweet in tweets.data:

                    if last_seen.get(user) == tweet.id:
                        continue

                    last_seen[user] = tweet.id
                    texto = tweet.text.lower()

                    if clasificar_tweet(texto) != "otro":
                        mensaje = mensaje_analisis(tweet, user)
                        enviar_a_telegram(mensaje)
                        print(f"Enviado a Telegram desde @{user}")

            time.sleep(60)

        except Exception as e:
            print("Error en el bot:", e)
            time.sleep(10)


threading.Thread(target=bot_loop, daemon=True).start()


# ========================
#       SERVIDOR WEB
# ========================

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running", "message": "Twitter bot activo"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
