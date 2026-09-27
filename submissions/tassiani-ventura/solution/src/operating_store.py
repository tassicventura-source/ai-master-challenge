from __future__ import annotations

"""Canonical customer-journey store: local SQLite demo or managed PostgreSQL.

Raw/processed analytics remain read-only. A field becomes operational truth only
when created natively or explicitly confirmed by an operator.
"""

from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable
import uuid

from sqlalchemy import (
    Boolean, Column, Date, Float, ForeignKey, Index, Integer, MetaData, String,
    Table, Text, UniqueConstraint, and_, create_engine, delete, event, func,
    insert, select, update,
)
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DEFAULT_DB_PATH = Path(os.getenv("RETENTION_DB_PATH", str(ROOT / "data" / "retention_actions.sqlite")))
LIFECYCLES = ("onboarding", "active", "paused", "churned")
HEALTH_STATES = ("normal", "atenção", "crítica")
VERIFICATION_STATES = ("not_validated", "partially_validated", "validated", "conflict")
TASK_STATUSES = ("open", "in_progress", "completed", "cancelled")
TASK_PRIORITIES = ("P1", "P2", "P3")
MOVEMENTS = ("renewal", "pause", "total_loss", "reactivation", "admin_end")
PLANS = ("Basic", "Pro", "Enterprise", "Custom", "Outro")
CURRENCIES = ("USD", "BRL", "EUR")
BILLING_FREQUENCIES = ("monthly", "quarterly", "annual", "other")

metadata = MetaData()
customers = Table(
    "op_customers", metadata,
    Column("customer_id", String(80), primary_key=True),
    Column("name", String(300), nullable=False),
    Column("industry", String(200), nullable=True),
    Column("country", String(100), nullable=True),
    Column("referral_source", String(120), nullable=True),
    Column("signup_date", Date, nullable=True),
    Column("lifecycle_status", String(40), nullable=True),
    Column("health_status", String(40), nullable=True),
    Column("owner", String(240), nullable=True),
    Column("verification_status", String(40), nullable=False),
    Column("verification_fields_json", Text, nullable=False, default="{}"),
    Column("origin", String(40), nullable=False),
    Column("sales_stage", String(80), nullable=True),
    Column("opportunity_value_estimate", Float, nullable=True),
    Column("opportunity_currency", String(8), nullable=True),
    Column("expected_close_date", Date, nullable=True),
    Column("notes", Text, nullable=True),
    Column("archived_at", String(40), nullable=True),
    Column("created_at", String(40), nullable=False),
    Column("updated_at", String(40), nullable=False),
)
Index("ix_op_customers_owner", customers.c.owner)
Index("ix_op_customers_lifecycle", customers.c.lifecycle_status)
Index("ix_op_customers_verification", customers.c.verification_status)

subscriptions = Table(
    "op_subscriptions", metadata,
    Column("subscription_id", String(80), primary_key=True),
    Column("customer_id", String(80), ForeignKey("op_customers.customer_id"), nullable=False),
    Column("contract_id", String(120), nullable=True),
    Column("plan_tier", String(80), nullable=True),
    Column("seats", Integer, nullable=True),
    Column("mrr_current", Float, nullable=True),
    Column("currency", String(8), nullable=True),
    Column("billing_frequency", String(40), nullable=True),
    Column("effective_from", Date, nullable=True),
    Column("effective_to", Date, nullable=True),
    Column("renewal_date", Date, nullable=True),
    Column("status", String(30), nullable=False),
    Column("verification_status", String(40), nullable=False),
    Column("confirmed_fields_json", Text, nullable=False, default="[]"),
    Column("movement_type", String(40), nullable=True),
    Column("source", String(40), nullable=False),
    Column("created_at", String(40), nullable=False),
)
Index("ix_op_subscriptions_customer_status", subscriptions.c.customer_id, subscriptions.c.status)

interactions = Table(
    "op_interactions", metadata,
    Column("interaction_id", String(80), primary_key=True),
    Column("customer_id", String(80), ForeignKey("op_customers.customer_id"), nullable=False),
    Column("interaction_type", String(60), nullable=False),
    Column("occurred_at", String(40), nullable=False),
    Column("summary", Text, nullable=False),
    Column("actor", String(240), nullable=False),
    Column("obstacle", Text, nullable=True),
    Column("outcome", Text, nullable=True),
    Column("source", String(40), nullable=False),
    Column("created_at", String(40), nullable=False),
)
Index("ix_op_interactions_customer_time", interactions.c.customer_id, interactions.c.occurred_at)

tasks = Table(
    "op_tasks", metadata,
    Column("task_id", String(80), primary_key=True),
    Column("customer_id", String(80), ForeignKey("op_customers.customer_id"), nullable=False),
    Column("title", String(500), nullable=False),
    Column("owner", String(240), nullable=False),
    Column("due_date", Date, nullable=False),
    Column("priority", String(8), nullable=False),
    Column("status", String(30), nullable=False),
    Column("created_from", String(80), nullable=True),
    Column("created_at", String(40), nullable=False),
    Column("completed_at", String(40), nullable=True),
    Column("completion_note", Text, nullable=True),
)
Index("ix_op_tasks_status_due", tasks.c.status, tasks.c.due_date)
Index("ix_op_tasks_owner_status", tasks.c.owner, tasks.c.status)
Index("ix_op_tasks_customer", tasks.c.customer_id)

alerts = Table(
    "op_alerts", metadata,
    Column("alert_id", String(80), primary_key=True),
    Column("alert_key", String(240), nullable=False, unique=True),
    Column("customer_id", String(80), ForeignKey("op_customers.customer_id"), nullable=False),
    Column("task_id", String(80), ForeignKey("op_tasks.task_id"), nullable=True),
    Column("alert_type", String(80), nullable=False),
    Column("severity", String(20), nullable=False),
    Column("reason", Text, nullable=False),
    Column("status", String(30), nullable=False),
    Column("created_at", String(40), nullable=False),
    Column("updated_at", String(40), nullable=False),
    Column("treated_at", String(40), nullable=True),
    Column("treated_by", String(240), nullable=True),
    Column("treatment_note", Text, nullable=True),
)
Index("ix_op_alerts_status_severity", alerts.c.status, alerts.c.severity)
Index("ix_op_alerts_customer", alerts.c.customer_id)

journey_events = Table(
    "op_journey_events", metadata,
    Column("event_id", String(80), primary_key=True),
    Column("customer_id", String(80), ForeignKey("op_customers.customer_id"), nullable=False),
    Column("event_type", String(100), nullable=False),
    Column("occurred_at", String(40), nullable=False),
    Column("actor", String(240), nullable=False),
    Column("source", String(80), nullable=False),
    Column("summary", Text, nullable=False),
    Column("previous_value_json", Text, nullable=False, default="{}"),
    Column("new_value_json", Text, nullable=False, default="{}"),
    Column("mrr_delta", Float, nullable=True),
    Column("related_entity_type", String(60), nullable=True),
    Column("related_entity_id", String(80), nullable=True),
)
Index("ix_op_events_customer_time", journey_events.c.customer_id, journey_events.c.occurred_at)

source_imports = Table(
    "op_source_imports", metadata,
    Column("source_table", String(80), primary_key=True),
    Column("file_hash", String(64), primary_key=True),
    Column("row_count", Integer, nullable=False),
    Column("imported_at", String(40), nullable=False),
)
source_records = Table(
    "op_source_records", metadata,
    Column("source_record_id", String(64), primary_key=True),
    Column("source_table", String(80), nullable=False),
    Column("source_key", String(240), nullable=False),
    Column("source_file_hash", String(64), nullable=False),
    Column("row_number", Integer, nullable=False),
    Column("customer_id", String(80), ForeignKey("op_customers.customer_id"), nullable=False),
    Column("raw_payload_json", Text, nullable=False),
    Column("imported_at", String(40), nullable=False),
    UniqueConstraint("source_table", "source_file_hash", "row_number", name="uq_op_source_row"),
)
Index("ix_op_source_customer_table", source_records.c.customer_id, source_records.c.source_table)

migrations = Table(
    "op_schema_migrations", metadata,
    Column("migration_id", String(100), primary_key=True),
    Column("applied_at", String(40), nullable=False),
)

SOURCE_FILES = (
    ("accounts", "ravenstack_accounts.csv", ("account_id",)),
    ("subscriptions", "ravenstack_subscriptions.csv", ("subscription_id",)),
    ("feature_usage", "ravenstack_feature_usage.csv", ("usage_id",)),
    ("support_tickets", "ravenstack_support_tickets.csv", ("ticket_id", "interaction_id")),
    ("churn_events", "ravenstack_churn_events.csv", ("churn_event_id", "event_id")),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def _date(value: date | str | None) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _secret_database_url() -> str | None:
    value = os.getenv("DATABASE_URL") or os.getenv("RAVENSTACK_DATABASE_URL")
    if value:
        return value.strip()
    try:
        import streamlit as st
        secret = st.secrets.get("DATABASE_URL") or st.secrets.get("RAVENSTACK_DATABASE_URL")
        if secret:
            return str(secret).strip()
    except Exception:
        pass
    return None


def resolve_database_url(explicit: str | None = None) -> str:
    url = explicit or _secret_database_url()
    if url:
        url = url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url
    return URL.create("sqlite", database=str(DEFAULT_DB_PATH)).render_as_string(hide_password=False)


@lru_cache(maxsize=16)
def _engine_for(url: str) -> Engine:
    connect_args = {"check_same_thread": False, "timeout": 30} if url.startswith("sqlite:") else {}
    engine = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()
    return engine


def _insert_ignore(conn, table: Table, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    dialect = conn.dialect.name
    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as dialect_insert
        stmt = dialect_insert(table).values(rows).on_conflict_do_nothing()
    elif dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
        stmt = dialect_insert(table).values(rows).on_conflict_do_nothing()
    else:
        stmt = insert(table).values(rows)
    conn.execute(stmt)


def _event_row(customer_id: str, event_type: str, actor: str, source: str,
               summary: str, previous: Any = None, new: Any = None,
               mrr_delta: float | None = None, related_entity_type: str | None = None,
               related_entity_id: str | None = None) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()), "customer_id": customer_id,
        "event_type": event_type, "occurred_at": _now(), "actor": actor,
        "source": source, "summary": summary,
        "previous_value_json": _json(previous or {}), "new_value_json": _json(new or {}),
        "mrr_delta": mrr_delta, "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
    }


def _raw_account_rows() -> list[dict[str, str]]:
    path = RAW / "ravenstack_accounts.csv"
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _seed_legacy_and_sources(engine: Engine) -> None:
    accounts_path = RAW / "ravenstack_accounts.csv"
    if not accounts_path.exists():
        raise FileNotFoundError(f"Fonte histórica ausente: {accounts_path}")
    with accounts_path.open(newline="", encoding="utf-8-sig") as f:
        account_rows = list(csv.DictReader(f))
    now = _now()
    with engine.begin() as conn:
        existing = set(conn.execute(select(customers.c.customer_id)).scalars())
        new_customers = []
        new_events = []
        for row in account_rows:
            customer_id = row.get("account_id", "").strip()
            if not customer_id or customer_id in existing:
                continue
            new_customers.append({
                "customer_id": customer_id, "name": row.get("account_name", "").strip() or customer_id,
                "industry": row.get("industry") or None, "country": row.get("country") or None,
                "referral_source": row.get("referral_source") or None,
                "signup_date": _date(row.get("signup_date")), "lifecycle_status": None,
                "health_status": None, "owner": None, "verification_status": "not_validated",
                "verification_fields_json": "{}", "origin": "legacy", "sales_stage": None,
                "opportunity_value_estimate": None, "opportunity_currency": None,
                "expected_close_date": None, "notes": None, "archived_at": None,
                "created_at": now, "updated_at": now,
            })
            new_events.append(_event_row(
                customer_id, "customer_imported", "system:seed", "legacy_import",
                "Conta histórica pré-carregada; estado atual não validado.", {},
                {"origin": "legacy", "verification_status": "not_validated",
                 "source_table": "accounts", "source_key": customer_id},
                related_entity_type="source_record", related_entity_id=customer_id,
            ))
        _insert_ignore(conn, customers, new_customers)
        _insert_ignore(conn, journey_events, new_events)

        for table_name, filename, id_cols in SOURCE_FILES:
            path = RAW / filename
            if not path.exists():
                continue
            data = path.read_bytes()
            file_hash = hashlib.sha256(data).hexdigest()
            if conn.execute(select(source_imports.c.source_table).where(and_(
                source_imports.c.source_table == table_name,
                source_imports.c.file_hash == file_hash,
            ))).first():
                continue
            imported_at = _now()
            decoded = data.decode("utf-8-sig").splitlines()
            reader = csv.DictReader(decoded)
            batch: list[dict[str, Any]] = []
            row_count = 0
            for row_number, row in enumerate(reader, start=1):
                customer_id = (row.get("account_id") or "").strip()
                if not customer_id:
                    continue
                source_key = next((row.get(key) for key in id_cols if row.get(key)), str(row_number))
                stable_id = hashlib.sha256(f"{table_name}:{file_hash}:{row_number}".encode()).hexdigest()
                batch.append({
                    "source_record_id": stable_id, "source_table": table_name,
                    "source_key": str(source_key), "source_file_hash": file_hash,
                    "row_number": row_number, "customer_id": customer_id,
                    "raw_payload_json": _json(row), "imported_at": imported_at,
                })
                row_count += 1
                if len(batch) >= 750:
                    _insert_ignore(conn, source_records, batch)
                    batch.clear()
            _insert_ignore(conn, source_records, batch)
            conn.execute(insert(source_imports).values({
                "source_table": table_name, "file_hash": file_hash,
                "row_count": row_count, "imported_at": imported_at,
            }))


def _migrate_old_crm(engine: Engine) -> None:
    """One-time, non-destructive migration from the previous demo CRM tables."""
    migration_id = "migrate_retention_demo_crm_v1"
    inspector = __import__("sqlalchemy").inspect(engine)
    if not inspector.has_table("crm_accounts"):
        return
    with engine.begin() as conn:
        if conn.execute(select(migrations.c.migration_id).where(migrations.c.migration_id == migration_id)).first():
            return
        old_accounts = conn.exec_driver_sql("SELECT * FROM crm_accounts").mappings().all()
        for old in old_accounts:
            identity = str(old["account_id"])
            current = conn.execute(select(customers).where(customers.c.customer_id == identity)).mappings().first()
            now = _now()
            manual = old.get("record_origin") == "Cadastro manual"
            if current is None:
                values = {
                    "customer_id": identity, "name": old["account_name"],
                    "industry": old.get("industry") or None, "country": old.get("country") or None,
                    "referral_source": old.get("referral_source") or None,
                    "signup_date": None, "lifecycle_status": None, "health_status": None,
                    "owner": old.get("owner_id") or None,
                    "verification_status": "partially_validated", "verification_fields_json": _json({
                        "owner": {"verified_at": now, "actor": "system:migration"}
                    }) if old.get("owner_id") else "{}",
                    "origin": "native" if manual else "legacy", "sales_stage": old.get("journey_stage"),
                    "opportunity_value_estimate": old.get("deal_value_estimate"),
                    "opportunity_currency": old.get("deal_currency"),
                    "expected_close_date": _date(old.get("expected_close_date")),
                    "notes": old.get("notes"), "archived_at": None, "created_at": now, "updated_at": now,
                }
                conn.execute(insert(customers).values(values))
                conn.execute(insert(journey_events).values(_event_row(
                    identity, "legacy_crm_migrated", "system:migration", "crm_migration",
                    "Registro do CRM demo anterior migrado sem promover assinatura ou lifecycle.", {}, values,
                )))
            else:
                # Keep any explicitly entered owner/opportunity details without treating them as lifecycle or MRR.
                changes = {}
                for old_key, new_key in (("owner_id", "owner"), ("journey_stage", "sales_stage"),
                                         ("deal_value_estimate", "opportunity_value_estimate"),
                                         ("deal_currency", "opportunity_currency"),
                                         ("expected_close_date", "expected_close_date")):
                    value = old.get(old_key)
                    if value not in (None, "") and current.get(new_key) in (None, ""):
                        changes[new_key] = _date(value) if new_key == "expected_close_date" else value
                if changes:
                    conn.execute(update(customers).where(customers.c.customer_id == identity).values(**changes, updated_at=now))
                    conn.execute(insert(journey_events).values(_event_row(
                        identity, "legacy_crm_context_migrated", "system:migration", "crm_migration",
                        "Contexto comercial antigo preservado; assinatura/lifecycle seguem não validados.", {}, changes,
                    )))

        if inspector.has_table("crm_interactions"):
            old_items = conn.exec_driver_sql("SELECT * FROM crm_interactions").mappings().all()
            for old in old_items:
                identity = str(old["interaction_id"])
                if conn.execute(select(interactions.c.interaction_id).where(interactions.c.interaction_id == identity)).first():
                    continue
                customer_id = str(old["account_id"])
                if not conn.execute(select(customers.c.customer_id).where(customers.c.customer_id == customer_id)).first():
                    continue
                occurred = str(old.get("occurred_at") or date.today().isoformat())
                interaction_values = {
                    "interaction_id": identity, "customer_id": customer_id,
                    "interaction_type": str(old.get("interaction_type") or "Outro"),
                    "occurred_at": occurred, "summary": str(old.get("summary") or "Atividade migrada do CRM demo"),
                    "actor": str(old.get("owner_id") or "Operador migrado"),
                    "obstacle": old.get("observation"), "outcome": old.get("outcome"),
                    "source": "crm_migration", "created_at": str(old.get("created_at") or _now()),
                }
                conn.execute(insert(interactions).values(interaction_values))
                ev = _event_row(customer_id, "interaction_recorded", "system:migration", "crm_migration",
                                "Interação migrada do CRM demo anterior.", {}, interaction_values,
                                related_entity_type="interaction", related_entity_id=identity)
                conn.execute(insert(journey_events).values(ev))
                next_action = str(old.get("next_action") or "").strip()
                if next_action:
                    _create_task_in_tx(conn, customer_id=customer_id, title=next_action,
                                       owner=str(old.get("owner_id") or "Operador migrado"),
                                       due_date=_date(old.get("next_action_due_at")) or date.today() + timedelta(days=3),
                                       priority="P2", created_from=ev["event_id"], actor="system:migration",
                                       source="crm_migration")
        conn.execute(insert(migrations).values({"migration_id": migration_id, "applied_at": _now()}))


@lru_cache(maxsize=16)
def _initialize_seeded(resolved: str) -> Engine:
    engine = _engine_for(resolved)
    metadata.create_all(engine)
    # Hashes and unique constraints make source import safe across process restarts.
    _seed_legacy_and_sources(engine)
    _migrate_old_crm(engine)
    return engine


def initialize_store(database_url: str | None = None, *, seed: bool = True) -> Engine:
    resolved = resolve_database_url(database_url)
    if seed:
        return _initialize_seeded(resolved)
    engine = _engine_for(resolved)
    metadata.create_all(engine)
    return engine


def database_mode(database_url: str | None = None) -> str:
    resolved = resolve_database_url(database_url)
    return "sqlite-demo-efemero" if resolved.startswith("sqlite:") else "postgresql-persistente"


def _engine(database_url: str | None = None) -> Engine:
    return initialize_store(database_url)


def _confirmed(value: Any) -> set[str]:
    try:
        return set(json.loads(value or "[]"))
    except (TypeError, json.JSONDecodeError):
        return set()


def _field_confirmations(value: Any) -> dict[str, Any]:
    try:
        return json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}


def _summary_subscriptions(conn, customer_id: str) -> dict[str, Any]:
    rows = conn.execute(select(subscriptions).where(
        subscriptions.c.customer_id == customer_id
    ).order_by(subscriptions.c.created_at)).mappings().all()
    return _summary_subscription_rows(rows)


def _summary_subscription_rows(all_rows) -> dict[str, Any]:
    active_rows = [row for row in all_rows if row["status"] == "active"]
    rows = list(active_rows)
    is_unconfirmed = False
    if not rows:
        rows = [row for row in all_rows if row["status"] == "unconfirmed"][-1:]
        is_unconfirmed = bool(rows)
    if not rows:
        return {"active_subscriptions": [], "plan_tier": None, "seats": None,
                "mrr_current": None, "currency": None, "billing_frequency": None,
                "renewal_date": None, "subscription_status": None}
    confirmed = [_confirmed(row["confirmed_fields_json"]) for row in rows]
    def only_if_all(field: str):
        return [row[field] for row, fields in zip(rows, confirmed) if field in fields]
    plans = only_if_all("plan_tier")
    seats = only_if_all("seats")
    mrrs = only_if_all("mrr_current")
    currencies = only_if_all("currency")
    billings = only_if_all("billing_frequency")
    renewals = only_if_all("renewal_date")
    same_currency = len(set(currencies)) == 1 and len(currencies) == len(rows)
    total_mrr = None if (is_unconfirmed or not same_currency or len(mrrs) != len(rows)
                         or any(x is None for x in mrrs)) else sum(float(x) for x in mrrs)
    total_seats = None if len(seats) != len(rows) or any(x is None for x in seats) else sum(int(x) for x in seats)
    return {
        "active_subscriptions": [dict(x) for x in rows],
        "plan_tier": plans[0] if len(rows) == 1 and len(plans) == 1 else ("Várias linhas" if len(rows) > 1 and plans else None),
        "seats": total_seats, "mrr_current": total_mrr,
        "currency": currencies[0] if same_currency and currencies else None,
        "billing_frequency": billings[0] if len(rows) == 1 and len(billings) == 1 else None,
        "renewal_date": renewals[0] if len(rows) == 1 and len(renewals) == 1 else None,
        "subscription_status": "unconfirmed" if is_unconfirmed else "active",
    }


def get_customer(customer_id: str, *, database_url: str | None = None) -> dict[str, Any] | None:
    engine = _engine(database_url)
    with engine.connect() as conn:
        row = conn.execute(select(customers).where(customers.c.customer_id == customer_id)).mappings().first()
        if not row:
            return None
        result = dict(row)
        result["verification_fields"] = _field_confirmations(result.pop("verification_fields_json"))
        result.update(_summary_subscriptions(conn, customer_id))
        result["open_tasks"] = conn.execute(select(func.count()).select_from(tasks).where(and_(
            tasks.c.customer_id == customer_id, tasks.c.status.in_(("open", "in_progress"))
        ))).scalar_one()
        result["last_interaction_at"] = conn.execute(select(func.max(interactions.c.occurred_at)).where(
            interactions.c.customer_id == customer_id
        )).scalar_one()
        return result


def list_customers(*, query: str = "", lifecycle: str | None = None,
                   owner: str | None = None, verification: str | None = None,
                   origin: str | None = None, database_url: str | None = None) -> list[dict[str, Any]]:
    engine = _engine(database_url)
    stmt = select(customers).where(customers.c.archived_at.is_(None))
    if lifecycle and lifecycle != "Todos":
        stmt = stmt.where(customers.c.lifecycle_status == lifecycle)
    if owner and owner != "Todos":
        stmt = stmt.where(customers.c.owner == owner)
    if verification and verification != "Todos":
        stmt = stmt.where(customers.c.verification_status == verification)
    if origin and origin != "Todos":
        stmt = stmt.where(customers.c.origin == origin)
    if query.strip():
        pattern = f"%{query.strip()}%"
        stmt = stmt.where(customers.c.name.ilike(pattern) | customers.c.customer_id.ilike(pattern))
    stmt = stmt.order_by(customers.c.name.collate("NOCASE") if engine.dialect.name == "sqlite" else func.lower(customers.c.name))
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
        ids = [row["customer_id"] for row in rows]
        sub_rows = conn.execute(select(subscriptions).where(subscriptions.c.customer_id.in_(ids))).mappings().all() if ids else []
        subs_by_customer: dict[str, list] = {}
        for sub_row in sub_rows:
            subs_by_customer.setdefault(sub_row["customer_id"], []).append(sub_row)
        result = []
        for row in rows:
            item = dict(row)
            item["verification_fields"] = _field_confirmations(item.pop("verification_fields_json"))
            item.update(_summary_subscription_rows(subs_by_customer.get(item["customer_id"], [])))
            result.append(item)
        return result


def list_subscriptions(customer_id: str, *, database_url: str | None = None) -> list[dict[str, Any]]:
    engine = _engine(database_url)
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(select(subscriptions).where(
            subscriptions.c.customer_id == customer_id
        ).order_by(subscriptions.c.effective_from.desc().nullslast(), subscriptions.c.created_at.desc())).mappings()]


def list_events(customer_id: str, *, limit: int = 100, database_url: str | None = None) -> list[dict[str, Any]]:
    engine = _engine(database_url)
    with engine.connect() as conn:
        rows = conn.execute(select(journey_events).where(journey_events.c.customer_id == customer_id).order_by(
            journey_events.c.occurred_at.desc(), journey_events.c.event_id.desc()
        ).limit(limit)).mappings().all()
        out = []
        for row in rows:
            item = dict(row)
            item["previous_value"] = json.loads(item.pop("previous_value_json") or "{}")
            item["new_value"] = json.loads(item.pop("new_value_json") or "{}")
            out.append(item)
        return out


def list_source_records(customer_id: str, *, source_table: str | None = None,
                        limit: int = 100, database_url: str | None = None) -> list[dict[str, Any]]:
    engine = _engine(database_url)
    stmt = select(source_records).where(source_records.c.customer_id == customer_id)
    if source_table:
        stmt = stmt.where(source_records.c.source_table == source_table)
    stmt = stmt.order_by(source_records.c.row_number.desc()).limit(limit)
    with engine.connect() as conn:
        out = []
        for row in conn.execute(stmt).mappings():
            item = dict(row)
            item["raw_payload"] = json.loads(item.pop("raw_payload_json"))
            out.append(item)
        return out


def _write_event(conn, *, customer_id: str, event_type: str, actor: str,
                 source: str, summary: str, previous: Any = None, new: Any = None,
                 mrr_delta: float | None = None, related_entity_type: str | None = None,
                 related_entity_id: str | None = None) -> str:
    row = _event_row(customer_id, event_type, actor, source, summary, previous, new,
                     mrr_delta, related_entity_type, related_entity_id)
    conn.execute(insert(journey_events).values(row))
    return row["event_id"]


def _create_task_in_tx(conn, *, customer_id: str, title: str, owner: str,
                        due_date: date, priority: str, created_from: str | None,
                        actor: str, source: str) -> str:
    title, owner = title.strip(), owner.strip()
    if not title or not owner:
        raise ValueError("Tarefa exige título e responsável.")
    if priority not in TASK_PRIORITIES:
        raise ValueError("Prioridade da tarefa inválida.")
    due = _date(due_date)
    if due is None:
        raise ValueError("Tarefa exige prazo.")
    identity = str(uuid.uuid4())
    now = _now()
    values = {"task_id": identity, "customer_id": customer_id, "title": title,
              "owner": owner, "due_date": due, "priority": priority, "status": "open",
              "created_from": created_from, "created_at": now, "completed_at": None,
              "completion_note": None}
    conn.execute(insert(tasks).values(values))
    _write_event(conn, customer_id=customer_id, event_type="task_created", actor=actor,
                 source=source, summary=f"Tarefa criada: {title} · {owner} · {due.isoformat()}.",
                 new=values, related_entity_type="task", related_entity_id=identity)
    return identity


def create_customer(*, name: str, owner: str, industry: str = "", country: str = "",
                    referral_source: str = "", signup_date: date | str,
                    plan_tier: str, seats: int, mrr_current: float, currency: str,
                    billing_frequency: str, renewal_date: date | str | None,
                    subscription_start: date | str, first_task_title: str,
                    first_task_due: date | str, first_task_priority: str = "P2",
                    health_status: str = "normal", actor: str = "Operador local",
                    database_url: str | None = None) -> str:
    name, owner = name.strip(), owner.strip()
    if not name or not owner:
        raise ValueError("Nome da conta e responsável são obrigatórios.")
    if plan_tier not in PLANS or currency not in CURRENCIES or billing_frequency not in BILLING_FREQUENCIES:
        raise ValueError("Plano, moeda ou ciclo de cobrança inválido.")
    if int(seats) < 1 or float(mrr_current) < 0:
        raise ValueError("Seats deve ser pelo menos 1 e MRR não pode ser negativo.")
    if health_status not in HEALTH_STATES:
        raise ValueError("Saúde inválida.")
    signup, start, renewal = _date(signup_date), _date(subscription_start), _date(renewal_date)
    if signup is None or start is None:
        raise ValueError("Data de início da conta e assinatura são obrigatórias.")
    if not first_task_title.strip() or not owner or _date(first_task_due) is None:
        raise ValueError("A primeira próxima ação exige título, responsável e prazo.")
    identity = "C-" + uuid.uuid4().hex[:12].upper()
    now = _now()
    verified = {
        key: {"verified_at": now, "actor": actor, "source": "native"}
        for key in ("name", "owner", "lifecycle_status", "health_status", "plan_tier", "seats",
                    "mrr_current", "currency", "billing_frequency", "renewal_date", "subscription_status")
    }
    sub_id = "S-" + uuid.uuid4().hex[:12].upper()
    sub_fields = ["plan_tier", "seats", "mrr_current", "currency", "billing_frequency",
                  "effective_from", "renewal_date", "status"]
    with _engine(database_url).begin() as conn:
        customer_values = {
            "customer_id": identity, "name": name, "industry": industry.strip() or None,
            "country": country.strip() or None, "referral_source": referral_source.strip() or None,
            "signup_date": signup, "lifecycle_status": "onboarding", "health_status": health_status,
            "owner": owner, "verification_status": "validated",
            "verification_fields_json": _json(verified), "origin": "native",
            "sales_stage": "Onboarding", "opportunity_value_estimate": None,
            "opportunity_currency": None, "expected_close_date": None, "notes": None,
            "archived_at": None, "created_at": now, "updated_at": now,
        }
        conn.execute(insert(customers).values(customer_values))
        _write_event(conn, customer_id=identity, event_type="customer_created", actor=actor,
                     source="native", summary=f"Cliente criado · assinatura inicial {plan_tier}.",
                     new=customer_values)
        subscription_values = {
            "subscription_id": sub_id, "customer_id": identity, "contract_id": None,
            "plan_tier": plan_tier, "seats": int(seats), "mrr_current": float(mrr_current),
            "currency": currency, "billing_frequency": billing_frequency,
            "effective_from": start, "effective_to": None, "renewal_date": renewal,
            "status": "active", "verification_status": "validated",
            "confirmed_fields_json": _json(sub_fields), "movement_type": "new_business",
            "source": "native", "created_at": now,
        }
        conn.execute(insert(subscriptions).values(subscription_values))
        _write_event(conn, customer_id=identity, event_type="subscription_started", actor=actor,
                     source="native", summary=f"Assinatura iniciada · {plan_tier} · {seats} seats · {currency} {mrr_current:,.2f} MRR.",
                     new=subscription_values, mrr_delta=float(mrr_current),
                     related_entity_type="subscription", related_entity_id=sub_id)
        _create_task_in_tx(conn, customer_id=identity, title=first_task_title, owner=owner,
                           due_date=_date(first_task_due), priority=first_task_priority,
                           created_from=None, actor=actor, source="native")
    return identity


def update_customer_profile(customer_id: str, *, actor: str, name: str | None = None,
                            industry: str | None = None, country: str | None = None,
                            referral_source: str | None = None, owner: str | None = None,
                            health_status: str | None = None,
                            sales_stage: str | None = None,
                            opportunity_value_estimate: float | None = None,
                            opportunity_currency: str | None = None,
                            expected_close_date: date | str | None = None,
                            notes: str | None = None,
                            database_url: str | None = None) -> None:
    """Update current operational profile fields with a before/after event."""
    allowed = {"name": name.strip() if name is not None else None,
               "industry": industry.strip() if industry is not None else None,
               "country": country.strip() if country is not None else None,
               "referral_source": referral_source.strip() if referral_source is not None else None,
               "owner": owner.strip() if owner is not None else None,
               "health_status": health_status,
               "sales_stage": sales_stage,
               "opportunity_value_estimate": opportunity_value_estimate,
               "opportunity_currency": opportunity_currency,
               "expected_close_date": _date(expected_close_date) if expected_close_date is not None else None,
               "notes": notes.strip() if notes is not None else None}
    values = {k: v for k, v in allowed.items() if v is not None}
    if not values:
        return
    if values.get("health_status") and values["health_status"] not in HEALTH_STATES:
        raise ValueError("Saúde inválida.")
    if "name" in values and not values["name"]:
        raise ValueError("Nome não pode ficar vazio.")
    if "owner" in values and not values["owner"]:
        raise ValueError("Responsável não pode ficar vazio.")
    if "opportunity_value_estimate" in values and values["opportunity_value_estimate"] < 0:
        raise ValueError("Valor estimado não pode ser negativo.")
    with _engine(database_url).begin() as conn:
        current = conn.execute(select(customers).where(customers.c.customer_id == customer_id)).mappings().first()
        if not current:
            raise ValueError("Cliente não encontrado.")
        changed = {k: {"before": current[k], "after": v} for k, v in values.items() if current[k] != v}
        if not changed:
            return
        verification = _field_confirmations(current["verification_fields_json"])
        for field in values:
            verification[field] = {"verified_at": _now(), "actor": actor, "source": "operator"}
        fields = set(verification)
        status = _verification_status(current["origin"], fields, current["verification_status"])
        conn.execute(update(customers).where(customers.c.customer_id == customer_id).values(
            **values, verification_fields_json=_json(verification), verification_status=status, updated_at=_now()))
        _write_event(conn, customer_id=customer_id, event_type="customer_updated", actor=actor,
                     source="operator", summary="Dados operacionais do cliente atualizados.",
                     previous={k: v["before"] for k, v in changed.items()},
                     new={k: v["after"] for k, v in changed.items()})


def _verification_status(origin: str, verified_fields: set[str], existing: str) -> str:
    required = {"owner", "lifecycle_status", "plan_tier", "seats", "mrr_current",
                "currency", "billing_frequency", "subscription_status"}
    if required.issubset(verified_fields):
        return "validated"
    if verified_fields:
        return "partially_validated"
    return "conflict" if existing == "conflict" else "not_validated"


def validate_legacy_fields(customer_id: str, *, selected_fields: dict[str, Any],
                           actor: str, mark_conflict: bool = False,
                           database_url: str | None = None) -> None:
    """Confirm only submitted fields. A None value is an explicit confirmed unknown."""
    if not selected_fields and not mark_conflict:
        raise ValueError("Selecione pelo menos um campo para validar.")
    allowed_customer = {"owner", "lifecycle_status", "health_status"}
    allowed_subscription = {"plan_tier", "seats", "mrr_current", "currency",
                            "billing_frequency", "renewal_date", "subscription_status"}
    invalid = set(selected_fields) - allowed_customer - allowed_subscription
    if invalid:
        raise ValueError(f"Campos não permitidos: {', '.join(sorted(invalid))}")
    if "lifecycle_status" in selected_fields and selected_fields["lifecycle_status"] not in LIFECYCLES:
        raise ValueError("Lifecycle inválido.")
    if "health_status" in selected_fields and selected_fields["health_status"] not in HEALTH_STATES:
        raise ValueError("Saúde inválida.")
    if "plan_tier" in selected_fields and selected_fields["plan_tier"] not in (*PLANS, None):
        raise ValueError("Plano inválido.")
    if "seats" in selected_fields and selected_fields["seats"] is not None and int(selected_fields["seats"]) < 1:
        raise ValueError("Seats precisa ser pelo menos 1 ou explicitamente desconhecido.")
    if "mrr_current" in selected_fields and selected_fields["mrr_current"] is not None and float(selected_fields["mrr_current"]) < 0:
        raise ValueError("MRR não pode ser negativo.")
    if "currency" in selected_fields and selected_fields["currency"] not in (*CURRENCIES, None):
        raise ValueError("Moeda inválida.")
    if "billing_frequency" in selected_fields and selected_fields["billing_frequency"] not in (*BILLING_FREQUENCIES, None):
        raise ValueError("Ciclo de billing inválido.")
    now = _now()
    with _engine(database_url).begin() as conn:
        current = conn.execute(select(customers).where(customers.c.customer_id == customer_id)).mappings().first()
        if not current:
            raise ValueError("Cliente não encontrado.")
        if current["origin"] != "legacy":
            raise ValueError("Validação progressiva é exclusiva de cliente histórico.")
        before_customer = {k: current[k] for k in selected_fields if k in allowed_customer}
        updates = {k: v for k, v in selected_fields.items() if k in allowed_customer}
        verification = _field_confirmations(current["verification_fields_json"])
        for field, value in selected_fields.items():
            verification[field] = {"verified_at": now, "actor": actor,
                                   "source": "operator", "confirmed_value": value}
        fields = set(verification)
        status = "conflict" if mark_conflict else _verification_status("legacy", fields, current["verification_status"])
        conn.execute(update(customers).where(customers.c.customer_id == customer_id).values(
            **updates, verification_fields_json=_json(verification), verification_status=status, updated_at=now))
        sub_fields = {k: v for k, v in selected_fields.items()
                      if k in allowed_subscription and k != "subscription_status"}
        before_sub = {}
        sub_id = None
        if sub_fields or "subscription_status" in selected_fields:
            active = conn.execute(select(subscriptions).where(and_(subscriptions.c.customer_id == customer_id,
                                                                  subscriptions.c.status == "active"))
                                  .order_by(subscriptions.c.created_at.desc())).mappings().first()
            if active is None:
                active = conn.execute(select(subscriptions).where(and_(subscriptions.c.customer_id == customer_id,
                                                                       subscriptions.c.status == "unconfirmed"))
                                      .order_by(subscriptions.c.created_at.desc())).mappings().first()
            sub_id = active["subscription_id"] if active else "S-" + uuid.uuid4().hex[:12].upper()
            requested_status = selected_fields.get("subscription_status", active["status"] if active else "unconfirmed")
            if requested_status not in ("active", "paused", "ended", "unconfirmed", None):
                raise ValueError("Status da assinatura inválido.")
            if requested_status is None:
                requested_status = "unconfirmed"
            old_confirmed = _confirmed(active["confirmed_fields_json"]) if active else set()
            for field in sub_fields:
                before_sub[field] = active[field] if active else None
            value_fields = set(old_confirmed) | set(sub_fields)
            row_values = {
                "customer_id": customer_id, "contract_id": active["contract_id"] if active else None,
                "plan_tier": active["plan_tier"] if active else None,
                "seats": active["seats"] if active else None,
                "mrr_current": active["mrr_current"] if active else None,
                "currency": active["currency"] if active else None,
                "billing_frequency": active["billing_frequency"] if active else None,
                "effective_from": active["effective_from"] if active else None,
                "effective_to": active["effective_to"] if active else None,
                "renewal_date": active["renewal_date"] if active else None,
                "status": requested_status,
                "verification_status": "partially_validated",
                "confirmed_fields_json": _json(sorted(value_fields)),
                "movement_type": active["movement_type"] if active else "legacy_validation",
                "source": "operator_validation", "created_at": active["created_at"] if active else now,
            }
            row_values.update(sub_fields)
            if active:
                conn.execute(update(subscriptions).where(subscriptions.c.subscription_id == sub_id).values(**row_values))
            else:
                conn.execute(insert(subscriptions).values(subscription_id=sub_id, **row_values))
            verified_status_fields = value_fields | ({"status"} if "subscription_status" in selected_fields else set())
            if verified_status_fields.issuperset({"plan_tier", "seats", "mrr_current", "currency",
                                                  "billing_frequency", "status"}):
                conn.execute(update(subscriptions).where(subscriptions.c.subscription_id == sub_id).values(verification_status="validated"))
        event_new = {**updates, **sub_fields, "subscription_status": selected_fields.get("subscription_status"),
                     "verification_status": status,
                     "mark_conflict": mark_conflict, "subscription_id": sub_id}
        _write_event(conn, customer_id=customer_id, event_type="legacy_fields_validated",
                     actor=actor, source="operator", summary="Campos selecionados do cliente histórico foram confirmados.",
                     previous={**before_customer, **before_sub}, new=event_new,
                     related_entity_type="subscription" if sub_id else None, related_entity_id=sub_id)


def _account_mrr(conn, customer_id: str) -> tuple[float | None, int | None, list[dict[str, Any]]]:
    rows = conn.execute(select(subscriptions).where(and_(subscriptions.c.customer_id == customer_id,
                                                        subscriptions.c.status == "active"))).mappings().all()
    active = [dict(r) for r in rows]
    if not active:
        # No operational subscription is not proof of zero MRR for a legacy account.
        return None, None, active
    mrrs, seats = [], []
    for row in active:
        confirmed = _confirmed(row["confirmed_fields_json"])
        if "mrr_current" not in confirmed or row["mrr_current"] is None:
            mrrs.append(None)
        else:
            mrrs.append(float(row["mrr_current"]))
        if "seats" not in confirmed or row["seats"] is None:
            seats.append(None)
        else:
            seats.append(int(row["seats"]))
    currency_values = [x["currency"] for x in active
                       if "currency" in _confirmed(x["confirmed_fields_json"]) and x["currency"]]
    same_currency = len(currency_values) == len(active) and len(set(currency_values)) == 1
    total_mrr = None if any(x is None for x in mrrs) or not same_currency else sum(mrrs)
    total_seats = None if any(x is None for x in seats) else sum(seats)
    return total_mrr, total_seats, active


def preview_subscription_change(customer_id: str, *, mrr_after: float,
                                currency: str, subscription_id: str | None = None,
                                create_parallel: bool = False,
                                database_url: str | None = None) -> dict[str, Any]:
    """Read-only economic preview; returns unknown instead of mixing currencies or gaps."""
    with _engine(database_url).connect() as conn:
        mrr_before, seats_before, active = _account_mrr(conn, customer_id)
        target = next((x for x in active if x["subscription_id"] == subscription_id), None) if subscription_id else None
        if subscription_id and target is None:
            raise ValueError("Assinatura selecionada não está vigente.")
        if not subscription_id and len(active) > 1 and not create_parallel:
            raise ValueError("Selecione a assinatura que será substituída.")
        if not subscription_id and active and not create_parallel:
            target = active[0]
        current_currencies = [x["currency"] for x in active
                              if "currency" in _confirmed(x["confirmed_fields_json"]) and x["currency"]]
        before_currency_compatible = (len(current_currencies) == len(active)
                                      and len(set(current_currencies)) == 1
                                      and current_currencies[0] == currency)
        comparable_before = mrr_before if before_currency_compatible else None
        others = [x for x in active if not target or x["subscription_id"] != target["subscription_id"]]
        others_known = all("mrr_current" in _confirmed(x["confirmed_fields_json"])
                           and x["mrr_current"] is not None
                           and "currency" in _confirmed(x["confirmed_fields_json"])
                           and x["currency"] == currency for x in others)
        after = sum(float(x["mrr_current"]) for x in others) + float(mrr_after) if others_known else None
        delta = after - comparable_before if after is not None and comparable_before is not None else None
        return {"mrr_before": comparable_before, "mrr_after": after,
                "mrr_delta": delta, "currency": currency,
                "seats_before": seats_before, "active_subscription_count": len(active),
                "known": delta is not None}


def preview_lifecycle_movement(customer_id: str, *, movement: str,
                               subscription_id: str | None = None,
                               reactivation_mrr: float | None = None,
                               currency: str | None = None,
                               database_url: str | None = None) -> dict[str, Any]:
    if movement not in MOVEMENTS:
        raise ValueError("Movimento inválido.")
    with _engine(database_url).connect() as conn:
        mrr_before, seats_before, active = _account_mrr(conn, customer_id)
        customer = conn.execute(select(customers).where(customers.c.customer_id == customer_id)).mappings().first()
        if not customer:
            raise ValueError("Cliente não encontrado.")
        remaining = active
        if movement == "total_loss":
            remaining = []
        elif movement in ("pause", "admin_end"):
            if not subscription_id or not any(x["subscription_id"] == subscription_id for x in active):
                raise ValueError("Selecione uma assinatura vigente.")
            remaining = [x for x in active if x["subscription_id"] != subscription_id]
        after = mrr_before
        after_seats = seats_before
        if movement in ("total_loss", "pause") and not remaining:
            after = 0.0 if active and mrr_before is not None else None
            after_seats = 0 if active and seats_before is not None else None
        elif movement == "admin_end" and len(remaining) != len(active):
            rows_known = all("mrr_current" in _confirmed(x["confirmed_fields_json"])
                             and x["mrr_current"] is not None
                             and "currency" in _confirmed(x["confirmed_fields_json"])
                             for x in remaining)
            ccy = {x["currency"] for x in remaining}
            after = sum(float(x["mrr_current"]) for x in remaining) if rows_known and len(ccy) == 1 else (0.0 if not remaining and mrr_before is not None else None)
            after_seats = sum(int(x["seats"]) for x in remaining) if all(
                "seats" in _confirmed(x["confirmed_fields_json"]) and x["seats"] is not None for x in remaining) else None
        elif movement == "reactivation":
            if reactivation_mrr is None or currency not in CURRENCIES:
                after = None
            elif not active:
                after, after_seats = float(reactivation_mrr), None
            else:
                rows_known = all("mrr_current" in _confirmed(x["confirmed_fields_json"])
                                 and x["mrr_current"] is not None
                                 and "currency" in _confirmed(x["confirmed_fields_json"])
                                 and x["currency"] == currency for x in active)
                after = sum(float(x["mrr_current"]) for x in active) + float(reactivation_mrr) if rows_known else None
        delta = after - mrr_before if after is not None and mrr_before is not None else None
        if movement == "total_loss" and mrr_before is not None:
            delta = -mrr_before
        return {"movement": movement, "lifecycle_before": customer["lifecycle_status"],
                "lifecycle_after": "churned" if movement == "total_loss" else "paused" if movement == "pause" and not remaining else "active" if movement == "reactivation" else customer["lifecycle_status"],
                "active_subscription_count_before": len(active),
                "active_subscription_count_after": len(remaining) + (1 if movement == "reactivation" else 0),
                "mrr_before": mrr_before, "mrr_after": after,
                "mrr_delta": delta, "currency": currency,
                "seats_before": seats_before, "seats_after": after_seats,
                "economic_impact_known": delta is not None}


def _new_subscription(conn, *, customer_id: str, plan_tier: str | None, seats: int | None,
                       mrr_current: float | None, currency: str | None, billing_frequency: str | None,
                       effective_from: date | None, renewal_date: date | None, status: str,
                       movement_type: str, actor: str, source: str,
                       confirmed_fields: Iterable[str] | None = None) -> str:
    identity, now = "S-" + uuid.uuid4().hex[:12].upper(), _now()
    confirmed = sorted(set(confirmed_fields or ()))
    sub_values = {
        "subscription_id": identity, "customer_id": customer_id, "contract_id": None,
        "plan_tier": plan_tier, "seats": seats, "mrr_current": mrr_current,
        "currency": currency, "billing_frequency": billing_frequency,
        "effective_from": effective_from, "effective_to": None, "renewal_date": renewal_date,
        "status": status, "verification_status": "validated" if {"plan_tier", "seats", "mrr_current", "status"}.issubset(confirmed) else "partially_validated",
        "confirmed_fields_json": _json(confirmed), "movement_type": movement_type,
        "source": source, "created_at": now,
    }
    conn.execute(insert(subscriptions).values(sub_values))
    return identity


def record_subscription_change(customer_id: str, *, plan_tier: str, seats: int,
                               mrr_after: float, currency: str, billing_frequency: str,
                               effective_date: date | str, renewal_date: date | str | None,
                               reason: str, actor: str, subscription_id: str | None = None,
                               movement_type: str = "subscription_change",
                               create_parallel: bool = False,
                               database_url: str | None = None) -> dict[str, Any]:
    if plan_tier not in PLANS or currency not in CURRENCIES or billing_frequency not in BILLING_FREQUENCIES:
        raise ValueError("Plano, moeda ou ciclo de cobrança inválido.")
    if int(seats) < 1 or float(mrr_after) < 0:
        raise ValueError("Seats deve ser pelo menos 1 e MRR não pode ser negativo.")
    effective, renewal = _date(effective_date), _date(renewal_date)
    if effective is None or not reason.strip():
        raise ValueError("Data efetiva e motivo são obrigatórios.")
    with _engine(database_url).begin() as conn:
        current_customer = conn.execute(select(customers).where(customers.c.customer_id == customer_id)).mappings().first()
        if not current_customer:
            raise ValueError("Cliente não encontrado.")
        mrr_before, seats_before, active_rows = _account_mrr(conn, customer_id)
        current_currencies = [x["currency"] for x in active_rows
                              if "currency" in _confirmed(x["confirmed_fields_json"]) and x["currency"]]
        before_currency_compatible = (len(current_currencies) == len(active_rows)
                                      and len(set(current_currencies)) == 1
                                      and current_currencies[0] == currency)
        target = None
        if create_parallel and subscription_id:
            raise ValueError("Uma nova linha paralela não pode selecionar uma assinatura para substituição.")
        if subscription_id:
            target = next((x for x in active_rows if x["subscription_id"] == subscription_id), None)
            if not target:
                raise ValueError("A assinatura selecionada não está vigente.")
        elif active_rows and not create_parallel:
            if len(active_rows) > 1:
                raise ValueError("Selecione qual assinatura ativa será alterada.")
            target = active_rows[0]
        other_rows = [x for x in active_rows if not target or x["subscription_id"] != target["subscription_id"]]
        other_mrr = None
        if all("mrr_current" in _confirmed(x["confirmed_fields_json"]) and x["mrr_current"] is not None
               and "currency" in _confirmed(x["confirmed_fields_json"]) and x["currency"] == currency
               for x in other_rows):
            other_mrr = sum(float(x["mrr_current"]) for x in other_rows)
        mrr_after_account = None if other_mrr is None else other_mrr + float(mrr_after)
        seats_after_account = None
        if all("seats" in _confirmed(x["confirmed_fields_json"]) and x["seats"] is not None for x in other_rows):
            seats_after_account = sum(int(x["seats"]) for x in other_rows) + int(seats)
        now = _now()
        before = {"plan_tier": target["plan_tier"] if target else None,
                  "seats": target["seats"] if target else None,
                  "mrr_current": mrr_before,
                  "currency": current_currencies[0] if len(set(current_currencies)) == 1 and current_currencies else None,
                  "active_subscription_count": len(active_rows)}
        if target:
            if target["effective_from"] and effective < target["effective_from"]:
                raise ValueError("A data efetiva não pode anteceder o início da assinatura selecionada.")
            end_date = effective - timedelta(days=1)
            conn.execute(update(subscriptions).where(subscriptions.c.subscription_id == target["subscription_id"]).values(
                status="ended", effective_to=end_date))
        new_id = _new_subscription(
            conn, customer_id=customer_id, plan_tier=plan_tier, seats=int(seats),
            mrr_current=float(mrr_after), currency=currency,
            billing_frequency=billing_frequency, effective_from=effective,
            renewal_date=renewal, status="active", movement_type=movement_type,
            actor=actor, source="operator", confirmed_fields=("plan_tier", "seats", "mrr_current", "currency", "billing_frequency", "effective_from", "renewal_date", "status"),
        )
        current_fields = _field_confirmations(current_customer["verification_fields_json"])
        for field in ("plan_tier", "seats", "mrr_current", "currency", "billing_frequency", "renewal_date", "subscription_status"):
            current_fields[field] = {"verified_at": now, "actor": actor, "source": "operator"}
        verification_status = _verification_status(current_customer["origin"], set(current_fields), current_customer["verification_status"])
        conn.execute(update(customers).where(customers.c.customer_id == customer_id).values(
            verification_fields_json=_json(current_fields), verification_status=verification_status,
            lifecycle_status="active" if current_customer["lifecycle_status"] in (None, "onboarding", "paused") else current_customer["lifecycle_status"],
            updated_at=now))
        delta = None if (not before_currency_compatible or mrr_before is None or mrr_after_account is None) else mrr_after_account - mrr_before
        after = {"plan_tier": plan_tier, "seats": seats_after_account,
                 "mrr_current": mrr_after_account, "active_subscription_count": len(other_rows) + 1,
                 "effective_date": effective, "renewal_date": renewal,
                 "subscription_id": new_id, "reason": reason.strip()}
        mrr_text = "impacto MRR não calculado: valor desconhecido ou moedas incompatíveis" if delta is None else f"delta de MRR {delta:+,.2f} {currency}"
        event_id = _write_event(conn, customer_id=customer_id, event_type=movement_type,
                                actor=actor, source="operator",
                                summary=f"Assinatura atualizada · {plan_tier} · {seats} seats · {mrr_text}.",
                                previous=before, new=after, mrr_delta=delta,
                                related_entity_type="subscription", related_entity_id=new_id)
        return {"subscription_id": new_id, "mrr_before": mrr_before,
                "mrr_after": mrr_after_account, "mrr_delta": delta,
                "seats_before": seats_before, "seats_after": seats_after_account,
                "event_id": event_id}


def record_renewal(customer_id: str, *, subscription_id: str, effective_date: date | str,
                   renewal_date: date | str, reason: str, actor: str,
                   database_url: str | None = None) -> dict[str, Any]:
    subs = list_subscriptions(customer_id, database_url=database_url)
    row = next((x for x in subs if x["subscription_id"] == subscription_id and x["status"] == "active"), None)
    if not row:
        raise ValueError("Selecione uma assinatura vigente para renovar.")
    confirmed = _confirmed(row["confirmed_fields_json"])
    required = {"plan_tier", "seats", "mrr_current", "currency", "billing_frequency"}
    if not required.issubset(confirmed) or row["mrr_current"] is None:
        raise ValueError("Valide plano, seats e MRR antes de registrar a renovação; dados não foram inferidos.")
    return record_subscription_change(
        customer_id, plan_tier=row["plan_tier"], seats=row["seats"], mrr_after=row["mrr_current"],
        currency=row["currency"], billing_frequency=row["billing_frequency"],
        effective_date=effective_date, renewal_date=renewal_date, reason=reason,
        actor=actor, subscription_id=subscription_id, movement_type="renewal",
        database_url=database_url)


def record_lifecycle_movement(customer_id: str, *, movement: str,
                              effective_date: date | str, reason: str, actor: str,
                              subscription_id: str | None = None, note: str = "",
                              reactivation_plan: str | None = None,
                              reactivation_seats: int | None = None,
                              reactivation_mrr: float | None = None,
                              currency: str | None = None, billing_frequency: str | None = None,
                              renewal_date: date | str | None = None,
                              database_url: str | None = None) -> dict[str, Any]:
    if movement not in MOVEMENTS:
        raise ValueError("Movimento inválido.")
    effective = _date(effective_date)
    if effective is None or not reason.strip():
        raise ValueError("Data efetiva e motivo são obrigatórios.")
    if movement == "renewal":
        if not subscription_id or not renewal_date:
            raise ValueError("Renovação exige assinatura e próxima data de renovação.")
        return record_renewal(customer_id, subscription_id=subscription_id,
                              effective_date=effective, renewal_date=renewal_date,
                              reason=reason, actor=actor, database_url=database_url)
    if movement == "reactivation":
        if reactivation_plan not in PLANS or reactivation_seats is None or reactivation_mrr is None:
            raise ValueError("Reativação exige plano, seats e MRR informados.")
        if currency not in CURRENCIES or billing_frequency not in BILLING_FREQUENCIES:
            raise ValueError("Moeda e ciclo de cobrança são obrigatórios na reativação.")
    with _engine(database_url).begin() as conn:
        customer = conn.execute(select(customers).where(customers.c.customer_id == customer_id)).mappings().first()
        if not customer:
            raise ValueError("Cliente não encontrado.")
        mrr_before, seats_before, active_rows = _account_mrr(conn, customer_id)
        if movement == "reactivation" and active_rows:
            raise ValueError("A conta ainda possui subscription operacional vigente; altere essa assinatura em vez de reativar em duplicidade.")
        before = {"lifecycle_status": customer["lifecycle_status"], "active_subscription_count": len(active_rows),
                  "mrr_current": mrr_before, "seats": seats_before}
        now = _now()
        related = None
        if movement in ("pause", "admin_end"):
            target = next((x for x in active_rows if x["subscription_id"] == subscription_id), None)
            if target is None:
                raise ValueError("Selecione uma assinatura vigente.")
            new_status = "paused" if movement == "pause" else "ended"
            conn.execute(update(subscriptions).where(subscriptions.c.subscription_id == subscription_id).values(
                status=new_status, effective_to=effective))
            related = subscription_id
        elif movement == "total_loss":
            for item in active_rows:
                conn.execute(update(subscriptions).where(subscriptions.c.subscription_id == item["subscription_id"]).values(
                    status="ended", effective_to=effective))
        elif movement == "reactivation":
            if float(reactivation_mrr) < 0 or int(reactivation_seats) < 1:
                raise ValueError("MRR não pode ser negativo e seats precisa ser pelo menos 1.")
            related = _new_subscription(conn, customer_id=customer_id,
                plan_tier=reactivation_plan, seats=int(reactivation_seats),
                mrr_current=float(reactivation_mrr), currency=currency,
                billing_frequency=billing_frequency, effective_from=effective,
                renewal_date=_date(renewal_date), status="active", movement_type="reactivation",
                actor=actor, source="operator", confirmed_fields=("plan_tier", "seats", "mrr_current", "currency", "billing_frequency", "effective_from", "renewal_date", "status"))
        remaining_mrr, remaining_seats, remaining = _account_mrr(conn, customer_id)
        lifecycle = customer["lifecycle_status"]
        if movement == "total_loss":
            lifecycle = "churned"
            after_mrr = 0.0 if active_rows and mrr_before is not None else None
            after_seats = 0 if active_rows and seats_before is not None else None
        elif movement == "reactivation":
            lifecycle = "active"
            after_mrr, after_seats = remaining_mrr, remaining_seats
        elif movement == "pause" and not remaining:
            lifecycle = "paused"
            after_mrr = 0.0 if active_rows and mrr_before is not None else None
            after_seats = 0 if active_rows and seats_before is not None else None
        else:
            # Ending an administrative line never implies account churn.
            after_mrr, after_seats = remaining_mrr, remaining_seats
        if movement == "pause" and remaining:
            after_mrr, after_seats = remaining_mrr, remaining_seats
        if movement == "admin_end" and active_rows and not remaining:
            after_mrr = 0.0 if mrr_before is not None else None
            after_seats = 0 if seats_before is not None else None
        delta = None if mrr_before is None or after_mrr is None else after_mrr - mrr_before
        customer_fields = _field_confirmations(customer["verification_fields_json"])
        if movement in ("total_loss", "pause", "reactivation"):
            customer_fields["lifecycle_status"] = {"verified_at": now, "actor": actor, "source": "operator"}
        verification_status = _verification_status(customer["origin"], set(customer_fields), customer["verification_status"])
        conn.execute(update(customers).where(customers.c.customer_id == customer_id).values(
            lifecycle_status=lifecycle, verification_fields_json=_json(customer_fields),
            verification_status=verification_status, updated_at=now))
        after = {"lifecycle_status": lifecycle, "active_subscription_count": len(remaining),
                 "mrr_current": after_mrr, "seats": after_seats, "effective_date": effective,
                 "movement": movement, "reason": reason.strip(), "note": note.strip(),
                 "related_subscription_id": related}
        economic = "impact econômico ainda desconhecido" if delta is None else f"delta MRR {delta:+,.2f}"
        event_id = _write_event(conn, customer_id=customer_id, event_type=movement,
            actor=actor, source="operator", summary=f"Movimento confirmado: {movement} · {economic}.",
            previous=before, new=after, mrr_delta=delta,
            related_entity_type="subscription" if related else None, related_entity_id=related)
        return {"event_id": event_id, "mrr_before": mrr_before, "mrr_after": after_mrr,
                "mrr_delta": delta, "lifecycle_status": lifecycle,
                "active_subscription_count": len(remaining)}


def _create_task(conn, *, customer_id: str, title: str, owner: str,
                 due_date: date, priority: str, created_from: str | None,
                 actor: str, source: str = "operator") -> str:
    exists = conn.execute(select(customers.c.customer_id).where(customers.c.customer_id == customer_id)).first()
    if not exists:
        raise ValueError("Cliente não encontrado.")
    return _create_task_in_tx(conn, customer_id=customer_id, title=title, owner=owner,
                              due_date=due_date, priority=priority, created_from=created_from,
                              actor=actor, source=source)


def create_task(customer_id: str, *, title: str, owner: str, due_date: date | str,
                priority: str, actor: str, created_from: str | None = None,
                database_url: str | None = None) -> str:
    with _engine(database_url).begin() as conn:
        return _create_task(conn, customer_id=customer_id, title=title, owner=owner,
                            due_date=_date(due_date), priority=priority,
                            created_from=created_from, actor=actor)


def record_interaction(customer_id: str, *, interaction_type: str,
                       occurred_at: datetime | date | str, summary: str, actor: str,
                       obstacle: str = "", outcome: str = "", next_action: str = "",
                       next_action_owner: str | None = None,
                       next_action_due: date | str | None = None,
                       task_priority: str = "P2", database_url: str | None = None) -> str:
    allowed = ("Ligação", "Reunião", "E-mail", "Nota", "Demonstração", "Check-in", "Atendimento", "Renovação", "Outro")
    if interaction_type not in allowed or not summary.strip() or not actor.strip():
        raise ValueError("Tipo, resumo e responsável pela interação são obrigatórios.")
    if next_action.strip() and (not next_action_owner or not next_action_owner.strip() or _date(next_action_due) is None):
        raise ValueError("Próxima ação exige responsável e prazo.")
    if not next_action.strip() and (next_action_owner or next_action_due):
        raise ValueError("Informe próxima ação antes de definir responsável ou prazo.")
    occurred = occurred_at.isoformat() if isinstance(occurred_at, (datetime, date)) else str(occurred_at)
    identity = "I-" + uuid.uuid4().hex[:12].upper()
    with _engine(database_url).begin() as conn:
        if not conn.execute(select(customers.c.customer_id).where(customers.c.customer_id == customer_id)).first():
            raise ValueError("Cliente não encontrado.")
        values = {"interaction_id": identity, "customer_id": customer_id,
                  "interaction_type": interaction_type, "occurred_at": occurred,
                  "summary": summary.strip(), "actor": actor.strip(),
                  "obstacle": obstacle.strip() or None, "outcome": outcome.strip() or None,
                  "source": "operator", "created_at": _now()}
        conn.execute(insert(interactions).values(values))
        event_id = _write_event(conn, customer_id=customer_id, event_type="interaction_recorded",
                                actor=actor, source="operator", summary=f"{interaction_type} registrada.",
                                new=values, related_entity_type="interaction", related_entity_id=identity)
        if next_action.strip():
            _create_task(conn, customer_id=customer_id, title=next_action,
                         owner=next_action_owner, due_date=_date(next_action_due),
                         priority=task_priority, created_from=event_id, actor=actor)
    return identity


def list_interactions(customer_id: str, *, database_url: str | None = None) -> list[dict[str, Any]]:
    with _engine(database_url).connect() as conn:
        return [dict(row) for row in conn.execute(select(interactions).where(
            interactions.c.customer_id == customer_id).order_by(interactions.c.occurred_at.desc())).mappings()]


def list_tasks(*, owner: str | None = None, status: str | None = None,
               customer_id: str | None = None, due_before: date | None = None,
               due_after: date | None = None, database_url: str | None = None) -> list[dict[str, Any]]:
    stmt = select(tasks)
    if owner and owner != "Todos":
        stmt = stmt.where(tasks.c.owner == owner)
    if status and status != "Todos":
        stmt = stmt.where(tasks.c.status == status)
    if customer_id:
        stmt = stmt.where(tasks.c.customer_id == customer_id)
    if due_before:
        stmt = stmt.where(tasks.c.due_date <= due_before)
    if due_after:
        stmt = stmt.where(tasks.c.due_date >= due_after)
    stmt = stmt.order_by(tasks.c.due_date, tasks.c.priority, tasks.c.created_at)
    with _engine(database_url).connect() as conn:
        rows = conn.execute(stmt).mappings().all()
        return [dict(x) for x in rows]


def update_task(task_id: str, *, actor: str, title: str | None = None,
                owner: str | None = None, due_date: date | str | None = None,
                priority: str | None = None, status: str | None = None,
                completion_note: str | None = None,
                database_url: str | None = None) -> None:
    values = {}
    if title is not None:
        values["title"] = title.strip()
    if owner is not None:
        values["owner"] = owner.strip()
    if due_date is not None:
        values["due_date"] = _date(due_date)
    if priority is not None:
        values["priority"] = priority
    if status is not None:
        values["status"] = status
    if completion_note is not None:
        values["completion_note"] = completion_note.strip() or None
    if not values:
        return
    if values.get("title") == "" or values.get("owner") == "":
        raise ValueError("Título e responsável não podem ficar vazios.")
    if values.get("priority") and values["priority"] not in TASK_PRIORITIES:
        raise ValueError("Prioridade inválida.")
    if values.get("status") and values["status"] not in TASK_STATUSES:
        raise ValueError("Status inválido.")
    with _engine(database_url).begin() as conn:
        current = conn.execute(select(tasks).where(tasks.c.task_id == task_id)).mappings().first()
        if not current:
            raise ValueError("Tarefa não encontrada.")
        changed = {k: {"before": current[k], "after": v} for k, v in values.items() if current[k] != v}
        if not changed:
            return
        if values.get("status") == "completed":
            values["completed_at"] = _now()
        elif values.get("status") in ("open", "in_progress", "cancelled"):
            values["completed_at"] = None
        conn.execute(update(tasks).where(tasks.c.task_id == task_id).values(**values))
        current_status = values.get("status", current["status"])
        _write_event(conn, customer_id=current["customer_id"], event_type="task_" + current_status,
                     actor=actor, source="operator", summary=f"Tarefa atualizada: {current['title']}.",
                     previous={k: x["before"] for k, x in changed.items()},
                     new={k: x["after"] for k, x in changed.items()},
                     related_entity_type="task", related_entity_id=task_id)


def complete_task(task_id: str, *, actor: str, note: str = "",
                  database_url: str | None = None) -> None:
    update_task(task_id, actor=actor, status="completed", completion_note=note, database_url=database_url)


def refresh_alerts(*, today: date | None = None, database_url: str | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    engine = _engine(database_url)
    desired: dict[str, dict[str, Any]] = {}
    with engine.connect() as conn:
        customer_map = {row["customer_id"]: dict(row) for row in conn.execute(select(customers)).mappings()}
        for task in conn.execute(select(tasks).where(tasks.c.status.in_(("open", "in_progress")))).mappings():
            if task["due_date"] < today:
                customer = customer_map.get(task["customer_id"])
                if customer:
                    key = f"overdue_task:{task['task_id']}"
                    desired[key] = {"alert_id": "AL-" + hashlib.sha256(key.encode()).hexdigest()[:16],
                        "alert_key": key, "customer_id": task["customer_id"], "task_id": task["task_id"],
                        "alert_type": "overdue_task", "severity": "high",
                        "reason": f"Tarefa vencida desde {task['due_date'].isoformat()}: {task['title']} · responsável {task['owner']}.",
                        "customer_name": customer["name"]}
        active_subs = conn.execute(select(subscriptions).where(subscriptions.c.status == "active")).mappings().all()
        for sub in active_subs:
            if "renewal_date" not in _confirmed(sub["confirmed_fields_json"]) or sub["renewal_date"] is None:
                continue
            days = (sub["renewal_date"] - today).days
            if 0 <= days <= 30:
                customer = customer_map.get(sub["customer_id"])
                if customer:
                    key = f"renewal:{sub['subscription_id']}:{sub['renewal_date'].isoformat()}"
                    desired[key] = {"alert_id": "AL-" + hashlib.sha256(key.encode()).hexdigest()[:16],
                        "alert_key": key, "customer_id": sub["customer_id"], "task_id": None,
                        "alert_type": "renewal", "severity": "high" if days <= 7 else "medium",
                        "reason": f"Renovação confirmada para {sub['renewal_date'].isoformat()} · em {days} dias.",
                        "customer_name": customer["name"]}
        open_customer_ids = set(conn.execute(select(tasks.c.customer_id).where(
            tasks.c.status.in_(("open", "in_progress")))).scalars())
        for customer in customer_map.values():
            if customer["lifecycle_status"] == "active" and customer["customer_id"] not in open_customer_ids:
                key = f"no_next_action:{customer['customer_id']}"
                desired[key] = {"alert_id": "AL-" + hashlib.sha256(key.encode()).hexdigest()[:16],
                    "alert_key": key, "customer_id": customer["customer_id"], "task_id": None,
                    "alert_type": "no_next_action", "severity": "medium",
                    "reason": "Conta ativa sem tarefa aberta com próxima ação e responsável.",
                    "customer_name": customer["name"]}
    with engine.begin() as conn:
        existing = {row["alert_key"]: dict(row) for row in conn.execute(select(alerts)).mappings()}
        for key, value in desired.items():
            current = existing.get(key)
            now = _now()
            if current is None:
                stored_value = {key: item for key, item in value.items() if key in alerts.c}
                conn.execute(insert(alerts).values(**stored_value, status="open", created_at=now,
                                                   updated_at=now, treated_at=None,
                                                   treated_by=None, treatment_note=None))
                _write_event(conn, customer_id=value["customer_id"], event_type="alert_created",
                             actor="system:intelligence", source="rules",
                             summary=value["reason"], new=value,
                             related_entity_type="alert", related_entity_id=value["alert_id"])
            elif current["status"] == "resolved":
                conn.execute(update(alerts).where(alerts.c.alert_id == current["alert_id"]).values(
                    status="open", severity=value["severity"], reason=value["reason"], updated_at=now,
                    treated_at=None, treated_by=None, treatment_note=None))
                _write_event(conn, customer_id=value["customer_id"], event_type="alert_reopened",
                             actor="system:intelligence", source="rules",
                             summary=value["reason"], new=value,
                             related_entity_type="alert", related_entity_id=value["alert_id"])
        desired_keys = set(desired)
        for key, current in existing.items():
            if key not in desired_keys and current["status"] == "open":
                now = _now()
                conn.execute(update(alerts).where(alerts.c.alert_id == current["alert_id"]).values(
                    status="resolved", updated_at=now, treated_at=now,
                    treated_by="system:intelligence", treatment_note="Condição deixou de estar ativa."))
                _write_event(conn, customer_id=current["customer_id"], event_type="alert_auto_resolved",
                             actor="system:intelligence", source="rules",
                             summary="Alerta resolvido porque sua condição deixou de estar ativa.",
                             previous={"status": current["status"]}, new={"status": "resolved"},
                             related_entity_type="alert", related_entity_id=current["alert_id"])
    return list_alerts(status="open", database_url=database_url)


def list_alerts(*, status: str = "open", customer_id: str | None = None,
                database_url: str | None = None) -> list[dict[str, Any]]:
    stmt = select(alerts, customers.c.name.label("customer_name")).join(
        customers, alerts.c.customer_id == customers.c.customer_id)
    if status and status != "Todos":
        stmt = stmt.where(alerts.c.status == status)
    if customer_id:
        stmt = stmt.where(alerts.c.customer_id == customer_id)
    stmt = stmt.order_by(alerts.c.severity, alerts.c.created_at)
    with _engine(database_url).connect() as conn:
        return [dict(row) for row in conn.execute(stmt).mappings()]


def treat_alert(alert_id: str, *, actor: str, note: str = "",
                database_url: str | None = None) -> None:
    if not actor.strip():
        raise ValueError("Informe quem está tratando o alerta.")
    with _engine(database_url).begin() as conn:
        current = conn.execute(select(alerts).where(alerts.c.alert_id == alert_id)).mappings().first()
        if not current:
            raise ValueError("Alerta não encontrado.")
        if current["status"] == "treated":
            return
        now = _now()
        conn.execute(update(alerts).where(alerts.c.alert_id == alert_id).values(
            status="treated", updated_at=now, treated_at=now,
            treated_by=actor.strip(), treatment_note=note.strip() or None))
        _write_event(conn, customer_id=current["customer_id"], event_type="alert_treated",
                     actor=actor, source="operator", summary=f"Alerta tratado: {current['reason']}",
                     previous={"status": current["status"]},
                     new={"status": "treated", "note": note.strip()},
                     related_entity_type="alert", related_entity_id=alert_id)


def work_queue(*, actor: str | None = None, today: date | None = None,
               database_url: str | None = None) -> dict[str, list[dict[str, Any]]]:
    today = today or date.today()
    refresh_alerts(today=today, database_url=database_url)
    engine = _engine(database_url)
    task_stmt = select(tasks, customers.c.name.label("customer_name"),
                       customers.c.origin.label("origin"),
                       customers.c.lifecycle_status.label("lifecycle_status")).join(
        customers, tasks.c.customer_id == customers.c.customer_id).where(
        tasks.c.status.in_(("open", "in_progress")))
    if actor:
        task_stmt = task_stmt.where(tasks.c.owner == actor)
    task_stmt = task_stmt.order_by(tasks.c.due_date, tasks.c.priority)
    with engine.connect() as conn:
        task_rows = [dict(x) for x in conn.execute(task_stmt).mappings()]
        for row in task_rows:
            row["bucket"] = "overdue" if row["due_date"] < today else "today" if row["due_date"] == today else "upcoming"
        alert_rows = list_alerts(status="open", database_url=database_url)
        if actor:
            alert_rows = [x for x in alert_rows if x.get("treated_by") in (None, actor)]
        renewals = []
        subs = conn.execute(select(subscriptions).where(subscriptions.c.status == "active")).mappings().all()
        customers_by_id = {x["customer_id"]: x for x in conn.execute(select(customers)).mappings()}
        for sub in subs:
            confirmed = _confirmed(sub["confirmed_fields_json"])
            renewal = sub["renewal_date"]
            if "renewal_date" not in confirmed or renewal is None:
                continue
            days = (renewal - today).days
            if 0 <= days <= 30:
                customer = customers_by_id.get(sub["customer_id"])
                if customer and (not actor or customer["owner"] == actor):
                    renewals.append({"subscription_id": sub["subscription_id"],
                        "customer_id": sub["customer_id"], "customer_name": customer["name"],
                        "renewal_date": renewal, "days_remaining": days,
                        "owner": customer["owner"], "plan_tier": sub["plan_tier"],
                        "mrr_current": sub["mrr_current"], "currency": sub["currency"]})
        renewals.sort(key=lambda x: (x["days_remaining"], x["customer_name"].casefold()))
        return {"today": [x for x in task_rows if x["bucket"] == "today"],
                "overdue": [x for x in task_rows if x["bucket"] == "overdue"],
                "upcoming": [x for x in task_rows if x["bucket"] == "upcoming"],
                "renewals": renewals, "alerts": alert_rows}


def management_summary(*, today: date | None = None,
                       database_url: str | None = None) -> dict[str, Any]:
    today = today or date.today()
    queue = work_queue(today=today, database_url=database_url)
    engine = _engine(database_url)
    with engine.connect() as conn:
        all_customers = conn.execute(select(customers).where(customers.c.archived_at.is_(None))).mappings().all()
        open_tasks = conn.execute(select(tasks).where(tasks.c.status.in_(("open", "in_progress")))).mappings().all()
        owners = {}
        for task in open_tasks:
            if task["due_date"] < today:
                owners[task["owner"]] = owners.get(task["owner"], 0) + 1
        no_next_action = []
        customer_ids_with_open_tasks = {x["customer_id"] for x in open_tasks}
        for customer in all_customers:
            if customer["lifecycle_status"] == "active" and customer["customer_id"] not in customer_ids_with_open_tasks:
                no_next_action.append({"customer_id": customer["customer_id"], "name": customer["name"], "owner": customer["owner"]})
        legacy_by_status = {}
        for customer in all_customers:
            if customer["origin"] == "legacy":
                key = customer["verification_status"]
                legacy_by_status[key] = legacy_by_status.get(key, 0) + 1
        movement_rows = conn.execute(select(journey_events).where(
            journey_events.c.event_type.in_(("subscription_change", "renewal", "pause", "total_loss", "reactivation"))
        ).order_by(journey_events.c.occurred_at.desc())).mappings().all()
        movements = []
        for row in movement_rows:
            customer = next((x for x in all_customers if x["customer_id"] == row["customer_id"]), None)
            movements.append({"event_id": row["event_id"], "customer_id": row["customer_id"],
                "customer_name": customer["name"] if customer else row["customer_id"],
                "event_type": row["event_type"], "occurred_at": row["occurred_at"],
                "actor": row["actor"], "mrr_delta": row["mrr_delta"], "summary": row["summary"]})
        counts = {
            "customers": len(all_customers),
            "native": sum(x["origin"] == "native" for x in all_customers),
            "legacy": sum(x["origin"] == "legacy" for x in all_customers),
            "legacy_by_verification": legacy_by_status,
            "open_alerts": len(list_alerts(status="open", database_url=database_url)),
            "treated_alerts": len(list_alerts(status="treated", database_url=database_url)),
            "overdue_by_owner": owners,
            "customers_without_next_action": len(no_next_action),
            "renewals_30_days": len(queue["renewals"]),
        }
        return {"counts": counts, "queue": queue, "overdue_by_owner": owners,
                "customers_without_next_action": no_next_action,
                "confirmed_movements": movements[:100]}


def source_import_status(*, database_url: str | None = None) -> list[dict[str, Any]]:
    engine = _engine(database_url)
    with engine.connect() as conn:
        return [dict(x) for x in conn.execute(select(source_imports).order_by(source_imports.c.source_table)).mappings()]


def is_persistent_database(database_url: str | None = None) -> bool:
    return not resolve_database_url(database_url).startswith("sqlite:")


def reset_demo_data(database_url: str | None = None) -> int:
    """Explicitly reset only the SQLite demo store, then reseed immutable source rows."""
    resolved = resolve_database_url(database_url)
    if not resolved.startswith("sqlite:"):
        raise ValueError("Reset demo só é permitido em SQLite local; não use em produção.")
    engine = initialize_store(resolved, seed=False)
    inspector = __import__("sqlalchemy").inspect(engine)
    old_tables = set(inspector.get_table_names())
    names = ["op_alerts", "op_tasks", "op_interactions", "op_subscriptions",
             "op_journey_events", "op_source_records", "op_source_imports", "op_customers",
             "retention_action_events", "retention_actions", "crm_events", "crm_interactions", "crm_accounts"]
    with engine.begin() as conn:
        customer_count = conn.execute(select(func.count()).select_from(customers)).scalar_one()
        for name in names:
            if name in old_tables:
                conn.exec_driver_sql(f'DELETE FROM "{name}"')
    _seed_legacy_and_sources(engine)
    return int(customer_count)



def create_opportunity(*, name: str, owner: str, actor: str,
                       industry: str = "", country: str = "", referral_source: str = "",
                       sales_stage: str = "Lead novo", opportunity_value_estimate: float | None = None,
                       opportunity_currency: str = "USD", expected_close_date: date | str | None = None,
                       next_action: str = "", next_action_due: date | str | None = None,
                       next_action_priority: str = "P2", notes: str = "",
                       database_url: str | None = None) -> str:
    """Create a native lead/opportunity, keeping contract and lifecycle unknown."""
    stages = ("Lead novo", "Qualificação", "Descoberta", "Proposta", "Negociação",
              "Fechado ganho", "Fechado perdido", "Onboarding", "Ativo", "Renovação", "Encerrado")
    name, owner, actor = name.strip(), owner.strip(), actor.strip()
    if not name or not owner or not actor:
        raise ValueError("Nome da oportunidade, responsável e ator são obrigatórios.")
    if sales_stage not in stages:
        raise ValueError("Etapa comercial inválida.")
    if opportunity_currency not in CURRENCIES:
        raise ValueError("Moeda da oportunidade inválida.")
    if opportunity_value_estimate is not None and float(opportunity_value_estimate) < 0:
        raise ValueError("Valor estimado não pode ser negativo.")
    if next_action.strip() and _date(next_action_due) is None:
        raise ValueError("Próxima ação exige prazo.")
    if not next_action.strip() and next_action_due:
        raise ValueError("Informe a próxima ação ou remova o prazo.")
    identity, now = "L-" + uuid.uuid4().hex[:12].upper(), _now()
    values = {"customer_id": identity, "name": name, "industry": industry.strip() or None,
              "country": country.strip() or None, "referral_source": referral_source.strip() or None,
              "signup_date": None, "lifecycle_status": None, "health_status": None,
              "owner": owner, "verification_status": "partially_validated",
              "verification_fields_json": _json({"name": {"verified_at": now, "actor": actor, "source": "native"},
                  "owner": {"verified_at": now, "actor": actor, "source": "native"}}),
              "origin": "native", "sales_stage": sales_stage,
              "opportunity_value_estimate": float(opportunity_value_estimate) if opportunity_value_estimate is not None else None,
              "opportunity_currency": opportunity_currency if opportunity_value_estimate is not None else None,
              "expected_close_date": _date(expected_close_date), "notes": notes.strip() or None,
              "archived_at": None, "created_at": now, "updated_at": now}
    with _engine(database_url).begin() as conn:
        conn.execute(insert(customers).values(values))
        _write_event(conn, customer_id=identity, event_type="opportunity_created", actor=actor,
                     source="native", summary=f"Oportunidade criada · etapa {sales_stage}.", new=values)
        if next_action.strip():
            _create_task(conn, customer_id=identity, title=next_action, owner=owner,
                         due_date=_date(next_action_due), priority=next_action_priority,
                         created_from=None, actor=actor, source="native")
    return identity
