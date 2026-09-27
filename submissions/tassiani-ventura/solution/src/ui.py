from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CSS = """
<style>
:root{--navy:#0B2545;--blue:#176BCE;--teal:#0C8A7B;--orange:#E76F2E;--paper:#ffffff;--bg:#F5F7FA;--ink:#162033;--muted:#667085;--line:#E4E7EC;}
.stApp{background:var(--bg);color:var(--ink)}
.block-container{max-width:1120px;padding-top:2rem;padding-bottom:4rem}
h1,h2,h3{color:var(--navy)}
[data-testid="stMetric"]{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.rs-card{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;margin:8px 0 16px 0}
.rs-callout{background:#EEF4FF;border-left:4px solid var(--blue);border-radius:10px;padding:14px 16px;margin:10px 0 18px 0}
.rs-warning{background:#FFF7ED;border-left:4px solid var(--orange);border-radius:10px;padding:14px 16px;margin:10px 0 18px 0}
.rs-good{background:#ECFDF3;border-left:4px solid var(--teal);border-radius:10px;padding:14px 16px;margin:10px 0 18px 0}
.small-muted{color:var(--muted);font-size:.95rem}
</style>
"""


def setup_page(st, title: str, icon: str = "📊"):
    st.markdown(CSS, unsafe_allow_html=True)
    st.caption("RavenStack · painel operacional para acompanhar clientes, tarefas e resultados")


def callout(st, text: str, kind: str = "info"):
    cls = {"info":"rs-callout","warning":"rs-warning","good":"rs-good"}.get(kind,"rs-callout")
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)
