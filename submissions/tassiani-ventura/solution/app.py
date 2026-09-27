from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import streamlit as st
from src.ui import CSS
from src.data_access import ensure_database
from src.operating_store import initialize_store

st.set_page_config(page_title='RavenStack | Jornada do cliente', page_icon='🧭', layout='wide')
st.markdown(CSS, unsafe_allow_html=True)
try:
    with st.spinner('Preparando as cinco bases…'):
        ensure_database()
        initialize_store()
except Exception as exc:
    st.error('Não foi possível preparar o app ou conectar ao armazenamento configurado. Confira data/raw, DATABASE_URL e o schema do banco.')
    with st.expander('Detalhe para manutenção'): st.code(str(exc))
    st.stop()

page=st.navigation({
    'Trabalhar': [st.Page('pages/00_Meu_Trabalho.py', title='Meu trabalho', default=True),
                            st.Page('pages/10_Clientes.py', title='Clientes'),
                            st.Page('pages/01_Conta_360.py', title='Cliente 360'),
                            st.Page('pages/11_Tarefas_Alertas.py', title='Tarefas & alertas'),
                            st.Page('pages/09_Operacao_CRM.py', title='Comercial · pipeline'),
                            st.Page('pages/12_Inteligencia.py', title='Inteligência'),
                            st.Page('pages/13_Gestao.py', title='Gestão')],
    'Investigar (secundário)': [st.Page('pages/08_Central_de_Retencao.py', title='Central de Retenção histórica'),
                            st.Page('pages/00_Visao_Executiva.py', title='Visão executiva'),
                            st.Page('pages/14_Conta_360_Historica.py', title='Conta 360 histórica')],
    'Análises por área': [st.Page('pages/05_Growth_e_Comercial.py', title='Growth e Comercial'),
                         st.Page('pages/03_Produto.py', title='Produto'),
                         st.Page('pages/04_Suporte_e_CS.py', title='Suporte e CS'),
                         st.Page('pages/06_Finance_RevOps.py', title='Finance e RevOps')],
    'Modelo e qualidade': [st.Page('pages/02_Jornada_e_Areas.py', title='Jornada e áreas'),
                          st.Page('pages/07_Dados_e_Arquitetura.py', title='Dados e arquitetura')],
})
page.run()
