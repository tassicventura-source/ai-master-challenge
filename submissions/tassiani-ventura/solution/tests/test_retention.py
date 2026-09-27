from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from src.action_store import list_actions, list_events, save_action
from src.data_access import load_table
from src.retention import AREAS, OBSERVATION_CUTOFF, PRIORITY_ORDER, build_signals, signal_snapshot


def build():
    return build_signals(
        load_table("account_360"), load_table("feature_usage"),
        load_table("customer_interactions"), load_table("lifecycle_events"),
    )


def test_signals_are_rule_based_auditable_and_cover_four_areas():
    signals = build()
    assert set(signals.area) == set(AREAS)
    assert signals.signal_id.is_unique
    assert signals.source_refs.map(bool).all()
    assert signals.priority.isin(PRIORITY_ORDER).all()
    assert signals.priority_order.is_monotonic_increasing
    assert signals.signal_date.le(OBSERVATION_CUTOFF).all()
    assert "score" not in signals.columns
    assert "probability" not in signals.columns


def test_growth_queue_uses_documented_mature_cohort_and_keeps_event_uncertainty():
    signals = build()
    growth = signals[signals.area.eq("Growth/Comercial")]
    assert len(growth) == 22
    assert growth.priority.eq("P3 — revisão planejada").all()
    all_signals = growth.evidence.map(lambda e: e["recorded_event_within_90d"])
    assert all_signals.value_counts().to_dict() == {"sim": 14, "não": 8}
    assert growth.uncertainty.str.contains("não classifica a conta como em risco").all()


def test_product_signals_only_use_subscription_window_and_explain_threshold():
    signals = build()
    product = signals[signals.area.eq("Produto")]
    assert len(product) > 0
    for row in product.itertuples():
        evidence = row.evidence
        assert evidence["error_count_sum_in_subscription_window"] >= 5
        assert evidence["threshold"] == "error_count somado >= 5 por conta × funcionalidade"
        ids = evidence["source_usage_event_ids"]
        assert ids and len(ids) == evidence["source_records"]
        assert all(ref.startswith("feature_usage:") for ref in row.source_refs)
        assert "5.568/25.000" in row.uncertainty


def test_support_signals_are_post_signup_and_urgent_or_escalated():
    signals = build()
    support = signals[signals.area.eq("CS/Suporte")]
    assert len(support) > 0
    for row in support.itertuples():
        evidence = row.evidence
        assert evidence["lifecycle_temporal_status"] == "on_or_after_signup"
        assert evidence["priority"] == "urgent" or evidence["escalation_flag"] is True
        assert evidence["ticket_id"] in row.source_refs[0]
        assert "não provam causa" in row.uncertainty


def test_finance_does_not_convert_legacy_events_to_economic_loss():
    signals = build()
    finance = signals[signals.area.eq("Finance/RevOps")]
    lifecycle = load_table("lifecycle_events")
    assert len(finance) == len(lifecycle) == 600
    for row in finance.itertuples():
        assert row.evidence["economic_outcome"] == "unreconciled"
        assert "não é perda confirmada" in row.uncertainty
        assert "churn_event" in row.uncertainty
    active_refund = finance[
        finance.evidence.map(lambda e: e["paid_context_at_event"] == "paid_line_active" and e["refund_amount_usd_as_recorded"] > 0)
    ]
    assert active_refund.priority.eq("P1 — verificar primeiro").all()


def test_action_insert_update_and_audit_survive_new_connections(tmp_path):
    signals = build()
    signal = signal_snapshot(signals.iloc[0])
    db = tmp_path / "actions.sqlite"
    action_id = save_action(
        signal=signal, action_text="Revisar o caso e falar com a conta", owner="Ana Silva",
        priority=signal["priority"], due_date=date(2026, 10, 3), status="Aberta",
        observation="Evidência revisada.", path=db,
    )
    loaded = list_actions(signal_id=signal["signal_id"], path=db)
    assert len(loaded) == 1
    assert loaded[0]["action_id"] == action_id
    assert loaded[0]["owner"] == "Ana Silva"
    assert json.loads(loaded[0]["signal_snapshot_json"])["signal_id"] == signal["signal_id"]
    history = list_events(action_id, path=db)
    assert len(history) == 1 and history[0]["event_type"] == "created"

    save_action(
        signal=signal, action_text="Cliente contatado; validar retorno", owner="Bruno Lima",
        priority=signal["priority"], due_date="2026-10-05", status="Em andamento",
        observation="Contato enviado.", action_id=action_id, path=db,
    )
    updated = list_actions(signal_id=signal["signal_id"], path=db)
    assert len(updated) == 1
    assert updated[0]["owner"] == "Bruno Lima"
    assert updated[0]["status"] == "Em andamento"
    history = list_events(action_id, path=db)
    assert [item["event_type"] for item in history] == ["created", "updated"]
    changes = json.loads(history[1]["changed_fields_json"])
    assert "owner" in changes and "status" in changes


def test_action_requires_owner_and_result_before_completion(tmp_path):
    signal = signal_snapshot(build().iloc[0])
    args = dict(signal=signal, action_text="Validar evidência", owner="CS", priority=signal["priority"],
                due_date=date(2026, 10, 1), status="Aberta", path=tmp_path / "actions.sqlite")
    with pytest.raises(ValueError, match="resultado"):
        save_action(**(args | {"status": "Concluída"}))
    with pytest.raises(ValueError, match="responsável"):
        save_action(**(args | {"owner": ""}))
    action_id = save_action(**(args | {"status": "Concluída", "result": "Caso revisado; sem perda confirmada."}))
    assert list_actions(signal_id=signal["signal_id"], path=tmp_path / "actions.sqlite")[0]["action_id"] == action_id


def test_action_cannot_be_moved_to_a_different_signal(tmp_path):
    signals = build()
    db = tmp_path / "actions.sqlite"
    first, second = signal_snapshot(signals.iloc[0]), signal_snapshot(signals.iloc[1])
    action_id = save_action(signal=first, action_text="Revisar", owner="CS", priority=first["priority"],
                            due_date=date(2026, 10, 1), status="Aberta", path=db)
    with pytest.raises(ValueError, match="outro sinal"):
        save_action(signal=second, action_text="Revisar", owner="CS", priority=second["priority"],
                    due_date=date(2026, 10, 1), status="Aberta", action_id=action_id, path=db)


def test_action_is_readable_after_process_restart(tmp_path):
    signal = signal_snapshot(build().iloc[0])
    db = tmp_path / "restart.sqlite"
    save_action(signal=signal, action_text="Reconciliar e acompanhar", owner="Finance",
                priority=signal["priority"], due_date=date(2026, 10, 8),
                status="Aberta", observation="Gravada antes do restart.", path=db)
    code = (
        "import json,sys; from src.action_store import list_actions; "
        "print(json.dumps(list_actions(signal_id=sys.argv[2], path=sys.argv[1])))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(db), signal["signal_id"]],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True,
    )
    actions = json.loads(result.stdout)
    assert len(actions) == 1
    assert actions[0]["owner"] == "Finance"
    assert actions[0]["observation"] == "Gravada antes do restart."


def test_rows_after_observation_cutoff_never_enter_signal_feed():
    from src.retention import build_signals

    accounts = load_table("account_360").copy()
    usage = load_table("feature_usage").copy()
    interactions = load_table("customer_interactions").copy()
    lifecycle = load_table("lifecycle_events").copy()
    account_index = accounts.index[
        accounts.referral_source.eq("organic") & accounts.first_paid_plan.eq("Enterprise")
    ][0]
    accounts.loc[account_index, "account_id"] = "A-FUTURE-CUTOFF-TEST"
    accounts.loc[account_index, "signup_date"] = pd.Timestamp("2025-01-01")
    accounts.loc[account_index, "first_paid_date"] = pd.Timestamp("2025-01-02")

    usage_index = usage.index[
        usage.temporal_status.eq("within_subscription") & usage.error_count.gt(0)
    ][0]
    usage.loc[usage_index, "usage_event_id"] = "U-FUTURE-CUTOFF-TEST"
    usage.loc[usage_index, "usage_date"] = pd.Timestamp("2025-01-03")
    usage.loc[usage_index, "error_count"] = 100

    interactions.loc[interactions.index[0], "interaction_id"] = "T-FUTURE-CUTOFF-TEST"
    interactions.loc[interactions.index[0], "occurred_at"] = pd.Timestamp("2025-01-04")
    interactions.loc[interactions.index[0], "lifecycle_temporal_status"] = "on_or_after_signup"
    interactions.loc[interactions.index[0], "priority"] = "urgent"
    interactions.loc[interactions.index[0], "escalation_flag"] = 0

    lifecycle.loc[lifecycle.index[0], "event_id"] = "LE-FUTURE-CUTOFF-TEST"
    lifecycle.loc[lifecycle.index[0], "event_date"] = pd.Timestamp("2025-01-05")

    signals = build_signals(accounts, usage, interactions, lifecycle)
    ids = set(signals.signal_id)
    assert "GRO-A-FUTURE-CUTOFF-TEST-2024-organic-enterprise" not in ids
    assert not any("U-FUTURE-CUTOFF-TEST" in refs for refs in signals.source_refs)
    assert "SUP-T-FUTURE-CUTOFF-TEST" not in ids
    assert "FIN-LE-FUTURE-CUTOFF-TEST" not in ids
