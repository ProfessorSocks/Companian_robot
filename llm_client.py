import json
import urllib.request


class LLMClient:
    def __init__(
        self,
        model,
        url="http://localhost:8000/api/chat",
    ):
        self.model = model
        self.url = url

    def chat(self, messages, timeout=180):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        return {
            "text": result["message"]["content"],
            "duration_ns": result.get("total_duration"),
            "model": result.get("model", self.model),
            "raw": result,
        }