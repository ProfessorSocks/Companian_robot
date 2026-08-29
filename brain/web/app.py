from pathlib import Path
import sys

from fastapi import (
    FastAPI,
    BackgroundTasks,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))

from brain_service import BrainService


app = FastAPI(title="Robot-Q")

brain = BrainService()


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)



class ChatRequest(BaseModel):
    message: str
    person: str = "Camille"


@app.get("/")
def home():
    return FileResponse(
        BASE_DIR / "templates" / "index.html"
    )


@app.get("/api/status")
def status():
    return {
        "status": "online",
        "robot": "Robot-Q",
    }


@app.get("/api/people")
def people():
    return {
        "people": brain.list_people()
    }


@app.get("/api/memories/{person_name}")
def memories(person_name: str):
    return {
        "person": person_name,
        "memories": brain.list_memories(
            person_name
        ),
    }


@app.post("/api/chat")
def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
):
    user_text = request.message.strip()
    person_name = request.person.strip()

    if not user_text:
        return {
            "error": "Message cannot be empty."
        }

    if not person_name:
        person_name = "Unknown"

    try:
        result = brain.chat(
            person_name=person_name,
            user_text=user_text,
        )

        # Only rebuild memories.md when a new
        # persistent memory was actually stored.
        if result.get("stored_memory"):
            background_tasks.add_task(
                brain.export_person_memories,
                person_name,
            )

        return result

    except Exception as error:
        import traceback

        print("\n" + "=" * 70)
        print("ROBOT-Q CHAT ERROR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70 + "\n")

        return {
            "error": str(error)
        }