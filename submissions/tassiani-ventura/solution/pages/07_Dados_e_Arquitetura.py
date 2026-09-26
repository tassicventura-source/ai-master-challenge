import streamlit as st
import pandas as pd
from pathlib import Path

from src.ui import setup_page, callout, ROOT
from src.data_access import load_table
from src.schemas import SCHEMA_CHANGES, NEW_FIELDS

setup_page(st, "Dados & Arquitetura", "🛠️")
st.title("Dados & Arquitetura")
st.write("Esta é a tela para explicar ao CEO e ao time técnico exatamente o que acontece com as cinco bases: o que fica, o que sai do canônico, o que é corrigido e o que começa a ser capturado daqui para frente.")

img = ROOT / "assets" / "arquitetura_tecnica.png"
if img.exists():
    with st.expander("Ver arquitetura técnica"):
        st.image(str(img), width="stretch")

st.subheader("As cinco bases: hoje → proposta")
summary = [
    ["accounts","accounts","Cadastro mestre da conta","Retira plan/seats/trial/churn como verdade da conta; adiciona origem detalhada, ICP, owner e estágio."],
    ["subscriptions","subscriptions","Contrato/assinatura no grão da linha","Retira flags sem timestamp; adiciona contract_id e movimento efetivo."],
    ["feature_usage","feature_usage","Comportamento no produto","Cria ID canônico, account_id, temporal_status e campos de usuário/ação/sucesso."],
    ["support_tickets","customer_interactions","Interações com o cliente","Preserva SLA/CSAT e adiciona área, tipo, tema, feature, impacto, causa, resultado e próxima ação."],
    ["churn_events","lifecycle_events","Eventos da jornada","Evento legado deixa de ser perda automática; adiciona tipo canônico e MRR/seats/plano antes e depois."],
]
st.dataframe(pd.DataFrame(summary, columns=["Base atual", "Base nova", "Função", "Mudança principal"]), hide_index=True, width="stretch")

st.subheader("Mapa campo a campo")
changes = pd.DataFrame(SCHEMA_CHANGES)
base = st.selectbox("Filtrar base", ["Todas"] + sorted(changes["base_atual"].unique().tolist()))
show = changes if base == "Todas" else changes[changes["base_atual"] == base]
st.dataframe(show, hide_index=True, width="stretch")

st.subheader("Novos campos mínimos a capturar nos sistemas atuais")
newf = pd.DataFrame(NEW_FIELDS)
area = st.selectbox("Área", ["Todas"] + sorted(newf["area"].unique().tolist()))
showf = newf if area == "Todas" else newf[newf["area"] == area]
st.dataframe(showf, hide_index=True, width="stretch")

st.subheader("Qualidade atual que o pipeline deixa explícita")
q = load_table("data_quality_summary")
q["percent"] = q["count"] / q["denominator"]
st.dataframe(q.style.format({"percent":"{:.1%}"}), hide_index=True, width="stretch")

callout(st, "Nenhuma informação ausente foi inventada. Campos novos aparecem com cobertura zero no histórico e passam a ser preenchidos quando os sistemas atuais forem configurados para capturá-los.", "good")

st.subheader("Arquivos processados gerados")
for f in sorted((ROOT / "data" / "processed").glob("*.csv")):
    st.write(f"- `{f.relative_to(ROOT)}`")
