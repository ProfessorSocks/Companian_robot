from pathlib import Path
import sys
import traceback

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Allows imports from the brain/ directory.
sys.path.insert(0, str(PROJECT_DIR))


# ============================================================
# ROBOT-Q IMPORTS
# ============================================================

from brain_service import BrainService
from dev.coder_tool_test import chat as coder_chat


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(title="Robot-Q")


# BrainService remains available for the existing
# people and memory API endpoints.
brain = BrainService()


# ============================================================
# STATIC WEBSITE FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str
    person: str = "Camille"


# ============================================================
# WEBSITE
# ============================================================

@app.get("/")
def home():
    return FileResponse(
        BASE_DIR / "templates" / "index.html"
    )


# ============================================================
# STATUS
# ============================================================

@app.get("/api/status")
def status():
    return {
        "status": "online",
        "robot": "Robot-Q",
        "model": "qwen2.5-coder:1.5b",
        "chat_mode": "coder_tool_test",
    }


# ============================================================
# PEOPLE
# ============================================================

@app.get("/api/people")
def people():
    return {
        "people": brain.list_people()
    }


# ============================================================
# MEMORIES
# ============================================================

@app.get("/api/memories/{person_name}")
def memories(person_name: str):
    return {
        "person": person_name,
        "memories": brain.list_memories(
            person_name
        ),
    }


# ============================================================
# CHAT
# ============================================================

@app.post("/api/chat")
def chat(request: ChatRequest):

    user_text = request.message.strip()
    person_name = request.person.strip()

    if not user_text:
        return {
            "error": "Message cannot be empty."
        }

    if not person_name:
        person_name = "Unknown"

    try:
        # Send the user's message through our experimental
        # Qwen Coder tool/controller system.
        reply = coder_chat(user_text)

        # Keep the response structure compatible with the
        # existing website JavaScript.
        return {
            "response": reply,
            "person": person_name,
            "route": "coder_tool_test",
            "model": "qwen2.5-coder:1.5b",
            "duration": None,
            "stored_memory": None,
        }

    except Exception as error:

        print("\n" + "=" * 70)
        print("ROBOT-Q CODER CHAT ERROR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70 + "\n")

        return {
            "error": str(error)
        }