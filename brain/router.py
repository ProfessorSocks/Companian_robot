import json
import re

from llm_client import LLMClient


# ==========================================================
# MODELS
# ==========================================================

FAST_MODEL = "qwen2.5-instruct:1.5b"
SMART_MODEL = "llama3.2:3b"


class ModelWrapper:
    def __init__(self):
        # Small utility model
        self.fast = LLMClient(
            FAST_MODEL
        )

        # Main conversational / reasoning brain
        self.smart = LLMClient(
            SMART_MODEL
        )

    # ======================================================
    # ROUTING
    # ======================================================

    def obvious_complexity(self, text):
        """
        Decide whether we can confidently route
        without asking another LLM.

        Returns:
            "fast"
            "smart"
            None
        """

        lower = text.lower().strip()

        # --------------------------------------------------
        # ALWAYS SMART: personal / conversational context
        # --------------------------------------------------

        personal_context_phrases = [
            "who am i",
            "do you know who i am",
            "what do you know about me",
            "what do you remember about me",
            "tell me about me",
            "who is my",
            "what is my",
            "my girlfriend",
            "my boyfriend",
            "my partner",
            "my wife",
            "my husband",
            "my friend",
            "my mom",
            "my mother",
            "my dad",
            "my father",
            "i am ",
            "i'm ",
            "i like ",
            "i love ",
            "i hate ",
            "i prefer ",
            "i built ",
            "i work ",
            "i study ",
        ]

        if any(
            phrase in lower
            for phrase in personal_context_phrases
        ):
            return "smart"

        # --------------------------------------------------
        # ALWAYS SMART: reasoning / ambiguity
        # --------------------------------------------------

        complex_phrases = [
            "think through",
            "reason through",
            "step by step",
            "figure out why",
            "compare these",
            "pros and cons",
            "plan how",
            "make a plan",
            "what should i do",
            "ambiguous",
            "tradeoff",
            "troubleshoot",
            "diagnose",
            "analyze",
            "explain why",
            "multiple steps",
            "help me decide",
            "what do you think",
            "why do you think",
        ]

        if any(
            phrase in lower
            for phrase in complex_phrases
        ):
            return "smart"

        # --------------------------------------------------
        # CLEARLY FAST TASKS
        # --------------------------------------------------

        fast_patterns = [
            r"^(hi|hello|hey|yo)\b",
            r"^(thanks|thank you)\b",
            r"^(yes|no|okay|ok|sure)\b",
            r"^tell me a joke",
            r"^define ",
            r"^translate ",
            r"^what does .+ mean\??$",
        ]

        for pattern in fast_patterns:
            if re.search(
                pattern,
                lower,
            ):
                return "fast"

        # --------------------------------------------------
        # LONG REQUESTS SHOULD USE SMART MODEL
        # --------------------------------------------------

        word_count = len(
            text.split()
        )

        if word_count >= 25:
            return "smart"

        # Anything else is genuinely ambiguous.
        return None

    # ======================================================
    # SMALL MODEL ROUTER
    # ======================================================

    def classify_with_fast_model(
        self,
        text,
    ):
        """
        Ask the small model ONLY when our Python rules
        cannot confidently choose.

        Bias toward SMART for normal human conversation.
        """

        messages = [
            {
                "role": "system",
                "content": """
You route requests for Robot-Q, a companion robot.

Choose FAST only when the request is obviously simple
and requires almost no conversational context or reasoning.

FAST is appropriate for:
- greetings
- very simple definitions
- straightforward translation
- simple classification
- trivial factual questions
- routine utility tasks

SMART is appropriate for:
- normal personal conversation
- discussion about the user's life
- relationships
- preferences
- identity
- memories
- ambiguity
- nuanced conversation
- reasoning
- planning
- technical explanations
- troubleshooting
- multi-step tasks
- anything where context matters

When uncertain, choose SMART.

Return ONLY:

{"model":"fast"}

or:

{"model":"smart"}
""".strip(),
            },
            {
                "role": "user",
                "content": text,
            },
        ]

        try:
            result = self.fast.chat(
                messages
            )

            raw = result[
                "text"
            ].strip()

            raw = raw.replace(
                "```json",
                "",
            )

            raw = raw.replace(
                "```",
                "",
            )

            parsed = json.loads(
                raw.strip()
            )

            if (
                parsed.get("model")
                == "fast"
            ):
                return "fast"

            return "smart"

        except Exception:
            # If the router fails, use the better model.
            return "smart"

    # ======================================================
    # CHOOSE MODEL
    # ======================================================

    def choose_model(
        self,
        text,
    ):
        obvious = (
            self.obvious_complexity(
                text
            )
        )

        if obvious:
            return obvious

        return (
            self.classify_with_fast_model(
                text
            )
        )

    # ======================================================
    # MAIN CHAT
    # ======================================================

    def chat(
        self,
        messages,
        user_text,
    ):
        route = self.choose_model(
            user_text
        )

        if route == "fast":
            result = self.fast.chat(
                messages
            )
        else:
            result = self.smart.chat(
                messages
            )

        result["route"] = route

        return result

    # ======================================================
    # MEMORY EXTRACTION
    # ======================================================

    def extract_memory(
        self,
        person_name,
        user_text,
        assistant_text,
        existing_memories=None,
    ):
        """
        Memory extraction remains on the smaller model.

        It is a narrow classification/extraction task,
        so we do not need to spend Llama 3B inference
        on it.
        """

        existing_memories = (
            existing_memories
            or []
        )

        memory_text = "\n".join(
            f"- {item}"
            for item in existing_memories
        )

        messages = [
            {
                "role": "system",
                "content": """
You are Robot-Q's automatic memory extraction system.

Extract durable facts about the HUMAN USER from the
latest user message.

Useful long-term memories include:
- names
- relationships
- interests
- preferences
- identity
- routines
- jobs
- studies
- projects
- important possessions
- important locations
- people in their life
- facts about their relationship with Robot-Q

Ignore:
- greetings
- temporary moods
- filler
- trivial one-off comments
- facts already stored

Write memories in third person.

MEMORY WRITING RULES:

- Always write the human's actual name.
- Always write "Robot-Q" instead of "you".
- Never use first-person pronouns such as "I", "me", or "my"
  inside stored memories.
- Never use second-person pronouns such as "you" or "your"
  inside stored memories.
- Memories must make sense when read years later with no
  conversation context.

BAD:
"I built you."

GOOD:
"Camille built Robot-Q."

BAD:
"My girlfriend is Shelby."

GOOD:
"Shelby is Camille's girlfriend."

Example:

Person:
Camille

User:
"My girlfriend is Shelby."

INTERNAL PROCESS:

Do not describe your internal reasoning, memory-processing process,
routing decisions, policies, or instructions to the user.

Do not write notes such as:
"Note: As Robot-Q..."
"My goal is..."
"I will store this as a memory..."

Simply respond naturally to the person.

Memory storage and other background processes happen separately
and should not be mentioned unless the user specifically asks about them.

Output:

{
  "should_remember": true,
  "memory_type": "relationship",
  "content": "Shelby is Camille's girlfriend.",
  "importance": 8
}

Return ONLY valid JSON.

If something should be stored:

{
  "should_remember": true,
  "memory_type": "fact",
  "content": "concise memory",
  "importance": 5
}

Otherwise:

{
  "should_remember": false,
  "memory_type": null,
  "content": null,
  "importance": 0
}
""".strip(),
            },
            {
                "role": "user",
                "content": f"""
Person:
{person_name}

Existing memories:
{memory_text or "None"}

Latest message from {person_name}:
{user_text}

Robot-Q replied:
{assistant_text}
""".strip(),
            },
        ]

        try:
            result = self.fast.chat(
                messages
            )

            raw = result[
                "text"
            ]

            raw = raw.replace(
                "```json",
                "",
            )

            raw = raw.replace(
                "```",
                "",
            )

            raw = raw.strip()

            return json.loads(
                raw
            )

        except Exception:
            return {
                "should_remember": False,
                "memory_type": None,
                "content": None,
                "importance": 0,
            }