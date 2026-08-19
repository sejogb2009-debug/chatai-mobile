import os
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret")
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5.6")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

conversations = {}

MODELS = [
    {
        "id": "gpt-5.6",
        "name": "GPT-5.6",
        "description": "Modelo principal de OpenAI."
    },
    {
        "id": "gpt-5-mini",
        "name": "GPT-5 mini",
        "description": "Modelo más ligero de OpenAI."
    }
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/info")
def info():
    return jsonify({
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "openai_configured": bool(OPENAI_API_KEY),
        "mode": "OpenAI" if OPENAI_API_KEY else "simulation",
        "active_sessions": len(conversations)
    })


@app.route("/api/models")
def models():
    return jsonify({
        "models": MODELS,
        "default": DEFAULT_MODEL
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}

        message = str(data.get("message", "")).strip()
        session_id = str(data.get("session_id", "default"))
        model = str(data.get("model", DEFAULT_MODEL))

        if not message:
            return jsonify({
                "error": "El mensaje no puede estar vacío."
            }), 400

        if len(message) > 12000:
            return jsonify({
                "error": "El mensaje es demasiado largo."
            }), 400

        available_models = {m["id"] for m in MODELS}

        if model not in available_models:
            model = DEFAULT_MODEL

        history = conversations.setdefault(session_id, [])

        history.append({
            "role": "user",
            "content": message
        })

        if client is None:
            response_text = (
                "⚠️ Modo simulación.\n\n"
                "El servidor funciona correctamente, pero todavía "
                "no has configurado la API Key de OpenAI."
            )

            history.append({
                "role": "assistant",
                "content": response_text
            })

            return jsonify({
                "response": response_text,
                "session_id": session_id,
                "model": "simulation"
            })

        response = client.responses.create(
            model=model,
            input=history[-20:],
            store=False
        )

        response_text = response.output_text

        history.append({
            "role": "assistant",
            "content": response_text
        })

        usage = getattr(response, "usage", None)

        total_tokens = (
            getattr(usage, "total_tokens", None)
            if usage else None
        )

        return jsonify({
            "response": response_text,
            "session_id": session_id,
            "model": model,
            "tokens_used": total_tokens
        })

    except Exception as error:
        app.logger.exception("Error en la API")

        return jsonify({
            "error": "No se pudo completar la solicitud.",
            "details": str(error)
        }), 500


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    data = request.get_json(silent=True) or {}

    session_id = str(
        data.get("session_id", "default")
    )

    conversations.pop(session_id, None)

    return jsonify({
        "success": True,
        "session_id": session_id
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port
    )