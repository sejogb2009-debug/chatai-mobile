import os
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "chatai-mobile-secret"
)

CORS(app)

# =========================
# GROQ
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

# Modelo actual de Groq
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Historial de conversaciones
conversations = {}


# =========================
# PÁGINA PRINCIPAL
# =========================

@app.route("/")
def index():
    return render_template("index.html")


# =========================
# CHAT
# =========================

@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No se recibieron datos"
            }), 400

        message = data.get("message", "").strip()

        session_id = data.get(
            "session_id",
            "default"
        )

        if not message:
            return jsonify({
                "error": "El mensaje no puede estar vacío"
            }), 400

        # Crear conversación
        if session_id not in conversations:
            conversations[session_id] = []

        # Añadir mensaje del usuario
        conversations[session_id].append({
            "role": "user",
            "content": message
        })

        # Comprobar API Key
        if not client:

            return jsonify({
                "error": "GROQ_API_KEY no está configurada"
            }), 500

        # Solicitud a Groq
        response = client.chat.completions.create(

            model=DEFAULT_MODEL,

            messages=conversations[session_id],

            temperature=0.7,

            max_tokens=1000
        )

        response_text = (
            response
            .choices[0]
            .message
            .content
        )

        # Guardar respuesta
        conversations[session_id].append({
            "role": "assistant",
            "content": response_text
        })

        return jsonify({

            "response": response_text,

            "session_id": session_id,

            "model": DEFAULT_MODEL

        })

    except Exception as e:

        logger.exception(
            "Error en Groq"
        )

        return jsonify({

            "error": str(e)

        }), 500


# =========================
# LIMPIAR CHAT
# =========================

@app.route("/api/clear", methods=["POST"])
def clear_chat():

    try:

        data = request.get_json() or {}

        session_id = data.get(
            "session_id",
            "default"
        )

        conversations[session_id] = []

        return jsonify({

            "success": True,

            "message": "Historial limpiado",

            "session_id": session_id

        })

    except Exception as e:

        return jsonify({

            "error": str(e)

        }), 500


# =========================
# INFORMACIÓN DEL SERVIDOR
# =========================

@app.route("/api/info")
def info():

    return jsonify({

        "status": "online",

        "timestamp":
            datetime.now().isoformat(),

        "openai_configured":
            bool(GROQ_API_KEY),

        "active_sessions":
            len(conversations),

        "mode":
            "Groq"

    })


# =========================
# MODELOS
# =========================

@app.route("/api/models")
def models():

    return jsonify({

        "models": [

            {

                "id":
                    DEFAULT_MODEL,

                "name":
                    "Llama 3.3 70B",

                "description":
                    "Modelo de IA ejecutado mediante Groq"

            }

        ]

    })


# =========================
# HEALTH CHECK
# =========================

@app.route("/health")
def health():

    return jsonify({

        "status":
            "healthy"

    })


# =========================
# EJECUTAR SERVIDOR
# =========================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )