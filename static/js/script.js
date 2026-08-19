class ChatApp {
    constructor() {
        this.sessionId = "mobile-" + Date.now();
        this.selectedModel = "gpt-5.6";
        this.isProcessing = false;

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadModels();
        this.checkServerStatus();

        this.addMessage(
            "assistant",
            "¡Hola! 👋 Soy tu asistente de IA. ¿En qué puedo ayudarte?"
        );
    }

    bindEvents() {
        const sendBtn = document.getElementById("sendBtn");
        const input = document.getElementById("messageInput");
        const clearBtn = document.getElementById("clearBtn");
        const modelBtn = document.getElementById("modelBtn");
        const infoBtn = document.getElementById("infoBtn");

        sendBtn.addEventListener("click", () => this.sendMessage());

        input.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
        });

        input.addEventListener("input", () => {
            input.style.height = "auto";
            input.style.height =
                Math.min(input.scrollHeight, 130) + "px";
        });

        clearBtn.addEventListener("click", () => this.clearChat());

        modelBtn.addEventListener("click", () => {
            this.showModal("modelModal");
        });

        infoBtn.addEventListener("click", () => {
            this.showModal("infoModal");
            this.loadSystemInfo();
        });

        document.querySelectorAll(".close-modal").forEach((button) => {
            button.addEventListener("click", () => this.hideModals());
        });

        document.querySelectorAll(".modal").forEach((modal) => {
            modal.addEventListener("click", (event) => {
                if (event.target === modal) {
                    this.hideModals();
                }
            });
        });
    }

    async checkServerStatus() {
        try {
            const response = await fetch("/health");

            if (!response.ok) {
                throw new Error("Servidor no disponible");
            }

            const data = await response.json();

            document.getElementById("statusText").textContent =
                "Conectado";

            document.getElementById("statusDot").style.background =
                "#22c55e";

        } catch (error) {
            console.error(error);

            document.getElementById("statusText").textContent =
                "Desconectado";

            document.getElementById("statusDot").style.background =
                "#ef4444";
        }
    }

    async loadModels() {
        try {
            const response = await fetch("/api/models");
            const data = await response.json();

            const list = document.getElementById("modelList");
            list.innerHTML = "";

            data.models.forEach((model) => {
                const item = document.createElement("div");

                item.className =
                    "model-item" +
                    (model.id === this.selectedModel
                        ? " selected"
                        : "");

                item.innerHTML = `
                    <div class="model-name">
                        ${model.name}
                    </div>

                    <div class="model-id">
                        ${model.id}
                    </div>

                    <div class="model-desc">
                        ${model.description}
                    </div>
                `;

                item.addEventListener("click", () => {
                    this.selectedModel = model.id;

                    document.getElementById(
                        "currentModel"
                    ).textContent = model.id;

                    this.hideModals();
                    this.loadModels();
                });

                list.appendChild(item);
            });

        } catch (error) {
            console.error("Error cargando modelos:", error);
        }
    }

    async sendMessage() {
        if (this.isProcessing) return;

        const input = document.getElementById("messageInput");
        const message = input.value.trim();

        if (!message) return;

        this.isProcessing = true;

        this.addMessage("user", message);

        input.value = "";
        input.style.height = "auto";

        this.showLoading(true);

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    model: this.selectedModel
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.details ||
                    data.error ||
                    "Error desconocido"
                );
            }

            this.addMessage(
                "assistant",
                data.response
            );

        } catch (error) {

            console.error(error);

            this.addMessage(
                "assistant",
                "⚠️ Ha ocurrido un error.\n\n" +
                error.message
            );

        } finally {

            this.isProcessing = false;
            this.showLoading(false);
        }
    }

    addMessage(role, text) {
        const container =
            document.getElementById("chatContainer");

        const message = document.createElement("div");

        message.className =
            "message " +
            (role === "user"
                ? "user-message"
                : "ai-message");

        message.textContent = text;

        container.appendChild(message);

        container.scrollTop =
            container.scrollHeight;
    }

    async clearChat() {
        try {
            await fetch("/api/clear", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
        } catch (error) {
            console.error(error);
        }

        document.getElementById(
            "chatContainer"
        ).innerHTML = "";

        this.addMessage(
            "assistant",
            "Chat limpiado. ¿Qué quieres preguntarme?"
        );
    }

    async loadSystemInfo() {
        const box =
            document.getElementById("serverInfo");

        try {
            const response =
                await fetch("/api/info");

            const data =
                await response.json();

            box.innerHTML = `
                <p>
                    <strong>Servidor:</strong>
                    ${data.status}
                </p>

                <p>
                    <strong>IA configurada:</strong>
                    ${data.openai_configured
                        ? "Sí ✅"
                        : "No ⚠️"}
                </p>

                <p>
                    <strong>Modo:</strong>
                    ${data.mode}
                </p>

                <p>
                    <strong>Sesiones:</strong>
                    ${data.active_sessions}
                </p>
            `;

        } catch (error) {

            box.textContent =
                "No se pudo obtener la información.";
        }
    }

    showModal(id) {
        document.getElementById(id)
            .classList.add("active");
    }

    hideModals() {
        document.querySelectorAll(".modal")
            .forEach((modal) => {
                modal.classList.remove("active");
            });
    }

    showLoading(show) {
        const overlay =
            document.getElementById("loadingOverlay");

        overlay.classList.toggle(
            "active",
            show
        );
    }
}

document.addEventListener(
    "DOMContentLoaded",
    () => {
        window.chatApp = new ChatApp();
    }
);