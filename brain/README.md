uvicorn web.app:app --host 0.0.0.0 --port 8765

hailo-ollama

python3 - <<'PY'
import sqlite3

conn = sqlite3.connect("data/robot.db")
cur = conn.cursor()

cur.execute("DELETE FROM conversations")

conn.commit()
conn.close()

print("All conversation history cleared.")
PY

python3 - <<'PY'
import sqlite3

conn = sqlite3.connect("data/robot.db")
cur = conn.cursor()

person = cur.execute(
    "SELECT id FROM people WHERE LOWER(name) = LOWER(?)",
    ("Camille",)
).fetchone()

if person:
    cur.execute(
        "DELETE FROM conversations WHERE person_id = ?",
        (person[0],)
    )
    conn.commit()
    print("Camille's conversation history cleared.")
else:
    print("Camille not found.")

conn.close()
PY