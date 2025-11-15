import os
import tweepy
import threading
from fastapi import FastAPI
import uvicorn
import time

# ========================
#   CONFIGURACIÓN TWITTER
# ========================

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Autenticación de Twitter
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET
)

# ========================
#     LISTAS DEL BOT
# ========================

USERS_TO_MONITOR = [
    "IvanCepedaCast", "RedPlanetaCol", "Ruzzarin", "petrogustavo"
    # agrega los demás aquí
]

KEYWORDS = [
    "comunismo", "capitalismo", "socialismo", "china",
    "colombia", "venezuela", "cuba", "stalin", "lenin"
]

RESPUESTAS = [
    "Reducir todo a propaganda barata es ignorar la historia material.",
    "Los trabajadores producen el valor; el capital solo lo captura.",
    "El anticomunismo siempre termina justificando autoritarismos.",
    "La soberanía de un pueblo incomoda al imperialismo, por eso lo atacan."
]

# ========================
#   LÓGICA PRINCIPAL BOT
# ========================

def bot_loop():
    print(">>> Bot de Twitter iniciado…")

    last_seen = {}

    while True:
        try:
            for user in USERS_TO_MONITOR:
                tweets = client.get_users_tweets(
                    id=client.get_user(username=user).data.id,
                    max_results=5
                )

                if not tweets or not tweets.data:
                    continue

                for tweet in tweets.data:
                    # evitar duplicados
                    if last_seen.get(user) == tweet.id:
                        continue

                    last_seen[user] = tweet.id

                    text = tweet.text.lower()

                    # buscar keywords
                    if any(k in text for k in KEYWORDS):
                        respuesta = RESPUESTAS[len(text) % len(RESPUESTAS)]

                        print(f"Respondiendo a @{user}: {respuesta}")

                        client.create_tweet(
                            text=respuesta,
                            in_reply_to_tweet_id=tweet.id
                        )

            time.sleep(60)  # evita límites de API

        except Exception as e:
            print("Error en el bot:", e)
            time.sleep(10)

# hilo paralelo donde corre el bot
threading.Thread(target=bot_loop, daemon=True).start()

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
