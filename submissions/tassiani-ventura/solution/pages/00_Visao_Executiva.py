import streamlit as st
from src.ui import setup_page
from src.data_access import load_table
from src.analytics import fmt_money, growth_by_source
from src.explore import table

setup_page(st, 'Visão executiva')
st.title('O que exige atenção agora')
st.write('Conecte o sinal do negócio à conta e à evidência que sustenta a decisão.')
a=load_table('account_360'); life=load_table('lifecycle_events')
active=life.paid_context_at_event.eq('paid_line_active').sum()
c1,c2,c3=st.columns(3)
c1.metric('Contas na base', len(a))
c2.metric('Eventos a reconciliar', len(life))
c3.metric('Reembolsos registrados', fmt_money(life.refund_amount_usd.sum(), 2))
st.subheader(f'{active} de {len(life)} eventos coexistem com linha paga vigente')
st.write('O registro legado de churn não permite concluir que houve perda de cliente ou receita. Finance/RevOps precisa confirmar o contrato e o movimento econômico de cada evento.')
st.page_link('pages/06_Finance_RevOps.py', label='Examinar os eventos e suas contas →')
st.divider()
st.subheader('O crescimento mudou de qualidade?')
g=growth_by_source(a)
annual=a.assign(ano=a.signup_date.dt.year).groupby('ano').agg(contas=('account_id','size'),valor=('initial_value_registered','sum'),elegiveis=('eligible_90d','sum'),eventos=('recorded_event_within_90d','sum'),incidencia=('recorded_event_within_90d','mean'))
for year,r in annual.iterrows():
    st.write(f"**{year}:** {int(r.contas)} cadastros · {fmt_money(r.valor)} de valor inicial · {int(r.eventos)}/{int(r.elegiveis)} contas com evento nos primeiros 90 dias ({r.incidencia:.1%}).")
st.caption('Valor inicial = soma do MRR das linhas não trial e positivas na primeira data paga. Não representa faturamento, caixa ou MRR atual. Eventos em 90 dias usam somente contas com janela completa.')
st.page_link('pages/05_Growth_e_Comercial.py', label='Comparar origens e investigar contas →')
with st.expander('Como interpretar os números'):
    st.write('Corte de observação: 31/12/2024, última data de evento registrada. A completude até essa data é uma premissa de análise do dataset. Reembolsos são valores informados na fonte, sem conciliação bancária. As bases são sintéticas; associações não demonstram causas.')
    st.page_link('pages/07_Dados_e_Arquitetura.py',label='Ver qualidade e definições')
