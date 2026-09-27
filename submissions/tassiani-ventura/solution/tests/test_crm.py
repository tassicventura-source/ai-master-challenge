from __future__ import annotations

from datetime import date, timedelta
import json

import pytest

from src.action_store import (
    CRM_STAGES,
    INTERACTION_AREAS,
    crm_counts,
    get_crm_account,
    list_crm_accounts,
    list_crm_events,
    list_crm_interactions,
    save_crm_account,
    save_crm_interaction,
)


def account_args(**overrides):
    values = {
        "account_name": "Example Prospect",
        "owner_id": "ana@example.test",
        "journey_stage": "Lead novo",
        "record_origin": "Cadastro manual",
        "industry": "SaaS",
        "country": "BR",
        "referral_source": "partner",
        "referral_detail": "Partner referral",
        "icp_segment": "Mid-market",
        "deal_value_estimate": 12000.0,
        "deal_currency": "USD",
        "expected_close_date": date(2026, 12, 15),
        "next_action": "Agendar descoberta",
        "next_action_due_at": date(2026, 10, 2),
        "notes": "Notas de teste",
    }
    return values | overrides


def test_crm_account_create_update_pipeline_and_event_audit(tmp_path):
    db = tmp_path / "crm.sqlite"
    account_id = save_crm_account(**account_args(), path=db)
    assert account_id.startswith("CRM-")
    account = get_crm_account(account_id, path=db)
    assert account["account_name"] == "Example Prospect"
    assert account["journey_stage"] == "Lead novo"
    assert account["deal_value_estimate"] == 12000.0
    assert account["next_action"] == "Agendar descoberta"

    save_crm_account(**account_args(journey_stage="Proposta", owner_id="bruno@example.test"),
                     account_id=account_id, path=db)
    updated = get_crm_account(account_id, path=db)
    assert updated["journey_stage"] == "Proposta"
    assert updated["owner_id"] == "bruno@example.test"
    events = list_crm_events(entity_type="account", entity_id=account_id, path=db)
    assert [event["event_type"] for event in events] == ["created", "updated"]
    changed = json.loads(events[1]["changed_fields_json"])
    assert changed["journey_stage"] == "Proposta"
    assert changed["owner_id"] == "bruno@example.test"
    assert list_crm_accounts(stage="Proposta", owner="bruno@example.test", path=db)[0]["account_id"] == account_id
    assert crm_counts(path=db)["open_opportunities"] == 1


def test_dataset_account_can_be_associated_without_mutating_analytics(tmp_path):
    db = tmp_path / "crm.sqlite"
    account_id = "A-EXISTING-HISTORICAL"
    saved_id = save_crm_account(**account_args(account_name="Historical Company",
                                               record_origin="Conta do dataset"),
                                account_id=account_id, path=db)
    assert saved_id == account_id
    row = get_crm_account(account_id, path=db)
    assert row["record_origin"] == "Conta do dataset"
    assert row["journey_stage"] == "Lead novo"


def test_crm_account_validations(tmp_path):
    db = tmp_path / "crm.sqlite"
    with pytest.raises(ValueError, match="nome da conta"):
        save_crm_account(**account_args(account_name=" "), path=db)
    with pytest.raises(ValueError, match="responsável"):
        save_crm_account(**account_args(owner_id=""), path=db)
    with pytest.raises(ValueError, match="Etapa"):
        save_crm_account(**account_args(journey_stage="Risco alto"), path=db)
    with pytest.raises(ValueError, match="prazo"):
        save_crm_account(**account_args(next_action_due_at=None), path=db)
    with pytest.raises(ValueError, match="próxima ação"):
        save_crm_account(**account_args(next_action="", next_action_due_at=date(2026, 10, 2)), path=db)
    assert CRM_STAGES


def test_interaction_and_followup_create_update_and_audit(tmp_path):
    db = tmp_path / "crm.sqlite"
    account_id = save_crm_account(**account_args(next_action="", next_action_due_at=None), path=db)
    interaction_id = save_crm_interaction(
        account_id=account_id,
        occurred_at=date(2026, 9, 26),
        area="Comercial",
        interaction_type="Reunião",
        summary="Reunião de descoberta realizada",
        owner_id="ana@example.test",
        outcome="Cliente pediu proposta",
        next_action="Enviar proposta",
        next_action_due_at=date(2026, 9, 30),
        status="Planejada",
        path=db,
    )
    items = list_crm_interactions(account_id=account_id, open_only=True, path=db)
    assert len(items) == 1
    assert items[0]["interaction_id"] == interaction_id
    assert items[0]["next_action"] == "Enviar proposta"
    assert crm_counts(path=db)["open_followups"] == 1

    save_crm_interaction(
        account_id=account_id,
        occurred_at=date(2026, 9, 26),
        area="Comercial",
        interaction_type="Reunião",
        summary="Reunião de descoberta realizada",
        owner_id="ana@example.test",
        outcome="Proposta enviada; reunião concluída",
        next_action="Agendar negociação",
        next_action_due_at=date(2026, 10, 5),
        status="Concluída",
        interaction_id=interaction_id,
        path=db,
    )
    updated = list_crm_interactions(account_id=account_id, path=db)[0]
    assert updated["status"] == "Concluída"
    assert updated["next_action"] == "Agendar negociação"
    events = list_crm_events(entity_type="interaction", entity_id=interaction_id, path=db)
    assert [event["event_type"] for event in events] == ["created", "updated"]
    assert "outcome" in json.loads(events[1]["changed_fields_json"])
    assert crm_counts(path=db)["open_followups"] == 0


def test_interaction_requires_account_owner_summary_result_and_followup_due(tmp_path):
    db = tmp_path / "crm.sqlite"
    account_id = save_crm_account(**account_args(next_action="", next_action_due_at=None), path=db)
    base = dict(account_id=account_id, occurred_at=date.today(), area=INTERACTION_AREAS[1],
                interaction_type="Ligação", summary="Contato", owner_id="Ana", path=db)
    with pytest.raises(ValueError, match="resultado"):
        save_crm_interaction(**base, status="Concluída")
    with pytest.raises(ValueError, match="prazo"):
        save_crm_interaction(**(base | {"next_action": "Retornar"}))
    with pytest.raises(ValueError, match="Cadastre/associe"):
        save_crm_interaction(**(base | {"account_id": "missing-account"}))
    with pytest.raises(ValueError, match="obrigatórios"):
        save_crm_interaction(**(base | {"summary": " "}))
    with pytest.raises(ValueError, match="responsável"):
        save_crm_interaction(**(base | {"owner_id": " "}))


def test_crm_account_and_followup_survive_new_process(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    db = tmp_path / "crm-restart.sqlite"
    account_id = save_crm_account(**account_args(), path=db)
    save_crm_interaction(
        account_id=account_id,
        occurred_at=date(2026, 9, 26),
        area="Comercial",
        interaction_type="Reunião",
        summary="Descoberta realizada",
        owner_id="ana@example.test",
        next_action="Enviar proposta",
        next_action_due_at=date(2026, 10, 2),
        path=db,
    )
    code = (
        "import json,sys; from src.action_store import get_crm_account,list_crm_interactions; "
        "a=get_crm_account(sys.argv[2],path=sys.argv[1]); "
        "i=list_crm_interactions(account_id=sys.argv[2],open_only=True,path=sys.argv[1]); "
        "print(json.dumps({'account':a,'interactions':i},default=str))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(db), account_id],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["account"]["owner_id"] == "ana@example.test"
    assert payload["account"]["journey_stage"] == "Lead novo"
    assert payload["interactions"][0]["next_action"] == "Enviar proposta"
