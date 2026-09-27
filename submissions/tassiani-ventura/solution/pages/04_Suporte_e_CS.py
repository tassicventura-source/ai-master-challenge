import streamlit as st
from src.ui import setup_page
from src.data_access import load_table
from src.analytics import support_priority_summary
from src.explore import account_filters, table, open_account
from src.retention_ui import render_area_queue

setup_page(st,'Suporte e CS')
st.title('Suporte e CS')
st.write('Observe a carga de atendimento e aprofunde a jornada das contas.')
render_area_queue('CS/Suporte')
st.divider()
a=account_filters(load_table('account_360'),'support')
x=load_table('customer_interactions'); x=x[x.account_id.isin(a.account_id)]
valid=x[x.lifecycle_temporal_status.eq('on_or_after_signup')]
c1,c2,c3=st.columns(3)
c1.metric('Atendimentos pós-cadastro',len(valid)); c2.metric('Escalados',int(valid.escalation_flag.sum()))
c3.metric('Satisfação respondida', f'{valid.satisfaction_score.notna().mean():.1%}' if len(valid) else '—')
st.caption(f'{len(x)-len(valid)} atendimentos anteriores ao cadastro ou sem contexto válido ficam fora da análise. O histórico contém somente tickets de suporte; não há contatos de CS registrados.')
st.subheader('Atendimento por prioridade')
table(support_priority_summary(x),'suporte_prioridades.csv')
priority=st.selectbox('Prioridade',['Todas']+sorted(valid.priority.dropna().unique().tolist()))
v=valid if priority=='Todas' else valid[valid.priority.eq(priority)]
escalated=st.checkbox('Somente atendimentos escalados')
if escalated: v=v[v.escalation_flag.eq(1)]
accounts=v.groupby('account_id').agg(interactions=('interaction_id','size')).reset_index().merge(a[['account_id','account_name','initial_value_registered']],on='account_id',validate='one_to_one').sort_values('interactions',ascending=False)
st.subheader('Contas atendidas')
open_account(accounts,'support_account')
table(accounts,'suporte_contas.csv')
with st.expander('O que ainda falta para orientar CS'):
    st.write('Tema, causa e impacto não existem no histórico de tickets; CS também não tem contatos de origem registrados. A tarefa e o resultado informado podem ser acompanhados no SQLite demo, sem substituir a captura desses campos nos sistemas oficiais. Satisfação representa apenas quem respondeu.')
