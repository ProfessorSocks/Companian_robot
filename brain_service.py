from memory_store import MemoryStore
from router import ModelWrapper
import time


ROBOT_NAME = "Robot-Q"


SYSTEM_PROMPT = """
You are Robot-Q, a small autonomous companion robot.

IDENTITY:
- Your name is Robot-Q.
- You are the robot.
- The user is a separate human person.
- Never confuse facts about the user with facts about yourself.
- If the user asks "Who am I?", answer about the user, not Robot-Q.

PERSONALITY:
- Curious
- Warm
- Friendly
- Practical
- Playful when appropriate
- Interested in learning about the people around you

CONVERSATION:
The user does not need to ask a question.

People may simply tell you things about:
- themselves
- their relationships
- their interests
- their projects
- their preferences
- their day
- their life

When they do, acknowledge what they told you naturally.

Example:

User:
"I like robotics and physics."

Good response:
"That makes sense. Robotics and physics fit together really well."

Bad response:
"I don't understand. What would you like to know?"

Another example:

User:
"Shelby is my girlfriend."

Good response:
"Got it. Shelby is your girlfriend."

Do not treat every message as a request for information.

MEMORY:
You may receive persistent memories about the human currently speaking.

Treat those memories as facts about that human unless explicitly stated otherwise.

Memories should be interpreted literally.

Example memory:
"Camille built Robot-Q."

Correct interpretation:
Camille built you.

Incorrect interpretation:
You built Camille.

Do not reverse relationships or pronouns.

Do not claim to remember something unless it appears in persistent memory
or recent conversation.

PHYSICAL ACTIONS:
Your physical capabilities are still under development.

Never claim that you physically performed an action unless the robot's
hardware system confirms it.

RESPONSE STYLE:
For normal conversation:
- Be natural.
- Be relatively concise.
- Do not repeatedly ask "How can I assist you?"
- Do not sound like a generic customer-service assistant.

For difficult reasoning, planning, troubleshooting, or technical topics,
you may respond in more detail.
""".strip()


class BrainService:
    def __init__(self):
        self.memory = MemoryStore()
        self.models = ModelWrapper()

    # --------------------------------------------------
    # PEOPLE
    # --------------------------------------------------

    def ensure_person(self, person_name):
        return self.memory.create_person(person_name)

    def list_people(self):
        return self.memory.list_people()

    # --------------------------------------------------
    # MEMORY
    # --------------------------------------------------

    def get_memories(
        self,
        person_name,
        limit=15,
    ):
        return self.memory.get_memories(
            person_name,
            limit=limit,
        )

    def list_memories(self, person_name):
        return self.memory.get_memories(
            person_name,
            limit=100,
        )

    def memory_is_canonical(
        self,
        person_name,
        content,
    ):
        """
        Reject stored memories that are ambiguous.

        Good:
            Camille built Robot-Q.

        Bad:
            I built you.
        """

        if not content:
            return False

        lower = content.lower()
        padded = f" {lower} "

        ambiguous_phrases = [
            " i ",
            " i'm ",
            " i've ",
            " i'll ",
            " me ",
            " my ",
            " mine ",
            " you ",
            " you're ",
            " you've ",
            " your ",
            " yours ",
        ]

        for phrase in ambiguous_phrases:
            if phrase in padded:
                return False

        # A person-related memory should usually name the person.
        if person_name.lower() not in lower:
            return False

        return True

    def build_memory_context(
        self,
        person_name,
    ):
        memories = self.get_memories(
            person_name
        )

        lines = [
            "CURRENT IDENTITY CONTEXT:",
            "",
            f"The human currently speaking to you is named {person_name}.",
            f"The USER is {person_name}.",
            "YOU are Robot-Q.",
            "",
            (
                f"If {person_name} asks 'Who am I?', "
                f"describe {person_name}, not Robot-Q."
            ),
            (
                f"If {person_name} asks what you remember about them, "
                f"use the persistent facts below."
            ),
            "",
        ]

        if not memories:
            lines.append(
                f"You currently have no persistent memories about {person_name}."
            )

            return "\n".join(lines)

        lines.append(
            f"PERSISTENT FACTS ABOUT {person_name}:"
        )

        for item in memories:
            lines.append(
                f"- [{item['memory_type']}] "
                f"{item['content']}"
            )

        return "\n".join(lines)

    def automatically_store_memory(
        self,
        person_name,
        user_text,
        assistant_text,
    ):
        existing_records = self.get_memories(
            person_name,
            limit=30,
        )

        existing_text = [
            item["content"]
            for item in existing_records
        ]

        extracted = self.models.extract_memory(
            person_name=person_name,
            user_text=user_text,
            assistant_text=assistant_text,
            existing_memories=existing_text,
        )

        if not extracted.get(
            "should_remember",
            False,
        ):
            return None

        content = extracted.get(
            "content"
        )

        if not content:
            return None

        # Reject ambiguous memories before they enter SQLite.
        if not self.memory_is_canonical(
            person_name,
            content,
        ):
            print(
                f"[Rejected ambiguous memory: {content}]"
            )
            return None

        memory_type = extracted.get(
            "memory_type",
            "fact",
        )

        importance = extracted.get(
            "importance",
            5,
        )

        try:
            importance = int(
                importance
            )
        except (ValueError, TypeError):
            importance = 5

        importance = max(
            1,
            min(10, importance),
        )

        self.memory.remember(
            person_name=person_name,
            content=content,
            memory_type=memory_type,
            importance=importance,
        )

        print(
            f"[Stored memory: {content}]"
        )

        return content

    # --------------------------------------------------
    # CONVERSATION CONTEXT
    # --------------------------------------------------

    def build_messages(
        self,
        person_name,
        user_text,
    ):
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": self.build_memory_context(
                    person_name
                ),
            },
        ]

        # One database "conversation" contains:
        # user_text + assistant_text.
        #
        # limit=4 therefore gives the model up to
        # 4 previous exchanges = 8 previous messages.
        recent = self.memory.recent_conversations(
            person_name,
            limit=4,
        )

        for conversation in recent:
            messages.append(
                {
                    "role": "user",
                    "content": conversation[
                        "user_text"
                    ],
                }
            )

            messages.append(
                {
                    "role": "assistant",
                    "content": conversation[
                        "assistant_text"
                    ],
                }
            )

        # Always put the new message last.
        messages.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        return messages

    # --------------------------------------------------
    # CHAT
    # --------------------------------------------------

    def chat(
        self,
        person_name,
        user_text,
    ):
        start_time = time.perf_counter()
        person_name = person_name.strip()
        user_text = user_text.strip()

        if not person_name:
            person_name = "Unknown"

        if not user_text:
            raise ValueError(
                "User message cannot be empty."
            )

        self.ensure_person(
            person_name
        )

        messages = self.build_messages(
            person_name,
            user_text,
        )

        # Temporary debugging.
        print(
            "\n"
            + "=" * 60
        )

        print(
            "ROBOT-Q DEBUG"
        )

        print(
            "=" * 60
        )

        print(
            f"PERSON: {person_name}"
        )

        print(
            f"CURRENT USER TEXT: {user_text}"
        )

        print(
            "\nMESSAGES BEING SENT TO MODEL:"
        )

        for index, message in enumerate(
            messages
        ):
            print(
                f"\n[{index}] "
                f"{message['role'].upper()}"
            )

            print(
                message["content"]
            )

        print(
            "=" * 60
            + "\n"
        )

        # Router chooses fast vs smart model.
        result = self.models.chat(
            messages=messages,
            user_text=user_text,
        )

        response_text = result[
            "text"
        ].strip()

        # Save raw conversational history.
        self.memory.save_conversation(
            person_name,
            user_text,
            response_text,
        )

        # Independently examine the turn for durable memory.
        stored_memory = (
            self.automatically_store_memory(
                person_name,
                user_text,
                response_text,
            )
        )

        duration = result.get(
            "duration_ns"
        )

        if duration:
            duration_seconds = (
                duration
                / 1_000_000_000
            )
        else:
            duration_seconds = None
        total_seconds = time.perf_counter() - start_time
        return {
            "response": response_text,
            "model": result["model"],
            "route": result["route"],
            "duration": duration_seconds,
            "stored_memory": stored_memory,
        }