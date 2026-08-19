const chat = document.getElementById("chat");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");

const routeDisplay = document.getElementById("route");
const modelDisplay = document.getElementById("model");
const durationDisplay = document.getElementById("duration");
const memoryStatus = document.getElementById("memory-status");
const personStatus = document.getElementById("person-status");


let currentPerson = null;


// --------------------------------------------------
// CHAT DISPLAY
// --------------------------------------------------

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


// --------------------------------------------------
// PERSON HANDLING
// --------------------------------------------------

function setCurrentPerson(name) {
    currentPerson = name.trim();

    if (!currentPerson) {
        return;
    }

    personStatus.textContent =
        `Person: ${currentPerson}`;

    localStorage.setItem(
        "robotQPerson",
        currentPerson
    );
}


function extractName(text) {
    let name = text.trim();

    const lower = name.toLowerCase();

    if (lower.startsWith("i'm ")) {
        name = name.slice(4).trim();

    } else if (lower.startsWith("i am ")) {
        name = name.slice(5).trim();

    } else if (lower.startsWith("this is ")) {
        name = name.slice(8).trim();

    } else if (lower.startsWith("my name is ")) {
        name = name.slice(11).trim();
    }

    return name;
}


// --------------------------------------------------
// INITIAL PERSON LOAD
// --------------------------------------------------

const savedPerson =
    localStorage.getItem("robotQPerson");

if (savedPerson) {
    setCurrentPerson(savedPerson);

    addMessage(
        "Robot-Q",
        `Welcome back, ${savedPerson}.`,
        "robot"
    );

} else {
    personStatus.textContent =
        "Person: Unknown";

    addMessage(
        "Robot-Q",
        "Who are you?",
        "robot"
    );
}


// --------------------------------------------------
// SEND MESSAGE
// --------------------------------------------------

async function sendMessage() {
    const text = input.value.trim();

    if (!text) {
        return;
    }

    addMessage(
        "You",
        text,
        "user"
    );

    input.value = "";


    // --------------------------------------------------
    // PERSON IDENTIFICATION
    // --------------------------------------------------

    if (!currentPerson) {
        const name = extractName(text);

        if (!name) {
            addMessage(
                "Robot-Q",
                "I didn't catch your name. Who are you?",
                "robot"
            );

            return;
        }

        setCurrentPerson(name);

        addMessage(
            "Robot-Q",
            `Got it. You're ${name}.`,
            "robot"
        );

        input.focus();

        return;
    }


    // --------------------------------------------------
    // MANUAL PERSON SWITCH
    // --------------------------------------------------

    if (
        text.toLowerCase().startsWith(
            "/person "
        )
    ) {
        const newPerson =
            text.slice(8).trim();

        if (newPerson) {
            setCurrentPerson(
                newPerson
            );

            addMessage(
                "Robot-Q",
                `Current person is now ${newPerson}.`,
                "robot"
            );
        }

        input.focus();

        return;
    }


    // --------------------------------------------------
    // SEND TO ROBOT-Q API
    // --------------------------------------------------

    sendButton.disabled = true;
    sendButton.textContent =
        "Thinking...";

    const requestStart =
        performance.now();

    try {
        const response = await fetch(
            "/api/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    message: text,
                    person: currentPerson
                })
            }
        );


        if (!response.ok) {
            throw new Error(
                `Server returned ${response.status}`
            );
        }


        const data =
            await response.json();


        // --------------------------------------------------
        // API ERROR
        // --------------------------------------------------

        if (data.error) {
            addMessage(
                "System",
                data.error,
                "robot"
            );

            return;
        }


        // --------------------------------------------------
        // ROBOT RESPONSE
        // --------------------------------------------------

        addMessage(
            "Robot-Q",
            data.response,
            "robot"
        );


        // --------------------------------------------------
        // ROUTE / MODEL
        // --------------------------------------------------

        routeDisplay.textContent =
            `Route: ${data.route ?? "—"}`;

        modelDisplay.textContent =
            `Model: ${data.model ?? "—"}`;


        // --------------------------------------------------
        // INFERENCE TIME
        // --------------------------------------------------

        if (
            data.duration !== null &&
            data.duration !== undefined
        ) {
            durationDisplay.textContent =
                `Inference: ${data.duration.toFixed(2)}s`;

        } else {
            durationDisplay.textContent =
                "Inference: —";
        }


        // --------------------------------------------------
        // MEMORY STATUS
        // --------------------------------------------------

        if (data.stored_memory) {
            memoryStatus.textContent =
                `Memory: ${data.stored_memory}`;

        } else {
            memoryStatus.textContent =
                "Memory: no new memory";
        }


        // --------------------------------------------------
        // TOTAL REQUEST TIME
        // --------------------------------------------------

        const totalSeconds =
            (
                performance.now()
                - requestStart
            )
            / 1000;

        console.log(
            `Total request time: ${totalSeconds.toFixed(2)}s`
        );

    } catch (error) {
        console.error(error);

        addMessage(
            "System",
            "Could not communicate with Robot-Q.",
            "robot"
        );

    } finally {
        sendButton.disabled = false;

        sendButton.textContent =
            "Send";

        input.focus();
    }
}


// --------------------------------------------------
// BUTTON
// --------------------------------------------------

sendButton.addEventListener(
    "click",
    sendMessage
);


// --------------------------------------------------
// ENTER KEY
// --------------------------------------------------

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