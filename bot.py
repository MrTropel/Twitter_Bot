import tweepy
import time
import requests

# ----------------------
#   CONFIGURACIÓN
# ----------------------

API_KEY = "TU_API_KEY"
API_SECRET = "TU_API_SECRET"
ACCESS_TOKEN = "TU_ACCESS_TOKEN"
ACCESS_SECRET = "TU_ACCESS_SECRET"

TELEGRAM_TOKEN = "TU_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

CUENTAS = [
    "Iván Cepeda Castro", "Partido Comunista Revolucionario", "Madeline Pendleton",
    "Rafael Solano", "ʟᴀɪᴋᴀ ☭", "LadyIzdihar", "Red Planeta", "★☭MassStrikeNow☭★",
    "Embajada de China en Colombia", "Diego Ruzzarin ☭", "Capitaine Ibrahim TRAORÉ",
    "Ma Wukong 马悟空", "antolin pulido", "Fibrik", "Feker", "BRICS News",
    "Spetsnaℤ 007", "Colombia Oscura", "David Rozo", "Guerra universitaria",
    "Prensa Libre", "Gustavo Petro", "Puma Chairo", "Pamphlets",
    "inhumans of capitalism (Ojibwa )☭", "Jackson Hinkle", "BlackRedGuard ☭",
    "Santiago Armesilla", "María Fernanda Cabal", "Memes Universidad Nacional",
    "Mateo Amaya Quimbayo"
]

KEYWORDS = [
    "comunismo", "capitalismo", "socialismo", "anarquia", "china", "colombia",
    "estados unidos", "venezuela", "cuba", "korea del norte", "ussr", "union sovietica",
    "revolucion", "stalin", "lenin", "uribe", "petro"
]


def generar_respuesta(texto):
    # Estilo "Mr. Tropel"
    respuestas = [
        "Reducir esto a consignas vacías es repetir propaganda vieja. Analiza el poder material detrás, no el cuento fácil.",
        "Los anticomunistas siempre terminan abrazando el fascismo cuando el capitalismo entra en crisis.",
        "El problema no es la ideología: es quién controla los medios de vida. Sin eso, no hay libertad real.",
        "La plusvalía no desaparece porque la ignores: la economía funciona por explotación, no por magia.",
        "Cuando te quedas sin argumentos recurres al insulto. Eso ya es una derrota política."
    ]
    return respuestas[hash(texto) % len(respuestas)]


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


# ----------------------
#   AUTENTICACIÓN
# ----------------------

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

print("Bot iniciado...")

# ----------------------
#   LOOP PRINCIPAL
# ----------------------

LAST_SEEN = None

while True:
    try:
        timeline = api.home_timeline(count=50, tweet_mode="extended")

        for t in timeline:
            texto = t.full_text.lower()

            if LAST_SEEN and t.id <= LAST_SEEN:
                continue

            if any(c.lower() in t.user.name.lower() for c in CUENTAS) or any(k in texto for k in KEYWORDS):
                respuesta = generar_respuesta(texto)

                api.update_status(
                    status=f"@{t.user.screen_name} {respuesta}",
                    in_reply_to_status_id=t.id
                )

                send_telegram(f"Respondí a @{t.user.screen_name}:\n\n{respuesta}")

        if timeline:
            LAST_SEEN = timeline[0].id

    except Exception as e:
        send_telegram(f"Error: {e}")

    time.sleep(30)