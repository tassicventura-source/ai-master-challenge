from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "ravenstack.sqlite"

DATE_COLS = {
    "accounts": ["signup_date"],
    "subscriptions": ["start_date", "end_date", "movement_effective_date"],
    "feature_usage": ["usage_date"],
    "customer_interactions": ["occurred_at", "closed_at", "next_action_due_at"],
    "lifecycle_events": ["event_date", "next_paid_start_date"],
    "account_360": ["signup_date", "first_paid_date", "last_valid_usage_date", "last_interaction_at", "first_recorded_event_date", "observation_end"],
}


ALLOWED_TABLES = frozenset([*DATE_COLS, "data_quality_summary"])


def ensure_database():
    if not DB_PATH.exists():
        from src.transform import build_all
        build_all(ROOT / "data/raw", ROOT / "data/processed", ROOT / "data/audit", DB_PATH)


@st.cache_data(show_spinner=False, max_entries=24)
def _load_table(name: str, version: int) -> pd.DataFrame:
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        df = pd.read_sql_query(f'SELECT * FROM "{name}"', conn)
    for c in DATE_COLS.get(name, []):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    for col in ["recorded_event_within_90d", "eligible_90d"]:
        if col in df:
            df[col] = df[col].astype("boolean")
    return df


def load_table(name: str) -> pd.DataFrame:
    if name not in ALLOWED_TABLES:
        raise ValueError("Tabela não permitida.")
    ensure_database()
    return _load_table(name, DB_PATH.stat().st_mtime_ns)
