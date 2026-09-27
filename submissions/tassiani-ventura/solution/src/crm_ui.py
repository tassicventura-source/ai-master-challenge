from __future__ import annotations

from datetime import date, timedelta
import json

import pandas as pd
import streamlit as st

from src.action_store import (
    CRM_CURRENCIES,
    CRM_STAGES,
    INTERACTION_AREAS,
    INTERACTION_STATUSES,
    INTERACTION_TYPES,
    crm_counts,
    list_crm_accounts,
    list_crm_events,
    list_crm_interactions,
    save_crm_account,
    save_crm_interaction,
)
from src.data_access import load_table


SOURCE_OPTIONS = ("", "organic", "ads", "partner", "event", "other")


def _account_labels(accounts: list[dict]) -> dict[str, str]:
    return {row["account_id"]: f"{row['account_name']} · {row['account_id']}"
            for row in accounts}


def _existing_dataset_accounts() -> pd.DataFrame:
    accounts = load_table("account_360")
    return accounts.sort_values(["account_name", "account_id"]).reset_index(drop=True)


def _render_account_form(existing: dict | None = None, dataset_row: pd.Series | None = None,
                         *, key_prefix: str = "crm_account") -> None:
    existing = existing or {}
    dataset_row = dataset_row if dataset_row is not None else pd.Series(dtype="object")
    record_origin = existing.get("record_origin", "Cadastro manual")

    def value(key: str, fallback=""):
        if key in existing and existing[key] not in (None, ""):
            return existing[key]
        if key in dataset_row and pd.notna(dataset_row[key]):
            return dataset_row[key]
        return fallback

    st.caption("Campos operacionais editáveis. O cadastro não altera as fontes analíticas, CRM externo, billing ou helpdesk.")
    with st.form(f"{key_prefix}_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        account_name = c1.text_input("Nome da conta / lead *", value=str(value("account_name")), key=f"{key_prefix}_name")
        owner_id = c2.text_input("Responsável comercial *", value=str(value("owner_id")),
                                 placeholder="Nome ou e-mail corporativo", key=f"{key_prefix}_owner")
        c3, c4 = st.columns(2)
        industry = c3.text_input("Setor", value=str(value("industry")), key=f"{key_prefix}_industry")
        country = c4.text_input("País", value=str(value("country")), key=f"{key_prefix}_country")
        c5, c6 = st.columns(2)
        source_value = str(value("referral_source"))
        source_idx = SOURCE_OPTIONS.index(source_value) if source_value in SOURCE_OPTIONS else 0
        referral_source = c5.selectbox("Origem", SOURCE_OPTIONS, index=source_idx,
                                       format_func=lambda x: x or "Não informado", key=f"{key_prefix}_source")
        referral_detail = c6.text_input("Campanha / parceiro / detalhe da origem",
                                        value=str(value("referral_detail")), key=f"{key_prefix}_source_detail")
        c7, c8 = st.columns(2)
        icp_segment = c7.text_input("Segmento ICP", value=str(value("icp_segment")), key=f"{key_prefix}_icp")
        stage_value = str(value("journey_stage", CRM_STAGES[0]))
        stage_idx = CRM_STAGES.index(stage_value) if stage_value in CRM_STAGES else 0
        journey_stage = c8.selectbox("Etapa da jornada / pipeline", CRM_STAGES, index=stage_idx, key=f"{key_prefix}_stage")
        c9, c10 = st.columns(2)
        current_currency = str(value("deal_currency", "USD"))
        currency_idx = CRM_CURRENCIES.index(current_currency) if current_currency in CRM_CURRENCIES else 0
        deal_currency = c9.selectbox("Moeda do valor estimado", CRM_CURRENCIES, index=currency_idx, key=f"{key_prefix}_currency")
        raw_value = value("deal_value_estimate")
        try:
            amount = float(raw_value) if raw_value not in (None, "") else None
        except (TypeError, ValueError):
            amount = None
        deal_value = c10.number_input("Valor estimado da oportunidade (não é receita realizada)",
                                      min_value=0.0, value=amount or 0.0, step=100.0,
                                      format="%.2f", key=f"{key_prefix}_deal_value")
        c11, c12 = st.columns(2)
        try:
            expected_default = date.fromisoformat(str(value("expected_close_date")))
        except (ValueError, TypeError):
            expected_default = None
        expected_close = c11.date_input("Previsão de fechamento (opcional)", value=expected_default,
                                        key=f"{key_prefix}_expected_close")
        account_next_action = c12.text_input("Próxima ação da conta", value=str(value("next_action")),
                                             key=f"{key_prefix}_next_action")
        try:
            next_default = date.fromisoformat(str(value("next_action_due_at")))
        except (ValueError, TypeError):
            next_default = None
        next_due = st.date_input("Prazo da próxima ação (opcional)", value=next_default,
                                 key=f"{key_prefix}_next_action_due")
        notes = st.text_area("Notas internas (não insira dados sensíveis)", value=str(value("notes")),
                             key=f"{key_prefix}_notes")
        submitted = st.form_submit_button("Salvar cadastro / atualização", type="primary")
    if submitted:
        try:
            amount_value = deal_value if deal_value > 0 else None
            existing_next = account_next_action.strip()
            next_date = next_due if existing_next else None
            saved_id = save_crm_account(
                account_id=existing.get("account_id"),
                record_origin=record_origin,
                account_name=account_name,
                owner_id=owner_id,
                industry=industry,
                country=country,
                referral_source=referral_source,
                referral_detail=referral_detail,
                icp_segment=icp_segment,
                journey_stage=journey_stage,
                deal_value_estimate=amount_value,
                deal_currency=deal_currency,
                expected_close_date=expected_close,
                next_action=existing_next,
                next_action_due_at=next_date,
                notes=notes,
            )
            if not existing and record_origin == "Cadastro manual":
                st.session_state["crm_registration_nonce"] = st.session_state.get("crm_registration_nonce", 0) + 1
            st.session_state["crm_flash"] = f"Conta salva · ID operacional {saved_id}. Os dados analíticos de origem não foram alterados."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _render_interaction_form(account_id: str, account_name: str, *, key_prefix: str,
                             existing: dict | None = None) -> None:
    st.markdown(f"#### Registrar atividade · {account_name}")
    existing = existing or {}

    def previous(name: str, fallback=""):
        return existing.get(name) if existing.get(name) not in (None, "") else fallback

    with st.form(f"{key_prefix}_interaction_form", clear_on_submit=existing is None):
        c1, c2, c3 = st.columns(3)
        try:
            occurred_default = date.fromisoformat(str(previous("occurred_at")))
        except (TypeError, ValueError):
            occurred_default = date.today()
        occurred_at = c1.date_input("Data da interação", value=occurred_default, key=f"{key_prefix}_date")
        previous_area = previous("area", "Comercial")
        area_idx = INTERACTION_AREAS.index(previous_area) if previous_area in INTERACTION_AREAS else 0
        area = c2.selectbox("Área que atuou", INTERACTION_AREAS, index=area_idx, key=f"{key_prefix}_area")
        previous_type = previous("interaction_type", INTERACTION_TYPES[0])
        type_idx = INTERACTION_TYPES.index(previous_type) if previous_type in INTERACTION_TYPES else 0
        interaction_type = c3.selectbox("Tipo", INTERACTION_TYPES, index=type_idx, key=f"{key_prefix}_type")
        summary = st.text_area("O que foi feito / combinado *", value=str(previous("summary")), key=f"{key_prefix}_summary")
        c4, c5 = st.columns(2)
        owner_id = c4.text_input("Responsável pela atividade *", value=str(previous("owner_id")), key=f"{key_prefix}_owner")
        previous_status = previous("status", "Planejada")
        status_idx = INTERACTION_STATUSES.index(previous_status) if previous_status in INTERACTION_STATUSES else 0
        status = c5.selectbox("Status da atividade", INTERACTION_STATUSES, index=status_idx, key=f"{key_prefix}_status")
        outcome = st.text_area("Resultado / retorno observado", value=str(previous("outcome")), key=f"{key_prefix}_outcome")
        next_action = st.text_input("Próxima ação", value=str(previous("next_action")), key=f"{key_prefix}_next")
        try:
            due_default = date.fromisoformat(str(previous("next_action_due_at")))
        except (TypeError, ValueError):
            due_default = date.today() + timedelta(days=3)
        next_due = st.date_input("Prazo da próxima ação (sugestão: 3 dias; revise)", value=due_default,
                                 key=f"{key_prefix}_due")
        observation = st.text_area("Observação interna (não insira dados sensíveis)", value=str(previous("observation")), key=f"{key_prefix}_observation")
        submitted = st.form_submit_button("Salvar atividade", type="primary")
    if submitted:
        try:
            saved_id = save_crm_interaction(
                account_id=account_id,
                occurred_at=occurred_at,
                area=area,
                interaction_type=interaction_type,
                summary=summary,
                owner_id=owner_id,
                outcome=outcome,
                next_action=next_action,
                next_action_due_at=next_due if next_action.strip() else None,
                status=status,
                observation=observation,
                interaction_id=existing.get("interaction_id"),
            )
            st.session_state["crm_flash"] = f"Atividade persistida · ID {saved_id[:8]}."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def render_account_crm(account_id: str) -> None:
    crm = next((x for x in list_crm_accounts() if x["account_id"] == account_id), None)
    if not crm:
        st.subheader("Operação comercial/CS")
        st.info("Esta conta histórica ainda não foi aberta no CRM operacional.")
        if st.button("Abrir conta no CRM e atribuir responsável", key=f"open_crm_{account_id}"):
            st.session_state["crm_prefill_account_id"] = account_id
            st.switch_page("pages/09_Operacao_CRM.py")
        return
    st.subheader("Conta operacional · pipeline e owner")
    st.caption(f"{crm['journey_stage']} · Responsável: {crm['owner_id']} · Origem do cadastro: {crm['record_origin']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Etapa", crm["journey_stage"])
    value = crm["deal_value_estimate"]
    c2.metric("Valor estimado", f"{crm['deal_currency']} {value:,.2f}" if value is not None else "Não informado")
    c3.metric("Próxima ação", crm["next_action"] or "Não informada")
    if crm["next_action_due_at"]:
        st.caption(f"Prazo da próxima ação: {crm['next_action_due_at']}")
    with st.expander("Editar responsável, etapa e dados do pipeline"):
        _render_account_form(existing=crm, key_prefix=f"crm_edit_{account_id}")
    interactions = list_crm_interactions(account_id=account_id)
    st.markdown("**Atividades e histórico de follow-up**")
    if interactions:
        for item in interactions:
            with st.container(border=True):
                st.markdown(f"**{item['occurred_at']} · {item['area']} · {item['interaction_type']} · {item['status']}**")
                st.write(item["summary"])
                if item["outcome"]:
                    st.caption(f"Resultado informado: {item['outcome']}")
                if item["next_action"]:
                    st.info(f"Próxima ação · {item['next_action']} · prazo {item['next_action_due_at']}")
                st.caption(f"Responsável: {item['owner_id']}")
        selected = st.selectbox("Trilha de auditoria da atividade", interactions,
                                format_func=lambda row: f"{row['occurred_at']} · {row['area']} · {row['summary'][:70]}",
                                key=f"crm_audit_select_{account_id}")
        events = list_crm_events(entity_type="interaction", entity_id=selected["interaction_id"])
        if events:
            with st.expander("Alterações registradas"):
                for event in events:
                    st.caption(f"{event['event_at']} UTC · {event['event_type']}")
                    st.json(json.loads(event["changed_fields_json"]), expanded=False)
    else:
        st.caption("Ainda não há atividades registradas para esta conta.")
    with st.expander("Registrar atividade nesta conta"):
        _render_interaction_form(account_id, crm["account_name"], key_prefix=f"crm_account_{account_id}")


def render_crm_workspace() -> None:
    st.title("CRM e Operação Comercial")
    st.write("Cadastre leads/clientes, mova oportunidades no pipeline, registre o que Comercial/CS/Suporte fez e deixe a próxima ação com responsável e prazo.")
    st.warning("Modo demo: estes registros usam SQLite local sem login ou controle de acesso. Esta versão pública não é segura para nomes, contatos, notas confidenciais ou dados reais de clientes. Consulte o README para configurar armazenamento persistente e restringir acesso antes de qualquer piloto real.")
    flash = st.session_state.pop("crm_flash", None)
    if flash:
        st.success(flash)
    counts = crm_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contas no CRM", counts["accounts"])
    c2.metric("Oportunidades abertas", counts["open_opportunities"])
    c3.metric("Follow-ups em aberto", counts["open_followups"])
    c4.metric("Atividades registradas", counts["interactions"])

    overview, register, pipeline, activities = st.tabs([
        "Visão operacional", "Cadastrar conta", "Pipeline", "Atividades e follow-ups",
    ])
    with overview:
        accounts = list_crm_accounts()
        if not accounts:
            st.info("O CRM está vazio. Cadastre um lead/cliente ou associe uma conta histórica na aba **Cadastrar conta** para começar.")
        else:
            df = pd.DataFrame(accounts)
            df = df[["account_id", "account_name", "journey_stage", "owner_id", "deal_value_estimate", "deal_currency", "expected_close_date", "next_action", "next_action_due_at", "record_origin"]].rename(columns={
                "account_id": "ID", "account_name": "Conta", "journey_stage": "Etapa",
                "owner_id": "Responsável", "deal_value_estimate": "Valor estimado",
                "deal_currency": "Moeda", "expected_close_date": "Previsão fechamento",
                "next_action": "Próxima ação", "next_action_due_at": "Prazo",
                "record_origin": "Origem do registro",
            })
            st.dataframe(df, hide_index=True, width="stretch")
        interactions = list_crm_interactions(open_only=True)
        st.subheader("Follow-ups planejados")
        if not interactions:
            st.caption("Nenhum follow-up aberto registrado.")
        else:
            crm_by_id = {x["account_id"]: x for x in list_crm_accounts()}
            for item in interactions:
                account_name = crm_by_id.get(item["account_id"], {}).get("account_name", item["account_id"])
                with st.container(border=True):
                    st.markdown(f"**{item['next_action_due_at'] or 'Sem prazo'} · {account_name} · {item['area']}**")
                    st.write(item["next_action"])
                    st.caption(f"Responsável: {item['owner_id']} · {item['status']} · Atividade: {item['summary']}")
    with register:
        st.subheader("Novo lead ou conta existente")
        mode = st.radio("Tipo de cadastro", ["Novo lead / cliente", "Associar conta histórica"], horizontal=True,
                        key="crm_registration_mode")
        account_id = None
        existing = None
        dataset_row = None
        if mode == "Associar conta histórica":
            data = _existing_dataset_accounts()
            data_map = data.set_index("account_id").account_name.to_dict()
            preferred = st.session_state.pop("crm_prefill_account_id", None)
            opts = data.account_id.tolist()
            idx = opts.index(preferred) if preferred in opts else 0
            account_id = st.selectbox("Conta observada no dataset", opts, index=idx,
                                      format_func=lambda x: f"{data_map[x]} · {x}", key="crm_dataset_account")
            dataset_row = data.set_index("account_id").loc[account_id]
            existing = next((x for x in list_crm_accounts() if x["account_id"] == account_id), None)
            st.info("Os dados abaixo vêm do dataset histórico; o novo owner, etapa e pipeline serão gravados numa camada operacional separada.")
        record_origin = "Conta do dataset" if mode == "Associar conta histórica" else "Cadastro manual"
        prefixed_existing = existing or ({"account_id": account_id, "record_origin": record_origin} if account_id else None)
        nonce = st.session_state.get("crm_registration_nonce", 0)
        _render_account_form(existing=prefixed_existing, dataset_row=dataset_row,
                             key_prefix=f"crm_new_{account_id or 'manual'}_{nonce}")
    with pipeline:
        st.subheader("Pipeline comercial")
        accounts = list_crm_accounts()
        stage_filter = st.selectbox("Filtrar por etapa", ["Todas", *CRM_STAGES], key="crm_stage_filter")
        owner_options = ["Todos", *sorted({x["owner_id"] for x in accounts if x["owner_id"]})]
        owner_filter = st.selectbox("Filtrar por responsável", owner_options, key="crm_owner_filter")
        visible = list_crm_accounts(stage=stage_filter, owner=owner_filter)
        if not visible:
            st.info("Nenhuma conta nesse recorte. Use a aba **Cadastrar conta** para iniciar o pipeline.")
        else:
            frame = pd.DataFrame(visible)[["account_name", "account_id", "journey_stage", "owner_id", "deal_value_estimate", "deal_currency", "expected_close_date", "next_action", "next_action_due_at"]].rename(columns={
                "account_name": "Conta", "account_id": "ID", "journey_stage": "Etapa",
                "owner_id": "Responsável", "deal_value_estimate": "Valor estimado",
                "deal_currency": "Moeda", "expected_close_date": "Fechamento previsto",
                "next_action": "Próxima ação", "next_action_due_at": "Prazo",
            })
            st.dataframe(frame, hide_index=True, width="stretch")
            labels = _account_labels(visible)
            selected_id = st.selectbox("Conta para registrar atuação comercial", list(labels),
                                       format_func=lambda x: labels[x], key="crm_pipeline_account")
            crm = next(x for x in visible if x["account_id"] == selected_id)
            with st.expander("Editar etapa/owner/valor estimado"):
                _render_account_form(existing=crm, key_prefix=f"crm_pipeline_edit_{selected_id}")
            _render_interaction_form(selected_id, crm["account_name"], key_prefix=f"crm_pipeline_activity_{selected_id}")
    with activities:
        st.subheader("Diário de atuação por área")
        all_accounts = list_crm_accounts()
        if not all_accounts:
            st.info("Cadastre primeiro uma conta na aba **Cadastrar conta**.")
        else:
            labels = _account_labels(all_accounts)
            selected_id = st.selectbox("Conta da atividade", list(labels), format_func=lambda x: labels[x],
                                       key="crm_activity_account")
            crm = next(x for x in all_accounts if x["account_id"] == selected_id)
            items = list_crm_interactions(account_id=selected_id)
            with st.expander("Registrar nova atuação", expanded=not items):
                _render_interaction_form(selected_id, crm["account_name"], key_prefix=f"crm_activity_new_{selected_id}")
            st.subheader("Histórico desta conta")
            if items:
                st.dataframe(pd.DataFrame(items)[[
                    "occurred_at", "area", "interaction_type", "summary", "owner_id", "status",
                    "outcome", "next_action", "next_action_due_at",
                ]].rename(columns={
                    "occurred_at": "Data", "area": "Área", "interaction_type": "Tipo",
                    "summary": "Atividade", "owner_id": "Responsável", "status": "Status",
                    "outcome": "Resultado", "next_action": "Próxima ação", "next_action_due_at": "Prazo",
                }), hide_index=True, width="stretch")
                selected_activity = st.selectbox(
                    "Atividade para atualizar", items,
                    format_func=lambda row: f"{row['occurred_at']} · {row['status']} · {row['summary'][:70]}",
                    key=f"crm_activity_edit_select_{selected_id}",
                )
                with st.expander("Atualizar status, resultado ou próxima ação"):
                    _render_interaction_form(
                        selected_id, crm["account_name"], existing=selected_activity,
                        key_prefix=f"crm_activity_edit_{selected_id}_{selected_activity['interaction_id']}",
                    )
            else:
                st.caption("Nenhuma atividade anterior para esta conta.")
