from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.transform import load_raw, transform_accounts, transform_subscriptions, transform_usage, transform_interactions, transform_lifecycle_events, build_account_360

RAW = ROOT / "data" / "raw"


def test_row_counts_preserved():
    raw = load_raw(RAW)
    assert len(transform_accounts(raw["accounts"])) == 500
    assert len(transform_subscriptions(raw["subscriptions"])) == 5000
    assert len(transform_usage(raw["feature_usage"], raw["subscriptions"], raw["accounts"])) == 25000
    assert len(transform_interactions(raw["support_tickets"], raw["accounts"])) == 2000
    assert len(transform_lifecycle_events(raw["churn_events"], raw["subscriptions"])) == 600


def test_usage_canonical_id_is_unique():
    raw = load_raw(RAW)
    u = transform_usage(raw["feature_usage"], raw["subscriptions"], raw["accounts"])
    assert u["usage_event_id"].is_unique
    assert u["source_usage_id"].nunique() == 24979


def test_known_temporal_populations():
    raw = load_raw(RAW)
    u = transform_usage(raw["feature_usage"], raw["subscriptions"], raw["accounts"])
    i = transform_interactions(raw["support_tickets"], raw["accounts"])
    assert (u["temporal_status"] == "within_subscription").sum() == 5568
    assert (i["lifecycle_temporal_status"] == "on_or_after_signup").sum() == 923


def test_lifecycle_context_matches_reproduced_finding():
    raw = load_raw(RAW)
    e = transform_lifecycle_events(raw["churn_events"], raw["subscriptions"])
    vc = e["paid_context_at_event"].value_counts().to_dict()
    assert vc.get("paid_line_active", 0) == 531
    assert vc.get("before_first_paid", 0) == 67
    assert vc.get("previously_paid_no_active_line", 0) == 2
    assert e["canonical_event_type"].isna().all()


def test_removed_legacy_fields_are_not_canonical():
    raw = load_raw(RAW)
    a = transform_accounts(raw["accounts"])
    s = transform_subscriptions(raw["subscriptions"])
    assert "churn_flag" not in a.columns
    assert "plan_tier" not in a.columns
    assert "upgrade_flag" not in s.columns
    assert "downgrade_flag" not in s.columns
    assert "churn_flag" not in s.columns


def test_account_360_keeps_one_row_per_account():
    raw = load_raw(RAW)
    p = {
        "accounts": transform_accounts(raw["accounts"]),
        "subscriptions": transform_subscriptions(raw["subscriptions"]),
        "feature_usage": transform_usage(raw["feature_usage"], raw["subscriptions"], raw["accounts"]),
        "customer_interactions": transform_interactions(raw["support_tickets"], raw["accounts"]),
        "lifecycle_events": transform_lifecycle_events(raw["churn_events"], raw["subscriptions"]),
    }
    a360 = build_account_360(raw, p)
    assert len(a360) == 500
    assert a360["account_id"].is_unique
