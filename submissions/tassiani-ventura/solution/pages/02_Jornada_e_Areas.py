import streamlit as st
import pandas as pd
from src.ui import setup_page, callout, ROOT

setup_page(st, "Jornada e áreas", "🔁")
st.title("Fluxo da jornada do cliente")
st.write("A operação continua nos sistemas atuais. A mudança é de campos, nomenclatura e regras para que as cinco bases reconstruam a mesma jornada.")

img = ROOT / "assets" / "jornada_cliente.png"
if img.exists():
    with st.expander("Ver mapa completo da jornada"):
        st.image(str(img), width="stretch")

callout(st, "<b>Fluxo:</b> Atrair → Converter → Ativar → Usar → Suportar → Acompanhar → Evoluir. Cada etapa grava dados nos sistemas já usados pela área; as cinco bases passam a compartilhar chaves e conceitos.", "good")

st.subheader("Responsabilidade por etapa")
data = [
    ["Growth/Marketing","Atrair","Origem detalhada, campanha/conteúdo/parceiro","accounts"],
    ["Comercial","Converter","Qualificação, oportunidade, valor, motivo de ganho/perda","customer_interactions + lifecycle_events"],
    ["Onboarding/CS","Ativar","Objetivo, marcos de ativação, bloqueios, próxima ação","customer_interactions"],
    ["Produto","Usar","Feature, usuário, ação, sucesso/erro, contexto","feature_usage"],
    ["Suporte","Suportar","Tema, feature, impacto, causa, recorrência, resolução","customer_interactions"],
    ["CS","Acompanhar","Risco, oportunidade, plano de ação e resultado","customer_interactions"],
    ["Comercial/CS/Finance","Evoluir","Renovação, expansão, contração, cancelamento, reativação","subscriptions + lifecycle_events"],
]
st.dataframe(pd.DataFrame(data, columns=["Área", "Etapa", "Registra", "Base"]), width="stretch", hide_index=True)
