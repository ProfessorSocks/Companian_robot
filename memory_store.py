import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PEOPLE_DIR = DATA_DIR / "people"
DATABASE_PATH = DATA_DIR / "robot.db"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_folder_name(name):
    cleaned = ""

    for char in name.lower().strip():
        if char.isalnum():
            cleaned += char
        elif char in {" ", "-", "_"}:
            cleaned += "_"

    return cleaned.strip("_")


class MemoryStore:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        PEOPLE_DIR.mkdir(exist_ok=True)

        self.connection = sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False,
        )

        self.connection.row_factory = sqlite3.Row

        self.lock = threading.RLock()

        self.create_tables()

    # --------------------------------------------------
    # DATABASE SETUP
    # --------------------------------------------------

    def create_tables(self):
        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS people (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    folder_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,

                    FOREIGN KEY(person_id)
                        REFERENCES people(id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER,
                    user_text TEXT NOT NULL,
                    assistant_text TEXT NOT NULL,
                    created_at TEXT NOT NULL,

                    FOREIGN KEY(person_id)
                        REFERENCES people(id)
                )
                """
            )

            self.connection.commit()

    # --------------------------------------------------
    # PEOPLE
    # --------------------------------------------------

    def create_person(
        self,
        name,
        relationship="unknown",
    ):
        name = name.strip()

        if not name:
            name = "Unknown"

        existing = self.get_person(name)

        if existing:
            return existing

        folder_name = safe_folder_name(name)
        person_dir = PEOPLE_DIR / folder_name

        faces_dir = person_dir / "faces"
        voice_dir = person_dir / "voice"
        notes_dir = person_dir / "notes"

        person_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        faces_dir.mkdir(exist_ok=True)
        voice_dir.mkdir(exist_ok=True)
        notes_dir.mkdir(exist_ok=True)

        profile = {
            "name": name,
            "relationship": relationship,
            "created_at": now_iso(),
            "face_recognition_enabled": False,
            "voice_recognition_enabled": False,
        }

        profile_path = person_dir / "profile.json"

        if not profile_path.exists():
            profile_path.write_text(
                json.dumps(
                    profile,
                    indent=2,
                ),
                encoding="utf-8",
            )

        memories_path = person_dir / "memories.md"

        if not memories_path.exists():
            memories_path.write_text(
                f"# Memories about {name}\n\n",
                encoding="utf-8",
            )

        with self.lock:
            cursor = self.connection.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO people (
                        name,
                        folder_path,
                        created_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        name,
                        str(person_dir),
                        now_iso(),
                    ),
                )

                self.connection.commit()

            except sqlite3.IntegrityError:
                # Another request may have created
                # the same person at the same time.
                pass

        return self.get_person(name)

    def get_person(self, name):
        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM people
                WHERE LOWER(name) = LOWER(?)
                """,
                (name.strip(),),
            )

            row = cursor.fetchone()

        return dict(row) if row else None

    def list_people(self):
        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM people
                ORDER BY name
                """
            )

            rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # --------------------------------------------------
    # MEMORIES
    # --------------------------------------------------

    def remember(
        self,
        person_name,
        content,
        memory_type="fact",
        importance=5,
    ):
        content = content.strip()

        if not content:
            return

        person = self.create_person(
            person_name
        )

        try:
            importance = int(importance)
        except (TypeError, ValueError):
            importance = 5

        importance = max(
            1,
            min(10, importance),
        )

        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                INSERT INTO memories (
                    person_id,
                    memory_type,
                    content,
                    importance,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    person["id"],
                    memory_type,
                    content,
                    importance,
                    now_iso(),
                ),
            )

            self.connection.commit()

    def _sync_memories_markdown(
        self,
        person,
    ):
        """
        Rebuild memories.md from SQLite.

        SQLite is the authoritative memory store.
        The Markdown file is a human-readable mirror.
        """

        person_dir = Path(
            person["folder_path"]
        )

        memories_file = (
            person_dir / "memories.md"
        )

        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                SELECT
                    memory_type,
                    content,
                    importance,
                    created_at
                FROM memories
                WHERE person_id = ?
                ORDER BY
                    importance DESC,
                    id ASC
                """,
                (
                    person["id"],
                ),
            )

            rows = cursor.fetchall()

        lines = [
            f"# Memories about {person['name']}",
            "",
        ]

        for row in rows:
            lines.append(
                f"- **{row['memory_type']}:** "
                f"{row['content']}"
            )

        # Always finish the file with a newline.
        text = "\n".join(lines) + "\n"

        with self.lock:
            memories_file.write_text(
                text,
                encoding="utf-8",
            )

    def get_memories(
        self,
        person_name,
        limit=20,
    ):
        person = self.get_person(
            person_name
        )

        if not person:
            return []

        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM memories
                WHERE person_id = ?
                ORDER BY
                    importance DESC,
                    id DESC
                LIMIT ?
                """,
                (
                    person["id"],
                    limit,
                ),
            )

            rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # --------------------------------------------------
    # CONVERSATIONS
    # --------------------------------------------------

    def save_conversation(
        self,
        person_name,
        user_text,
        assistant_text,
    ):
        person = self.create_person(
            person_name
        )

        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                INSERT INTO conversations (
                    person_id,
                    user_text,
                    assistant_text,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    person["id"],
                    user_text.strip(),
                    assistant_text.strip(),
                    now_iso(),
                ),
            )

            self.connection.commit()

    def recent_conversations(
        self,
        person_name,
        limit=5,
    ):
        person = self.get_person(
            person_name
        )

        if not person:
            return []

        with self.lock:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM conversations
                WHERE person_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    person["id"],
                    limit,
                ),
            )

            rows = cursor.fetchall()

        rows = list(reversed(rows))

        return [
            dict(row)
            for row in rows
        ]

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    def close(self):
        with self.lock:
            self.connection.close()

    def export_memories_markdown(
        self,
        person_name,
    ):
        """
        Export a person's current SQLite memories
        into their memories.md file.

        SQLite remains the source of truth.
        """

        person = self.get_person(
            person_name
        )

        if not person:
            return False

        memories = self.get_memories(
            person_name,
            limit=10000,
        )

        person_dir = Path(
            person["folder_path"]
        )

        memories_file = (
            person_dir / "memories.md"
        )

        lines = [
            f"# Memories about {person_name}",
            "",
        ]

        for item in memories:
            lines.append(
                f"- **{item['memory_type']}:** "
                f"{item['content']}"
            )

        text = "\n".join(lines) + "\n"

        with self.lock:
            memories_file.write_text(
                text,
                encoding="utf-8",
            )

        return True