import pandas as pd
import streamlit as st
from src.ui import setup_page
from src.data_access import load_table
from src.analytics import fmt_money
from src.explore import account_filters, table, CONTEXTS
from src.retention_ui import render_account_operations

setup_page(st,'Conta 360')
st.title('Conta 360')
st.write('Reconstrua a jornada e confira o contexto de cada registro.')
a=load_table('account_360').sort_values(['account_name','account_id'])
requested=st.session_state.pop('requested_account_id',None)
if requested:
    st.session_state.pop('account_origins',None); st.session_state.pop('account_plans',None)
    st.session_state['account_choice']=requested
filtered=account_filters(a,'account')
if filtered.empty: st.info('A combinação de filtros não contém contas.'); st.stop()
names=filtered.set_index('account_id').account_name.to_dict()
if st.session_state.get('account_choice') not in names: st.session_state['account_choice']=filtered.account_id.iloc[0]
aid=st.selectbox('Conta', filtered.account_id.tolist(), format_func=lambda x:f'{names[x]} · {x}', key='account_choice')
r=a.set_index('account_id').loc[aid]
st.caption(f"{r.industry} · {r.country} · cadastro em {r.signup_date:%d/%m/%Y} · origem {r.referral_source}")
c1,c2,c3=st.columns(3)
c1.metric('Valor inicial registrado',fmt_money(r.initial_value_registered))
c2.metric('Usos na janela da assinatura',int(r.valid_usage_count))
c3.metric('Eventos legados',int(r.recorded_lifecycle_events))
st.caption('Valor inicial não é MRR atual. Ausência de uso válido significa ausência no recorte observável, não inatividade comprovada.')
if pd.notna(r.recorded_event_within_90d) and bool(r.recorded_event_within_90d):
    st.warning('Há evento legado nos primeiros 90 dias. Confira abaixo o contexto pago antes de concluir perda.')
elif not r.eligible_90d:
    st.info('Esta conta não possui 90 dias completos até o corte de observação; fica fora da incidência de 90 dias.')
rows=[dict(date=r.signup_date,type='Cadastro',detail='Entrada da conta',validity='Registro de origem',source_id=aid)]
for _,x in load_table('subscriptions').query('account_id == @aid').iterrows():
    rows.append(dict(date=x.start_date,type='Assinatura',detail=f"Início · {x.plan_tier} · {x.seats} licenças · MRR {fmt_money(x.mrr_amount)} · {'trial' if x.is_trial else 'não trial'}",validity='Linha contratual',source_id=x.subscription_id))
    if pd.notna(x.end_date): rows.append(dict(date=x.end_date,type='Assinatura',detail=f'Encerramento de linha · {x.plan_tier}',validity='Não confirma perda da conta',source_id=x.subscription_id))
for _,x in load_table('customer_interactions').query('account_id == @aid').iterrows():
    rows.append(dict(date=x.occurred_at,type='Atendimento',detail=f"Suporte · prioridade {x.priority}",validity='Pós-cadastro' if x.lifecycle_temporal_status=='on_or_after_signup' else 'Antes do cadastro',source_id=x.interaction_id))
for _,x in load_table('lifecycle_events').query('account_id == @aid').iterrows():
    rows.append(dict(date=x.event_date,type='Evento legado',detail=f'{x.reason_code} · {CONTEXTS.get(x.paid_context_at_event,x.paid_context_at_event)}',validity='Impacto econômico não reconciliado',source_id=x.event_id))
for _,x in load_table('feature_usage').query('account_id == @aid').iterrows():
    rows.append(dict(date=x.usage_date,type='Produto',detail=f'{x.feature_name} · {x.usage_count} usos · {x.error_count} erros',validity='Dentro da assinatura' if x.temporal_status=='within_subscription' else 'Fora da janela / desconhecido',source_id=x.usage_event_id))
timeline=pd.DataFrame(rows).sort_values(['date','source_id'],ascending=[False,True])
st.subheader('Jornada observada')
kind=st.multiselect('Tipos de registro', ['Cadastro','Assinatura','Evento legado','Atendimento','Produto'], default=['Cadastro','Assinatura','Evento legado'])
show_anomalies=st.checkbox('Incluir uso fora da janela e atendimento anterior ao cadastro',value=False)
view=timeline[timeline.type.isin(kind)]
if not show_anomalies: view=view[~view.validity.isin(['Antes do cadastro','Fora da janela / desconhecido'])]
st.caption(f'{len(view)} de {len(timeline)} registros · mais recentes primeiro')
table(view,'jornada_'+aid+'.csv')
with st.expander('Resumo de uso e atendimento'):
    st.write(f'{int(r.valid_features_used)} funcionalidades com uso na janela · {int(r.valid_errors)} erros registrados · {int(r.valid_interactions)} atendimentos pós-cadastro.')
    st.write('Owner e próxima ação não existem no histórico de origem. O registro criado aqui fica no SQLite local de demonstração; não atualiza CRM, billing ou helpdesk.')
st.divider()
render_account_operations(aid)
