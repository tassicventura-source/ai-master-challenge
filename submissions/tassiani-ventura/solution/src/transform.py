from __future__ import annotations

from pathlib import Path
import hashlib
import sqlite3
import os
import tempfile
import pandas as pd
import numpy as np

RAW_FILES = {
    "accounts": "ravenstack_accounts.csv",
    "subscriptions": "ravenstack_subscriptions.csv",
    "feature_usage": "ravenstack_feature_usage.csv",
    "support_tickets": "ravenstack_support_tickets.csv",
    "churn_events": "ravenstack_churn_events.csv",
}


def _parse_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")
    return out


def load_raw(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    frames = {name: pd.read_csv(raw_dir / fname) for name, fname in RAW_FILES.items()}
    frames["accounts"] = _parse_dates(frames["accounts"], ["signup_date"])
    frames["subscriptions"] = _parse_dates(frames["subscriptions"], ["start_date", "end_date"])
    frames["feature_usage"] = _parse_dates(frames["feature_usage"], ["usage_date"])
    frames["support_tickets"] = _parse_dates(frames["support_tickets"], ["submitted_at", "closed_at"])
    frames["churn_events"] = _parse_dates(frames["churn_events"], ["churn_date"])
    validate_raw(frames)
    return frames


def validate_raw(frames):
    """Fail explicitly on structural defects; temporal anomalies remain auditable."""
    keys = {"accounts": "account_id", "subscriptions": "subscription_id",
            "support_tickets": "ticket_id", "churn_events": "churn_event_id"}
    for name, key in keys.items():
        d = frames[name]
        if d[key].isna().any() or not d[key].is_unique:
            raise ValueError(f"{name}: chave {key} ausente ou duplicada.")
    for name in ["subscriptions", "support_tickets", "churn_events"]:
        if not frames[name]["account_id"].isin(frames["accounts"]["account_id"]).all():
            raise ValueError(f"{name}: conta de referência inexistente.")
    if not frames["feature_usage"]["subscription_id"].isin(frames["subscriptions"]["subscription_id"]).all():
        raise ValueError("feature_usage: assinatura de referência inexistente.")
    required_dates = {"accounts": "signup_date", "subscriptions": "start_date",
                      "feature_usage": "usage_date", "support_tickets": "submitted_at",
                      "churn_events": "churn_date"}
    for name, col in required_dates.items():
        if frames[name][col].isna().any():
            raise ValueError(f"{name}: {col} ausente ou inválida.")


def transform_accounts(raw: pd.DataFrame) -> pd.DataFrame:
    keep = ["account_id", "account_name", "industry", "country", "signup_date", "referral_source"]
    out = raw[keep].copy()
    out["referral_detail"] = pd.NA
    out["icp_segment"] = pd.NA
    out["owner_id"] = pd.NA
    out["journey_stage"] = pd.NA
    out["source_system"] = "source_not_identified"
    return out


def transform_subscriptions(raw: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "subscription_id", "account_id", "start_date", "end_date", "plan_tier", "seats",
        "mrr_amount", "arr_amount", "is_trial", "billing_frequency", "auto_renew_flag"
    ]
    out = raw[keep].copy()
    out.insert(2, "contract_id", pd.NA)
    out["record_state"] = np.where(out["end_date"].notna(), "ended_record", "open_record")
    out["movement_type"] = pd.NA
    out["movement_effective_date"] = pd.NaT
    out["source_system"] = "source_not_identified"
    return out


def _canonical_usage_id(row: pd.Series) -> str:
    payload = "|".join(str(row.get(c, "")) for c in [
        "usage_id", "subscription_id", "usage_date", "feature_name", "usage_count",
        "usage_duration_secs", "error_count", "is_beta_feature"
    ])
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"UE-{digest}"


def transform_usage(raw: pd.DataFrame, subscriptions_raw: pd.DataFrame, accounts_raw: pd.DataFrame) -> pd.DataFrame:
    subs = subscriptions_raw[["subscription_id", "account_id", "start_date", "end_date"]].copy()
    out = raw.merge(subs, on="subscription_id", how="left", validate="many_to_one")
    out = out.merge(accounts_raw[["account_id", "signup_date"]], on="account_id", how="left", validate="many_to_one")

    out["source_usage_id"] = out["usage_id"]
    out["usage_event_id"] = out.apply(_canonical_usage_id, axis=1)
    # Hash collisions are improbable; make any collision deterministic without deleting rows.
    dup_seq = out.groupby("usage_event_id").cumcount()
    mask = dup_seq.gt(0)
    out.loc[mask, "usage_event_id"] = out.loc[mask, "usage_event_id"] + "-" + dup_seq[mask].astype(str)

    within = (out["usage_date"] >= out["start_date"]) & (out["end_date"].isna() | (out["usage_date"] <= out["end_date"]))
    before = out["usage_date"] < out["start_date"]
    after = out["end_date"].notna() & (out["usage_date"] > out["end_date"])
    out["temporal_status"] = np.select([within, before, after], ["within_subscription", "before_subscription", "after_subscription"], default="unknown")
    out["signup_temporal_status"] = np.where(out["usage_date"] < out["signup_date"], "before_signup", "on_or_after_signup")
    out["user_id"] = pd.NA
    out["action_name"] = pd.NA
    out["event_success"] = pd.NA
    out["context"] = pd.NA
    out["source_system"] = "source_not_identified"

    cols = [
        "usage_event_id", "source_usage_id", "subscription_id", "account_id", "usage_date",
        "feature_name", "user_id", "action_name", "usage_count", "usage_duration_secs",
        "error_count", "event_success", "is_beta_feature", "context", "temporal_status",
        "signup_temporal_status", "source_system"
    ]
    return out[cols].copy()


def transform_interactions(raw: pd.DataFrame, accounts_raw: pd.DataFrame) -> pd.DataFrame:
    out = raw.merge(accounts_raw[["account_id", "signup_date"]], on="account_id", how="left", validate="many_to_one")
    out["interaction_id"] = out["ticket_id"]
    out["occurred_at"] = out["submitted_at"]
    out["area"] = "Support"
    out["interaction_type"] = "support_ticket"
    out["channel"] = pd.NA
    out["owner_id"] = pd.NA
    out["topic"] = pd.NA
    out["feature_name"] = pd.NA
    out["problem_type"] = pd.NA
    out["impact_level"] = pd.NA
    out["root_cause"] = pd.NA
    out["recurrence_flag"] = pd.NA
    out["outcome"] = np.where(out["closed_at"].notna(), "closed", "open")
    out["next_action"] = pd.NA
    out["next_action_due_at"] = pd.NaT
    out["lifecycle_temporal_status"] = np.where(out["submitted_at"] < out["signup_date"], "before_signup", "on_or_after_signup")
    out["source_system"] = "source_not_identified"
    cols = [
        "interaction_id", "account_id", "occurred_at", "closed_at", "area", "interaction_type",
        "channel", "owner_id", "topic", "feature_name", "problem_type", "impact_level",
        "root_cause", "recurrence_flag", "outcome", "next_action", "next_action_due_at", "priority",
        "first_response_time_minutes", "resolution_time_hours", "satisfaction_score", "escalation_flag",
        "lifecycle_temporal_status", "source_system"
    ]
    return out[cols].copy()


def _paid_context_for_event(event_row: pd.Series, paid_subs: pd.DataFrame) -> tuple[str, bool, pd.Timestamp | pd.NaT]:
    acct = event_row["account_id"]
    dt = event_row["churn_date"]
    s = paid_subs[paid_subs["account_id"] == acct]
    if s.empty:
        return "no_paid_history_observed", False, pd.NaT
    first_paid = s["start_date"].min()
    active = s[(s["start_date"] <= dt) & (s["end_date"].isna() | (s["end_date"] >= dt))]
    had_paid_before = bool((s["start_date"] <= dt).any())
    next_starts = s.loc[s["start_date"] > dt, "start_date"]
    next_paid = next_starts.min() if not next_starts.empty else pd.NaT
    if not active.empty:
        return "paid_line_active", had_paid_before, next_paid
    if dt < first_paid:
        return "before_first_paid", had_paid_before, next_paid
    return "previously_paid_no_active_line", had_paid_before, next_paid


def transform_lifecycle_events(raw: pd.DataFrame, subscriptions_raw: pd.DataFrame) -> pd.DataFrame:
    paid = subscriptions_raw[(~subscriptions_raw["is_trial"]) & (subscriptions_raw["mrr_amount"] > 0)].copy()
    contexts = raw.apply(lambda r: _paid_context_for_event(r, paid), axis=1)
    out = raw.copy()
    out["event_id"] = out["churn_event_id"]
    out["event_date"] = out["churn_date"]
    out["recorded_event_type"] = "churn_recorded"
    # Source README describes this flag as previous churn, not an event timestamp/type.
    out["legacy_reactivation_flag"] = out["is_reactivation"]
    out["canonical_event_type"] = pd.NA
    out["economic_outcome"] = "unreconciled"
    out["mrr_before"] = pd.NA
    out["mrr_after"] = pd.NA
    out["seats_before"] = pd.NA
    out["seats_after"] = pd.NA
    out["plan_before"] = pd.NA
    out["plan_after"] = pd.NA
    out["paid_context_at_event"] = [x[0] for x in contexts]
    out["had_paid_before"] = [x[1] for x in contexts]
    out["next_paid_start_date"] = [x[2] for x in contexts]
    out["reconciliation_status"] = "requires_contract_billing_confirmation"
    out["source_system"] = "source_not_identified"
    cols = [
        "event_id", "account_id", "event_date", "recorded_event_type", "legacy_reactivation_flag", "canonical_event_type",
        "reason_code", "economic_outcome", "mrr_before", "mrr_after", "seats_before", "seats_after",
        "plan_before", "plan_after", "refund_amount_usd", "paid_context_at_event", "had_paid_before",
        "next_paid_start_date", "reconciliation_status", "feedback_text", "source_system"
    ]
    return out[cols].copy()


def build_account_360(raw: dict[str, pd.DataFrame], processed: dict[str, pd.DataFrame], observation_end=None) -> pd.DataFrame:
    accounts = processed["accounts"].copy()
    subs = raw["subscriptions"].copy()
    paid = subs[(~subs["is_trial"]) & (subs["mrr_amount"] > 0)].copy()

    first_date = paid.groupby("account_id")["start_date"].min().rename("first_paid_date")
    first_rows = paid.merge(first_date, on="account_id", how="left")
    first_rows = first_rows[first_rows["start_date"] == first_rows["first_paid_date"]]
    initial = first_rows.groupby("account_id").agg(
        initial_value_registered=("mrr_amount", "sum"),
        initial_paid_lines=("subscription_id", "count"),
        initial_seats_sum=("seats", "sum"),
    ).reset_index().merge(first_date.reset_index(), on="account_id", how="left")

    # Representative first plan only when unique on first paid date; otherwise explicitly mixed.
    def first_plan(g: pd.DataFrame) -> str:
        plans = sorted(g["plan_tier"].dropna().astype(str).unique())
        return plans[0] if len(plans) == 1 else "mixed_same_day"
    fp = first_rows.groupby("account_id").apply(first_plan, include_groups=False).rename("first_paid_plan").reset_index()
    initial = initial.merge(fp, on="account_id", how="left")

    usage = processed["feature_usage"]
    uv = usage[usage["temporal_status"] == "within_subscription"]
    usage_agg = uv.groupby("account_id").agg(
        valid_usage_events=("usage_event_id", "count"),
        valid_usage_count=("usage_count", "sum"),
        valid_features_used=("feature_name", "nunique"),
        valid_errors=("error_count", "sum"),
        last_valid_usage_date=("usage_date", "max"),
    ).reset_index()

    interactions = processed["customer_interactions"]
    iv = interactions[interactions["lifecycle_temporal_status"] == "on_or_after_signup"]
    int_agg = iv.groupby("account_id").agg(
        valid_interactions=("interaction_id", "count"),
        escalations=("escalation_flag", "sum"),
        median_first_response_min=("first_response_time_minutes", "median"),
        median_resolution_hours=("resolution_time_hours", "median"),
        last_interaction_at=("occurred_at", "max"),
    ).reset_index()

    life = processed["lifecycle_events"]
    life_agg = life.groupby("account_id").agg(
        recorded_lifecycle_events=("event_id", "count"),
        first_recorded_event_date=("event_date", "min"),
        refunds_recorded=("refund_amount_usd", "sum"),
    ).reset_index()

    out = accounts.merge(initial, on="account_id", how="left")
    out = out.merge(usage_agg, on="account_id", how="left")
    out = out.merge(int_agg, on="account_id", how="left")
    out = out.merge(life_agg, on="account_id", how="left")
    out["days_to_first_paid"] = (out["first_paid_date"] - out["signup_date"]).dt.days
    out["recorded_event_within_90d"] = (
        out["first_recorded_event_date"].notna() &
        ((out["first_recorded_event_date"] - out["signup_date"]).dt.days.between(0, 90))
    )
    # Cohorts need a complete observation window. The cutoff is explicit and reproducible.
    cutoff = pd.Timestamp(observation_end) if observation_end is not None else raw["churn_events"]["churn_date"].max()
    out["observation_end"] = cutoff
    out["eligible_90d"] = (cutoff - out["signup_date"]).dt.days.ge(90)
    out["recorded_event_within_90d"] = out["recorded_event_within_90d"].astype("boolean").mask(~out["eligible_90d"])
    counts = ["valid_usage_events", "valid_usage_count", "valid_features_used", "valid_errors",
              "valid_interactions", "escalations", "recorded_lifecycle_events", "refunds_recorded"]
    out[counts] = out[counts].fillna(0)
    return out


def quality_summary(raw: dict[str, pd.DataFrame], processed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    accounts = raw["accounts"]
    subs = raw["subscriptions"]
    usage = processed["feature_usage"]
    interactions = processed["customer_interactions"]
    life = processed["lifecycle_events"]

    ev_accounts = set(raw["churn_events"]["account_id"])
    sub_end_accounts = set(subs.loc[subs["end_date"].notna(), "account_id"])
    flag_accounts = set(accounts.loc[accounts["churn_flag"], "account_id"])
    disagree = sum(1 for aid in accounts["account_id"] if len({aid in ev_accounts, aid in sub_end_accounts, aid in flag_accounts}) > 1)

    rows = [
        ("accounts", "Linhas", len(accounts), len(accounts), "ok"),
        ("subscriptions", "Linhas", len(subs), len(subs), "ok"),
        ("feature_usage", "Eventos dentro da janela da subscription", int((usage["temporal_status"] == "within_subscription").sum()), len(usage), "attention"),
        ("customer_interactions", "Interações no ou após signup", int((interactions["lifecycle_temporal_status"] == "on_or_after_signup").sum()), len(interactions), "attention"),
        ("lifecycle_events", "Eventos com contexto pago ativo", int((life["paid_context_at_event"] == "paid_line_active").sum()), len(life), "critical"),
        ("accounts", "Contas com desacordo entre três sinais legados de churn", int(disagree), len(accounts), "critical"),
        ("feature_usage", "IDs de origem duplicados", int(raw["feature_usage"]["usage_id"].duplicated(keep=False).sum()), len(raw["feature_usage"]), "attention"),
        ("customer_interactions", "Satisfaction ausente", int(raw["support_tickets"]["satisfaction_score"].isna().sum()), len(raw["support_tickets"]), "attention"),
    ]
    return pd.DataFrame(rows, columns=["base", "check", "count", "denominator", "status"])


def build_all(raw_dir: str | Path, processed_dir: str | Path, audit_dir: str | Path, db_path: str | Path) -> dict[str, pd.DataFrame]:
    raw_dir, processed_dir, audit_dir, db_path = Path(raw_dir), Path(processed_dir), Path(audit_dir), Path(db_path)
    processed_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    raw = load_raw(raw_dir)

    processed = {
        "accounts": transform_accounts(raw["accounts"]),
        "subscriptions": transform_subscriptions(raw["subscriptions"]),
        "feature_usage": transform_usage(raw["feature_usage"], raw["subscriptions"], raw["accounts"]),
        "customer_interactions": transform_interactions(raw["support_tickets"], raw["accounts"]),
        "lifecycle_events": transform_lifecycle_events(raw["churn_events"], raw["subscriptions"]),
    }
    account_360 = build_account_360(raw, processed)
    quality = quality_summary(raw, processed)

    for name, df in processed.items():
        df.to_csv(processed_dir / f"{name}.csv", index=False)
    account_360.to_csv(processed_dir / "account_360.csv", index=False)
    quality.to_csv(audit_dir / "data_quality_summary.csv", index=False)

    # Preserve fields intentionally removed from canonical tables for auditability.
    raw["accounts"][["account_id", "plan_tier", "seats", "is_trial", "churn_flag"]].to_csv(audit_dir / "accounts_legacy_fields.csv", index=False)
    raw["subscriptions"][["subscription_id", "upgrade_flag", "downgrade_flag", "churn_flag"]].to_csv(audit_dir / "subscriptions_legacy_flags.csv", index=False)
    raw["churn_events"][["churn_event_id", "preceding_upgrade_flag", "preceding_downgrade_flag", "is_reactivation"]].to_csv(audit_dir / "churn_legacy_flags.csv", index=False)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=".sqlite", dir=db_path.parent)
    os.close(fd)
    conn = sqlite3.connect(temp_path)
    try:
        for name, df in processed.items():
            write = df.copy()
            for c in write.columns:
                if pd.api.types.is_datetime64_any_dtype(write[c]):
                    write[c] = write[c].astype("string")
            write.to_sql(name, conn, if_exists="replace", index=False)
        tmp = account_360.copy()
        for c in tmp.columns:
            if pd.api.types.is_datetime64_any_dtype(tmp[c]):
                tmp[c] = tmp[c].astype("string")
        tmp.to_sql("account_360", conn, if_exists="replace", index=False)
        quality.to_sql("data_quality_summary", conn, if_exists="replace", index=False)
        for table in [*processed, "account_360"]:
            conn.execute(f'CREATE INDEX "idx_{table}_account" ON "{table}" (account_id)')
        conn.commit()
    except Exception:
        conn.close()
        Path(temp_path).unlink(missing_ok=True)
        raise
    else:
        conn.close()
        os.replace(temp_path, db_path)

    return {**processed, "account_360": account_360, "data_quality_summary": quality}
