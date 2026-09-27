import pandas as pd
import streamlit as st

from src.action_store import list_crm_accounts
from src.analytics import fmt_money
from src.crm_ui import render_account_crm
from src.data_access import load_table
from src.explore import CONTEXTS, account_filters, table
from src.retention_ui import render_account_operations
from src.ui import setup_page

setup_page(st, "Conta 360")
st.title("Conta 360")
st.write("Histórico observado, dados operacionais, atividades e próximos passos da conta.")
accounts = load_table("account_360").sort_values(["account_name", "account_id"])
crm_accounts = list_crm_accounts()
crm_by_id = {row["account_id"]: row for row in crm_accounts}
requested = st.session_state.pop("requested_account_id", None)
if requested:
    st.session_state.pop("account_origins", None)
    st.session_state.pop("account_plans", None)
    st.session_state["account_choice"] = requested

filtered = account_filters(accounts, "account")
if filtered.empty and not crm_accounts:
    st.info("A combinação de filtros não contém contas. Cadastre um lead/cliente na página CRM e operação comercial para começar.")
    st.stop()
if filtered.empty and crm_accounts:
    st.info("Os filtros excluíram o histórico observado; abaixo também estão disponíveis as contas cadastradas no CRM operacional.")

historical_names = filtered.set_index("account_id").account_name.to_dict()
visible_history = set(filtered.account_id)
crm_not_in_filter = [row for row in crm_accounts if row["account_id"] not in visible_history]
choice_names = historical_names | {row["account_id"]: row["account_name"] for row in crm_not_in_filter}
choices = list(filtered.account_id) + [row["account_id"] for row in crm_not_in_filter]
if st.session_state.get("account_choice") not in choice_names:
    st.session_state["account_choice"] = choices[0]
aid = st.selectbox("Conta / lead", choices,
                   format_func=lambda x: f"{choice_names[x]} · {x}", key="account_choice")
crm = crm_by_id.get(aid)

if aid in set(accounts.account_id):
    r = accounts.set_index("account_id").loc[aid]
    st.caption(f"{r.industry} · {r.country} · cadastro observado em {r.signup_date:%d/%m/%Y} · origem histórica {r.referral_source}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Valor inicial registrado", fmt_money(r.initial_value_registered))
    c2.metric("Usos na janela da assinatura", int(r.valid_usage_count))
    c3.metric("Eventos legados", int(r.recorded_lifecycle_events))
    st.caption("Valor inicial não é MRR atual. Ausência de uso válido significa ausência no recorte observável, não inatividade comprovada.")
    if pd.notna(r.recorded_event_within_90d) and bool(r.recorded_event_within_90d):
        st.warning("Há evento legado nos primeiros 90 dias. Confira abaixo o contexto pago antes de concluir perda.")
    elif not r.eligible_90d:
        st.info("Esta conta não possui 90 dias completos até o corte de observação; fica fora da incidência de 90 dias.")
    rows = [dict(date=r.signup_date, type="Cadastro histórico", detail="Entrada da conta", validity="Registro de origem", source_id=aid)]
    for _, x in load_table("subscriptions").query("account_id == @aid").iterrows():
        rows.append(dict(date=x.start_date, type="Assinatura", detail=f"Início · {x.plan_tier} · {x.seats} licenças · MRR {fmt_money(x.mrr_amount)} · {'trial' if x.is_trial else 'não trial'}", validity="Linha contratual", source_id=x.subscription_id))
        if pd.notna(x.end_date):
            rows.append(dict(date=x.end_date, type="Assinatura", detail=f"Encerramento de linha · {x.plan_tier}", validity="Não confirma perda da conta", source_id=x.subscription_id))
    for _, x in load_table("customer_interactions").query("account_id == @aid").iterrows():
        rows.append(dict(date=x.occurred_at, type="Atendimento histórico", detail=f"Suporte · prioridade {x.priority}", validity="Pós-cadastro" if x.lifecycle_temporal_status == "on_or_after_signup" else "Antes do cadastro", source_id=x.interaction_id))
    for _, x in load_table("lifecycle_events").query("account_id == @aid").iterrows():
        rows.append(dict(date=x.event_date, type="Evento legado", detail=f"{x.reason_code} · {CONTEXTS.get(x.paid_context_at_event, x.paid_context_at_event)}", validity="Impacto econômico não reconciliado", source_id=x.event_id))
    for _, x in load_table("feature_usage").query("account_id == @aid").iterrows():
        rows.append(dict(date=x.usage_date, type="Produto", detail=f"{x.feature_name} · {x.usage_count} usos · {x.error_count} erros", validity="Dentro da assinatura" if x.temporal_status == "within_subscription" else "Fora da janela / desconhecido", source_id=x.usage_event_id))
    timeline = pd.DataFrame(rows).sort_values(["date", "source_id"], ascending=[False, True])
    st.subheader("Jornada observada no dataset (até 2024-12-31)")
    kind = st.multiselect("Tipos de registro", ["Cadastro histórico", "Assinatura", "Evento legado", "Atendimento histórico", "Produto"], default=["Cadastro histórico", "Assinatura", "Evento legado"])
    show_anomalies = st.checkbox("Incluir uso fora da janela e atendimento anterior ao cadastro", value=False)
    view = timeline[timeline.type.isin(kind)]
    if not show_anomalies:
        view = view[~view.validity.isin(["Antes do cadastro", "Fora da janela / desconhecido"])]
    st.caption(f"{len(view)} de {len(timeline)} registros · mais recentes primeiro")
    table(view, "jornada_" + aid + ".csv")
    with st.expander("Resumo de uso e atendimento observados"):
        st.write(f"{int(r.valid_features_used)} funcionalidades com uso na janela · {int(r.valid_errors)} erros registrados · {int(r.valid_interactions)} atendimentos pós-cadastro.")
        st.write("Owner e próxima ação não existem no histórico de origem. Novos registros ficam na camada operacional e não atualizam CRM/billing/helpdesk externo.")
else:
    st.info("Lead/cliente cadastrado no CRM operacional, sem histórico correspondente nas bases analíticas fornecidas. Não há métricas históricas para exibir.")
    if crm:
        st.dataframe(pd.DataFrame([{
            "ID": crm["account_id"], "Origem": crm["record_origin"], "Setor": crm["industry"] or "—",
            "País": crm["country"] or "—", "Canal": crm["referral_source"] or "—",
        }]), hide_index=True, width="stretch")

st.divider()
render_account_crm(aid)
st.divider()
render_account_operations(aid)
