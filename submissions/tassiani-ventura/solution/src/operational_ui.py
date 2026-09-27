from __future__ import annotations

from datetime import date, datetime, timedelta
import json

import pandas as pd
import streamlit as st

from src.action_store import list_actions as list_signal_actions, list_events as list_signal_action_events
from src.data_access import load_table
from src.operating_store import (
    BILLING_FREQUENCIES, CURRENCIES, HEALTH_STATES, LIFECYCLES, MOVEMENTS, PLANS,
    TASK_PRIORITIES, TASK_STATUSES, create_customer, create_task, database_mode,
    create_opportunity, get_customer, is_persistent_database, list_alerts, list_customers, list_events,
    list_interactions, list_source_records, list_subscriptions, list_tasks,
    management_summary, preview_lifecycle_movement, preview_subscription_change,
    record_interaction, record_lifecycle_movement, record_subscription_change,
    refresh_alerts, reset_demo_data, treat_alert, update_customer_profile,
    update_task, validate_legacy_fields, work_queue,
)
from src.ui import setup_page

LIFECYCLE_LABELS = {"onboarding": "Implantação", "active": "Ativo", "paused": "Pausado", "churned": "Encerrado"}
VERIFICATION_LABELS = {"not_validated": "Ainda não confirmado", "partially_validated": "Parcialmente confirmado", "validated": "Confirmado", "conflict": "Precisa de revisão"}
TASK_STATUS_LABELS = {"open": "Aberta", "in_progress": "Em andamento", "completed": "Concluída", "cancelled": "Cancelada"}
SUBSCRIPTION_STATUS_LABELS = {"active": "Ativa", "paused": "Pausada", "ended": "Encerrada", "unconfirmed": "A confirmar"}
EVENT_LABELS = {"customer_created": "Cliente cadastrado", "interaction": "Interação registrada", "task_created": "Tarefa criada", "task_completed": "Tarefa concluída", "subscription_change": "Assinatura alterada", "pause": "Conta pausada", "renewal": "Renovação", "reactivation": "Conta reativada", "admin_end": "Linha encerrada administrativamente", "total_loss": "Encerramento total"}
HEALTH_LABELS = {"healthy": "Saudável", "normal": "Normal", "at_risk": "Em atenção", "critical": "Crítica"}
ORIGIN_LABELS = {"legacy": "Importada (histórico)", "native": "Cadastrada agora"}
ALERT_STATUS_LABELS = {"open": "Aberto", "treated": "Tratado", "resolved": "Resolvido"}
ALERT_SEVERITY_LABELS = {"info": "Informativo", "low": "Baixa", "medium": "Média", "warning": "Atenção", "high": "Alta", "critical": "Crítica", "urgent": "Urgente"}


def _actor() -> str:
    return str(st.session_state.get("actor_identity") or st.session_state.get("current_actor_input") or "Operador local").strip() or "Operador local"


def _persist_actor_identity() -> None:
    st.session_state["actor_identity"] = str(st.session_state.get("current_actor_input", "")).strip() or "Operador local"


def _money(value, currency="USD") -> str:
    if value is None:
        return "Não validado"
    try:
        return f"{currency or ''} {float(value):,.2f}".strip()
    except (ValueError, TypeError):
        return "Não validado"


def _flash() -> None:
    message = st.session_state.pop("operational_flash", None)
    if message:
        st.success(message)


def _open_customer(customer_id: str) -> None:
    st.session_state["requested_customer_id"] = customer_id
    st.session_state["requested_account_id"] = customer_id
    st.switch_page("pages/01_Conta_360.py")


def _customer_options(items: list[dict]) -> tuple[list[str], dict[str, str]]:
    options = [x["customer_id"] for x in items]
    labels = {x["customer_id"]: f"{x['name']} · {x['customer_id']}" for x in items}
    return options, labels


def _customer_button(customer_id: str, key: str, label="Abrir cliente") -> None:
    if st.button(label, key=key):
        _open_customer(customer_id)


def _signal_action_card(action: dict, prefix: str) -> None:
    due = date.fromisoformat(action["due_date"])
    bucket = "VENCIDA" if due < date.today() else "HOJE" if due == date.today() else "PRÓXIMA"
    with st.container(border=True):
        st.markdown(f"**{bucket} · {action['action_text']}**")
        st.caption(f"{action['account_name']} · {action['area']} · {action['owner']} · prazo {due:%d/%m/%Y} · {action['priority']} · {action['status']}")
        st.write(action["title"])
        if action.get("observation"):
            st.caption(f"Observação: {action['observation']}")
        if st.button("Abrir sinal e atualizar ação", key=f"{prefix}_signal_{action['action_id']}"):
            st.session_state["requested_signal_id"] = action["signal_id"]
            st.switch_page("pages/08_Central_de_Retencao.py")


def _task_card(task: dict, *, prefix: str, allow_edit: bool = False) -> None:
    due = task["due_date"]
    bucket = "VENCIDA" if due < date.today() else "HOJE" if due == date.today() else "PRÓXIMA"
    with st.container(border=True):
        st.markdown(f"**{bucket} · {task['title']}**")
        st.caption(f"{task.get('customer_name', task['customer_id'])} · {task['owner']} · prazo {due:%d/%m/%Y} · {task['priority']}")
        c1, c2, c3 = st.columns([1, 1, 2])
        if c1.button("Abrir cliente", key=f"{prefix}_open_{task['task_id']}"):
            _open_customer(task["customer_id"])
        with c2.popover("Atualizar tarefa", use_container_width=True):
            with st.form(f"{prefix}_task_edit_{task['task_id']}"):
                title = st.text_input("Título", value=task["title"])
                owner = st.text_input("Responsável", value=task["owner"])
                due_date = st.date_input("Prazo", value=due)
                priority = st.selectbox("Prioridade", TASK_PRIORITIES, index=TASK_PRIORITIES.index(task["priority"]))
                status = st.selectbox("Status", TASK_STATUSES, index=TASK_STATUSES.index(task["status"]))
                note = st.text_area("Resultado / observação de conclusão", value=task.get("completion_note") or "")
                saved = st.form_submit_button("Salvar", type="primary")
            if saved:
                try:
                    update_task(task["task_id"], actor=_actor(), title=title, owner=owner,
                                due_date=due_date, priority=priority, status=status,
                                completion_note=note)
                    st.session_state["operational_flash"] = "Tarefa atualizada e evento registrado na jornada."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        if task["status"] != "completed":
            with c3.popover("Concluir", use_container_width=True):
                with st.form(f"{prefix}_task_complete_{task['task_id']}"):
                    result = st.text_area("Resultado (opcional, recomendado)")
                    submitted = st.form_submit_button("Marcar concluída", type="primary")
                if submitted:
                    try:
                        update_task(task["task_id"], actor=_actor(), status="completed",
                                    completion_note=result)
                        st.session_state["operational_flash"] = "Tarefa concluída e retirada da fila aberta."
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))


def _alert_card(alert: dict, *, prefix: str) -> None:
    with st.container(border=True):
        st.markdown(f"**{alert['customer_name']} · {alert['alert_type'].replace('_', ' ').title()}**")
        st.write(alert["reason"])
        st.caption(f"Prioridade {ALERT_SEVERITY_LABELS.get(alert['severity'], alert['severity'])} · situação: {ALERT_STATUS_LABELS.get(alert['status'], alert['status'])} · criada {str(alert['created_at'])[:10]}")
        c1, c2 = st.columns([1, 1])
        if c1.button("Abrir cliente", key=f"{prefix}_alert_open_{alert['alert_id']}"):
            _open_customer(alert["customer_id"])
        with c2.popover("Marcar tratado", use_container_width=True):
            note = st.text_area("O que foi verificado ou feito?", key=f"{prefix}_alert_note_{alert['alert_id']}")
            if st.button("Confirmar tratamento", key=f"{prefix}_alert_treat_{alert['alert_id']}", type="primary"):
                try:
                    treat_alert(alert["alert_id"], actor=_actor(), note=note)
                    st.session_state["operational_flash"] = "Alerta tratado; permaneceu no histórico."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        if alert.get("task_id"):
            task = next((x for x in list_tasks(status="open") if x["task_id"] == alert["task_id"]), None)
            if task:
                st.caption(f"Tarefa vinculada: {task['title']} · {task['owner']} · prazo {task['due_date']:%d/%m/%Y}")


def render_my_work() -> None:
    setup_page(st, "Minha fila", "◈")
    st.title("Minha fila")
    st.caption(f"Seus próximos compromissos: tarefas, clientes que precisam de contato e alertas atribuídos a você. Operador: {_actor()}.")
    _flash()
    try:
        queue = work_queue(actor=_actor())
        signal_actions = [x for x in list_signal_actions(open_only=True)
                          if x["owner"].strip().casefold() == _actor().casefold()]
    except Exception as exc:
        st.error(f"Não foi possível carregar a fila operacional: {exc}")
        st.stop()
    signal_overdue = [x for x in signal_actions if date.fromisoformat(x["due_date"]) < date.today()]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ações de hoje", len(queue["today"]) + sum(x["due_date"] == date.today().isoformat() for x in signal_actions))
    c2.metric("Vencidas", len(queue["overdue"]) + len(signal_overdue))
    c3.metric("Renovações em 30 dias", len(queue["renewals"]))
    c4.metric("Alertas abertos", len(queue["alerts"]))

    today_tab, overdue_tab, renewal_tab, alert_tab, signal_tab = st.tabs(
        ["Hoje", "Vencidas", "Renovações", "Alertas", "Acompanhamentos históricos"],
        key="my_work_tabs", on_change="rerun")
    with today_tab:
        rows = queue["today"] + [x for x in queue["upcoming"] if x["due_date"] == date.today()]
        if not rows:
            st.info("Nenhuma tarefa vence hoje. Cadastre um cliente, registre interação ou abra uma tarefa para montar sua fila.")
        for item in rows:
            _task_card(item, prefix="today")
        if queue["upcoming"]:
            st.subheader("Próximas ações")
            for item in queue["upcoming"][:12]:
                _task_card(item, prefix="upcoming")
        due_signal_actions = [x for x in signal_actions if x["due_date"] >= date.today().isoformat()]
        if due_signal_actions:
            st.subheader("Ações da Central de Retenção")
            for item in due_signal_actions:
                _signal_action_card(item, "today_signal")
    with overdue_tab:
        st.subheader("Ações vencidas")
        if not queue["overdue"]:
            st.success("Nenhuma tarefa vencida para este responsável.")
        for item in queue["overdue"]:
            _task_card(item, prefix="overdue")
        for item in signal_overdue:
            _signal_action_card(item, "overdue_signal")
    with renewal_tab:
        if not queue["renewals"]:
            st.info("Sem datas de renovação confirmadas nos próximos 30 dias. Datas históricas não aparecem como atuais.")
        for item in queue["renewals"]:
            with st.container(border=True):
                st.markdown(f"**{item['customer_name']} · renovação em {item['days_remaining']} dias**")
                st.caption(f"Data {item['renewal_date']:%d/%m/%Y} · owner {item['owner'] or 'não atribuído'} · {item['plan_tier'] or 'plano não validado'} · {_money(item['mrr_current'], item['currency'])}")
                _customer_button(item["customer_id"], f"renew_open_{item['subscription_id']}")
    with alert_tab:
        if not queue["alerts"]:
            st.success("Nenhum alerta operacional aberto.")
        for alert in queue["alerts"]:
            _alert_card(alert, prefix="work")
    with signal_tab:
        if not signal_actions:
            st.info("Nenhuma ação de sinal aberta atribuída a você. Ações por evidência histórica podem ser atribuídas na Central de Retenção.")
        for item in sorted(signal_actions, key=lambda x: (x["due_date"], x["priority"])):
            _signal_action_card(item, "all_signal")


def render_customers_page() -> None:
    setup_page(st, "Clientes", "◈")
    st.title("Clientes")
    st.caption("Encontre uma conta existente ou cadastre um cliente. Abra a ficha para registrar contatos, atualizar dados confirmados e definir quem fará o próximo passo e quando.")
    _flash()
    customers_all = list_customers()
    with st.expander("Buscar e filtrar clientes", expanded=True):
        query = st.text_input("Buscar cliente ou ID", key="customers_search")
        f1, f2, f3, f4 = st.columns(4)
        lifecycle = f1.selectbox("Situação do cliente", ["Todos", *LIFECYCLES], key="customers_lifecycle", format_func=lambda x: "Todos" if x == "Todos" else LIFECYCLE_LABELS.get(x, x))
        owners = ["Todos", *sorted({x["owner"] for x in customers_all if x["owner"]})]
        owner = f2.selectbox("Responsável", owners, key="customers_owner")
        verification = f3.selectbox("Qualidade dos dados", ["Todos", "not_validated", "partially_validated", "validated", "conflict"], key="customers_verification", format_func=lambda x: "Todos" if x == "Todos" else VERIFICATION_LABELS.get(x, x))
        origin = f4.selectbox("Origem", ["Todos", "legacy", "native"], key="customers_origin")
    visible = list_customers(query=query, lifecycle=lifecycle, owner=owner,
                             verification=verification, origin=origin)
    st.caption(f"{len(visible)} cliente(s) neste recorte · {sum(x['origin']=='legacy' for x in visible)} históricos · {sum(x['origin']=='native' for x in visible)} nativos")
    new_tab, list_tab = st.tabs(["+ Novo cliente", "Lista de trabalho"],
                                key="customers_tabs", on_change="rerun")
    with new_tab:
        st.write("O cadastro cria em uma transação o cliente, a assinatura inicial, os eventos de jornada e a primeira tarefa.")
        with st.form("native_customer_form", clear_on_submit=False):
            st.markdown("**Conta**")
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Nome da conta *")
            industry = c2.text_input("Indústria")
            country = c3.text_input("País")
            c4, c5 = st.columns(2)
            referral = c4.text_input("Origem / canal")
            signup = c5.date_input("Data de início da conta *", value=date.today())
            owner_new = st.text_input("Responsável (owner) *")
            st.markdown("**Assinatura inicial — valores informados pelo operador**")
            s1, s2, s3, s4 = st.columns(4)
            plan = s1.selectbox("Plano *", PLANS)
            seats = s2.number_input("Seats *", min_value=1, value=1, step=1)
            currency = s3.selectbox("Moeda *", CURRENCIES)
            billing = s4.selectbox("Billing *", BILLING_FREQUENCIES)
            s5, s6, s7 = st.columns(3)
            mrr = s5.number_input("MRR informado *", min_value=0.0, value=0.0, step=100.0)
            sub_start = s6.date_input("Início da assinatura *", value=date.today())
            renewal = s7.date_input("Data de renovação (se conhecida)", value=None)
            st.markdown("**Responsabilidade e primeiro próximo passo**")
            first_action = st.text_input("Primeira tarefa / próxima ação *")
            t1, t2 = st.columns(2)
            first_due = t1.date_input("Prazo da primeira ação *", value=date.today() + timedelta(days=3))
            first_priority = t2.selectbox("Prioridade inicial", TASK_PRIORITIES, index=1)
            submitted = st.form_submit_button("Criar cliente e abrir jornada", type="primary")
        if submitted:
            try:
                customer_id = create_customer(name=name, owner=owner_new, industry=industry,
                    country=country, referral_source=referral, signup_date=signup,
                    plan_tier=plan, seats=int(seats), mrr_current=float(mrr), currency=currency,
                    billing_frequency=billing, renewal_date=renewal, subscription_start=sub_start,
                    first_task_title=first_action, first_task_due=first_due,
                    first_task_priority=first_priority, actor=_actor())
                st.session_state["operational_flash"] = "Cliente nativo criado, assinatura inicial confirmada e primeira tarefa atribuída."
                st.session_state["requested_customer_id"] = customer_id
                _open_customer(customer_id)
            except (ValueError, TypeError) as exc:
                st.error(str(exc))
    with list_tab:
        if not visible:
            st.info("Nenhum cliente encontrado. Ajuste os filtros ou cadastre um novo.")
        else:
            frame = pd.DataFrame([{
                "Cliente": x["name"], "ID": x["customer_id"], "Origem": ORIGIN_LABELS.get(x["origin"], x["origin"]),
                "Situação atual": LIFECYCLE_LABELS.get(x["lifecycle_status"], "Não informada"),
                "Qualidade dos dados": VERIFICATION_LABELS.get(x["verification_status"], x["verification_status"]), "Plano": x["plan_tier"] or "Não confirmado",
                "Seats": x["seats"] if x["seats"] is not None else "Não validado",
                "MRR atual": _money(x["mrr_current"], x["currency"]), "Responsável": x["owner"] or "Não atribuído",
                "Próxima renovação": x["renewal_date"].strftime("%d/%m/%Y") if x["renewal_date"] else "Não validada",
            } for x in visible])
            st.dataframe(frame, hide_index=True, width="stretch")
            options, labels = _customer_options(visible)
            selected = st.selectbox("Cliente para abrir", options,
                                    format_func=lambda x: labels[x], key="customer_open_picker")
            if st.button("Abrir Cliente 360", key="customer_open_360", type="primary"):
                _open_customer(selected)


def _render_customer_edit(customer: dict) -> None:
    with st.form(f"customer_edit_{customer['customer_id']}"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome", value=customer["name"])
        owner = c2.text_input("Responsável", value=customer["owner"] or "")
        c3, c4 = st.columns(2)
        industry = c3.text_input("Indústria", value=customer["industry"] or "")
        country = c4.text_input("País", value=customer["country"] or "")
        referral = st.text_input("Origem / canal", value=customer["referral_source"] or "")
        health = st.selectbox("Saúde operacional informada", HEALTH_STATES,
                              index=HEALTH_STATES.index(customer["health_status"]) if customer["health_status"] in HEALTH_STATES else 0)
        stages = ["Lead novo", "Qualificação", "Descoberta", "Proposta", "Negociação",
                  "Fechado ganho", "Fechado perdido", "Onboarding", "Ativo", "Renovação", "Encerrado"]
        current_stage = customer["sales_stage"] if customer["sales_stage"] in stages else "Onboarding" if customer["origin"] == "native" else "Lead novo"
        stage = st.selectbox("Etapa da jornada comercial", stages, index=stages.index(current_stage))
        notes = st.text_area("Notas operacionais", value=customer["notes"] or "")
        submitted = st.form_submit_button("Salvar informações da conta", type="primary")
    if submitted:
        try:
            update_customer_profile(customer["customer_id"], actor=_actor(), name=name,
                owner=owner, industry=industry, country=country, referral_source=referral,
                health_status=health, sales_stage=stage, notes=notes)
            st.session_state["operational_flash"] = "Conta atualizada e alteração registrada na jornada."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _render_validate_legacy(customer: dict) -> None:
    if customer["origin"] != "legacy":
        st.caption("A validação progressiva é específica das contas históricas.")
        return
    st.info("Confirme somente o que foi verificado com o cliente/sistema oficial. Campos não selecionados permanecem sem validar; uma confirmação explícita de 'desconhecido' é permitida.")
    cid = customer["customer_id"]
    c1, c2, c3 = st.columns(3)
    owner_known = c1.checkbox("Validar responsável", key=f"v_owner_{cid}")
    life_known = c2.checkbox("Validar lifecycle", key=f"v_life_{cid}")
    health_known = c3.checkbox("Validar saúde", key=f"v_health_{cid}")
    st.markdown("**Assinatura atual — confirme cada campo separadamente**")
    s1, s2, s3 = st.columns(3)
    plan_known = s1.checkbox("Confirmar plano", key=f"v_plan_{cid}")
    seats_known = s2.checkbox("Confirmar seats", key=f"v_seats_{cid}")
    mrr_known = s3.checkbox("Confirmar MRR", key=f"v_mrr_{cid}")
    x1, x2, x3 = st.columns(3)
    currency_known = x1.checkbox("Confirmar moeda", key=f"v_ccy_{cid}")
    billing_known = x2.checkbox("Confirmar billing", key=f"v_bill_{cid}")
    renewal_known = x3.checkbox("Confirmar renovação", key=f"v_renewal_{cid}")
    with st.form(f"validate_legacy_{cid}"):
        picks = {}
        c1, c2, c3 = st.columns(3)
        if owner_known:
            picks["owner"] = c1.text_input("Responsável confirmado", value=customer["owner"] or "", key=f"v_owner_value_{cid}")
        if life_known:
            current = customer["lifecycle_status"] if customer["lifecycle_status"] in LIFECYCLES else LIFECYCLES[1]
            picks["lifecycle_status"] = c2.selectbox("Lifecycle atual confirmado", LIFECYCLES,
                index=LIFECYCLES.index(current), key=f"v_lifecycle_{cid}")
        if health_known:
            current = customer["health_status"] if customer["health_status"] in HEALTH_STATES else HEALTH_STATES[0]
            picks["health_status"] = c3.selectbox("Saúde observada", HEALTH_STATES,
                index=HEALTH_STATES.index(current), key=f"v_health_value_{cid}")
        s1, s2, s3 = st.columns(3)
        if plan_known:
            current_plan = customer["plan_tier"] if customer["plan_tier"] in PLANS else PLANS[0]
            picks["plan_tier"] = s1.selectbox("Plano confirmado", PLANS, index=PLANS.index(current_plan), key=f"v_plan_value_{cid}")
        if seats_known:
            picks["seats"] = s2.number_input("Seats confirmados", min_value=1, value=max(1, int(customer["seats"] or 1)), step=1, key=f"v_seats_value_{cid}")
        if mrr_known:
            picks["mrr_current"] = s3.number_input("MRR confirmado", min_value=0.0, value=max(0.0, float(customer["mrr_current"] or 0)), step=100.0, key=f"v_mrr_value_{cid}")
        x1, x2, x3 = st.columns(3)
        if currency_known:
            current = customer["currency"] if customer["currency"] in CURRENCIES else CURRENCIES[0]
            picks["currency"] = x1.selectbox("Moeda confirmada", CURRENCIES, index=CURRENCIES.index(current), key=f"v_ccy_value_{cid}")
        if billing_known:
            current = customer["billing_frequency"] if customer["billing_frequency"] in BILLING_FREQUENCIES else BILLING_FREQUENCIES[0]
            picks["billing_frequency"] = x2.selectbox("Billing confirmado", BILLING_FREQUENCIES, index=BILLING_FREQUENCIES.index(current), key=f"v_bill_value_{cid}")
        if renewal_known:
            picks["renewal_date"] = x3.date_input("Próxima renovação confirmada", value=customer["renewal_date"] or date.today(), key=f"v_renewal_value_{cid}")
        status = st.selectbox("Status contratual (opcional, validar só se conhecido)",
                              ["Não confirmar", "active", "paused", "ended"], key=f"v_sub_status_{cid}")
        if status != "Não confirmar":
            picks["subscription_status"] = status
        mark_conflict = st.checkbox("Sinalizar conflito observado entre fontes (não escolhido acima)", key=f"v_conflict_{cid}")
        submitted = st.form_submit_button("Salvar campos selecionados", type="primary")
    if submitted:
        try:
            validate_legacy_fields(customer["customer_id"], selected_fields=picks,
                                   actor=_actor(), mark_conflict=mark_conflict)
            st.session_state["operational_flash"] = "Campos selecionados validados; fontes históricas foram preservadas."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _render_interaction(customer: dict, *, key: str) -> None:
    c1, c2 = st.columns(2)
    kind = c1.selectbox("Tipo", ["Ligação", "Reunião", "E-mail", "Nota", "Demonstração", "Check-in", "Atendimento", "Renovação", "Outro"], key=f"interaction_kind_{key}")
    occurred = c2.date_input("Data da interação", value=date.today(), key=f"interaction_date_{key}")
    summary = st.text_area("Resumo do que aconteceu / combinado *", key=f"interaction_summary_{key}")
    obstacle = st.text_input("Obstáculo / contexto (opcional)", key=f"interaction_obstacle_{key}")
    outcome = st.text_input("Resultado observado (opcional)", key=f"interaction_outcome_{key}")
    create_next = st.checkbox("Criar próxima ação", key=f"interaction_create_next_{key}")
    next_action, next_owner, due, priority = "", None, None, "P2"
    if create_next:
        next_action = st.text_input("Próxima ação *", key=f"interaction_next_action_{key}")
        n1, n2, n3 = st.columns(3)
        next_owner = n1.text_input("Responsável pela próxima ação *", value=customer["owner"] or "", key=f"interaction_next_owner_{key}")
        due = n2.date_input("Prazo *", value=date.today() + timedelta(days=7), key=f"interaction_next_due_{key}")
        priority = n3.selectbox("Prioridade", TASK_PRIORITIES, index=1, key=f"interaction_next_priority_{key}")
    submitted = st.button("Salvar interação", type="primary", key=f"save_interaction_{key}")
    if submitted:
        try:
            record_interaction(customer["customer_id"], interaction_type=kind,
                occurred_at=occurred, summary=summary, actor=_actor(), obstacle=obstacle,
                outcome=outcome, next_action=next_action, next_action_owner=next_owner,
                next_action_due=due, task_priority=priority)
            st.session_state["operational_flash"] = "Interação registrada na jornada" + (" e tarefa criada." if create_next else ".")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _render_task_form(customer: dict) -> None:
    with st.form(f"task_new_{customer['customer_id']}"):
        title = st.text_input("Título da tarefa *")
        c1, c2, c3 = st.columns(3)
        owner = c1.text_input("Responsável *", value=customer["owner"] or "")
        due = c2.date_input("Prazo *", value=date.today() + timedelta(days=3))
        priority = c3.selectbox("Prioridade", TASK_PRIORITIES, index=1)
        submitted = st.form_submit_button("Criar tarefa", type="primary")
    if submitted:
        try:
            create_task(customer["customer_id"], title=title, owner=owner,
                        due_date=due, priority=priority, actor=_actor())
            st.session_state["operational_flash"] = "Tarefa criada e enviada para Meu Trabalho."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _render_subscription_change(customer: dict) -> None:
    active = [x for x in list_subscriptions(customer["customer_id"]) if x["status"] == "active"]
    if not active:
        st.info("Não há assinatura operacional vigente. Use validação progressiva do legacy ou registre uma reativação explícita.")
        return
    options = [x["subscription_id"] for x in active]
    labels = {x["subscription_id"]: f"{x['plan_tier'] or 'Plano não validado'} · {x['subscription_id']}" for x in active}
    parallel = st.checkbox("Adicionar uma nova assinatura em paralelo (não substituir a atual)",
                           key=f"parallel_sub_{customer['customer_id']}",
                           help="Use quando o cliente terá duas assinaturas ativas ao mesmo tempo. A assinatura atual não será encerrada.")
    selected = None if parallel else (st.selectbox("Assinatura a alterar", options, format_func=lambda x: labels[x], key=f"change_sub_{customer['customer_id']}") if len(active) > 1 else options[0])
    current = next((x for x in active if x["subscription_id"] == selected), active[0])
    c1, c2, c3, c4 = st.columns(4)
    plan = c1.selectbox("Plano confirmado após mudança", PLANS,
                        index=PLANS.index(current["plan_tier"]) if current["plan_tier"] in PLANS else 0,
                        key=f"new_plan_{customer['customer_id']}")
    seats = c2.number_input("Seats", min_value=1, value=max(1, int(current["seats"] or 1)), step=1,
                            key=f"new_seats_{customer['customer_id']}")
    currency = c3.selectbox("Moeda", CURRENCIES,
                            index=CURRENCIES.index(current["currency"]) if current["currency"] in CURRENCIES else 0,
                            key=f"new_currency_{customer['customer_id']}")
    billing = c4.selectbox("Billing", BILLING_FREQUENCIES,
                           index=BILLING_FREQUENCIES.index(current["billing_frequency"]) if current["billing_frequency"] in BILLING_FREQUENCIES else 0,
                           key=f"new_billing_{customer['customer_id']}")
    c5, c6 = st.columns(2)
    mrr = c5.number_input("Novo MRR confirmado", min_value=0.0,
                          value=max(0.0, float(current["mrr_current"] or 0)), step=100.0,
                          key=f"new_mrr_{customer['customer_id']}")
    effective = c6.date_input("Data efetiva", value=date.today(), key=f"new_effective_{customer['customer_id']}")
    renewal = st.date_input("Próxima renovação (se conhecida)", value=current["renewal_date"], key=f"new_renewal_{customer['customer_id']}")
    reason = st.text_area("Motivo da mudança *", key=f"new_reason_{customer['customer_id']}")
    preview = preview_subscription_change(customer["customer_id"], mrr_after=float(mrr), currency=currency,
                                         subscription_id=selected, create_parallel=parallel)
    if preview["known"]:
        st.info(f"Prévia antes de confirmar: MRR {_money(preview['mrr_before'], currency)} → {_money(preview['mrr_after'], currency)} · delta {_money(preview['mrr_delta'], currency)}")
    else:
        st.warning("Prévia econômica: MRR antes/depois/delta não comparáveis (há campos sem confirmação ou moedas diferentes). A alteração será registrada sem calcular impacto.")
    if parallel:
        st.caption("A nova linha é adicionada; nenhuma assinatura existente será encerrada.")
    if st.button("Confirmar alteração de assinatura", key=f"save_subscription_{customer['customer_id']}", type="primary"):
        try:
            result = record_subscription_change(customer["customer_id"], plan_tier=plan,
                seats=int(seats), mrr_after=float(mrr), currency=currency,
                billing_frequency=billing, effective_date=effective, renewal_date=renewal,
                reason=reason, actor=_actor(), subscription_id=selected, create_parallel=parallel)
            delta = "não calculado" if result["mrr_delta"] is None else f"{result['mrr_delta']:+,.2f} {currency}"
            st.session_state["operational_flash"] = f"Assinatura atualizada; delta MRR {delta}. Evento de jornada gravado."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _render_movement(customer: dict) -> None:
    active = [x for x in list_subscriptions(customer["customer_id"]) if x["status"] == "active"]
    labels = {x["subscription_id"]: f"{x['plan_tier'] or 'Plano não validado'} · {x['subscription_id']}" for x in active}
    movement = st.selectbox("Movimento explícito", MOVEMENTS,
                            format_func=lambda x: {"renewal":"Renovação", "pause":"Pausa", "total_loss":"Perda total da conta", "reactivation":"Reativação", "admin_end":"Encerramento administrativo de uma linha"}[x],
                            key=f"movement_kind_{customer['customer_id']}",
                            help="Registre aqui uma mudança confirmada no ciclo da conta. Sinais históricos não alteram o estado atual automaticamente.")
    effective = st.date_input("Data efetiva", value=date.today(), key=f"movement_date_{customer['customer_id']}")
    reason = st.text_input("Motivo informado *", key=f"movement_reason_{customer['customer_id']}",
                          help="Explique o que foi confirmado pelo cliente ou por uma fonte oficial.")
    note = st.text_area("Observação", key=f"movement_note_{customer['customer_id']}")
    sub_id = None
    renewal_date = None
    react_plan = None
    react_seats = None
    react_mrr = None
    currency = None
    billing = None
    if movement in ("pause", "admin_end", "renewal") and active:
        key = "renewal" if movement == "renewal" else "movement"
        sub_id = st.selectbox("Assinatura a afetar", list(labels), format_func=lambda x: labels[x], key=f"{key}_sub_{customer['customer_id']}")
    if movement == "renewal":
        renewal_date = st.date_input("Próxima data de renovação", value=date.today() + timedelta(days=365), key=f"renewal_date_{customer['customer_id']}")
    if movement == "reactivation":
        r1, r2, r3, r4 = st.columns(4)
        react_plan = r1.selectbox("Plano", PLANS, key=f"react_plan_{customer['customer_id']}")
        react_seats = r2.number_input("Seats", min_value=1, value=1, key=f"react_seats_{customer['customer_id']}")
        react_mrr = r3.number_input("MRR informado", min_value=0.0, value=0.0, key=f"react_mrr_{customer['customer_id']}")
        currency = r4.selectbox("Moeda", CURRENCIES, key=f"react_currency_{customer['customer_id']}")
        billing = st.selectbox("Billing", BILLING_FREQUENCIES, key=f"react_billing_{customer['customer_id']}")
        renewal_date = st.date_input("Renovação (se conhecida)", value=date.today() + timedelta(days=365), key=f"react_renewal_{customer['customer_id']}")
    try:
        preview = preview_lifecycle_movement(customer["customer_id"], movement=movement,
            subscription_id=sub_id, reactivation_mrr=float(react_mrr) if react_mrr is not None else None,
            currency=currency)
        economic = "impacto MRR não validado/não comparável" if not preview["economic_impact_known"] else f"MRR {_money(preview['mrr_before'], preview['currency'])} → {_money(preview['mrr_after'], preview['currency'])} (delta {preview['mrr_delta']:+,.2f})"
        st.info(f"Prévia antes de confirmar: {preview['lifecycle_before'] or 'não validado'} → {preview['lifecycle_after']} · assinaturas vigentes {preview['active_subscription_count_before']} → {preview['active_subscription_count_after']} · {economic}")
    except ValueError as exc:
        st.warning(str(exc))
    if movement == "total_loss":
        st.warning("Este comando encerra explicitamente todas as assinaturas operacionais e marca a conta como churned. Eventos históricos de churn não acionam esta mudança.")
        confirm_loss = st.checkbox("Confirmo a perda total verificada com o cliente/sistema oficial", key=f"confirm_total_loss_{customer['customer_id']}")
    else:
        confirm_loss = True
    if movement == "admin_end":
        st.caption("Encerrar uma linha administrativa não altera lifecycle para churned; outra subscription vigente mantém a conta ativa.")
    if st.button("Confirmar movimento", key=f"save_movement_{customer['customer_id']}", type="primary", disabled=not confirm_loss):
        try:
            result = record_lifecycle_movement(customer["customer_id"], movement=movement,
                effective_date=effective, reason=reason, actor=_actor(), subscription_id=sub_id,
                note=note, reactivation_plan=react_plan, reactivation_seats=int(react_seats) if react_seats is not None else None,
                reactivation_mrr=float(react_mrr) if react_mrr is not None else None,
                currency=currency, billing_frequency=billing, renewal_date=renewal_date)
            delta_text = "não calculado" if result["mrr_delta"] is None else f"{result['mrr_delta']:+,.2f}"
            st.session_state["operational_flash"] = f"Movimento {movement} registrado. Lifecycle: {result['lifecycle_status'] or 'não alterado'}; delta MRR {delta_text}"
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def render_customer_360() -> None:
    setup_page(st, "Visão do cliente", "◈")
    st.title("Visão do cliente")
    _flash()
    items = list_customers()
    if not items:
        st.info("Nenhum cliente carregado. Verifique as fontes e o seed.")
        return
    requested = st.session_state.pop("requested_customer_id", None) or st.session_state.pop("requested_account_id", None)
    requested = requested or st.query_params.get("customer_id")
    if requested and any(x["customer_id"] == requested for x in items):
        st.session_state["operational_customer_id"] = requested
        st.query_params["customer_id"] = requested
    options, labels = _customer_options(items)
    current = st.session_state.get("operational_customer_id")
    idx = options.index(current) if current in options else 0
    selected = st.selectbox("Buscar / selecionar cliente", options,
                            format_func=lambda x: labels[x], index=idx,
                            key="operational_customer_picker",
                            help="Escolha uma conta para ver o contexto, registrar uma interação ou atualizar a próxima ação.")
    st.session_state["operational_customer_id"] = selected
    st.query_params["customer_id"] = selected
    customer = get_customer(selected)
    if customer is None:
        st.error("Cliente não encontrado.")
        return
    _render_customer_header(customer)
    open_tasks = [x for x in list_tasks(customer_id=selected) if x["status"] in ("open", "in_progress")]
    first = min(open_tasks, key=lambda x: (x["due_date"], x["priority"])) if open_tasks else None
    st.subheader("Próximo passo")
    st.caption("O trabalho prioritário da conta. Se não houver um próximo passo, defina um antes de encerrar o atendimento.")
    if first:
        action_cols = st.columns([2.4, 1, 1, 1])
        action_cols[0].info(f"{first['title']} · {first['owner'] or 'sem responsável'} · prazo {first['due_date']:%d/%m/%Y} · {TASK_STATUS_LABELS.get(first['status'], first['status'])}")
        action_cols[1].button("Concluir", key=f"top_complete_{first['task_id']}", disabled=True, help="A conclusão detalhada continua disponível em Minha fila.")
        action_cols[2].button("Alterar prazo", key=f"top_due_{first['task_id']}", disabled=True, help="Use Editar tarefa na Minha fila para alterar o prazo.")
        action_cols[3].button("Ver tarefa", key=f"top_open_{first['task_id']}", disabled=True, help="Acesse Minha fila para abrir e editar a tarefa.")
    else:
        st.warning("Nenhum próximo passo definido para esta conta.")
        st.caption("Defina uma tarefa com responsável e prazo para que a conta não fique sem acompanhamento.")
    top_cols = st.columns([1.1, 1.1, 1.8])
    with top_cols[0]:
        with st.expander("Registrar atendimento", expanded=False):
            _render_interaction(customer, key=f"top_{selected}")
    with top_cols[1]:
        with st.expander("Definir próximo passo", expanded=False):
            _render_task_form(customer)
    with top_cols[2]:
        st.markdown("**Último contato · histórico recente**")
        recent_interactions = list_interactions(selected)[:3]
        if recent_interactions:
            for item in recent_interactions:
                st.caption(f"{str(item['occurred_at'])[:10]} · {item['interaction_type']} · {item['actor']}")
                st.write(item["summary"])
        else:
            st.caption("Nenhum atendimento registrado ainda.")
    tabs = st.tabs(["Resumo e atendimentos", "Contrato", "Histórico importado"],
                   key=f"customer_360_tabs_{selected}", on_change="rerun")
    with tabs[0]:
        st.subheader("Alertas que precisam de atenção")
        customer_alerts = list_alerts(status="open", customer_id=selected)
        if customer_alerts:
            for alert in customer_alerts:
                _alert_card(alert, prefix=f"c360_{selected}")
        else:
            st.caption("Nenhum alerta operacional aberto.")
        st.subheader("Contexto da conta")
        st.caption("Informações úteis para o atendimento de hoje; contrato e histórico detalhado ficam nas abas ao lado.")
        st.write(f"Responsável: **{customer['owner'] or 'não atribuído'}**")
        st.write(f"Situação atual: **{LIFECYCLE_LABELS.get(customer['lifecycle_status'], 'Não informada')}** · saúde: **{HEALTH_LABELS.get(customer['health_status'], 'não informada')}**")
        st.write(f"Plano e usuários: **{customer['plan_tier'] or 'não confirmado'}** · **{customer['seats'] if customer['seats'] is not None else 'não confirmados'}**")
        st.write(f"Valor mensal: **{_money(customer['mrr_current'], customer['currency'])}** · renovação: **{customer['renewal_date'].strftime('%d/%m/%Y') if customer['renewal_date'] else 'não confirmada'}**")
        st.subheader("Ações recomendadas")
        st.caption("Atividades sugeridas por sinais históricos. Elas não alteram a situação da conta sozinhas.")
        signal_actions = list_signal_actions(account_id=selected)
        if not signal_actions:
            st.caption("Nenhuma ação ligada a sinal histórico para esta conta.")
        for action in signal_actions:
            with st.container(border=True):
                st.markdown(f"**{action['status']} · {action['action_text']}**")
                st.caption(f"{action['area']} · responsável {action['owner']} · prazo {action['due_date']} · {action['priority']}")
                st.write(f"Sinal: {action['title']}")
                st.caption(f"Observação: {action['observation'] or '—'} · Resultado: {action['result'] or '—'}")
                with st.expander("Histórico da ação"):
                    for event in list_signal_action_events(action["action_id"]):
                        st.caption(f"{event['event_at']} UTC · {event['event_type']}")
                        st.json(json.loads(event["changed_fields_json"]), expanded=False)
        st.subheader("Atendimentos registrados")
        current_interactions = list_interactions(selected)
        if not current_interactions:
            st.caption("Sem atendimentos operacionais ainda.")
        for item in current_interactions:
            with st.container(border=True):
                st.markdown(f"**{item['interaction_type']} · {str(item['occurred_at'])[:16]} · {item['actor']}**")
                st.write(item["summary"])
                if item["obstacle"]:
                    st.caption(f"Contexto/obstáculo: {item['obstacle']}")
                if item["outcome"]:
                    st.caption(f"Resultado informado: {item['outcome']}")
        with st.expander("Editar informações da conta", expanded=False):
            _render_customer_edit(customer)
    with tabs[1]:
        st.subheader("Contrato e valores confirmados")
        st.caption("Plano, usuários, valor mensal e mudanças contratuais. Dados antigos não são tratados como contrato atual automaticamente.")
        subs = list_subscriptions(selected)
        if not subs:
            st.info("Nenhuma assinatura operacional. Linhas do arquivo histórico abaixo não são o contrato atual.")
        for sub in subs:
            with st.container(border=True):
                confirmed = set(json.loads(sub["confirmed_fields_json"] or "[]"))
                st.markdown(f"**{sub['plan_tier'] or 'Plano não confirmado'} · {SUBSCRIPTION_STATUS_LABELS.get(sub['status'], sub['status'])} · {VERIFICATION_LABELS.get(sub['verification_status'], sub['verification_status'])}**")
                st.write(f"Usuários: {sub['seats'] if 'seats' in confirmed else 'não confirmados'} · Valor mensal: {_money(sub['mrr_current'] if 'mrr_current' in confirmed else None, sub['currency'])} · renovação: {sub['renewal_date'] if 'renewal_date' in confirmed else 'não confirmada'}")
                st.caption(f"Vigência {sub['effective_from'] or 'não informada'} → {sub['effective_to'] or 'vigente/sem fim'} · origem {sub['source']} · movimento {sub['movement_type']}")
        if customer["origin"] == "legacy":
            with st.expander("Validar apenas os campos confirmados", expanded=not customer["verification_fields"]):
                _render_validate_legacy(customer)
        st.divider()
        st.subheader("Alterar assinatura — prévia antes de confirmar")
        st.caption("Use para confirmar plano, seats, valor mensal ou adicionar uma nova linha de assinatura.")
        _render_subscription_change(customer)
        st.subheader("Registrar mudança na situação da conta")
        st.caption("Use somente quando a mudança tiver sido confirmada. O sistema registra quem fez, quando e por quê.")
        _render_movement(customer)
    with tabs[2]:
        st.subheader("Histórico importado e qualidade da fonte")
        st.caption("Use quando precisar consultar informações antigas, validar campos ou entender a origem de um dado. Isso não bloqueia o atendimento diário.")
        st.write(f"Origem do cadastro: **{'Criado no sistema' if customer['origin'] == 'native' else 'Importado do histórico'}** · qualidade: **{VERIFICATION_LABELS.get(customer['verification_status'], customer['verification_status'])}**")
        st.write(f"Campos com confirmação explícita: {', '.join(sorted(customer['verification_fields'])) or 'nenhum'}")
        if customer["origin"] == "legacy":
            st.info("Informações antigas ainda não confirmadas. Você pode registrar contatos e tarefas normalmente.")
        st.subheader("Registros históricos de produto e suporte")
        for table, label in (("feature_usage", "Uso de produto"), ("support_tickets", "Atendimentos históricos")):
            rows = list_source_records(selected, source_table=table, limit=100)
            with st.expander(f"{label} · {len(rows)} registro(s)"):
                if rows:
                    st.dataframe(pd.DataFrame([{"ID fonte": x["source_key"], **x["raw_payload"]} for x in rows]),
                                 hide_index=True, width="stretch")
                else:
                    st.caption("Nenhum registro nesta fonte para a conta.")
        st.subheader("Jornada do cliente")
        events = list_events(selected)
        if not events:
            st.info("A jornada recebe automaticamente cadastro, validações, tarefas, interações e movimentos.")
        for event in events:
            with st.container(border=True):
                st.markdown(f"**{EVENT_LABELS.get(event['event_type'], event['event_type'].replace('_', ' ').title())} · {str(event['occurred_at'])[:16]} UTC**")
                st.write(event["summary"])
                st.caption(f"Responsável/ator: {event['actor']} · origem: {event['source']}")
                if event["mrr_delta"] is not None:
                    st.caption(f"Delta de MRR registrado: {float(event['mrr_delta']):+,.2f} (moeda do evento no detalhe)")
                with st.expander("Antes / depois"):
                    st.json({"antes": event["previous_value"], "depois": event["new_value"]}, expanded=False)
        with st.expander("Dados históricos brutos da conta"):
            raw_records = list_source_records(selected, limit=100)
            if raw_records:
                for record in raw_records:
                    st.markdown(f"**{record['source_table']} · {record['source_key']} · linha {record['row_number']}**")
                    st.json(record["raw_payload"], expanded=False)
            else:
                st.caption("Sem linhas-fonte vinculadas.")
        with st.expander("Trilha de auditoria do cadastro"):
            st.json(customer["verification_fields"], expanded=True)


def _render_customer_header(customer: dict) -> None:
    c1, c2, c3, c4 = st.columns([1.7, 1, 1, 1.2])
    c1.subheader(customer["name"])
    c1.caption(f"{customer['industry'] or 'Setor não informado'} · {customer['country'] or 'País não informado'} · {customer['customer_id']}")
    c2.metric("Saúde e risco", HEALTH_LABELS.get(customer["health_status"], "Não informada"), help="Leitura de atenção da conta. Não substitui a análise do responsável; consulte os alertas e a próxima ação.")
    c3.metric("Situação da conta", LIFECYCLE_LABELS.get(customer["lifecycle_status"], "Não informada"), help="Estado operacional confirmado: implantação, ativa, pausada ou encerrada.")
    c4.metric("Confiança dos dados", VERIFICATION_LABELS.get(customer["verification_status"], "Não informado"), help="Indica quanto dos dados principais já foi confirmado por uma pessoa do time. Não é uma nota de saúde.")
    if customer["origin"] == "legacy" and customer["verification_status"] != "validated":
        st.warning("Dados importados / não validados. A ficha pode ser usada normalmente; confirme campos individuais quando disponíveis.")
    elif customer["origin"] == "native":
        st.caption("Cliente nativo · dados iniciais informados ao criar e validados no sistema.")
    st.caption(f"Responsável: {customer['owner'] or 'não atribuído'} · etapa: {customer['sales_stage'] or 'não informada'} · valor mensal: {_money(customer['mrr_current'], customer['currency'])}")


def render_tasks_page() -> None:
    setup_page(st, "Tarefas e alertas", "◈")
    st.title("Tarefas e alertas")
    _flash()
    all_customers = list_customers()
    owners = ["Todos", *sorted({x["owner"] for x in all_customers if x["owner"]})]
    c1, c2, c3 = st.columns(3)
    owner = c1.selectbox("Responsável", owners, key="tasks_owner")
    status = c2.selectbox("Status", ["open", "in_progress", "completed", "cancelled", "Todos"], key="tasks_status", format_func=lambda x: "Todos" if x == "Todos" else TASK_STATUS_LABELS.get(x, x))
    scope = c3.selectbox("Fila", ["Todas", "Vencidas", "Próximas", "Histórico"], key="tasks_scope")
    tasks = list_tasks(owner=owner, status=status)
    today = date.today()
    if scope == "Vencidas":
        tasks = [x for x in tasks if x["status"] in ("open", "in_progress") and x["due_date"] < today]
    elif scope == "Próximas":
        tasks = [x for x in tasks if x["status"] in ("open", "in_progress") and x["due_date"] >= today]
    elif scope == "Histórico":
        tasks = [x for x in tasks if x["status"] in ("completed", "cancelled")]
    with st.expander("Criar tarefa avulsa", expanded=False):
        if all_customers:
            options, labels = _customer_options(all_customers)
            customer_id = st.selectbox("Cliente", options, format_func=lambda x: labels[x], key="task_customer")
            with st.form("task_standalone"):
                title = st.text_input("Título")
                c1, c2, c3 = st.columns(3)
                assignee = c1.text_input("Responsável", value=_actor())
                due = c2.date_input("Prazo", value=today + timedelta(days=3))
                priority = c3.selectbox("Prioridade", TASK_PRIORITIES, index=1)
                submitted = st.form_submit_button("Criar tarefa", type="primary")
            if submitted:
                try:
                    create_task(customer_id, title=title, owner=assignee, due_date=due,
                                priority=priority, actor=_actor())
                    st.session_state["operational_flash"] = "Tarefa criada e disponível na fila."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.info("Cadastre/importa um cliente antes de criar tarefa.")
    task_tab, alert_tab = st.tabs(["Tarefas", "Alertas"], key="task_alert_tabs", on_change="rerun")
    with task_tab:
        if not tasks:
            st.info("Nenhuma tarefa neste filtro.")
        names = {x["customer_id"]: x["name"] for x in all_customers}
        for item in tasks:
            _task_card(item | {"customer_name": names.get(item["customer_id"], item["customer_id"])}, prefix="tasks")
    with alert_tab:
        alert_status = st.selectbox("Status do alerta", ["open", "treated", "resolved", "Todos"], key="alert_status_filter")
        alerts = list_alerts(status=alert_status)
        if not alerts:
            st.info("Nenhum alerta neste filtro.")
        for alert in alerts:
            _alert_card(alert, prefix="task_alert")


def render_intelligence_page() -> None:
    setup_page(st, "Sinais e recomendações", "◈")
    st.title("Sinais e recomendações")
    st.info("Para que serve: esta tela mostra o que merece atenção hoje e quais contas históricas precisam de confirmação. Ela não dá uma nota automática de saúde nem substitui a decisão do responsável.")
    try:
        queue = work_queue()
    except Exception as exc:
        st.error(str(exc))
        return
    st.subheader("1 · O que precisa de atenção hoje")
    st.caption("Alertas gerados por regras simples: tarefa vencida, renovação próxima ou conta ativa sem próxima ação.")
    if not queue["alerts"]:
        st.info("Sem alertas abertos. As regras são: tarefa vencida, renovação confirmada em até 30 dias e conta ativa sem tarefa aberta.")
    for alert in queue["alerts"][:50]:
        _alert_card(alert, prefix="intelligence")
    st.subheader("2 · Contas históricas a confirmar")
    st.caption("Use esta lista para completar informações que vieram de bases antigas. Dado ausente não significa risco.")
    legacy = [x for x in list_customers(origin="legacy") if x["verification_status"] != "validated"]
    st.caption(f"{len(legacy)} contas históricas ainda sem validação completa. Ausência de dados não significa saúde ou risco.")
    if legacy:
        frame = pd.DataFrame([{"Conta": x["name"], "ID": x["customer_id"],
                               "Validação": x["verification_status"], "Owner": x["owner"] or "Não atribuído"}
                              for x in legacy[:100]])
        st.dataframe(frame, hide_index=True, width="stretch")
        options, labels = _customer_options(legacy)
        selected = st.selectbox("Legacy para validar", options, format_func=lambda x: labels[x], key="intelligence_legacy_picker")
        _customer_button(selected, "intelligence_open_legacy", "Abrir e validar Cliente 360")
    st.subheader("3 · Evidências históricas para investigação")
    st.warning("Esses itens ajudam a formular perguntas sobre o passado. Não são alertas atuais e não provam churn, perda de receita ou causa do problema.")
    try:
        from src.retention_ui import load_signals
        signals = load_signals()
        area = st.selectbox("Fila histórica", ["Todas", *sorted(signals.area.unique())], key="historical_signal_area")
        view = signals if area == "Todas" else signals[signals.area.eq(area)]
        view = view.sort_values(["priority_order", "signal_date", "signal_id"]).head(100)
        if view.empty:
            st.info("Nenhum sinal no recorte.")
        else:
            show = view[["priority", "area", "account_name", "title", "signal_date", "evidence_summary", "uncertainty"]].rename(columns={
                "priority":"Prioridade explícita", "area":"Área", "account_name":"Conta",
                "title":"Sinal histórico", "signal_date":"Data histórica", "evidence_summary":"Evidência",
                "uncertainty":"Limite / incerteza"})
            st.dataframe(show, hide_index=True, width="stretch")
            aid = st.selectbox("Sinal para abrir na Central", view.signal_id.tolist(),
                               format_func=lambda x: f"{view.set_index('signal_id').loc[x, 'priority']} · {view.set_index('signal_id').loc[x, 'account_name']} · {view.set_index('signal_id').loc[x, 'title']}",
                               key="historical_signal_picker")
            if st.button("Abrir Central para decidir", key="go_central"):
                st.session_state["requested_signal_id"] = aid
                st.switch_page("pages/08_Central_de_Retencao.py")
    except Exception as exc:
        st.error(f"Sinais históricos indisponíveis: {exc}")


def render_management_page() -> None:
    setup_page(st, "Carteira e resultados", "◈")
    st.title("Carteira e resultados")
    st.info("Para que serve: ajudar gestores a decidir onde cobrar execução, redistribuir trabalho e garantir que nenhuma conta ativa fique sem próxima ação. Não é um painel de receita realizada.")
    summary = management_summary()
    counts = summary["counts"]
    signal_actions = list_signal_actions()
    signal_open = [x for x in signal_actions if x["status"] not in ("Concluída", "Cancelada")]
    signal_overdue = [x for x in signal_open if x["due_date"] < date.today().isoformat()]
    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes", counts["customers"])
    c2.metric("Tarefas vencidas", sum(counts["overdue_by_owner"].values()))
    c3.metric("Renovações confirmadas (30d)", counts["renewals_30_days"])
    c4, c5, c6 = st.columns(3)
    c4.metric("Clientes sem tarefa (lifecycle ativo)", counts["customers_without_next_action"])
    c5.metric("Alertas abertos", counts["open_alerts"])
    c6.metric("Alertas tratados (histórico)", counts["treated_alerts"])
    c7, c8, c9 = st.columns(3)
    c7.metric("Ações históricas abertas", len(signal_open))
    c8.metric("Ações históricas vencidas", len(signal_overdue))
    c9.metric("Ações históricas concluídas", sum(x["status"] == "Concluída" for x in signal_actions))
    st.subheader("Ações recomendadas por responsável")
    if signal_actions:
        owner_rows = []
        for owner in sorted({x["owner"] for x in signal_actions}):
            own = [x for x in signal_actions if x["owner"] == owner]
            owner_rows.append({"Responsável": owner, "Abertas": sum(x["status"] not in ("Concluída", "Cancelada") for x in own),
                "Vencidas": sum(x["status"] not in ("Concluída", "Cancelada") and x["due_date"] < date.today().isoformat() for x in own),
                "Concluídas": sum(x["status"] == "Concluída" for x in own)})
        st.dataframe(pd.DataFrame(owner_rows), hide_index=True, width="stretch")
    else:
        st.caption("Ainda não há ações da Central de Retenção histórica registradas.")
    st.subheader("Onde há atraso")
    if counts["overdue_by_owner"]:
        st.dataframe(pd.DataFrame([{"Responsável": k, "Vencidas": v} for k, v in sorted(counts["overdue_by_owner"].items())]), hide_index=True, width="stretch")
    else:
        st.success("Nenhuma tarefa vencida.")
    st.subheader("Contas ativas sem próximo passo")
    if summary["customers_without_next_action"]:
        for i, customer in enumerate(summary["customers_without_next_action"][:30]):
            with st.container(border=True):
                st.markdown(f"**{customer['name']}** · owner {customer['owner'] or 'não atribuído'}")
                _customer_button(customer["customer_id"], f"management_no_action_{i}")
    else:
        st.success("Todos os clientes de lifecycle ativo têm tarefa aberta.")
    st.subheader("Contas importadas que ainda precisam de confirmação")
    st.caption("Este bloco mostra qualidade de cadastro, não desempenho comercial. Use-o para planejar a coleta de informações.")
    verification = counts["legacy_by_verification"]
    st.dataframe(pd.DataFrame([{"Estado de validação": k, "Contas": v} for k, v in sorted(verification.items())]), hide_index=True, width="stretch")
    st.caption("Clientes nativos e legacy não são misturados; campos legacy atuais são desconhecidos até validação humana.")
    st.subheader("Mudanças de valor registradas")
    st.caption("Somente mudanças confirmadas manualmente aparecem aqui; eventos históricos de churn não são tratados como perda automaticamente.")
    if summary["confirmed_movements"]:
        frame = pd.DataFrame([{ "Data UTC": x["occurred_at"], "Conta": x["customer_name"],
            "Movimento": x["event_type"], "Delta MRR registrado": x["mrr_delta"] if x["mrr_delta"] is not None else "Não calculado",
            "Ator informado": x["actor"], "Contexto": x["summary"], "ID": x["event_id"]}
            for x in summary["confirmed_movements"]])
        st.dataframe(frame, hide_index=True, width="stretch")
    else:
        st.info("Ainda não há movimentos de assinatura registrados. Eventos churn históricos não são incluídos como perdas confirmadas.")
    if database_mode() == "sqlite-demo-efemero":
        st.divider()
        st.warning("SQLite demo: bom para clone/local; o filesystem do Streamlit Community Cloud pode ser efêmero. Sem DATABASE_URL, mudanças não têm garantia após reboot/redeploy.")
        with st.expander("Resetar banco demo local (apaga registros operacionais)"):
            st.caption("A fonte analítica e os CSVs são somente leitura e permanecem intactos. Reset não está disponível para PostgreSQL.")
            confirm = st.text_input("Digite RESETAR DEMO para confirmar", key="reset_demo_word")
            if st.button("Resetar base operacional demo", key="reset_demo_button", disabled=confirm != "RESETAR DEMO"):
                try:
                    n = reset_demo_data()
                    st.session_state["operational_flash"] = f"Base demo reiniciada; {n} cadastros operacionais foram removidos e as contas históricas foram recarregadas."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))


def render_operational_shell() -> None:
    """Shared navigation context for use on each standalone Streamlit page."""
    if "actor_identity" not in st.session_state:
        st.session_state["actor_identity"] = str(st.session_state.get("current_actor_input") or "Operador local").strip() or "Operador local"
    if "current_actor_input" not in st.session_state:
        st.session_state["current_actor_input"] = st.session_state["actor_identity"]
    with st.sidebar:
        st.markdown("### RavenStack")
        st.caption("Customer Journey · MVP operacional")
        st.text_input("Quem está usando? (MVP)", key="current_actor_input", on_change=_persist_actor_identity,
                      help="Campo de autoria autodeclarado; não substitui login.")
        mode = database_mode()
        if mode == "sqlite-demo-efemero":
            st.warning("SQLite local/demo · pode ser efêmero no Cloud")
        else:
            st.success("PostgreSQL configurado")
        query = st.text_input("Buscar cliente globalmente", key="global_customer_search", placeholder="Nome ou ID")
        if query.strip():
            matches = list_customers(query=query)[:6]
            if not matches:
                st.caption("Nenhum cliente encontrado.")
            for index, customer in enumerate(matches):
                if st.button(f"{customer['name']} · {customer['customer_id']}", key=f"global_customer_{index}_{customer['customer_id']}"):
                    _open_customer(customer["customer_id"])
        st.divider()
        st.caption("Dados do conjunto histórico até 31/12/2024")



def render_sales_workspace() -> None:
    setup_page(st, "Comercial · Pipeline", "◈")
    st.title("Comercial · pipeline e atuação")
    st.caption("Aqui o time cadastra leads, atualiza etapa/owner e registra cada conversa. Valor de oportunidade é estimativa, não receita ou MRR.")
    _flash()
    all_items = list_customers()
    stages = ["Lead novo", "Qualificação", "Descoberta", "Proposta", "Negociação",
              "Fechado ganho", "Fechado perdido", "Onboarding", "Ativo", "Renovação", "Encerrado"]
    stage_items = [x for x in all_items if x["sales_stage"] in stages]
    c1, c2, c3 = st.columns(3)
    c1.metric("Oportunidades no pipeline", len([x for x in stage_items if x["sales_stage"] not in ("Fechado ganho", "Fechado perdido", "Encerrado")]))
    c2.metric("Follow-ups abertos", sum(1 for x in list_tasks() if x["status"] in ("open", "in_progress")))
    c3.metric("Interações registradas", sum(len(list_interactions(x["customer_id"])) for x in stage_items[:150]))
    register, pipeline, activities = st.tabs(["+ Cadastrar lead", "Pipeline", "Atividades"],
                                             key="sales_workspace_tabs", on_change="rerun")
    with register:
        with st.form("opportunity_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Empresa / oportunidade *")
            owner = c2.text_input("Responsável comercial *", value=_actor())
            stage = c3.selectbox("Etapa inicial", stages[:7])
            c4, c5, c6 = st.columns(3)
            industry = c4.text_input("Indústria")
            country = c5.text_input("País")
            source = c6.text_input("Origem / canal")
            c7, c8, c9 = st.columns(3)
            amount = c7.number_input("Valor estimado da oportunidade (opcional)", min_value=0.0, value=0.0, step=500.0)
            currency = c8.selectbox("Moeda estimada", CURRENCIES)
            close_date = c9.date_input("Previsão de fechamento (opcional)", value=None)
            st.markdown("**Próximo passo (opcional)**")
            next_title = st.text_input("Próxima ação")
            a1, a2 = st.columns(2)
            next_due = a1.date_input("Prazo", value=date.today() + timedelta(days=3))
            next_priority = a2.selectbox("Prioridade da tarefa", TASK_PRIORITIES, index=1)
            notes = st.text_area("Contexto inicial (não inserir dados sensíveis)")
            submitted = st.form_submit_button("Cadastrar oportunidade", type="primary")
        if submitted:
            try:
                identity = create_opportunity(name=name, owner=owner, actor=_actor(),
                    industry=industry, country=country, referral_source=source,
                    sales_stage=stage, opportunity_value_estimate=float(amount) if amount > 0 else None,
                    opportunity_currency=currency, expected_close_date=close_date,
                    next_action=next_title, next_action_due=next_due if next_title.strip() else None,
                    next_action_priority=next_priority, notes=notes)
                st.session_state["operational_flash"] = "Oportunidade cadastrada no pipeline; lifecycle e assinatura permanecem não confirmados até fechamento/cadastro do cliente."
                _open_customer(identity)
            except ValueError as exc:
                st.error(str(exc))
    with pipeline:
        with st.expander("Filtrar pipeline", expanded=True):
            f1, f2, f3 = st.columns(3)
            stage_filter = f1.selectbox("Etapa", ["Todas", *stages], key="sales_stage_filter")
            owners = ["Todos", *sorted({x["owner"] for x in stage_items if x["owner"]})]
            owner_filter = f2.selectbox("Responsável", owners, key="sales_owner_filter")
            search = f3.text_input("Buscar empresa", key="sales_search")
        items = list_customers(query=search, owner=owner_filter,
                               database_url=None)
        items = [x for x in items if x["sales_stage"] in stages and (stage_filter == "Todas" or x["sales_stage"] == stage_filter)]
        if not items:
            st.info("Pipeline vazio neste filtro. Use **Cadastrar lead** para registrar uma oportunidade.")
        else:
            frame = pd.DataFrame([{
                "Empresa": x["name"], "Etapa": x["sales_stage"], "Responsável": x["owner"] or "Não atribuído",
                "Valor oportunidade (estimado)": _money(x["opportunity_value_estimate"], x["opportunity_currency"]),
                "Fechamento previsto": x["expected_close_date"].strftime("%d/%m/%Y") if x["expected_close_date"] else "—",
                "Próxima ação": next((t["title"] for t in list_tasks(customer_id=x["customer_id"]) if t["status"] in ("open", "in_progress")), "Sem tarefa aberta"),
                "ID": x["customer_id"],
            } for x in items])
            st.dataframe(frame, hide_index=True, width="stretch")
            options, labels = _customer_options(items)
            selected_id = st.selectbox("Oportunidade para atuar", options,
                                       format_func=lambda x: labels[x], key="sales_account_picker")
            selected = get_customer(selected_id)
            with st.expander("Atualizar informações / mover etapa", expanded=True):
                _render_customer_edit(selected)
            st.subheader("Registrar atividade comercial")
            _render_interaction(selected, key=f"sales_activity_{selected_id}")
    with activities:
        with st.expander("Buscar atividade", expanded=True):
            q = st.text_input("Cliente / ID", key="sales_activity_search")
            owner = st.text_input("Responsável da atividade", key="sales_activity_owner")
        all_matches = list_customers(query=q)
        records = []
        for item in all_matches:
            for interaction in list_interactions(item["customer_id"]):
                if not owner or owner.casefold() in interaction["actor"].casefold():
                    records.append({"Cliente": item["name"], "ID": item["customer_id"],
                                    "Data": interaction["occurred_at"], "Tipo": interaction["interaction_type"],
                                    "Responsável": interaction["actor"], "Resumo": interaction["summary"],
                                    "Resultado": interaction["outcome"] or "—"})
        if records:
            st.dataframe(pd.DataFrame(records), hide_index=True, width="stretch")
        else:
            st.info("Sem atividades no recorte. Abra uma oportunidade e registre ligação, reunião, e-mail ou nota.")
