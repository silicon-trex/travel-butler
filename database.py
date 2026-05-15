import sqlite3
import json
from typing import Optional, List, Dict, Any

DB_PATH = "travel.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS itineraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT,
            start_date TEXT,
            days INTEGER,
            plan_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_itinerary(destination: str, start_date: str, days: int, plan: Dict[str, Any]) -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO itineraries (destination, start_date, days, plan_json) VALUES (?, ?, ?, ?)",
        (destination, start_date, days, json.dumps(plan, ensure_ascii=False)),
    )
    conn.commit()
    last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return last_id


def get_latest_itinerary() -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT plan_json FROM itineraries ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None


def get_all_itineraries() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, destination, start_date, days, created_at FROM itineraries ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "destination": r[1], "start_date": r[2], "days": r[3], "created_at": r[4]}
        for r in rows
    ]
