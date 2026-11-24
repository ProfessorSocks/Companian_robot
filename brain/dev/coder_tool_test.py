import requests

from brain.dev.conversation_history import ConversationHistory

from brain.tools.people import (
    get_person_name,
    get_relationship_text,
    get_speaker_context,
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "qwen2.5-coder:1.5b"
URL = "http://localhost:8000/api/chat"

# For now, Camille is the person using this test interface.
CURRENT_SPEAKER = "camille"


# ============================================================
# RECENT CONVERSATION
# ============================================================

# Six messages gives Robot-Q approximately three complete
# user/assistant exchanges of short-term conversational memory.

conversation = ConversationHistory(
    max_messages=6
)


# ============================================================
# BATTERY TOOL
# ============================================================

def get_battery_state():
    """
    Fake battery sensor for testing.

    Later, battery_percent can come from Robot-Q's
    actual battery hardware.
    """

    battery_percent = 73

    return {
        "battery_percent": battery_percent,
        "is_fully_charged": battery_percent >= 100,
        "is_below_50_percent": battery_percent < 50,
        "is_below_20_percent": battery_percent < 20,
    }


# ============================================================
# ROUTER
# ============================================================

ROUTER_PROMPT = """
Classify Camille's message as BATTERY, PEOPLE, or CHAT.

BATTERY:
Use when Camille asks about Robot-Q's own current battery state.

Examples:
"What's your battery level?" -> BATTERY
"Are you fully charged?" -> BATTERY
"Do you need charging?" -> BATTERY
"Are you below 20%?" -> BATTERY

PEOPLE:
Use when Camille asks about someone's identity or relationship
to another known person.

Examples:
"Who am I?" -> PEOPLE
"Who are you?" -> PEOPLE
"Who is Shelby to me?" -> PEOPLE
"Who am I to Shelby?" -> PEOPLE
"Is Shelby my girlfriend?" -> PEOPLE
"Is Shelby your girlfriend?" -> PEOPLE

CHAT:
Use for normal conversation that does not require current
battery information or identity/relationship lookup.

Examples:
"Hello!" -> CHAT
"I built a robot yesterday." -> CHAT
"How do batteries work?" -> CHAT
"My phone is at 10%." -> CHAT
"Tell me about robots." -> CHAT

Important:
- "I", "me", and "my" refer to Camille.
- "you" and "your" refer to Robot-Q.
- Do not choose BATTERY just because battery words appear.
- Do not choose PEOPLE just because a person's name appears.
- PEOPLE is for questions about identity or relationships.

Output exactly one word:
BATTERY
PEOPLE
CHAT
""".strip()


def classify_message(message):
    """
    Ask Coder which capability the message requires.
    """

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": ROUTER_PROMPT
            },
            {
                "role": "user",
                "content": message
            },
        ],
        "stream": False,
    }

    response = requests.post(
        URL,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    content = (
        response
        .json()["message"]["content"]
        .strip()
        .upper()
    )

    print(f"\n[ROUTER] {content}")

    if content in {
        "BATTERY",
        "PEOPLE",
        "CHAT",
    }:
        return content

    raise ValueError(
        f"Invalid router output: {content}"
    )


# ============================================================
# BATTERY ANSWERS
# ============================================================

def answer_battery_question(message, battery):
    """
    Python answers factual battery-state questions.

    Coder does not get to modify objective battery facts.
    """

    text = message.lower()
    percent = battery["battery_percent"]


    # --------------------------------------------------------
    # FULLY CHARGED
    # --------------------------------------------------------

    if (
        "fully charged" in text
        or "full charge" in text
    ):

        if battery["is_fully_charged"]:
            return (
                f"Yes, I'm fully charged "
                f"at {percent}%."
            )

        return (
            f"No, I'm not fully charged. "
            f"I'm at {percent}%."
        )


    # --------------------------------------------------------
    # 100 PERCENT
    # --------------------------------------------------------

    if "100%" in text:

        if percent == 100:
            return (
                "Yes, my battery is at 100%."
            )

        return (
            f"No, my battery is at {percent}%."
        )


    # --------------------------------------------------------
    # BELOW 20 PERCENT
    # --------------------------------------------------------

    if (
        "below 20" in text
        or "under 20" in text
    ):

        if battery["is_below_20_percent"]:
            return (
                f"Yes, I'm below 20%. "
                f"I'm at {percent}%."
            )

        return (
            f"No, I'm not below 20%. "
            f"I'm at {percent}%."
        )


    # --------------------------------------------------------
    # BELOW 50 PERCENT
    # --------------------------------------------------------

    if (
        "below 50" in text
        or "under 50" in text
    ):

        if battery["is_below_50_percent"]:
            return (
                f"Yes, I'm below 50%. "
                f"I'm at {percent}%."
            )

        return (
            f"No, I'm not below 50%. "
            f"I'm at {percent}%."
        )


    # --------------------------------------------------------
    # GENERAL BATTERY QUESTION
    # --------------------------------------------------------

    return (
        f"My battery is at {percent}%."
    )


# ============================================================
# PEOPLE / RELATIONSHIP TOOL
# ============================================================

def resolve_person_reference(reference, speaker_id):
    """
    Convert conversational references into stable person IDs.

    Examples:

        "I"      -> camille
        "me"     -> camille
        "you"    -> robot_q
        "Shelby" -> shelby

    Python owns this mapping rather than asking Coder to guess.
    """

    reference = reference.lower().strip()

    context = get_speaker_context(
        speaker_id
    )

    if context is None:
        return None


    # --------------------------------------------------------
    # CURRENT SPEAKER
    # --------------------------------------------------------

    if reference in {
        "i",
        "me",
        "my",
        "myself",
    }:
        return context["speaker_id"]


    # --------------------------------------------------------
    # ROBOT-Q
    # --------------------------------------------------------

    if reference in {
        "you",
        "your",
        "yourself",
        "robot-q",
        "robot q",
        "robot_q",
    }:
        return "robot_q"


    # --------------------------------------------------------
    # KNOWN PEOPLE
    # --------------------------------------------------------

    known_people = {
        "camille": "camille",
        "shelby": "shelby",
    }

    return known_people.get(reference)


def answer_people_question(
    message,
    speaker_id=CURRENT_SPEAKER
):
    """
    Answer simple identity and relationship questions using
    authoritative Python data.

    Coder does not invent the relationship.
    """

    text = message.lower().strip()

    speaker_name = get_person_name(
        speaker_id
    )

    robot_name = get_person_name(
        "robot_q"
    )


    # --------------------------------------------------------
    # WHO AM I?
    # --------------------------------------------------------

    if text in {
        "who am i?",
        "who am i",
    }:
        return (
            f"You are {speaker_name}."
        )


    # --------------------------------------------------------
    # WHO ARE YOU?
    # --------------------------------------------------------

    if text in {
        "who are you?",
        "who are you",
    }:
        return (
            f"I'm {robot_name}."
        )


    # --------------------------------------------------------
    # SHELBY TO CAMILLE
    # --------------------------------------------------------

    if (
        "who is shelby to me" in text
        or "what is shelby to me" in text
    ):

        relationship = get_relationship_text(
            "shelby",
            speaker_id
        )

        if relationship is None:
            return (
                "I don't have a known relationship "
                "between you and Shelby."
            )

        return (
            f"Shelby is your {relationship}."
        )


    # --------------------------------------------------------
    # CAMILLE TO SHELBY
    # --------------------------------------------------------

    if (
        "who am i to shelby" in text
        or "what am i to shelby" in text
    ):

        relationship = get_relationship_text(
            speaker_id,
            "shelby"
        )

        if relationship is None:
            return (
                "I don't have a known relationship "
                "between you and Shelby."
            )

        return (
            f"You are Shelby's {relationship}."
        )


    # --------------------------------------------------------
    # IS SHELBY MY GIRLFRIEND?
    # --------------------------------------------------------

    if (
        "is shelby my girlfriend" in text
    ):

        relationship = get_relationship_text(
            "shelby",
            speaker_id
        )

        if relationship == "girlfriend":
            return (
                "Yes, Shelby is your girlfriend."
            )

        return (
            "No known relationship says "
            "Shelby is your girlfriend."
        )


    # --------------------------------------------------------
    # IS SHELBY YOUR GIRLFRIEND?
    # --------------------------------------------------------

    if (
        "is shelby your girlfriend" in text
    ):

        relationship = get_relationship_text(
            "shelby",
            "robot_q"
        )

        if relationship == "girlfriend":
            return (
                "Yes, Shelby is my girlfriend."
            )

        return (
            "No. Shelby is not my girlfriend."
        )


    # --------------------------------------------------------
    # UNKNOWN PEOPLE QUESTION
    # --------------------------------------------------------

    return (
        "I don't know how to answer that relationship "
        "question yet."
    )


# ============================================================
# NORMAL CONVERSATION
# ============================================================

CHAT_PROMPT = """
You are Robot-Q, Camille's companion robot.

Camille is the human speaking to you.
You are Robot-Q, not Camille.

Respond naturally and briefly.
Usually use 1-2 short sentences.

Pay attention to the recent conversation.
When Camille refers to something said earlier, use the conversation
history to understand what she means.

Do not repeatedly offer assistance.
Do not introduce yourself.
Do not invent information about your physical state.
""".strip()


def normal_chat(message):
    """
    Send recent conversation history to Coder along
    with Camille's newest message.
    """

    messages = [
        {
            "role": "system",
            "content": CHAT_PROMPT
        }
    ]

    # Add previous conversation.
    messages.extend(
        conversation.get_messages()
    )

    # Add Camille's newest message.
    messages.append({
        "role": "user",
        "content": message
    })


    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }


    response = requests.post(
        URL,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    return (
        response
        .json()["message"]["content"]
        .strip()
    )


# ============================================================
# CONTROLLER
# ============================================================

def chat(message):
    """
    Main Robot-Q controller.

    Coder decides which capability is needed.

    Python owns deterministic facts.
    """

    route = classify_message(
        message
    )


    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    if route == "BATTERY":

        battery = get_battery_state()

        print(
            "[TOOL] get_battery_state() CALLED"
        )

        print(
            "[TOOL RESULT]",
            battery
        )

        reply = answer_battery_question(
            message,
            battery
        )


    # --------------------------------------------------------
    # PEOPLE
    # --------------------------------------------------------

    elif route == "PEOPLE":

        print(
            "[TOOL] people.py CALLED"
        )

        speaker_context = get_speaker_context(
            CURRENT_SPEAKER
        )

        print(
            "[TOOL CONTEXT]",
            speaker_context
        )

        reply = answer_people_question(
            message,
            CURRENT_SPEAKER
        )

        print(
            "[TOOL RESULT]",
            reply
        )


    # --------------------------------------------------------
    # NORMAL CHAT
    # --------------------------------------------------------

    elif route == "CHAT":

        print(
            "[CONTROLLER] No tool needed."
        )

        reply = normal_chat(
            message
        )


    else:

        raise ValueError(
            f"Unknown route: {route}"
        )


    # ========================================================
    # STORE RECENT CONVERSATION
    # ========================================================

    conversation.add_user(
        message
    )

    conversation.add_assistant(
        reply
    )

    return reply


# ============================================================
# CLEAR RECENT CONVERSATION
# ============================================================

def clear_conversation():
    """
    Clear temporary conversation history.

    Long-term memory is not affected.
    """

    conversation.clear()


# ============================================================
# TERMINAL TEST INTERFACE
# ============================================================

if __name__ == "__main__":

    print(
        "Robot-Q People + Conversation Test"
    )

    print(
        "Model:",
        MODEL
    )

    print(
        "Current speaker:",
        get_person_name(CURRENT_SPEAKER)
    )

    print(
        "Recent history: 6 messages"
    )

    print(
        "Type 'clear' to clear recent history."
    )

    print(
        "Type 'quit' to exit."
    )


    while True:

        user_input = input(
            "\nCamille: "
        ).strip()


        if user_input.lower() == "quit":
            break


        if user_input.lower() == "clear":

            clear_conversation()

            print(
                "\n[CONVERSATION CLEARED]"
            )

            continue


        try:

            reply = chat(
                user_input
            )

            print(
                "\nRobot-Q:",
                reply
            )


        except Exception as error:

            print(
                "\nERROR:",
                error
            )