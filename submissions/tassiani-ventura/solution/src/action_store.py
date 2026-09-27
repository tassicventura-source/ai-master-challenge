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
CREATE TABLE IF NOT EXISTS crm_accounts (
    account_id TEXT PRIMARY KEY,
    record_origin TEXT NOT NULL DEFAULT 'Cadastro manual',
    account_name TEXT NOT NULL,
    industry TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    referral_source TEXT NOT NULL DEFAULT '',
    referral_detail TEXT NOT NULL DEFAULT '',
    icp_segment TEXT NOT NULL DEFAULT '',
    owner_id TEXT NOT NULL,
    journey_stage TEXT NOT NULL,
    deal_value_estimate REAL,
    deal_currency TEXT NOT NULL DEFAULT 'USD',
    expected_close_date TEXT,
    next_action TEXT NOT NULL DEFAULT '',
    next_action_due_at TEXT,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_crm_accounts_stage_owner ON crm_accounts(journey_stage,owner_id);
CREATE TABLE IF NOT EXISTS crm_interactions (
    interaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES crm_accounts(account_id),
    occurred_at TEXT NOT NULL,
    area TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    outcome TEXT NOT NULL DEFAULT '',
    next_action TEXT NOT NULL DEFAULT '',
    next_action_due_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('Planejada','Concluída','Cancelada')),
    observation TEXT NOT NULL DEFAULT '',
    result TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_crm_interactions_account_date ON crm_interactions(account_id,occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_crm_interactions_owner_due ON crm_interactions(owner_id,status,next_action_due_at);
CREATE TABLE IF NOT EXISTS crm_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('account','interaction')),
    entity_id TEXT NOT NULL,
    event_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    changed_fields_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_crm_events_entity ON crm_events(entity_type,entity_id,event_id);
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


CRM_STAGES = (
    "Lead novo", "Qualificação", "Descoberta", "Proposta", "Negociação",
    "Fechado ganho", "Fechado perdido", "Onboarding", "Ativo", "Renovação", "Encerrado",
)
CRM_CURRENCIES = ("USD", "BRL", "EUR")
INTERACTION_AREAS = (
    "Growth/Marketing", "Comercial", "CS/Onboarding", "Customer Success",
    "Produto", "Suporte", "Finance/RevOps",
)
INTERACTION_TYPES = (
    "Ligação", "E-mail", "Reunião", "Demonstração", "Proposta enviada",
    "Check-in", "Renovação", "Atendimento", "Outro",
)
INTERACTION_STATUSES = ("Planejada", "Concluída", "Cancelada")


def _event(conn: sqlite3.Connection, entity_type: str, entity_id: str,
           event_type: str, changed: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO crm_events(entity_type,entity_id,event_at,event_type,changed_fields_json) VALUES (?,?,?,?,?)",
        (entity_type, entity_id, _timestamp(), event_type, _json(changed)),
    )


def list_crm_accounts(*, query: str = "", stage: str | None = None,
                      owner: str | None = None, path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize(path)
    clauses: list[str] = []
    params: list[Any] = []
    if stage and stage != "Todas":
        clauses.append("journey_stage = ?")
        params.append(stage)
    if owner and owner != "Todos":
        clauses.append("owner_id = ?")
        params.append(owner)
    if query.strip():
        pattern = f"%{query.strip()}%"
        clauses.append("(account_id LIKE ? OR account_name LIKE ? OR owner_id LIKE ? OR referral_detail LIKE ?)")
        params.extend([pattern] * 4)
    sql = "SELECT * FROM crm_accounts"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY CASE journey_stage WHEN 'Lead novo' THEN 1 WHEN 'Qualificação' THEN 2 WHEN 'Descoberta' THEN 3 WHEN 'Proposta' THEN 4 WHEN 'Negociação' THEN 5 WHEN 'Fechado ganho' THEN 6 WHEN 'Onboarding' THEN 7 WHEN 'Ativo' THEN 8 WHEN 'Renovação' THEN 9 WHEN 'Fechado perdido' THEN 10 ELSE 11 END, expected_close_date, account_name COLLATE NOCASE"
    with closing(_connect(path)) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def get_crm_account(account_id: str, *, path: str | Path | None = None) -> dict[str, Any] | None:
    initialize(path)
    with closing(_connect(path)) as conn:
        row = conn.execute("SELECT * FROM crm_accounts WHERE account_id = ?", (account_id,)).fetchone()
        return dict(row) if row else None


def save_crm_account(*, account_name: str, owner_id: str, journey_stage: str,
                     account_id: str | None = None, record_origin: str = "Cadastro manual",
                     industry: str = "", country: str = "", referral_source: str = "",
                     referral_detail: str = "", icp_segment: str = "",
                     deal_value_estimate: float | None = None, deal_currency: str = "USD",
                     expected_close_date: date | str | None = None, next_action: str = "",
                     next_action_due_at: date | str | None = None, notes: str = "",
                     path: str | Path | None = None) -> str:
    account_name = account_name.strip()
    owner_id = owner_id.strip()
    if not account_name or not owner_id:
        raise ValueError("Informe o nome da conta e a pessoa responsável.")
    if journey_stage not in CRM_STAGES:
        raise ValueError("Etapa da jornada inválida.")
    if deal_currency not in CRM_CURRENCIES:
        raise ValueError("Moeda inválida.")
    if deal_value_estimate is not None and float(deal_value_estimate) < 0:
        raise ValueError("O valor estimado não pode ser negativo.")
    if next_action.strip() and not next_action_due_at:
        raise ValueError("Defina o prazo da próxima ação.")
    if not next_action.strip() and next_action_due_at:
        raise ValueError("Informe a próxima ação ou remova o prazo.")
    identity = account_id.strip() if account_id else f"CRM-{uuid.uuid4().hex[:10].upper()}"
    close_iso = date.fromisoformat(str(expected_close_date)).isoformat() if expected_close_date else None
    next_iso = date.fromisoformat(str(next_action_due_at)).isoformat() if next_action_due_at else None
    values = {
        "record_origin": record_origin,
        "account_name": account_name,
        "industry": industry.strip(),
        "country": country.strip(),
        "referral_source": referral_source.strip(),
        "referral_detail": referral_detail.strip(),
        "icp_segment": icp_segment.strip(),
        "owner_id": owner_id,
        "journey_stage": journey_stage,
        "deal_value_estimate": float(deal_value_estimate) if deal_value_estimate is not None else None,
        "deal_currency": deal_currency,
        "expected_close_date": close_iso,
        "next_action": next_action.strip(),
        "next_action_due_at": next_iso,
        "notes": notes.strip(),
    }
    now = _timestamp()
    initialize(path)
    with closing(_connect(path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute("SELECT * FROM crm_accounts WHERE account_id = ?", (identity,)).fetchone()
        if current is None:
            columns = ["account_id", *values, "created_at", "updated_at"]
            params = [identity, *values.values(), now, now]
            conn.execute(
                f"INSERT INTO crm_accounts ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                params,
            )
            _event(conn, "account", identity, "created", values)
        else:
            changed = {key: value for key, value in values.items() if current[key] != value}
            if changed:
                assignments = ",".join(f"{key} = ?" for key in values)
                conn.execute(
                    f"UPDATE crm_accounts SET {assignments}, updated_at = ? WHERE account_id = ?",
                    [*values.values(), now, identity],
                )
                _event(conn, "account", identity, "updated", changed)
        conn.commit()
    return identity


def list_crm_interactions(*, account_id: str | None = None, owner: str | None = None,
                          open_only: bool = False, path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize(path)
    clauses: list[str] = []
    params: list[Any] = []
    if account_id:
        clauses.append("account_id = ?")
        params.append(account_id)
    if owner and owner != "Todos":
        clauses.append("owner_id = ?")
        params.append(owner)
    if open_only:
        clauses.append("status = 'Planejada'")
    sql = "SELECT * FROM crm_interactions"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY CASE WHEN next_action_due_at IS NULL THEN 1 ELSE 0 END, next_action_due_at, occurred_at DESC"
    with closing(_connect(path)) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def save_crm_interaction(*, account_id: str, occurred_at: date | str,
                         area: str, interaction_type: str, summary: str, owner_id: str,
                         outcome: str = "", next_action: str = "",
                         next_action_due_at: date | str | None = None,
                         status: str = "Planejada", observation: str = "",
                         interaction_id: str | None = None,
                         path: str | Path | None = None) -> str:
    if not account_id.strip() or not summary.strip() or not owner_id.strip():
        raise ValueError("Conta, resumo da interação e responsável são obrigatórios.")
    if area not in INTERACTION_AREAS or interaction_type not in INTERACTION_TYPES:
        raise ValueError("Área ou tipo de interação inválido.")
    if status not in INTERACTION_STATUSES:
        raise ValueError("Status da interação inválido.")
    if status == "Concluída" and not outcome.strip():
        raise ValueError("Registre o resultado antes de concluir a interação.")
    if next_action.strip() and not next_action_due_at:
        raise ValueError("Defina o prazo da próxima ação.")
    if not next_action.strip() and next_action_due_at:
        raise ValueError("Informe a próxima ação ou remova o prazo.")
    occurred_iso = date.fromisoformat(str(occurred_at)).isoformat()
    due_iso = date.fromisoformat(str(next_action_due_at)).isoformat() if next_action_due_at else None
    identity = interaction_id or str(uuid.uuid4())
    values = {
        "account_id": account_id.strip(),
        "occurred_at": occurred_iso,
        "area": area,
        "interaction_type": interaction_type,
        "summary": summary.strip(),
        "owner_id": owner_id.strip(),
        "outcome": outcome.strip(),
        "next_action": next_action.strip(),
        "next_action_due_at": due_iso,
        "status": status,
        "observation": observation.strip(),
    }
    now = _timestamp()
    initialize(path)
    with closing(_connect(path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        if not conn.execute("SELECT 1 FROM crm_accounts WHERE account_id = ?", (account_id.strip(),)).fetchone():
            conn.rollback()
            raise ValueError("Cadastre/associe a conta antes de registrar uma interação.")
        current = conn.execute("SELECT * FROM crm_interactions WHERE interaction_id = ?", (identity,)).fetchone()
        if current is None:
            columns = ["interaction_id", *values, "created_at", "updated_at"]
            params = [identity, *values.values(), now, now]
            conn.execute(
                f"INSERT INTO crm_interactions ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                params,
            )
            _event(conn, "interaction", identity, "created", values)
        else:
            changed = {key: value for key, value in values.items() if current[key] != value}
            if changed:
                assignments = ",".join(f"{key} = ?" for key in values)
                conn.execute(
                    f"UPDATE crm_interactions SET {assignments}, updated_at = ? WHERE interaction_id = ?",
                    [*values.values(), now, identity],
                )
                _event(conn, "interaction", identity, "updated", changed)
        conn.commit()
    return identity


def list_crm_events(*, entity_type: str, entity_id: str,
                    path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize(path)
    with closing(_connect(path)) as conn:
        return [dict(row) for row in conn.execute(
            "SELECT event_id,entity_type,entity_id,event_at,event_type,changed_fields_json FROM crm_events WHERE entity_type = ? AND entity_id = ? ORDER BY event_id",
            (entity_type, entity_id),
        ).fetchall()]


def crm_counts(*, path: str | Path | None = None) -> dict[str, int]:
    initialize(path)
    with closing(_connect(path)) as conn:
        accounts = conn.execute("SELECT COUNT(*) FROM crm_accounts").fetchone()[0]
        interactions = conn.execute("SELECT COUNT(*) FROM crm_interactions").fetchone()[0]
        open_followups = conn.execute(
            "SELECT COUNT(*) FROM crm_interactions WHERE status = 'Planejada' AND next_action <> ''"
        ).fetchone()[0]
        open_opportunities = conn.execute(
            "SELECT COUNT(*) FROM crm_accounts WHERE journey_stage IN ('Lead novo','Qualificação','Descoberta','Proposta','Negociação')"
        ).fetchone()[0]
    return {"accounts": accounts, "interactions": interactions,
            "open_followups": open_followups, "open_opportunities": open_opportunities}
