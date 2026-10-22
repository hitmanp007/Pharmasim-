import sqlite3
from datetime import datetime, timezone
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts(
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, module TEXT NOT NULL,
  scenario_id TEXT NOT NULL, score REAL NOT NULL, possible REAL NOT NULL,
  percent REAL NOT NULL, completed_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id, completed_at);
"""


def init_db(path):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.commit()
    con.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def record_attempt(sid, module, scenario_id, score, possible, percent):
    db = get_db()
    db.execute("INSERT INTO attempts(session_id,module,scenario_id,score,possible,percent,completed_at) VALUES(?,?,?,?,?,?,?)",
               (sid, module, scenario_id, score, possible, percent, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    db.commit()


def history(sid):
    return get_db().execute("SELECT * FROM attempts WHERE session_id=? ORDER BY id DESC LIMIT 100", (sid,)).fetchall()
