from __future__ import annotations

from datetime import date, timedelta
import hashlib
from pathlib import Path
import sqlite3

import pytest

from src.operating_store import (
    CURRENCIES, create_customer, create_opportunity, create_task, get_customer,
    initialize_store, list_alerts, list_customers, list_events, list_interactions,
    list_source_records, list_subscriptions, list_tasks, management_summary,
    preview_lifecycle_movement, preview_subscription_change, record_interaction,
    record_lifecycle_movement, record_subscription_change, reset_demo_data,
    source_import_status, treat_alert, update_task, validate_legacy_fields, work_queue,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def database_url(tmp_path):
    url = f"sqlite:///{tmp_path / 'operating.sqlite'}"
    initialize_store(url)
    return url


def make_native(url, *, name="Conta nativa QA", owner="Camila CS", renewal=None, due=None):
    return create_customer(
        name=name, owner=owner, industry="SaaS", country="Brasil", referral_source="Inbound",
        signup_date=date(2026, 1, 1), plan_tier="Pro", seats=10, mrr_current=1200,
        currency="USD", billing_frequency="monthly", renewal_date=renewal,
        subscription_start=date(2026, 1, 1), first_task_title="Fazer kickoff",
        first_task_due=due or date.today() + timedelta(days=2), actor="QA",
        database_url=url,
    )


def test_legacy_import_is_complete_idempotent_and_never_promotes_current_contract(database_url):
    first = list_customers(database_url=database_url)
    initialize_store(database_url)
    again = list_customers(database_url=database_url)
    assert len(first) == len(again) == 500
    legacy = next(x for x in again if x["origin"] == "legacy")
    assert legacy["verification_status"] == "not_validated"
    assert legacy["lifecycle_status"] is None
    assert legacy["health_status"] is None
    assert legacy["mrr_current"] is None
    assert legacy["plan_tier"] is None
    assert legacy["active_subscriptions"] == []
    assert len(list_source_records(legacy["customer_id"], database_url=database_url)) > 0
    assert len(source_import_status(database_url=database_url)) == 5


def test_partial_legacy_confirmation_keeps_unconfirmed_fields_unknown(database_url):
    legacy = next(x for x in list_customers(database_url=database_url) if x["origin"] == "legacy")
    validate_legacy_fields(legacy["customer_id"], selected_fields={"owner": "Camila"}, actor="QA", database_url=database_url)
    updated = get_customer(legacy["customer_id"], database_url=database_url)
    assert updated["owner"] == "Camila"
    assert updated["verification_status"] == "partially_validated"
    assert updated["mrr_current"] is None
    assert updated["lifecycle_status"] is None


def test_partial_legacy_plan_and_seats_only_do_not_confirm_mrr_or_status(database_url):
    legacy = next(x for x in list_customers(database_url=database_url) if x["origin"] == "legacy")
    validate_legacy_fields(legacy["customer_id"], selected_fields={"plan_tier": "Enterprise", "seats": 12},
                           actor="RevOps QA", database_url=database_url)
    updated = get_customer(legacy["customer_id"], database_url=database_url)
    assert updated["plan_tier"] == "Enterprise" and updated["seats"] == 12
    assert updated["mrr_current"] is None and updated["lifecycle_status"] is None
    assert updated["subscription_status"] == "unconfirmed"
    assert updated["verification_status"] == "partially_validated"
    sources = list_source_records(legacy["customer_id"], database_url=database_url)
    assert sources and all(x["raw_payload"] for x in sources)


def test_legacy_confirmed_values_activate_only_when_explicitly_selected(database_url):
    legacy = next(x for x in list_customers(database_url=database_url) if x["origin"] == "legacy")
    validate_legacy_fields(legacy["customer_id"], selected_fields={
        "owner": "Camila", "lifecycle_status": "active", "plan_tier": "Pro",
        "seats": 8, "mrr_current": 900.0, "currency": "USD",
        "billing_frequency": "monthly", "subscription_status": "active",
    }, actor="QA", database_url=database_url)
    current = get_customer(legacy["customer_id"], database_url=database_url)
    assert current["verification_status"] == "validated"
    assert current["lifecycle_status"] == "active"
    assert current["mrr_current"] == 900
    assert current["currency"] == "USD"
    assert len([x for x in list_subscriptions(legacy["customer_id"], database_url=database_url)
                if x["status"] == "active"]) == 1
    event = list_events(legacy["customer_id"], database_url=database_url)[0]
    assert event["actor"] == "QA"
    assert event["previous_value"] and event["new_value"]


def test_native_customer_and_initial_subscription_task_are_atomic(database_url):
    customer_id = make_native(database_url)
    account = get_customer(customer_id, database_url=database_url)
    assert account["origin"] == "native"
    assert account["verification_status"] == "validated"
    assert account["lifecycle_status"] == "onboarding"
    assert account["mrr_current"] == 1200
    assert len(list_subscriptions(customer_id, database_url=database_url)) == 1
    assert len(list_tasks(customer_id=customer_id, database_url=database_url)) == 1
    assert {e["event_type"] for e in list_events(customer_id, database_url=database_url)} >= {"customer_created", "subscription_started", "task_created"}


def test_sales_lead_registration_has_no_contract_or_lifecycle_claim(database_url):
    lead_id = create_opportunity(name="Nova oportunidade", owner="Carla Sales", actor="QA",
        sales_stage="Qualificação", opportunity_value_estimate=5000, opportunity_currency="USD",
        next_action="Reunião de descoberta", next_action_due=date.today()+timedelta(days=3),
        database_url=database_url)
    lead = get_customer(lead_id, database_url=database_url)
    assert lead["origin"] == "native"
    assert lead["sales_stage"] == "Qualificação"
    assert lead["opportunity_value_estimate"] == 5000
    assert lead["lifecycle_status"] is None
    assert lead["mrr_current"] is None
    assert list_subscriptions(lead_id, database_url=database_url) == []
    assert len(list_tasks(customer_id=lead_id, database_url=database_url)) == 1


def test_interaction_creates_journey_event_and_followup(database_url):
    customer_id = make_native(database_url)
    interaction_id = record_interaction(customer_id, interaction_type="Ligação",
        occurred_at=date.today(), summary="Cliente solicitou agenda da implantação",
        obstacle="Falta acesso", outcome="Acesso prometido",
        next_action="Confirmar acesso", next_action_owner="Camila CS",
        next_action_due=date.today()+timedelta(days=2), actor="Camila CS",
        database_url=database_url)
    interactions = list_interactions(customer_id, database_url=database_url)
    tasks = list_tasks(customer_id=customer_id, database_url=database_url)
    assert any(x["interaction_id"] == interaction_id for x in interactions)
    assert any(x["title"] == "Confirmar acesso" and x["owner"] == "Camila CS" for x in tasks)
    event = next(x for x in list_events(customer_id, database_url=database_url)
                 if x["related_entity_id"] == interaction_id)
    assert event["actor"] == "Camila CS"
    assert event["new_value"]["summary"] == "Cliente solicitou agenda da implantação"
    assert any(x["title"] == "Confirmar acesso" for x in work_queue(actor="Camila CS", database_url=database_url)["upcoming"])


def test_tasks_are_editable_and_completion_is_audited(database_url):
    customer_id = make_native(database_url)
    task_id = create_task(customer_id, title="Confirmar integração", owner="Diego",
        due_date=date.today(), priority="P1", actor="QA", database_url=database_url)
    update_task(task_id, actor="Diego", status="completed", completion_note="Integração validada",
                database_url=database_url)
    task = next(x for x in list_tasks(customer_id=customer_id, database_url=database_url)
                if x["task_id"] == task_id)
    assert task["status"] == "completed"
    assert task["completion_note"] == "Integração validada"
    event = next(x for x in list_events(customer_id, database_url=database_url)
                 if x["related_entity_id"] == task_id and x["event_type"] == "task_completed")
    assert event["actor"] == "Diego"
    assert event["previous_value"]["status"] == "open"
    assert event["new_value"]["status"] == "completed"


def test_subscription_change_preview_then_confirm_records_real_delta(database_url):
    customer_id = make_native(database_url)
    subscription = list_subscriptions(customer_id, database_url=database_url)[0]
    preview = preview_subscription_change(customer_id, mrr_after=1500, currency="USD",
                                         subscription_id=subscription["subscription_id"], database_url=database_url)
    assert preview["known"] and preview["mrr_before"] == 1200 and preview["mrr_after"] == 1500
    assert preview["mrr_delta"] == 300
    result = record_subscription_change(customer_id, plan_tier="Enterprise", seats=20,
        mrr_after=1500, currency="USD", billing_frequency="monthly",
        effective_date=date.today(), renewal_date=date.today()+timedelta(days=365),
        reason="Upgrade validado pelo cliente", actor="Camila", subscription_id=subscription["subscription_id"],
        database_url=database_url)
    assert result["mrr_delta"] == 300
    account = get_customer(customer_id, database_url=database_url)
    assert account["mrr_current"] == 1500
    assert len([x for x in list_subscriptions(customer_id, database_url=database_url) if x["status"] == "active"]) == 1
    event = next(x for x in list_events(customer_id, database_url=database_url) if x["event_id"] == result["event_id"])
    assert event["mrr_delta"] == 300
    assert event["previous_value"]["mrr_current"] == 1200


def test_currency_mismatch_never_calculates_combined_mrr(database_url):
    customer_id = make_native(database_url)
    sub = list_subscriptions(customer_id, database_url=database_url)[0]
    preview = preview_subscription_change(customer_id, mrr_after=3000, currency="BRL",
                                          subscription_id=sub["subscription_id"], database_url=database_url)
    assert not preview["known"]
    assert preview["mrr_before"] is None
    result = record_subscription_change(customer_id, plan_tier="Pro", seats=10,
        mrr_after=3000, currency="BRL", billing_frequency="monthly",
        effective_date=date.today(), renewal_date=None, reason="Mudança de moeda confirmada",
        actor="QA", subscription_id=sub["subscription_id"], database_url=database_url)
    assert result["mrr_before"] == 1200
    assert result["mrr_after"] == 3000
    assert result["mrr_delta"] is None


def test_admin_end_does_not_imply_churn_and_total_loss_is_explicit(database_url):
    customer_id = make_native(database_url)
    sub = list_subscriptions(customer_id, database_url=database_url)[0]
    result = record_lifecycle_movement(customer_id, movement="admin_end", subscription_id=sub["subscription_id"],
        effective_date=date.today(), reason="Encerramento administrativo confirmado", actor="Finance",
        database_url=database_url)
    account = get_customer(customer_id, database_url=database_url)
    assert account["lifecycle_status"] == "onboarding"
    assert result["lifecycle_status"] == "onboarding"
    assert not [x for x in list_subscriptions(customer_id, database_url=database_url) if x["status"] == "active"]
    result = record_lifecycle_movement(customer_id, movement="total_loss", effective_date=date.today(),
        reason="Perda total confirmada com o cliente", actor="CS", database_url=database_url)
    assert result["lifecycle_status"] == "churned"
    assert get_customer(customer_id, database_url=database_url)["lifecycle_status"] == "churned"
    assert result["mrr_delta"] is None  # the line's end was administrative; no second, invented economic delta


def test_explicit_total_loss_from_active_subscription_records_confirmed_economic_delta(database_url):
    customer_id = make_native(database_url)
    result = record_lifecycle_movement(customer_id, movement="total_loss", effective_date=date.today(),
        reason="Perda total confirmada pelo cliente", actor="CS", database_url=database_url)
    assert result["lifecycle_status"] == "churned"
    assert result["mrr_before"] == 1200 and result["mrr_after"] == 0
    assert result["mrr_delta"] == -1200
    event = next(x for x in list_events(customer_id, database_url=database_url)
                 if x["event_id"] == result["event_id"])
    assert event["event_type"] == "total_loss" and event["mrr_delta"] == -1200


def test_partial_line_end_preserves_remaining_subscription_and_no_churn(database_url):
    customer_id = make_native(database_url)
    first = list_subscriptions(customer_id, database_url=database_url)[0]
    added = record_subscription_change(customer_id, plan_tier="Basic", seats=2, mrr_after=200,
        currency="USD", billing_frequency="monthly", effective_date=date.today(), renewal_date=None,
        reason="Linha contratual adicional confirmada", actor="Finance", create_parallel=True,
        database_url=database_url)
    assert get_customer(customer_id, database_url=database_url)["mrr_current"] == 1400
    result = record_lifecycle_movement(customer_id, movement="admin_end", subscription_id=first["subscription_id"],
        effective_date=date.today(), reason="Uma linha terminou; outra continua", actor="Finance",
        database_url=database_url)
    assert result["lifecycle_status"] == "active"
    active = [x for x in list_subscriptions(customer_id, database_url=database_url) if x["status"] == "active"]
    assert len(active) == 1 and active[0]["subscription_id"] == added["subscription_id"]
    assert get_customer(customer_id, database_url=database_url)["mrr_current"] == 200


def test_reactivation_requires_all_active_rows_to_be_ended(database_url):
    customer_id = make_native(database_url)
    sub = list_subscriptions(customer_id, database_url=database_url)[0]
    record_lifecycle_movement(customer_id, movement="total_loss", effective_date=date.today(),
        reason="Perda verificada", actor="CS", database_url=database_url)
    preview = preview_lifecycle_movement(customer_id, movement="reactivation", reactivation_mrr=700,
                                         currency="USD", database_url=database_url)
    assert preview["mrr_before"] is None
    result = record_lifecycle_movement(customer_id, movement="reactivation", effective_date=date.today(),
        reason="Retorno confirmado", actor="Sales", reactivation_plan="Pro", reactivation_seats=5,
        reactivation_mrr=700, currency="USD", billing_frequency="monthly",
        renewal_date=date.today()+timedelta(days=365), database_url=database_url)
    assert result["lifecycle_status"] == "active"
    account = get_customer(customer_id, database_url=database_url)
    assert account["mrr_current"] == 700
    assert len([x for x in list_subscriptions(customer_id, database_url=database_url) if x["status"] == "active"]) == 1


def test_renewal_is_confirmed_and_alert_is_treated_without_deleting_history(database_url):
    due = date.today() + timedelta(days=5)
    customer_id = make_native(database_url, renewal=due, due=date.today()-timedelta(days=1))
    queue = work_queue(actor="Camila CS", database_url=database_url)
    assert any(x["task_id"] for x in queue["overdue"])
    renewal_alert = next(x for x in queue["alerts"] if x["alert_type"] == "renewal")
    treat_alert(renewal_alert["alert_id"], actor="Camila CS", note="Reunião marcada", database_url=database_url)
    treated = list_alerts(status="treated", customer_id=customer_id, database_url=database_url)
    assert any(x["treatment_note"] == "Reunião marcada" and x["treated_by"] == "Camila CS" for x in treated)
    assert any(x["event_type"] == "alert_treated" for x in list_events(customer_id, database_url=database_url))
    assert not any(x["alert_id"] == renewal_alert["alert_id"] for x in work_queue(database_url=database_url)["alerts"])


def test_treated_alert_stays_auditable_after_condition_ends(database_url):
    customer_id = make_native(database_url, due=date.today()-timedelta(days=2))
    overdue = next(x for x in work_queue(database_url=database_url)["alerts"] if x["alert_type"] == "overdue_task")
    treat_alert(overdue["alert_id"], actor="Camila", note="Cliente retornou", database_url=database_url)
    assert list_alerts(status="treated", customer_id=customer_id, database_url=database_url)
    task = next(x for x in list_tasks(customer_id=customer_id, database_url=database_url) if x["task_id"] == overdue["task_id"])
    update_task(task["task_id"], actor="Camila", status="completed", completion_note="Concluído", database_url=database_url)
    work_queue(database_url=database_url)
    history = list_alerts(status="treated", customer_id=customer_id, database_url=database_url)
    assert any(x["alert_id"] == overdue["alert_id"] for x in history)


def test_management_does_not_include_historical_churn_as_confirmed_economic_loss(database_url):
    summary = management_summary(database_url=database_url)
    assert summary["counts"]["customers"] == 500
    assert summary["confirmed_movements"] == []


def test_legacy_customer_can_receive_interactions_and_tasks_before_contract_validation(database_url):
    legacy = next(x for x in list_customers(origin="legacy", database_url=database_url))
    record_interaction(legacy["customer_id"], interaction_type="Ligação", occurred_at=date.today(),
        summary="Confirmação de necessidades", actor="CS QA", next_action="Enviar resumo da ligação",
        next_action_owner="CS QA", next_action_due=date.today()+timedelta(days=7), database_url=database_url)
    task_id = create_task(legacy["customer_id"], title="Validar próximo passo com cliente",
        owner="Sales QA", due_date=date.today()+timedelta(days=3), priority="P2", actor="Sales QA",
        database_url=database_url)
    current = get_customer(legacy["customer_id"], database_url=database_url)
    assert current["verification_status"] == "not_validated"
    assert current["mrr_current"] is None and current["lifecycle_status"] is None
    tasks = list_tasks(customer_id=legacy["customer_id"], database_url=database_url)
    assert {x["title"] for x in tasks} >= {"Enviar resumo da ligação", "Validar próximo passo com cliente"}
    assert task_id in {x["task_id"] for x in tasks}


def test_source_files_remain_byte_identical_after_import_and_operations(database_url):
    paths = sorted((ROOT / "data" / "raw").glob("*.csv"))
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    legacy_id = next(x["customer_id"] for x in list_customers(origin="legacy", database_url=database_url))
    record_interaction(legacy_id, interaction_type="Nota", occurred_at=date.today(),
        summary="Registro de operação QA", actor="QA", database_url=database_url)
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    assert before == after


def test_reset_only_operates_on_demo_sqlite_and_reseeds_sources(database_url):
    create_opportunity(name="Para apagar no reset", owner="Sales", actor="QA", database_url=database_url)
    removed = reset_demo_data(database_url)
    assert removed == 501
    all_rows = list_customers(database_url=database_url)
    assert len(all_rows) == 500
    assert not any(x["name"] == "Para apagar no reset" for x in all_rows)
    with pytest.raises(ValueError, match="SQLite local"):
        reset_demo_data("postgresql+psycopg://localhost/test")


def test_task_requires_owner_due_and_title(database_url):
    customer_id = make_native(database_url)
    with pytest.raises(ValueError):
        create_task(customer_id, title="", owner="A", due_date=date.today(), priority="P1", actor="QA", database_url=database_url)
    with pytest.raises(ValueError):
        create_task(customer_id, title="Validação", owner="", due_date=date.today(), priority="P1", actor="QA", database_url=database_url)


def test_open_subscription_mrr_for_legacy_stays_unknown_until_status_is_confirmed(database_url):
    legacy = next(x for x in list_customers(origin="legacy", database_url=database_url))
    validate_legacy_fields(legacy["customer_id"], selected_fields={
        "plan_tier":"Pro", "seats":5, "mrr_current":500, "currency":"USD",
        "billing_frequency":"monthly",
    }, actor="QA", database_url=database_url)
    current = get_customer(legacy["customer_id"], database_url=database_url)
    assert current["mrr_current"] is None
    assert current["subscription_status"] == "unconfirmed"
    validate_legacy_fields(legacy["customer_id"], selected_fields={"subscription_status":"active"}, actor="QA", database_url=database_url)
    current = get_customer(legacy["customer_id"], database_url=database_url)
    assert current["mrr_current"] == 500
