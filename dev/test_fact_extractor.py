import sys
import time
from pathlib import Path


# --------------------------------------------------
# PROJECT PATH
# --------------------------------------------------

# This file lives in:
# Companian_Robot/dev/test_fact_extractor.py
#
# parents[1] points to:
# Companian_Robot/

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

from llm_client import LLMClient
from prompt_loader import (
    load_text_prompt,
    render_prompt,
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MODEL = "qwen2.5-instruct:1.5b"

DEFAULT_PERSON = "Camille"

PROMPT_FILE = "memory/extractor.txt"


# --------------------------------------------------
# LOAD PROMPT TEMPLATE
# --------------------------------------------------

template = load_text_prompt(
    PROMPT_FILE
)


# --------------------------------------------------
# MODEL CLIENT
# --------------------------------------------------

client = LLMClient(
    MODEL
)


# --------------------------------------------------
# RUN ONE TEST
# --------------------------------------------------

def run_test(
    person_name,
    user_message,
):
    prompt = render_prompt(
        template,
        person_name=person_name,
        user_message=user_message,
    )

    messages = [
        {
            "role": "system",
            "content": prompt,
        }
    ]

    print()
    print("=" * 70)
    print("ROBOT-Q FACT EXTRACTOR TEST")
    print("=" * 70)

    print()
    print("MODEL:")
    print(MODEL)

    print()
    print("PERSON:")
    print(person_name)

    print()
    print("INPUT:")
    print(user_message)

    print()
    print("Running model...")

    start_time = time.perf_counter()

    try:
        result = client.chat(
            messages
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print()
        print("OUTPUT:")
        print(result["text"])

        print()
        print(
            f"TOTAL TEST TIME: "
            f"{elapsed:.2f} seconds"
        )

        if result.get("duration_ns"):
            inference_seconds = (
                result["duration_ns"]
                / 1_000_000_000
            )

            print(
                f"HAILO INFERENCE TIME: "
                f"{inference_seconds:.2f} seconds"
            )

        print()
        print("=" * 70)

    except Exception as error:
        elapsed = (
            time.perf_counter()
            - start_time
        )

        print()
        print("ERROR:")
        print(error)

        print()
        print(
            f"FAILED AFTER: "
            f"{elapsed:.2f} seconds"
        )

        print()
        print("=" * 70)


# --------------------------------------------------
# INTERACTIVE TEST LOOP
# --------------------------------------------------

def main():
    print()
    print("=" * 70)
    print("ROBOT-Q FACT EXTRACTOR LAB")
    print("=" * 70)

    print()
    print(f"Model: {MODEL}")
    print(f"Default person: {DEFAULT_PERSON}")

    print()
    print("Type a sentence to test.")

    print()
    print("Commands:")
    print("  /exit")
    print("      Quit the tester.")
    print()
    print("  /person NAME")
    print("      Change the person being tested.")
    print()
    print("  /prompt")
    print("      Show the full rendered prompt for the next test.")
    print()

    person_name = DEFAULT_PERSON
    show_prompt = False

    while True:
        print()
        user_message = input(
            f"{person_name}> "
        ).strip()

        if not user_message:
            continue

        # ------------------------------------------
        # EXIT
        # ------------------------------------------

        if user_message.lower() in {
            "/exit",
            "/quit",
        }:
            print()
            print("Exiting fact extractor lab.")
            break

        # ------------------------------------------
        # CHANGE PERSON
        # ------------------------------------------

        if user_message.lower().startswith(
            "/person "
        ):
            new_name = user_message[
                len("/person "):
            ].strip()

            if new_name:
                person_name = new_name

                print(
                    f"Current person changed to: "
                    f"{person_name}"
                )

            continue

        # ------------------------------------------
        # SHOW PROMPT NEXT TIME
        # ------------------------------------------

        if user_message.lower() == "/prompt":
            show_prompt = not show_prompt

            print(
                f"Show full prompt: "
                f"{show_prompt}"
            )

            continue

        # ------------------------------------------
        # OPTIONAL PROMPT DISPLAY
        # ------------------------------------------

        if show_prompt:
            rendered = render_prompt(
                template,
                person_name=person_name,
                user_message=user_message,
            )

            print()
            print("-" * 70)
            print("RENDERED PROMPT")
            print("-" * 70)
            print(rendered)
            print("-" * 70)

        # ------------------------------------------
        # RUN TEST
        # ------------------------------------------

        run_test(
            person_name,
            user_message,
        )


if __name__ == "__main__":
    main()