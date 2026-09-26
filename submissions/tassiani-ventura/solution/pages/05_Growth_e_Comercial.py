import streamlit as st
import plotly.express as px
from src.ui import setup_page
from src.data_access import load_table
from src.analytics import growth_by_source
from src.explore import account_filters, table, open_account, LABELS

setup_page(st,'Growth e Comercial')
st.title('Growth e Comercial')
st.write('Compare volume, valor de entrada e eventos precoces por origem.')
a=account_filters(load_table('account_360'),'growth')
if a.empty: st.info('Ajuste os filtros para continuar.'); st.stop()
g=growth_by_source(a)
metric=st.radio('Comparar por',['Valor inicial','Novas contas','Eventos em 90 dias'],horizontal=True)
col={'Valor inicial':'initial_value','Novas contas':'accounts','Eventos em 90 dias':'recorded_event_90d'}[metric]
g['signup_year']=g.signup_year.astype(str)
fig=px.bar(g,x='referral_source',y=col,color='signup_year',barmode='group',labels=LABELS,
           color_discrete_sequence=['#9AAAC1','#176BCE'])
if col=='recorded_event_90d': fig.update_yaxes(tickformat='.0%')
fig.update_layout(height=340, margin=dict(t=20, b=30))
st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
st.caption('Janela de 90 dias completa até 31/12/2024. Evento legado não é churn confirmado. Valor inicial soma o MRR na primeira data paga; não é faturamento ou MRR atual.')
with st.expander('Ver valores e denominadores',expanded=True): table(g,'growth_por_origem.csv')
st.subheader('Do canal à conta')
show=a[['account_id','account_name','referral_source','first_paid_plan','initial_value_registered','recorded_lifecycle_events']].sort_values('initial_value_registered',ascending=False)
open_account(show,'growth_account')
with st.expander('Contas deste recorte'): table(show,'growth_contas.csv')
