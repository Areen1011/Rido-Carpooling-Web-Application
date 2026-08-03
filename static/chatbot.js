// ================= CHATBOT =================

// ---------- Elements ----------

const chatbotBtn = document.getElementById("chatbot-btn");
const chatbotBox = document.getElementById("chatbot-box");
const chatbotClose = document.getElementById("chatbot-close");
const chatbotInput = document.getElementById("chatbot-input");
const chatbotMessages = document.getElementById("chatbot-messages");

// ---------- Toggle Chat ----------

function toggleChat() {

    const isOpen = chatbotBox.style.display === "block";

    chatbotBox.style.display = isOpen ? "none" : "block";

    if (!isOpen) {
        chatbotInput.focus();
    }

}

// ---------- Add Message ----------

function addMessage(text, sender) {

    const message = document.createElement("div");

    message.className = sender === "user"
        ? "user-msg"
        : "bot-msg";

    message.textContent = text;

    chatbotMessages.appendChild(message);

    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

}

// ---------- Send Message ----------

async function sendMessage() {

    const message = chatbotInput.value.trim();

    if (!message) return;

    addMessage(message, "user");

    chatbotInput.value = "";

    try {

        const response = await fetch("/chatbot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        addMessage(data.reply, "bot");

    }

    catch (error) {

        addMessage(
            "⚠️ Server error. Please try again.",
            "bot"
        );

    }

}

// ---------- Events ----------

chatbotBtn.addEventListener("click", toggleChat);

chatbotClose.addEventListener("click", toggleChat);

chatbotInput.addEventListener("keydown", function (event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendMessage();

    }

});