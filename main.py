from memory_store import MemoryStore
from router import ModelWrapper


ROBOT_NAME = "Robot-Q"


SYSTEM_PROMPT = """
You are Robot-Q, a small autonomous companion robot.

You are:
- curious
- warm
- friendly
- practical
- playful when appropriate

You are a companion, not merely a question-answering chatbot.

You may receive persistent memories about the person
currently speaking to you. Use those memories naturally.

Do not claim to remember something unless it appears in
the supplied persistent memories or recent conversation.

Your physical capabilities are still under development.
Never claim that you physically performed an action unless
the robot's hardware system confirms that it happened.

Answer concisely for simple questions.
Use more detail when the subject actually requires it.
""".strip()


memory = MemoryStore()
models = ModelWrapper()


def get_memory_records(person_name, limit=15):
    return memory.get_memories(
        person_name,
        limit=limit,
    )


def build_memory_context(person_name):
    memories = get_memory_records(person_name)

    if not memories:
        return (
            f"You are currently talking to {person_name}.\n"
            "There are no persistent memories about this "
            "person yet."
        )

    lines = [
        f"You are currently talking to {person_name}.",
        "",
        "Persistent memories:",
    ]

    for item in memories:
        lines.append(
            f"- [{item['memory_type']}] "
            f"{item['content']}"
        )

    return "\n".join(lines)


def build_messages(
    person_name,
    current_message,
):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "system",
            "content": build_memory_context(
                person_name
            ),
        },
    ]

    recent = memory.recent_conversations(
        person_name,
        limit=4,
    )

    for conversation in recent:
        messages.append(
            {
                "role": "user",
                "content": conversation["user_text"],
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

    messages.append(
        {
            "role": "user",
            "content": current_message,
        }
    )

    return messages


def show_people():
    people = memory.list_people()

    print("\nKnown people:")

    if not people:
        print("  None")

    for person in people:
        print(
            f"  - {person['name']}"
        )

    print()


def show_memories(person_name):
    memories = get_memory_records(
        person_name,
        limit=100,
    )

    print(
        f"\nMemories about {person_name}:"
    )

    if not memories:
        print("  None\n")
        return

    for item in memories:
        print(
            f"  [{item['memory_type']}] "
            f"{item['content']}"
        )

    print()


def automatically_store_memory(
    person_name,
    user_text,
    assistant_text,
):
    existing_records = get_memory_records(
        person_name,
        limit=30,
    )

    existing_text = [
        item["content"]
        for item in existing_records
    ]

    extracted = models.extract_memory(
        person_name=person_name,
        user_text=user_text,
        assistant_text=assistant_text,
        existing_memories=existing_text,
    )

    if not extracted.get(
        "should_remember",
        False,
    ):
        return

    content = extracted.get("content")

    if not content:
        return

    memory_type = extracted.get(
        "memory_type",
        "fact",
    )

    importance = extracted.get(
        "importance",
        5,
    )

    try:
        importance = int(importance)
    except (ValueError, TypeError):
        importance = 5

    importance = max(
        1,
        min(10, importance),
    )

    memory.remember(
        person_name=person_name,
        content=content,
        memory_type=memory_type,
        importance=importance,
    )

    print(
        f"[Robot-Q remembered: {content}]"
    )


def show_help():
    print(
        """
Commands:

/help
    Show commands.

/people
    Show known people.

/person NAME
    Switch current person.

/memories
    Show memories for current person.

/exit
    Quit Robot-Q.
"""
    )


def main():
    print("=" * 55)
    print("Robot-Q Companion Brain V0.2")
    print("Dual-model routing + automatic memory")
    print("=" * 55)

    person_name = input(
        "\nWho is talking to Robot-Q? "
    ).strip()

    if not person_name:
        person_name = "Unknown"

    memory.create_person(person_name)

    print(
        f"\nCurrent person: {person_name}"
    )

    print(
        "Type /help for commands.\n"
    )

    while True:
        try:
            user_input = input(
                f"{person_name}: "
            ).strip()

            if not user_input:
                continue

            lower = user_input.lower()

            # ----------------------------------
            # EXIT
            # ----------------------------------

            if lower in {
                "/exit",
                "/quit",
                "exit",
                "quit",
            }:
                print(
                    f"\n{ROBOT_NAME}: "
                    "See you later!"
                )
                break

            # ----------------------------------
            # HELP
            # ----------------------------------

            if lower == "/help":
                show_help()
                continue

            # ----------------------------------
            # PEOPLE
            # ----------------------------------

            if lower == "/people":
                show_people()
                continue

            # ----------------------------------
            # MEMORIES
            # ----------------------------------

            if lower == "/memories":
                show_memories(person_name)
                continue

            # ----------------------------------
            # SWITCH PERSON
            # ----------------------------------

            if lower.startswith(
                "/person "
            ):
                new_name = user_input[
                    len("/person "):
                ].strip()

                if new_name:
                    memory.create_person(
                        new_name
                    )

                    person_name = new_name

                    print(
                        f"\nCurrent person: "
                        f"{person_name}\n"
                    )

                continue

            # ----------------------------------
            # BUILD CONTEXT
            # ----------------------------------

            messages = build_messages(
                person_name,
                user_input,
            )

            print(
                f"\n{ROBOT_NAME} is thinking..."
            )

            # ----------------------------------
            # AUTOMATIC MODEL ROUTING
            # ----------------------------------

            result = models.chat(
                messages=messages,
                user_text=user_input,
            )

            response_text = result["text"]
            route = result["route"]
            model_name = result["model"]

            print(
                f"\n{ROBOT_NAME}: "
                f"{response_text}\n"
            )

            print(
                f"[Model: {model_name}]"
            )

            print(
                f"[Route: {route}]"
            )

            duration = result.get(
                "duration_ns"
            )

            if duration:
                seconds = (
                    duration
                    / 1_000_000_000
                )

                print(
                    f"[Inference: "
                    f"{seconds:.2f}s]"
                )

            # ----------------------------------
            # SAVE CONVERSATION
            # ----------------------------------

            memory.save_conversation(
                person_name,
                user_input,
                response_text,
            )

            # ----------------------------------
            # AUTOMATIC MEMORY EXTRACTION
            # ----------------------------------

            print(
                "[Checking for useful memory...]"
            )

            automatically_store_memory(
                person_name,
                user_input,
                response_text,
            )

            print()

        except KeyboardInterrupt:
            print(
                f"\n\n{ROBOT_NAME}: "
                "Shutting down."
            )
            break

        except Exception as error:
            print(
                f"\nRobot-Q error: "
                f"{error}\n"
            )

    memory.close()


if __name__ == "__main__":
    main()