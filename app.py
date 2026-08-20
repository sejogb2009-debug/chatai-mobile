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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chatai-mobile-secret")
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

DEFAULT_MODEL = "llama-3.1-8b-instant"
conversations = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")

        if not message:
            return jsonify({"error": "El mensaje no puede estar vacío"}), 400

        if session_id not in conversations:
            conversations[session_id] = []

        conversations[session_id].append({
            "role": "user",
            "content": message
        })

        if not client:
            return jsonify({
                "response": "⚠️ Falta configurar GROQ_API_KEY en Render."
            }), 500

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=conversations[session_id],
            temperature=0.7,
            max_tokens=1000
        )

        response_text = response.choices[0].message.content

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
        logger.exception("Error en Groq")
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")

    conversations[session_id] = []

    return jsonify({
        "success": True,
        "session_id": session_id
    })


@app.route("/api/info")
def info():
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": bool(GROQ_API_KEY),
        "active_sessions": len(conversations),
        "mode": "Groq"
    })


@app.route("/api/models")
def models():
    return jsonify({
        "models": [
            {
                "id": DEFAULT_MODEL,
                "name": "Llama 3.1 8B",
                "description": "Modelo rápido de Groq"
            }
        ]
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )