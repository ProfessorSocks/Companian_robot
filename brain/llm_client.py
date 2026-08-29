import json
import threading
import urllib.request
from urllib.error import HTTPError, URLError


# --------------------------------------------------
# GLOBAL HAILO LOCK
# --------------------------------------------------

# Hailo-Ollama / the Hailo device should only be handling
# one model request at a time.
#
# This lock is shared by ALL LLMClient instances:
#
#   Qwen
#   Llama
#   DeepSeek
#   etc.
#
# If one model is currently using Hailo, another request
# waits here until the first request finishes.

HAILO_LOCK = threading.RLock()


class LLMClient:
    def __init__(
        self,
        model,
        url="http://localhost:8000/api/chat",
    ):
        self.model = model
        self.url = url

    def chat(
        self,
        messages,
        timeout=180,
    ):
        # --------------------------------------------------
        # BUILD REQUEST
        # --------------------------------------------------

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        # --------------------------------------------------
        # REQUEST INFORMATION
        # --------------------------------------------------

        total_characters = sum(
            len(
                message.get(
                    "content",
                    "",
                )
            )
            for message in messages
        )

        total_words = sum(
            len(
                message.get(
                    "content",
                    "",
                ).split()
            )
            for message in messages
        )

        # --------------------------------------------------
        # SEND REQUEST
        # --------------------------------------------------

        try:
            # Only ONE Hailo request may run inside
            # this block at a time.
            with HAILO_LOCK:

                print()
                print(
                    f"[Hailo lock acquired: "
                    f"{self.model}]"
                )

                with urllib.request.urlopen(
                    request,
                    timeout=timeout,
                ) as response:

                    response_text = (
                        response
                        .read()
                        .decode(
                            "utf-8"
                        )
                    )

                    result = json.loads(
                        response_text
                    )

                print(
                    f"[Hailo request complete: "
                    f"{self.model}]"
                )

        # --------------------------------------------------
        # HAILO RETURNED AN HTTP ERROR
        # --------------------------------------------------

        except HTTPError as error:
            try:
                error_body = (
                    error
                    .read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )

            except Exception:
                error_body = (
                    "<Could not read response body>"
                )

            print()
            print("=" * 70)
            print("HAILO-OLLAMA HTTP ERROR")
            print("=" * 70)

            print(
                f"Model: {self.model}"
            )

            print(
                f"URL: {self.url}"
            )

            print(
                f"Status: {error.code}"
            )

            print(
                f"Reason: {error.reason}"
            )

            print()
            print("RESPONSE BODY:")
            print(error_body)

            print()
            print("REQUEST INFORMATION:")

            print(
                f"Messages: "
                f"{len(messages)}"
            )

            print(
                f"Characters: "
                f"{total_characters}"
            )

            print(
                f"Approximate words: "
                f"{total_words}"
            )

            print("=" * 70)
            print()

            raise

        # --------------------------------------------------
        # COULD NOT CONNECT TO HAILO
        # --------------------------------------------------

        except URLError as error:
            print()
            print("=" * 70)
            print(
                "HAILO-OLLAMA CONNECTION ERROR"
            )
            print("=" * 70)

            print(
                f"Model: {self.model}"
            )

            print(
                f"URL: {self.url}"
            )

            print(
                f"Reason: {error.reason}"
            )

            print()
            print("REQUEST INFORMATION:")

            print(
                f"Messages: "
                f"{len(messages)}"
            )

            print(
                f"Characters: "
                f"{total_characters}"
            )

            print(
                f"Approximate words: "
                f"{total_words}"
            )

            print("=" * 70)
            print()

            raise

        # --------------------------------------------------
        # VALIDATE RESPONSE
        # --------------------------------------------------

        if "message" not in result:
            raise RuntimeError(
                "Hailo-Ollama response did not "
                "contain a 'message' field."
            )

        if "content" not in result["message"]:
            raise RuntimeError(
                "Hailo-Ollama response did not "
                "contain message content."
            )

        # --------------------------------------------------
        # RETURN NORMALIZED RESULT
        # --------------------------------------------------

        return {
            "text": result[
                "message"
            ][
                "content"
            ],

            "duration_ns": result.get(
                "total_duration"
            ),

            "model": result.get(
                "model",
                self.model,
            ),

            "raw": result,
        }