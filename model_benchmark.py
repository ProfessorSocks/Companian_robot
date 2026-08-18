import json
import time

from llm_client import LLMClient


MODELS = [
    "qwen2.5-instruct:1.5b",
    "deepseek_r1_distill_qwen:1.5b",
    "llama3.2:3b",
]


TESTS = [
    {
        "name": "Pets",
        "input": "hey I like cats I have two",
    },
    {
        "name": "Relationship",
        "input": "My girlfriend is Shelby.",
    },
    {
        "name": "Interest",
        "input": "I really enjoy robotics and physics.",
    },
    {
        "name": "Temporary information",
        "input": "I'm tired today.",
    },
    {
        "name": "Robot relationship",
        "input": "I built you and I'm your mom.",
    },
    {
        "name": "Greeting",
        "input": "Hey Q, how are you?",
    },
]


SYSTEM_PROMPT = """
You are a memory extraction component for Robot-Q.

The human currently speaking is named Camille.
The robot is named Robot-Q.

Determine whether the user's message contains durable information
worth remembering about Camille.

Examples of durable information:
- relationships
- interests
- preferences
- important personal facts
- long-term projects
- pets
- facts about Camille's relationship with Robot-Q

Do NOT remember:
- greetings
- temporary moods
- temporary conditions
- ordinary questions
- conversational filler

IMPORTANT:
The memory must be a standalone third-person fact.

Never use:
- I
- me
- my
- you
- your

Use explicit names instead.

Examples:

"My girlfriend is Shelby."
becomes:
"Shelby is Camille's girlfriend."

"I built you."
becomes:
"Camille built Robot-Q."

Return ONLY valid JSON.

If something should be remembered:

{
    "should_remember": true,
    "memory_type": "fact",
    "content": "standalone third-person fact",
    "importance": 5
}

If nothing should be remembered:

{
    "should_remember": false,
    "memory_type": null,
    "content": null,
    "importance": 0
}
""".strip()


def clean_json(text):
    text = text.strip()

    text = text.replace(
        "```json",
        "",
    )

    text = text.replace(
        "```",
        "",
    )

    return text.strip()


def test_model(model_name):
    print("\n")
    print("=" * 70)
    print(f"MODEL: {model_name}")
    print("=" * 70)

    client = LLMClient(
        model_name
    )

    for number, test in enumerate(
        TESTS,
        start=1,
    ):
        print()
        print("-" * 70)
        print(
            f"TEST {number}: {test['name']}"
        )
        print("-" * 70)

        print(
            f"INPUT: {test['input']}"
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": test["input"],
            },
        ]

        start = time.perf_counter()

        try:
            result = client.chat(
                messages
            )

            elapsed = (
                time.perf_counter()
                - start
            )

            raw = result["text"]

            cleaned = clean_json(
                raw
            )

            try:
                parsed = json.loads(
                    cleaned
                )

                valid_json = True

            except json.JSONDecodeError:
                parsed = None
                valid_json = False

            print(
                f"TIME: {elapsed:.2f}s"
            )

            print(
                f"VALID JSON: {valid_json}"
            )

            print(
                "RAW OUTPUT:"
            )

            print(raw)

            if valid_json:
                print(
                    "PARSED:"
                )

                print(
                    json.dumps(
                        parsed,
                        indent=2,
                    )
                )

        except Exception as error:
            elapsed = (
                time.perf_counter()
                - start
            )

            print(
                f"TIME: {elapsed:.2f}s"
            )

            print(
                f"ERROR: {error}"
            )


def main():
    print(
        "\nROBOT-Q MEMORY MODEL BENCHMARK"
    )

    print(
        f"Models: {len(MODELS)}"
    )

    print(
        f"Tests per model: {len(TESTS)}"
    )

    print(
        f"Total tests: {len(MODELS) * len(TESTS)}"
    )

    for model in MODELS:
        test_model(
            model
        )

    print()
    print("=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()