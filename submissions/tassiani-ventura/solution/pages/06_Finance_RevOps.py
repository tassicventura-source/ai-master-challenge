import streamlit as st
import plotly.express as px
from src.ui import setup_page
from src.data_access import load_table
from src.analytics import fmt_money
from src.explore import account_filters, table, open_account, CONTEXTS, display_frame
from src.retention_ui import render_area_queue

setup_page(st,'Finance e RevOps')
st.title('Finance e RevOps')
st.write('Confira quais eventos precisam de confirmação contratual e econômica.')
render_area_queue('Finance/RevOps')
st.divider()
a=account_filters(load_table('account_360'),'finance')
life=load_table('lifecycle_events'); life=life[life.account_id.isin(a.account_id)]
c1,c2,c3=st.columns(3)
c1.metric('Eventos não reconciliados',len(life));c2.metric('Contas afetadas',life.account_id.nunique());c3.metric('Reembolsos registrados',fmt_money(life.refund_amount_usd.sum(), 2))
st.caption('Registros de reembolso não comprovam liquidação em caixa. Linha encerrada, flag de reativação e evento legado não confirmam perda, renovação ou retorno do cliente.')
ctx=life.groupby('paid_context_at_event').size().reset_index(name='events')
if not ctx.empty:
    fig=px.bar(display_frame(ctx),x='Registros',y='Contexto pago na data',orientation='h',text='Registros',color_discrete_sequence=['#176BCE'])
    fig.update_layout(yaxis_title=None)
    fig.update_layout(height=340, margin=dict(t=20, b=30))
    st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
st.subheader('Fila de investigação')
context=st.selectbox('Contexto pago',['Todos']+list(CONTEXTS),format_func=lambda v:CONTEXTS.get(v,v))
v=life if context=='Todos' else life[life.paid_context_at_event.eq(context)]
refund_only=st.checkbox('Somente eventos com reembolso')
if refund_only:v=v[v.refund_amount_usd.gt(0)]
v=v.merge(a[['account_id','account_name']],on='account_id',validate='many_to_one').sort_values(['refund_amount_usd','event_date'],ascending=False)
table(v[['event_id','account_id','account_name','event_date','paid_context_at_event','reason_code','refund_amount_usd','next_paid_start_date']],'finance_eventos.csv')
open_account(v[['account_id','account_name']].drop_duplicates(),'finance_account')
st.info('Responsável sugerido: Finance/RevOps, com Comercial. Para cada evento, confirmar contrato, movimento e MRR antes/depois nos registros de origem. A ação e seu acompanhamento são persistidos em modo demo; a conciliação econômica continua pendente nos sistemas de origem.')
with st.expander('Critério de classificação'):
    st.write('Linha paga: não trial e MRR positivo. Vigência: início ≤ evento ≤ fim, incluindo limites; fim vazio é aberto no histórico. Contexto pago não equivale a pagamento liquidado. Tipo canônico e impacto econômico permanecem vazios até confirmação.')
