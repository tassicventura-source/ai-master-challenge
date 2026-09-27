from __future__ import annotations

import pandas as pd
import numpy as np


def fmt_money(v, decimals=0) -> str:
    if pd.isna(v):
        return "—"
    return "US$ " + f"{float(v):,.{decimals}f}".translate(str.maketrans({",": ".", ".": ","}))


def executive_metrics(account_360: pd.DataFrame, lifecycle: pd.DataFrame, interactions: pd.DataFrame, usage: pd.DataFrame) -> dict:
    a = account_360.copy()
    return {
        "accounts": int(len(a)),
        "initial_value": float(a["initial_value_registered"].fillna(0).sum()),
        "recorded_events": int(len(lifecycle)),
        "paid_active_events": int((lifecycle["paid_context_at_event"] == "paid_line_active").sum()),
        "before_paid_events": int((lifecycle["paid_context_at_event"] == "before_first_paid").sum()),
        "post_paid_no_active": int((lifecycle["paid_context_at_event"] == "previously_paid_no_active_line").sum()),
        "valid_interactions": int((interactions["lifecycle_temporal_status"] == "on_or_after_signup").sum()),
        "valid_usage": int((usage["temporal_status"] == "within_subscription").sum()),
    }


def growth_by_source(account_360: pd.DataFrame) -> pd.DataFrame:
    d = account_360.copy()
    d["signup_year"] = d["signup_date"].dt.year
    out = d.groupby(["signup_year", "referral_source"], dropna=False).agg(
        accounts=("account_id", "nunique"),
        eligible_90d=("eligible_90d", "sum"),
        events_90d=("recorded_event_within_90d", "sum"),
        initial_value=("initial_value_registered", "sum"),
        median_initial_value=("initial_value_registered", "median"),
        recorded_event_90d=("recorded_event_within_90d", "mean"),
    ).reset_index()
    return out


def product_summary(account_360: pd.DataFrame) -> pd.DataFrame:
    cols = ["account_id", "industry", "referral_source", "first_paid_plan", "initial_value_registered", "valid_usage_count", "valid_features_used", "valid_errors", "valid_interactions"]
    return account_360[cols].copy()


def support_priority_summary(interactions: pd.DataFrame) -> pd.DataFrame:
    d = interactions[interactions["lifecycle_temporal_status"] == "on_or_after_signup"].copy()
    return d.groupby("priority").agg(
        interactions=("interaction_id", "count"),
        median_first_response_min=("first_response_time_minutes", "median"),
        median_resolution_h=("resolution_time_hours", "median"),
        escalation_rate=("escalation_flag", "mean"),
        csat_response_rate=("satisfaction_score", lambda s: s.notna().mean()),
        csat_mean=("satisfaction_score", "mean"),
    ).reset_index()


def missing_new_fields(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    rows=[]
    for f in fields:
        if f not in df.columns:
            continue
        s=df[f]
        missing = int(s.isna().sum() + (s.astype("string").str.strip().eq("").fillna(False).sum() if s.dtype == object else 0))
        rows.append({"field":f,"filled":len(df)-missing,"rows":len(df),"coverage":(len(df)-missing)/len(df) if len(df) else np.nan})
    return pd.DataFrame(rows)
