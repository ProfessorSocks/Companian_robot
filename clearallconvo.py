python3 - <<'PY'
import sqlite3

conn = sqlite3.connect("data/robot.db")
cur = conn.cursor()

cur.execute("DELETE FROM conversations")

conn.commit()
conn.close()

print("All conversation history cleared.")
PY