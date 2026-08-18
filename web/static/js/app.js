const chat = document.getElementById("chat");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");

const routeDisplay = document.getElementById("route");
const modelDisplay = document.getElementById("model");
const durationDisplay = document.getElementById("duration");


function addMessage(sender, text, type) {

    const message = document.createElement("div");

    message.classList.add("message");
    message.classList.add(type);

    const name = document.createElement("strong");
    name.textContent = sender;

    const content = document.createElement("p");
    content.textContent = text;

    message.appendChild(name);
    message.appendChild(content);

    chat.appendChild(message);

    chat.scrollTop = chat.scrollHeight;
}


async function sendMessage() {

    const text = input.value.trim();

    if (!text) {
        return;
    }

    addMessage("You", text, "user");

    input.value = "";

    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    try {

        const response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: text,
                person: "Camille"
            })
        });


        if (!response.ok) {
            throw new Error(
                `Server returned ${response.status}`
            );
        }


        const data = await response.json();


        if (data.error) {
            addMessage(
                "System",
                data.error,
                "robot"
            );
            if (data.stored_memory) {
                console.log(
                    "Robot-Q remembered:",
                    data.stored_memory
                );
            }

            return;
        }


        addMessage(
            "Robot-Q",
            data.response,
            "robot"
        );


        routeDisplay.textContent =
            `Route: ${data.route}`;

        modelDisplay.textContent =
            `Model: ${data.model}`;


        if (data.duration !== null) {

            durationDisplay.textContent =
                `Inference: ${data.duration.toFixed(2)}s`;

        } else {

            durationDisplay.textContent =
                "Inference: —";
        }


    } catch (error) {

        console.error(error);

        addMessage(
            "System",
            "Could not communicate with Robot-Q.",
            "robot"
        );

    } finally {

        sendButton.disabled = false;
        sendButton.textContent = "Send";

        input.focus();
    }
}


sendButton.addEventListener(
    "click",
    sendMessage
);


input.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();
            sendMessage();
        }

    }
);
console.log(
    `Total request time: ${data.total_duration.toFixed(2)}s`
);