from __future__ import annotations

from datetime import date, timedelta
import json

import pandas as pd
import streamlit as st

from src.action_store import STATUSES, actions_frame, list_actions, list_events, save_action
from src.data_access import load_table
from src.retention import AREAS, OBSERVATION_CUTOFF, PRIORITIES, build_signals, signal_snapshot


@st.cache_data(show_spinner=False, max_entries=2)
def load_signals() -> pd.DataFrame:
    return build_signals(
        load_table("account_360"), load_table("feature_usage"),
        load_table("customer_interactions"), load_table("lifecycle_events"),
    )


def _queue_view(signals: pd.DataFrame, *, area: str | None = None,
                priority: str | None = None, search: str = "") -> pd.DataFrame:
    out = signals.copy()
    if area:
        out = out[out.area.eq(area)]
    if priority and priority != "Todas":
        out = out[out.priority.eq(priority)]
    term = search.strip().casefold()
    if term:
        mask = (
            out.account_name.astype(str).str.casefold().str.contains(term, regex=False)
            | out.account_id.astype(str).str.casefold().str.contains(term, regex=False)
            | out.title.astype(str).str.casefold().str.contains(term, regex=False)
            | out.evidence_summary.astype(str).str.casefold().str.contains(term, regex=False)
        )
        out = out[mask]
    return out.sort_values(["priority_order", "signal_date", "signal_id"], na_position="last").reset_index(drop=True)


def _signal_label(row: pd.Series) -> str:
    return f"{row.priority} · {row.account_name} · {row.title} · {row.signal_date}"


def _action_summary(area: str | None = None) -> tuple[int, int, int]:
    actions = list_actions(area=area)
    today = date.today().isoformat()
    active = [a for a in actions if a["status"] not in ("Concluída", "Cancelada")]
    overdue = [a for a in active if a["due_date"] < today]
    return len(active), len(overdue), len(actions)


def _show_action_editor(signal: pd.Series, scope: str) -> None:
    existing = list_actions(signal_id=str(signal.signal_id))
    selected_action = None
    if existing:
        options = ["Criar nova ação"] + [
            f"{a['updated_at'][:10]} · {a['owner']} · {a['status']} · {a['action_text'][:65]}"
            for a in existing
        ]
        choice = st.selectbox("Ações já registradas para este sinal", options, key=f"action_choice_{scope}_{signal.signal_id}")
        if choice != options[0]:
            selected_action = existing[options.index(choice) - 1]
    st.markdown("**Registrar ou atualizar ação**")
    initial_action = selected_action or {}
    form_key = f"action_form_{scope}_{signal.signal_id}_{initial_action.get('action_id', 'new')}"
    action_key = initial_action.get("action_id", "new")
    with st.form(form_key, clear_on_submit=False):
        action_text = st.text_area(
            "Ação a executar", value=initial_action.get("action_text", signal.next_action),
            key=f"action_text_{scope}_{signal.signal_id}_{action_key}",
        )
        c1, c2 = st.columns(2)
        owner = c1.text_input("Responsável", value=initial_action.get("owner", ""),
                              placeholder="Nome da pessoa responsável", key=f"owner_{scope}_{signal.signal_id}_{action_key}")
        priority_options = list(PRIORITIES)
        priority_default = initial_action.get("priority", str(signal.priority))
        priority_idx = priority_options.index(priority_default) if priority_default in priority_options else 1
        priority = c2.selectbox("Prioridade da ação", priority_options, index=priority_idx,
                                key=f"priority_{scope}_{signal.signal_id}_{action_key}")
        c3, c4 = st.columns(2)
        try:
            due_default = date.fromisoformat(initial_action.get("due_date", ""))
        except (TypeError, ValueError):
            due_default = date.today() + timedelta(days=3)
        due = c3.date_input("Prazo", value=due_default, key=f"due_{scope}_{signal.signal_id}_{action_key}")
        previous_status = initial_action.get("status", "Aberta")
        status_idx = STATUSES.index(previous_status) if previous_status in STATUSES else 0
        status = c4.selectbox("Status", STATUSES, index=status_idx,
                              key=f"status_{scope}_{signal.signal_id}_{action_key}")
        observation = st.text_area("Observação", value=initial_action.get("observation", ""),
                                   key=f"observation_{scope}_{signal.signal_id}_{action_key}")
        result = st.text_area("Resultado (preencher ao concluir)", value=initial_action.get("result", ""),
                              key=f"result_{scope}_{signal.signal_id}_{action_key}")
        submitted = st.form_submit_button("Salvar ação", type="primary")
    if submitted:
        try:
            saved_id = save_action(
                signal=signal_snapshot(signal), action_text=action_text, owner=owner,
                priority=priority, due_date=due, status=status,
                observation=observation, result=result,
                action_id=initial_action.get("action_id"),
            )
            st.success(f"Ação persistida · ID {saved_id[:8]} · modo demo SQLite.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _show_detail(signal: pd.Series, scope: str) -> None:
    st.markdown(f"### {signal.title}")
    st.caption(f"{signal.area} · {signal.account_name} ({signal.account_id}) · data histórica {signal.signal_date} · {signal.priority}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**O que aconteceu**")
        st.write(signal.what_happened)
        st.markdown("**Por que importa**")
        st.write(signal.why_it_matters)
    with c2:
        st.markdown("**Evidência observada**")
        st.write(signal.evidence_summary)
        st.markdown("**Incerteza / limite**")
        st.warning(signal.uncertainty)
    st.markdown("**Próxima ação sugerida**")
    st.info(signal.next_action)
    with st.expander("Abrir evidência e IDs de origem"):
        st.json(signal.evidence, expanded=True)
        st.caption("Fontes: " + ", ".join(signal.source_refs))
        st.caption("Regra de prioridade: " + signal.priority_reason)
    if st.button("Abrir ficha do cliente", key=f"open_account_{scope}_{signal.signal_id}"):
        st.session_state["requested_account_id"] = str(signal.account_id)
        st.switch_page("pages/01_Conta_360.py")
    _show_action_editor(signal, scope)

    with st.expander("Acompanhamento e trilha de auditoria"):
        actions = list_actions(signal_id=str(signal.signal_id))
        if not actions:
            st.caption("Nenhuma ação registrada para este sinal.")
        for action in actions:
            st.markdown(
                f"**{action['status']} · {action['owner']} · prazo {action['due_date']} · {action['priority']}**\n\n"
                f"{action['action_text']}\n\n"
                f"Observação: {action['observation'] or '—'} · Resultado: {action['result'] or '—'}"
            )
            events = list_events(action["action_id"])
            for event in events:
                changes = json.loads(event["changed_fields_json"])
                changed_labels = ", ".join(changes.keys()) or "sem mudança de campo"
                st.caption(f"{event['event_at']} UTC · {event['event_type']} · campos: {changed_labels}")
                st.json(changes, expanded=False)


def render_retention_central() -> None:
    signals = load_signals()
    st.title("Revisar sinais históricos")
    st.write("Para cada registro antigo: entenda o fato e seus limites, decida se ainda requer contato e, se sim, registre responsável, prazo e resultado.")
    st.page_link("pages/09_Operacao_CRM.py", label="Para cadastrar uma oportunidade ou registrar contato, abra Vendas e oportunidades", icon="👥")
    st.warning(f"Os dados terminam em {OBSERVATION_CUTOFF}. Eles não monitoram o estado atual. Cada regra mostra evidência e limites; evento antigo, erro, ticket ou valor inicial não comprovam cancelamento ou perda de receita.")
    open_count, overdue, total = _action_summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("Sinais para triagem", len(signals))
    c2.metric("Ações abertas", open_count)
    c3.metric("Ações fora do prazo", overdue)
    noun = "ação persistida" if total == 1 else "ações persistidas"
    st.caption(f"{total} {noun} no modo demo · ordenação: prioridade operacional explicada, data do registro (mais antiga primeiro) e ID estável.")
    with st.expander("Como as filas e prioridades são calculadas"):
        st.write("**P1:** ticket marcado urgent/escalado; ou evento Finance com refund/crédito informado e linha paga vigente — somente para verificar primeiro. **P2:** erro agregado ≥ 5 na mesma conta × feature, apenas dentro da janela da assinatura; ou evento Finance com linha paga vigente. **P3:** revisão da coorte Growth 2024 Organic × Enterprise, ou demais eventos Finance para reconciliação.")
        st.write("Não existe soma ponderada, probabilidade nem risco calculado. Cada regra mostra denominador/limiar e limitações. A ordem secundária é a data do sinal mais antiga primeiro; não é um score.")
    filters = st.columns([1, 1, 2])
    area = filters[0].selectbox("Área", ["Todas", *AREAS], key="central_area_filter")
    priority = filters[1].selectbox("Prioridade", ["Todas", *PRIORITIES], key="central_priority_filter")
    query = filters[2].text_input("Buscar conta, ID ou situação", key="central_search")
    rows = _queue_view(signals, area=None if area == "Todas" else area,
                       priority=priority, search=query)
    _render_queue(rows, scope="central")
    st.divider()
    st.subheader("Filas por área")
    links = {
        "Growth/Comercial": "pages/05_Growth_e_Comercial.py",
        "Produto": "pages/03_Produto.py",
        "CS/Suporte": "pages/04_Suporte_e_CS.py",
        "Finance/RevOps": "pages/06_Finance_RevOps.py",
    }
    cols = st.columns(4)
    for col, area_name in zip(cols, AREAS):
        with col:
            st.page_link(links[area_name], label=area_name)
            st.caption(f"{int(signals.area.eq(area_name).sum())} itens")


def render_area_queue(area: str) -> None:
    signals = load_signals()
    rows = _queue_view(signals, area=area)
    open_count, overdue, _ = _action_summary(area)
    st.subheader("Fila operacional")
    st.caption(f"Registros históricos até {OBSERVATION_CUTOFF}. Confirme o estado atual da conta em sistemas oficiais antes de uma intervenção. Selecione um item para ver evidência e registrar o acompanhamento.")
    cols = st.columns([2, 1])
    priority = cols[0].selectbox("Prioridade da fila", ["Todas", *PRIORITIES], key=f"{area}_queue_priority")
    query = cols[1].text_input("Buscar conta / situação", key=f"{area}_queue_search")
    rows = _queue_view(signals, area=area, priority=priority, search=query)
    a, b, c = st.columns(3)
    a.metric("Sinais nesta área", len(rows))
    b.metric("Ações abertas", open_count)
    c.metric("Ações fora do prazo", overdue)
    _render_queue(rows, scope=area.replace("/", "_").replace(" ", "_"))
    actions = actions_frame(list_actions(area=area))
    with st.expander("Ações registradas nesta fila"):
        if actions.empty:
            st.caption("Ainda não há ações registradas.")
        else:
            st.dataframe(actions, hide_index=True, width="stretch")
            st.download_button("Baixar ações da área em CSV", actions.to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"acoes_{area.lower().replace('/', '_').replace(' ', '_')}.csv",
                               mime="text/csv", key=f"download_actions_{area}")


def _render_queue(rows: pd.DataFrame, scope: str) -> None:
    if rows.empty:
        st.info("Nenhum sinal nesta combinação de filtros.")
        return
    requested_signal = st.session_state.pop("requested_signal_id", None)
    st.caption(f"{len(rows)} sinais · a tabela não é uma classificação de churn confirmado.")
    page_size = 25
    page_count = max(1, (len(rows) + page_size - 1) // page_size)
    page_key = f"queue_page_{scope}"
    if requested_signal and rows.signal_id.astype(str).eq(str(requested_signal)).any():
        requested_position = int(rows.index[rows.signal_id.astype(str).eq(str(requested_signal))][0])
        st.session_state[page_key] = requested_position // page_size + 1
    current_page = min(max(int(st.session_state.get(page_key, 1)), 1), page_count)
    st.session_state[page_key] = current_page
    page = st.number_input("Página da fila", min_value=1, max_value=page_count,
                           step=1, key=page_key)
    start = (int(page) - 1) * page_size
    page_rows = rows.iloc[start:start + page_size]
    st.caption(f"Exibindo {start + 1}–{start + len(page_rows)} de {len(rows)} sinais ordenados.")
    shown = page_rows[["priority", "area", "account_name", "account_id", "title", "signal_date", "evidence_summary"]].rename(columns={
        "priority": "Prioridade", "area": "Área", "account_name": "Conta", "account_id": "ID", "title": "Situação", "signal_date": "Data", "evidence_summary": "Evidência curta",
    })
    st.dataframe(shown, hide_index=True, width="stretch")
    labels = [_signal_label(row) for _, row in page_rows.iterrows()]
    signal_key = f"signal_choice_{scope}"
    if requested_signal:
        target = page_rows[page_rows.signal_id.astype(str).eq(str(requested_signal))]
        if not target.empty:
            st.session_state[signal_key] = _signal_label(target.iloc[0])
    selected_label = st.selectbox("Conta/situação para decidir", labels, key=signal_key)
    signal = page_rows.iloc[labels.index(selected_label)]
    with st.container(border=True):
        _show_detail(signal, scope)


def render_account_operations(account_id: str) -> None:
    signals = load_signals()
    rows = signals[signals.account_id.eq(account_id)].copy()
    st.subheader("Sinais e ações desta conta")
    if rows.empty:
        st.info("Nenhum sinal determinístico desta versão está associado à conta. Isso não equivale a risco zero nem a ausência de problema.")
        actions = actions_frame(list_actions())
        if not actions.empty:
            account_actions = actions[actions.account_id.eq(account_id)]
            if not account_actions.empty:
                st.dataframe(account_actions, hide_index=True, width="stretch")
        return
    st.caption(f"{len(rows)} sinal(is) baseado(s) em regra explícita. Cada item conserva evidência, incerteza e próxima ação.")
    st.dataframe(rows[["priority", "area", "signal_date", "title", "evidence_summary"]].rename(columns={
        "priority": "Prioridade", "area": "Área", "signal_date": "Data", "title": "Situação", "evidence_summary": "Evidência curta",
    }), hide_index=True, width="stretch")
    labels = [_signal_label(row) for _, row in rows.iterrows()]
    choice = st.selectbox("Sinal desta conta", labels, key=f"account_signal_{account_id}")
    _show_detail(rows.iloc[labels.index(choice)], f"account_{account_id}")
