import streamlit as st
import plotly.express as px
from src.ui import setup_page
from src.data_access import load_table
from src.explore import account_filters, table, open_account, LABELS
from src.retention_ui import render_area_queue

setup_page(st,'Produto')
st.title('Produto')
st.write('Localize funcionalidades com erros e investigue as contas afetadas.')
render_area_queue('Produto')
st.divider()
a=account_filters(load_table('account_360'),'product')
u=load_table('feature_usage'); u=u[u.account_id.isin(a.account_id)]
uv=u[u.temporal_status.eq('within_subscription')]
c1,c2,c3=st.columns(3)
c1.metric('Registros na janela',len(uv)); c2.metric('Contas com uso na janela',uv.account_id.nunique()); c3.metric('Erros registrados',int(uv.error_count.sum()))
st.caption(f'{len(u)-len(uv)} registros fora da janela da assinatura ou com contexto desconhecido ficam fora desta análise. Erros / 100 usos é uma razão agregada, não uma taxa de falha por usuário.')
feat=uv.groupby('feature_name').agg(events=('usage_event_id','size'),usage=('usage_count','sum'),errors=('error_count','sum'),accounts=('account_id','nunique')).reset_index()
feat['errors_per_100_usage']=feat.errors.div(feat.usage.where(feat.usage.ne(0)))*100
if not feat.empty:
    fig=px.scatter(feat,x='usage',y='errors_per_100_usage',size='accounts',hover_name='feature_name',labels=LABELS,color_discrete_sequence=['#176BCE'])
    fig.update_layout(height=340, margin=dict(t=20, b=30))
    st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})
with st.expander('Ver todas as funcionalidades'): table(feat,'produto_funcionalidades.csv')
feature=st.selectbox('Investigar funcionalidade',['Todas']+feat.feature_name.sort_values().tolist())
selected=uv if feature=='Todas' else uv[uv.feature_name.eq(feature)]
selected=selected.groupby('account_id').agg(usage=('usage_count','sum'),errors=('error_count','sum')).reset_index()
accounts=selected.merge(a[['account_id','account_name','initial_value_registered']],on='account_id',validate='one_to_one').sort_values('errors',ascending=False)
st.subheader('Contas com uso no recorte')
open_account(accounts,'product_account')
table(accounts,'produto_contas.csv')
st.caption('Responsável sugerido: Produto. Inspecionar contas e registros com erros; validar o mecanismo antes de atribuir qualquer perda ao produto.')
