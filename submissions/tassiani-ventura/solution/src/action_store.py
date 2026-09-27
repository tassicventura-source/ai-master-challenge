from __future__ import annotations

"""SQLite-backed demo action log. Replace with a shared authenticated service in production."""

from datetime import date, datetime, timezone
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import uuid
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("RETENTION_DB_PATH", str(ROOT / "data" / "retention_actions.sqlite")))
STATUSES = ("Aberta", "Em andamento", "Bloqueada", "Concluída", "Cancelada")

SCHEMA = """
CREATE TABLE IF NOT EXISTS retention_actions (
    action_id TEXT PRIMARY KEY,
    signal_id TEXT NOT NULL,
    area TEXT NOT NULL,
    account_id TEXT NOT NULL,
    account_name TEXT NOT NULL,
    title TEXT NOT NULL,
    action_text TEXT NOT NULL,
    owner TEXT NOT NULL,
    priority TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Aberta','Em andamento','Bloqueada','Concluída','Cancelada')),
    observation TEXT NOT NULL DEFAULT '',
    result TEXT NOT NULL DEFAULT '',
    signal_snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_retention_actions_signal ON retention_actions(signal_id);
CREATE INDEX IF NOT EXISTS idx_retention_actions_area_status_due ON retention_actions(area,status,due_date);
CREATE TABLE IF NOT EXISTS retention_action_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id TEXT NOT NULL REFERENCES retention_actions(action_id),
    event_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    changed_fields_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_action_events_action ON retention_action_events(action_id,event_id);
"""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect(path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(path) if path is not None else DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def initialize(path: str | Path | None = None) -> None:
    with closing(_connect(path)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def list_actions(*, area: str | None = None, signal_id: str | None = None,
                 open_only: bool = False, path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize(path)
    clauses: list[str] = []
    params: list[Any] = []
    if area:
        clauses.append("area = ?")
        params.append(area)
    if signal_id:
        clauses.append("signal_id = ?")
        params.append(signal_id)
    if open_only:
        clauses.append("status NOT IN ('Concluída','Cancelada')")
    query = "SELECT * FROM retention_actions"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY CASE priority WHEN 'P1 — verificar primeiro' THEN 1 WHEN 'P2 — próxima execução' THEN 2 ELSE 3 END, due_date, updated_at DESC"
    with closing(_connect(path)) as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def save_action(*, signal: dict[str, Any], action_text: str, owner: str,
                priority: str, due_date: date | str, status: str,
                observation: str = "", result: str = "",
                action_id: str | None = None, path: str | Path | None = None) -> str:
    """Insert or update an action and append an immutable change-log event."""
    required = {
        "owner": owner.strip(), "action_text": action_text.strip(),
        "account_id": str(signal.get("account_id", "")).strip(),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise ValueError("Preencha responsável, ação e conta.")
    if status not in STATUSES:
        raise ValueError("Status inválido.")
    if status == "Concluída" and not result.strip():
        raise ValueError("Registre o resultado antes de concluir a ação.")
    if isinstance(due_date, date):
        due_iso = due_date.isoformat()
    else:
        due_iso = date.fromisoformat(str(due_date)).isoformat()
    signal_id = str(signal.get("signal_id", "")).strip()
    if not signal_id:
        raise ValueError("Sinal sem identificador estável.")
    now = _timestamp()
    action_id = action_id or str(uuid.uuid4())
    snapshot = _json(signal)
    values = {
        "signal_id": signal_id,
        "area": str(signal.get("area", "")),
        "account_id": required["account_id"],
        "account_name": str(signal.get("account_name", required["account_id"])),
        "title": str(signal.get("title", "")),
        "action_text": required["action_text"],
        "owner": required["owner"],
        "priority": str(priority),
        "due_date": due_iso,
        "status": status,
        "observation": observation.strip(),
        "result": result.strip(),
        "signal_snapshot_json": snapshot,
    }
    if values["priority"] not in ("P1 — verificar primeiro", "P2 — próxima execução", "P3 — revisão planejada"):
        raise ValueError("Prioridade inválida.")

    initialize(path)
    with closing(_connect(path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute("SELECT * FROM retention_actions WHERE action_id=?", (action_id,)).fetchone()
        if current is None:
            conn.execute(
                """INSERT INTO retention_actions (
                    action_id,signal_id,area,account_id,account_name,title,action_text,owner,priority,
                    due_date,status,observation,result,signal_snapshot_json,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (action_id, values["signal_id"], values["area"], values["account_id"], values["account_name"],
                 values["title"], values["action_text"], values["owner"], values["priority"],
                 values["due_date"], values["status"], values["observation"], values["result"], snapshot, now, now),
            )
            event_type = "created"
            changed = values | {"signal_snapshot_json": signal}
        else:
            if current["signal_id"] != signal_id:
                raise ValueError("A ação não pode ser associada a outro sinal.")
            changed = {k: v for k, v in values.items() if current[k] != v}
            if changed:
                conn.execute(
                    """UPDATE retention_actions SET
                        action_text=?,owner=?,priority=?,due_date=?,status=?,observation=?,result=?,
                        signal_snapshot_json=?,updated_at=? WHERE action_id=?""",
                    (values["action_text"], values["owner"], values["priority"], values["due_date"],
                     values["status"], values["observation"], values["result"], snapshot, now, action_id),
                )
            event_type = "updated" if changed else "unchanged"
        conn.execute(
            "INSERT INTO retention_action_events(action_id,event_at,event_type,changed_fields_json) VALUES (?,?,?,?)",
            (action_id, now, event_type, _json(changed)),
        )
        conn.commit()
    return action_id


def list_events(action_id: str, *, path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize(path)
    with closing(_connect(path)) as conn:
        return [dict(row) for row in conn.execute(
            "SELECT event_id,action_id,event_at,event_type,changed_fields_json FROM retention_action_events WHERE action_id=? ORDER BY event_id",
            (action_id,),
        ).fetchall()]


def actions_frame(actions: list[dict[str, Any]]):
    """Return a clean table frame without exposing the stored JSON snapshot."""
    import pandas as pd
    if not actions:
        return pd.DataFrame(columns=["area", "account_name", "title", "action_text", "owner", "priority", "due_date", "status", "observation", "result", "updated_at"])
    frame = pd.DataFrame(actions)
    return frame.drop(columns=["signal_snapshot_json"], errors="ignore")
