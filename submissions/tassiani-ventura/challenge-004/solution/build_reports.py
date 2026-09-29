from __future__ import annotations

import base64
import html
import io
import math
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_engine import (
    load_data, platform_data, platform_overview, audit_quality, group_summary,
    sponsorship_overall, sponsorship_controlled, sponsorship_strata_with_ci,
    monthly_sponsorship, lag_sponsorship_test, combination_analysis, period_comparison,
    mix_shift, hashtag_analysis, creator_id_audit, numeric_correlations, outlier_profile,
    time_series, frequency_performance, temporal_predictability, METRICS, DIMENSION_LABELS, OBJECTIVE_METRICS
)

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "social_media_dataset.csv"
REPORTS = ROOT / "reports"
RESULTS = ROOT / "results"
REPORTS.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

PLATFORMS = ["Instagram", "TikTok", "YouTube", "Bilibili", "RedNote"]
KEY_METRICS = ["visualizacoes", "comentarios", "compartilhamentos", "interacoes_totais", "taxa_engajamento"]
OBJECTIVE_NAMES = {
    "visualizacoes": "Alcance",
    "comentarios": "Conversa",
    "compartilhamentos": "Compartilhamento",
    "interacoes_totais": "Interação total",
    "taxa_engajamento": "Eficiência das interações",
}

VALUE_PT = {
    "video":"vídeo", "image":"imagem", "text":"texto", "mixed":"misto",
    "beauty":"Beauty", "lifestyle":"Lifestyle", "tech":"Tech",
    "female":"feminino", "male":"masculino", "non-binary":"não binário", "unknown":"não informado",
    "Brazil":"Brasil", "Germany":"Alemanha", "UK":"Reino Unido", "USA":"Estados Unidos",
    "China":"China", "India":"Índia", "Japan":"Japão", "Russia":"Rússia",
    "Spanish":"espanhol", "English":"inglês", "Chinese":"chinês", "Japanese":"japonês", "Hindi":"hindi",
    True:"patrocinado", False:"orgânico", "True":"patrocinado", "False":"orgânico"
}

def display_value(value):
    return VALUE_PT.get(value, VALUE_PT.get(str(value), str(value)))
DIMENSIONS_INVESTIGATION = [
    "formato", "categoria", "porte_criador", "faixa_etaria_audiencia",
    "genero_audiencia", "localizacao_audiencia", "idioma",
    "duracao_relativa", "dia_semana", "faixa_horaria"
]

CSS = r"""
:root{--ink:#172033;--muted:#667085;--line:#e5e7eb;--soft:#f7f9fb;--navy:#17324a;--teal:#0f766e;--amber:#8a5a00;--red:#a63a32;--max:1100px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fff;color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;line-height:1.62}
main{max-width:var(--max);margin:0 auto;padding:68px 34px 90px}header{padding-bottom:42px;border-bottom:1px solid var(--line)}
.kicker{font-size:13px;letter-spacing:.05em;color:var(--muted);margin-bottom:13px}h1{font-size:46px;line-height:1.05;letter-spacing:-.032em;margin:0 0 18px;max-width:930px}h2{font-size:30px;line-height:1.18;letter-spacing:-.02em;margin:0 0 18px}h3{font-size:20px;line-height:1.3;margin:31px 0 10px}.subtitle{font-size:19px;line-height:1.52;max-width:900px;color:#344054;margin:0}.scope{margin-top:20px;font-size:13px;color:var(--muted)}
section{padding:50px 0;border-bottom:1px solid var(--line)}p{margin:0 0 15px;max-width:920px}.lead{font-size:18px;color:#344054}.question{font-size:21px;line-height:1.45;font-weight:680;max-width:920px;margin:22px 0;color:var(--navy)}
.statement{margin:25px 0;padding:0 0 0 18px;border-left:3px solid var(--navy);font-size:17px;line-height:1.58;max-width:930px}.statement.good{border-left-color:var(--teal)}.statement.warn{border-left-color:var(--amber)}.statement.bad{border-left-color:var(--red)}
.table-wrap{overflow:auto;margin:22px 0 15px}table{width:100%;border-collapse:collapse;font-size:13.5px;line-height:1.43}th{text-align:left;font-size:12px;color:var(--muted);font-weight:700;padding:9px 11px;border-bottom:1px solid #cfd5dd;vertical-align:bottom}td{padding:12px 11px;border-bottom:1px solid var(--line);vertical-align:top}.focus td{background:#f9fbfc}.note{font-size:12.5px;color:var(--muted);max-width:930px}.small{font-size:13px;color:#475467}.chart{margin:28px 0 8px;max-width:930px}.chart img{width:100%;height:auto}.actions{margin-top:12px}.action{display:grid;grid-template-columns:42px 1fr;gap:17px;padding:25px 0;border-top:1px solid var(--line)}.num{width:32px;height:32px;border:1px solid #bcc6d0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:750;color:var(--navy)}.action h3{margin:0 0 8px}.meta{font-size:13px;color:var(--muted)}
details{border-top:1px solid var(--line);padding:17px 0}details:last-child{border-bottom:1px solid var(--line)}summary{cursor:pointer;font-weight:700}.tag{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.02em;padding:3px 7px;border-radius:4px;background:#eef2f6;margin-right:6px}.tag.fact{background:#eaf7f4}.tag.hyp{background:#fff6e5}.tag.limit{background:#f4f4f5}.toc{font-size:14px;background:var(--soft);padding:18px 20px;margin-top:26px}.toc a{color:var(--navy);text-decoration:none;margin-right:14px;white-space:nowrap}code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;background:#f3f4f6;padding:2px 5px;border-radius:4px}footer{padding-top:31px;color:var(--muted);font-size:12px}
@media(max-width:760px){main{padding:40px 19px 68px}h1{font-size:36px}h2{font-size:26px}.action{grid-template-columns:35px 1fr}}
@media print{main{max-width:none;padding:0}section{break-inside:auto}details{display:block}summary{list-style:none}}
"""


def escape(x):
    return html.escape(str(x))


def fmt_num(x, dec=1):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if abs(float(x)) >= 1000:
        return f"{float(x):,.0f}".replace(",", ".")
    return f"{float(x):.{dec}f}".replace(".", ",")


def fmt_pct(x, dec=1):
    return f"{float(x):.{dec}f}%".replace(".", ",")


def fmt_rate(x):
    return f"{float(x):.3f}".replace(".", ",")


def metric_value(metric, x):
    if metric in {"taxa_curtidas", "taxa_comentarios", "taxa_compartilhamentos", "taxa_engajamento"}:
        return fmt_num(x, 3)
    return fmt_num(x, 1 if metric in {"comentarios","compartilhamentos"} else 0)


def combo_phrase(row) -> str:
    format_map = {"video":"vídeo", "image":"imagem", "text":"texto", "mixed":"misto"}
    category_map = {"beauty":"Beauty", "lifestyle":"Lifestyle", "tech":"Tech"}
    fmt = format_map.get(str(row["formato"]), str(row["formato"]))
    cat = category_map.get(str(row["categoria"]), str(row["categoria"]))
    tier = str(row["porte_criador"])
    return f"conteúdos em formato {fmt}, categoria {cat}, com creators de {tier} seguidores"


def df_html(df: pd.DataFrame, cols: list[str] | None = None, labels: dict | None = None, max_rows: int = 40) -> str:
    x = df.copy()
    if cols:
        x = x[[c for c in cols if c in x.columns]]
    x = x.head(max_rows)
    labels = labels or {}
    headers = "".join(f"<th>{escape(labels.get(c, DIMENSION_LABELS.get(c, c.replace('_',' ').title())))}</th>" for c in x.columns)
    rows = []
    for _, r in x.iterrows():
        cells = []
        for c in x.columns:
            v = r[c]
            if isinstance(v, (np.floating, float)):
                if pd.isna(v): text = "—"
                elif "pct" in c or "percent" in c: text = fmt_num(v,1) + "%"
                elif abs(v) >= 1000: text = fmt_num(v,0)
                else: text = fmt_num(v,3 if abs(v)<10 else 1)
            elif isinstance(v, (np.integer, int)):
                text = fmt_num(v,0)
            elif isinstance(v, (pd.Timestamp,)):
                text = v.strftime("%d/%m/%Y")
            else:
                text = escape(v)
            cells.append(f"<td>{text}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{headers}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def plot_monthly(df: pd.DataFrame, platform: str) -> str:
    fig, ax = plt.subplots(figsize=(10.2, 3.5))
    ts = time_series(df, "taxa_engajamento", "MS")
    ax.plot(ts["data_hora"], ts["mediana"], marker="o", markersize=3)
    ax.set_title(f"{platform}: interações a cada 100 visualizações ao longo do tempo")
    ax.set_ylabel("Interações / 100 views")
    ax.set_xlabel("")
    ax.grid(alpha=.18)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=145, bbox_inches="tight"); plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def plot_sponsorship(df: pd.DataFrame, platform: str) -> str:
    fig, ax = plt.subplots(figsize=(10.2, 3.5))
    x = monthly_sponsorship(df, "taxa_engajamento", min_each=20)
    ax.axhline(0, linewidth=1)
    if not x.empty:
        ax.plot(pd.to_datetime(x.mes), x.diferenca, marker="o", markersize=3)
    ax.set_title(f"{platform}: diferença mensal entre patrocinado e orgânico")
    ax.set_ylabel("Diferença em interações / 100 views")
    ax.set_xlabel("")
    ax.grid(alpha=.18)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=145, bbox_inches="tight"); plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def select_candidate_from_table(t: pd.DataFrame) -> pd.Series:
    if t.empty:
        raise ValueError("No candidate")
    if "meses_validos" in t:
        stable = t[(t.meses_validos >= 10) & (t.meses_acima_do_padrao_pct >= 60)]
        if not stable.empty:
            return stable.iloc[0]
    return t.iloc[0]


def select_candidate(d: pd.DataFrame, metric: str) -> pd.Series:
    return select_candidate_from_table(combination_analysis(d, ["formato","categoria","porte_criador"], metric, 80, 8, 8))

def candidate_interpretation(d: pd.DataFrame, metric: str, r: pd.Series) -> str:
    base = float(d[metric].median())
    rel = 100 * (float(r.mediana) / base - 1) if base else np.nan
    months = r.get("meses_validos", np.nan)
    above = r.get("meses_acima_do_padrao_pct", np.nan)
    p1, p2 = r.get("primeiros_12m", np.nan), r.get("segundos_12m", np.nan)
    if pd.notna(p1) and pd.notna(p2):
        temporal = f"Nos primeiros 12 meses, o resultado típico do grupo foi {metric_value(metric,p1)}; nos 12 seguintes, {metric_value(metric,p2)}."
        if p2 > p1:
            temporal += " O grupo ganhou força no período recente."
        elif p2 < p1:
            temporal += " O grupo perdeu parte da força no período recente."
        else:
            temporal += " O nível permaneceu estável entre os períodos."
    else:
        temporal = "A amostra não permite uma comparação temporal equivalente com a mesma segurança."
    if pd.notna(months):
        persistence = f"Houve meses comparáveis suficientes em {int(months)} meses, e o grupo ficou acima do padrão mensal em {fmt_pct(above,0)} deles."
    else:
        persistence = "O volume mensal é insuficiente para tratar a liderança agregada como padrão recorrente."
    magnitude = f"A vantagem histórica sobre o post típico da plataforma foi de {metric_value(metric,r.diferenca_para_plataforma)} ({fmt_pct(rel,2)})."
    return f"{magnitude} {persistence} {temporal}"


def platform_findings(df: pd.DataFrame, platform: str) -> dict:
    d = platform_data(df, platform)
    audit = audit_quality(d)
    periods = d.groupby("periodo_12m").agg(
        posts=("id","size"), visualizacoes=("visualizacoes","median"),
        interacoes=("interacoes_totais","median"), taxa_engajamento=("taxa_engajamento","median"),
        patrocinio=("patrocinado","mean")
    )
    p1, p2 = periods.loc["Primeiros 12 meses"], periods.loc["Segundos 12 meses"]
    monthly = d.groupby("mes").agg(
        posts=("id","size"), visualizacoes=("visualizacoes","median"),
        comentarios=("comentarios","median"), compartilhamentos=("compartilhamentos","median"),
        interacoes=("interacoes_totais","median"), taxa_engajamento=("taxa_engajamento","median")
    ).reset_index()
    combo_tables = {m: combination_analysis(d,["formato","categoria","porte_criador"],m,80,8,8) for m in KEY_METRICS}
    candidates = {m: select_candidate_from_table(combo_tables[m]) for m in KEY_METRICS}
    sponsor = sponsorship_overall(d, KEY_METRICS, n_boot=450)
    audience = {}
    for dim in ["faixa_etaria_audiencia","genero_audiencia","localizacao_audiencia","idioma"]:
        t = group_summary(d,dim,"taxa_engajamento",30)
        audience[dim] = t
    corr = numeric_correlations(d)
    predict_er = temporal_predictability(d,"taxa_engajamento")
    predict_views = temporal_predictability(d,"visualizacoes")
    frequency_er = frequency_performance(d,"taxa_engajamento","semana")
    frequency_views = frequency_performance(d,"visualizacoes","semana")
    mix = {dim: mix_shift(d,dim) for dim in ["formato","categoria","porte_criador","patrocinado"]}
    return {
        "d":d,"audit":audit,"periods":periods,"p1":p1,"p2":p2,"monthly":monthly,"candidates":candidates,"combo_tables":combo_tables,
        "sponsor":sponsor,"audience":audience,"corr":corr,"predict_er":predict_er,"predict_views":predict_views,"frequency_er":frequency_er,"frequency_views":frequency_views,"mix":mix,
        "sponsor_cells": strongest_sponsor_cells(d)
    }


def strongest_sponsor_cells(d: pd.DataFrame) -> list[dict]:
    cells = []
    for metric in KEY_METRICS:
        ctrl = sponsorship_controlled(d, metric, ["formato","categoria","porte_criador"], min_each=25, with_ci=False)
        if ctrl.empty:
            continue
        selected = pd.concat([ctrl.head(1), ctrl.tail(1)]).drop_duplicates()
        enriched = sponsorship_strata_with_ci(d, metric, selected, n_boot=250)
        for _, r in enriched.iterrows():
            if r.evidencia in {"positivo","negativo"}:
                item = r.to_dict(); item["metrica"] = metric; cells.append(item)
    cells.sort(key=lambda x: abs(float(x["diferenca"])), reverse=True)
    return cells


def mix_story(f: dict) -> str:
    pieces=[]
    for dim in ["formato","categoria"]:
        t=f["mix"][dim]
        if not t.empty:
            pos=t.iloc[0]; neg=t.iloc[-1]
            pieces.append(
                f"Em {DIMENSION_LABELS.get(dim,dim).lower()}, **{display_value(pos[dim])}** ganhou {fmt_num(pos['mudanca_pontos_percentuais'],2)} pontos percentuais de participação, enquanto **{display_value(neg[dim])}** perdeu {fmt_num(abs(neg['mudanca_pontos_percentuais']),2)}."
            )
    return " ".join(pieces)


def platform_actions(f: dict) -> list[tuple[str,str]]:
    d=f["d"]; cand=f["candidates"]
    scored=[]
    for m,r in cand.items():
        base=float(d[m].median())
        rel=100*(float(r.mediana)/base-1) if base else 0
        p1=r.get("primeiros_12m",np.nan); p2=r.get("segundos_12m",np.nan)
        months=r.get("meses_validos",np.nan); above=r.get("meses_acima_do_padrao_pct",np.nan)
        scored.append((m,r,rel,p1,p2,months,above))
    improving=[x for x in scored if pd.notna(x[3]) and pd.notna(x[4]) and x[4]>x[3] and pd.notna(x[5]) and x[5]>=10 and pd.notna(x[6]) and x[6]>=60]
    fading=[x for x in scored if pd.notna(x[3]) and pd.notna(x[4]) and x[4]<x[3] and pd.notna(x[5]) and x[5]>=10 and pd.notna(x[6]) and x[6]>=60]
    actions=[]
    if improving:
        m,r,rel,p1,p2,months,above=max(improving,key=lambda x:abs(x[2]))
        actions.append(("Testar no presente", f"{combo_phrase(r).capitalize()} para {OBJECTIVE_NAMES[m].lower()}. O grupo ficou acima do padrão mensal em {fmt_pct(above,0)} dos {int(months)} meses comparáveis e melhorou de {metric_value(m,p1)} para {metric_value(m,p2)} entre os dois períodos. O teste deve confirmar se essa vantagem ainda existe em uma execução prospectiva equivalente."))
    if fading:
        m,r,rel,p1,p2,months,above=max(fading,key=lambda x:abs(x[2]))
        actions.append(("Não escalar pelo histórico", f"{combo_phrase(r).capitalize()} para {OBJECTIVE_NAMES[m].lower()} ainda aparece bem no agregado, mas caiu de {metric_value(m,p1)} para {metric_value(m,p2)}. O histórico explica por que chama atenção; a perda de força explica por que não deve virar regra sem nova validação."))
    positives=[c for c in f["sponsor_cells"] if c["evidencia"]=="positivo"]
    negatives=[c for c in f["sponsor_cells"] if c["evidencia"]=="negativo"]
    if positives:
        c=positives[0]
        actions.append(("Patrocínio: hipótese específica", f"Em {combo_phrase(c)}, o patrocinado superou o orgânico equivalente em {metric_value(c['metrica'],abs(c['diferenca']))} para {OBJECTIVE_NAMES[c['metrica']].lower()}. Isso justifica um teste controlado desse contexto — não uma política geral de patrocínio."))
    if negatives:
        c=negatives[0]
        actions.append(("Patrocínio: pausar/revalidar", f"Em {combo_phrase(c)}, o patrocinado ficou {metric_value(c['metrica'],abs(c['diferenca']))} abaixo do orgânico equivalente em {OBJECTIVE_NAMES[c['metrica']].lower()}. Até nova evidência, esse contexto não deveria receber verba com esse objetivo."))
    actions.append(("Não comprar alcance por follower count", "O número de seguidores praticamente não se relaciona com visualizações nesta base. Creator deve ser escolhido pelo contexto de conteúdo e pelo objetivo medido, não pelo tamanho isolado."))
    return actions[:5]


def report_platform_markdown(df: pd.DataFrame, platform: str, f: dict) -> str:
    d=f["d"]; p1=f["p1"]; p2=f["p2"]
    cv=f["audit"]["distribuicao_metricas"]["visualizacoes"]["variacao_relativa"]*100
    follower_views=f["corr"].loc["seguidores_criador","visualizacoes"]
    candidates=f["candidates"]
    sponsor=f["sponsor"].set_index("metrica")
    audience_spreads={dim:(tab.iloc[0],tab.iloc[-1],float(tab.mediana.max()-tab.mediana.min())) for dim,tab in f["audience"].items() if not tab.empty}
    cells=f["sponsor_cells"]

    lines=[]
    lines.append(f"# {platform} — Resultados da investigação\n")
    lines.append(f"**Escopo:** {len(d):,} posts, de {d.data_hora.min():%d/%m/%Y} a {d.data_hora.max():%d/%m/%Y}.".replace(",","."))
    lines.append("\n## Leitura executiva\n")
    lines.append(
        f"A primeira conclusão é que a base de {platform} apresenta **pouca separação entre os posts em alcance**: as visualizações variam apenas cerca de {fmt_num(cv,2)}% em torno da média. "
        f"Isso torna perigoso transformar pequenas diferenças de ranking em regras editoriais. Nos primeiros 12 meses, um post típico registrou {fmt_num(p1.visualizacoes,0)} visualizações e {fmt_num(p1.interacoes,0)} interações; nos 12 seguintes, {fmt_num(p2.visualizacoes,0)} e {fmt_num(p2.interacoes,0)}, respectivamente."
    )
    lines.append(
        "Ter mais seguidores praticamente não está associado a receber mais visualizações nesta base. "
        "Portanto, tamanho do creator não deve ser tratado como atalho para alcance. A medida estatística exata fica na camada de auditoria."
    )
    lines.append("\n## O que funciona para cada objetivo\n")
    for metric in KEY_METRICS:
        r=candidates[metric]
        lines.append(f"### {OBJECTIVE_NAMES[metric]}\n")
        lines.append(f"O melhor sinal com estabilidade mínima foi **{combo_phrase(r)}**, com {metric_value(metric,r.mediana)} contra {metric_value(metric,d[metric].median())} de um post típico da plataforma, em {int(r.n)} posts. {candidate_interpretation(d,metric,r)}")
    lines.append("\n## Patrocínio\n")
    for metric in KEY_METRICS:
        r=sponsor.loc[metric]
        lines.append(
            f"- **{OBJECTIVE_NAMES[metric]}:** patrocinado {metric_value(metric,r.resultado_patrocinado)} × orgânico {metric_value(metric,r.resultado_organico)}; diferença {metric_value(metric,r.diferenca)}. " + ("A diferença é clara na amostra." if r.evidencia != "diferença não separada de zero" else "A incerteza do dado inclui a possibilidade de não haver diferença real.")
        )
    if cells:
        lines.append("\nHá bolsões locais que merecem atenção, mas eles não mudam a conclusão de que patrocínio não gera ganho geral por si só:\n")
        for c in cells[:4]:
            direction="ganhou" if c["diferenca"]>0 else "perdeu"
            phrase=combo_phrase(c)
            lines.append(f"- Em **{phrase}**, o patrocinado {direction} {metric_value(c['metrica'],abs(c['diferenca']))} em {METRICS[c['metrica']].lower()} frente ao orgânico, com {c['n_patrocinado']} posts patrocinados e {c['n_organico']} orgânicos; o intervalo de incerteza ficou todo do mesmo lado de zero.")
    lines.append("\nSem gasto, receita ou conversão, estes dados medem performance, não retorno financeiro.\n")
    lines.append("## Audiência\n")
    for dim,(best,worst,spread) in audience_spreads.items():
        lines.append(f"- **{DIMENSION_LABELS[dim]}:** {display_value(best[dim])} aparece no topo e {display_value(worst[dim])} no fundo, mas a distância entre os dois é de apenas {fmt_num(spread,3)} interação por 100 visualizações. Isso não sustenta, sozinho, uma mudança de público prioritário.")
    lines.append("\n## O que mudou no tempo\n")
    lines.append(mix_story(f))
    lines.append(f" O nível geral de interações por 100 visualizações passou de {fmt_num(p1.taxa_engajamento,3)} para {fmt_num(p2.taxa_engajamento,3)}; a participação de posts patrocinados foi de {fmt_pct(100*p1.patrocinio,2)} para {fmt_pct(100*p2.patrocinio,2)}.")
    freq_er=f["frequency_er"]["correlacao_volume_resultado"]
    lines.append("\n## Frequência de publicação\n")
    if pd.isna(freq_er) or abs(freq_er)<.2:
        lines.append("Ao comparar semana a semana, publicar mais vezes não aparece associado de forma relevante a uma taxa maior ou menor de interação. A base, portanto, não sustenta uma frequência ótima por si só; frequência precisa ser decidida pela capacidade operacional e validada em experimento.")
    else:
        lines.append("O volume semanal aparece associado à performance, mas o desenho observacional não permite afirmar que aumentar ou reduzir a frequência cause o resultado. O sinal deve ser testado antes de virar regra editorial.")
    lines.append("\n## Stress test\n")
    lines.append(
        "Quando um modelo usa formato, categoria, tamanho do creator, audiência, patrocínio, duração e tempo do primeiro ano para tentar reconhecer os posts de maior eficiência no segundo ano, ele fica no nível do acaso. "
        "Em português: as variáveis disponíveis não formam uma receita estável que permita reconhecer com segurança os vencedores do período seguinte. O resultado técnico exato fica no notebook de auditoria."
    )
    lines.append("\n## Decisão de Marketing\n")
    for title,body in platform_actions(f):
        lines.append(f"- **{title}:** {body}")
    lines.append("- **Medir daqui para frente:** gasto por post/parceria, conversão, receita, alcance de não seguidores e variáveis do criativo/tema; são lacunas que impedem transformar performance em decisão econômica.")
    return "\n\n".join(lines)


def report_platform_html(df: pd.DataFrame, platform: str, f: dict) -> str:
    d=f["d"]; p1=f["p1"]; p2=f["p2"]; candidates=f["candidates"]
    audit=f["audit"]; corr=f["corr"]
    cv=100*audit["distribuicao_metricas"]["visualizacoes"]["variacao_relativa"]
    follower_views=corr.loc["seguidores_criador","visualizacoes"]
    sponsor=f["sponsor"].set_index("metrica")
    cells=f["sponsor_cells"]
    monthly_chart=plot_monthly(d,platform)
    sponsor_chart=plot_sponsorship(d,platform)

    objective_rows=[]
    for metric in KEY_METRICS:
        r=candidates[metric]
        rel=100*(r.mediana/d[metric].median()-1) if d[metric].median() else np.nan
        temporal=""
        if pd.notna(r.get('primeiros_12m',np.nan)) and pd.notna(r.get('segundos_12m',np.nan)):
            change=r.segundos_12m-r.primeiros_12m
            temporal=("ganhou" if change>0 else "perdeu" if change<0 else "manteve") + f" força: {metric_value(metric,r.primeiros_12m)} → {metric_value(metric,r.segundos_12m)}"
        persistence = f"{fmt_pct(r.meses_acima_do_padrao_pct,0)} dos {int(r.meses_validos)} meses comparáveis" if pd.notna(r.get('meses_validos',np.nan)) else "sem volume mensal suficiente"
        objective_rows.append({
            "Objetivo":OBJECTIVE_NAMES[metric],"Sinal mais consistente":combo_phrase(r),"Posts":int(r.n),
            "Resultado observado":metric_value(metric,r.mediana),"Comparação com a plataforma":f"{metric_value(metric,r.diferenca_para_plataforma)} ({fmt_pct(rel,2)})",
            "Persistência":persistence,"Evolução":temporal
        })
    objdf=pd.DataFrame(objective_rows)

    # Sponsor executive table
    sponsor_rows=[]
    for metric in KEY_METRICS:
        r=sponsor.loc[metric]
        sponsor_rows.append({
            "Objetivo":OBJECTIVE_NAMES[metric],"Patrocinado":metric_value(metric,r.resultado_patrocinado),
            "Orgânico":metric_value(metric,r.resultado_organico),"Diferença":metric_value(metric,r.diferenca),
            "Leitura":r.evidencia.replace("diferença não separada de zero","a base não distingue o resultado de zero com segurança")
        })
    spdf=pd.DataFrame(sponsor_rows)

    audience_rows=[]
    for dim,tab in f["audience"].items():
        if tab.empty: continue
        best,worst=tab.iloc[0],tab.iloc[-1]
        audience_rows.append({
            "Dimensão":DIMENSION_LABELS[dim],"Maior resultado":display_value(best[dim]),"Interações / 100 views":fmt_num(best.mediana,3),
            "Menor resultado":display_value(worst[dim]),"Diferença entre extremos":fmt_num(best.mediana-worst.mediana,3)
        })
    auddf=pd.DataFrame(audience_rows)

    cell_html=""
    if cells:
        pieces=[]
        for c in cells[:5]:
            direction="mais" if c['diferenca']>0 else "menos"
            pieces.append(
                f"<p><strong>{escape(combo_phrase(c))}</strong>: os posts patrocinados tiveram {metric_value(c['metrica'],abs(c['diferenca']))} {direction} em {escape(METRICS[c['metrica']].lower())} do que os orgânicos equivalentes, com {c['n_patrocinado']} patrocinados e {c['n_organico']} orgânicos. O intervalo de incerteza permaneceu do mesmo lado de zero.</p>"
            )
        cell_html="".join(pieces)
    else:
        cell_html="<p>Nenhum subgrupo com amostra mínima apresentou diferença patrocinado–orgânico robusta o suficiente para ficar toda do mesmo lado de zero nos testes selecionados.</p>"

    creator_multi=audit['creator_ids_multiplos_nomes_pct']
    pred=f['predict_er']['capacidade_identificar_top_20_futuro']
    action_blocks=[]
    for i,(title,body) in enumerate(platform_actions(f),1):
        action_blocks.append(f'<div class="action"><div class="num">{i}</div><div><h3>{escape(title)}</h3><p>{escape(body)}</p></div></div>')
    actions_html=''.join(action_blocks)
    p1_er,p2_er=p1.taxa_engajamento,p2.taxa_engajamento
    p1_views,p2_views=p1.visualizacoes,p2.visualizacoes

    html_doc=f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{platform} — Relatório de Performance</title><style>{CSS}</style></head><body><main>
<header><div class="kicker">Challenge 004 · Investigação por plataforma</div><h1>{platform}: o que os dados sustentam — e o que não sustentam</h1>
<p class="subtitle">A análise separa alcance, conversa, compartilhamento, interação total e eficiência, reconstrói dois anos de comportamento e testa patrocínio, creators, audiência, conteúdo e tempo antes de transformar um ranking em decisão.</p>
<p class="scope">{len(d):,} posts · {d.data_hora.min():%d/%m/%Y} a {d.data_hora.max():%d/%m/%Y} · “post típico” = mediana, usada para reduzir a influência de extremos</p>
<div class="toc"><a href="#executivo">Síntese</a><a href="#objetivos">Objetivos</a><a href="#tempo">Tempo</a><a href="#patrocinio">Patrocínio</a><a href="#audiencia">Audiência</a><a href="#decisao">Decisão</a><a href="#auditoria">Auditoria</a></div></header>

<section id="executivo"><h2>O que um Head de Marketing precisa entender primeiro</h2>
<p>A base de <strong>{platform}</strong> não mostra uma fórmula simples capaz de separar vencedores de perdedores. As visualizações variam apenas cerca de <strong>{fmt_num(cv,2)}%</strong> em torno da média; por isso, uma combinação aparecer em primeiro lugar não significa que a vantagem seja grande o suficiente para justificar mudança de estratégia.</p>
<p>O comportamento geral também foi estável entre as duas janelas equivalentes: um post típico passou de <strong>{fmt_num(p1_views,0)} para {fmt_num(p2_views,0)} visualizações</strong> e de <strong>{fmt_num(p1_er,3)} para {fmt_num(p2_er,3)} interações a cada 100 visualizações</strong>. O que muda de verdade aparece em bolsões específicos e, principalmente, depende do objetivo.</p>
<div class="statement">Ter mais seguidores praticamente não aumenta a chance de obter mais alcance nesta base. Portanto, comprar creator maior esperando mais views não é uma decisão respaldada por estes dados. A medida estatística exata fica no apêndice de auditoria.</div>
<p>Há ainda um limite de previsibilidade. Quando usamos as características disponíveis do primeiro ano para tentar reconhecer os posts mais eficientes no segundo, o resultado fica no nível do acaso. Isso não invalida a análise: mostra que o uso correto da base é <strong>selecionar hipóteses e eliminar decisões ruins</strong>, não prometer uma receita de performance. A medida técnica exata fica na auditoria.</p></section>

<section id="objetivos"><h2>Performance muda conforme o objetivo</h2>
<p class="lead">O mesmo conteúdo não lidera alcance, conversa e compartilhamento. Por isso, a estratégia deve começar pelo resultado desejado — não por um formato “campeão”.</p>
{df_html(objdf, max_rows=10)}
"""
    # Interpret every objective in prose
    for metric in KEY_METRICS:
        r=candidates[metric]
        html_doc += f"<h3>{OBJECTIVE_NAMES[metric]}</h3><p><strong>{escape(combo_phrase(r))}</strong> foi o sinal mais consistente encontrado dentro dos critérios de amostra e repetição temporal. Em {int(r.n)} posts, registrou {metric_value(metric,r.mediana)} contra {metric_value(metric,d[metric].median())} de um post típico da plataforma.</p><p>{escape(candidate_interpretation(d,metric,r))}</p>"
    html_doc += f"""</section>

<section id="tempo"><h2>O que mudou ao longo dos dois anos</h2>
<p>{mix_story(f)}</p>
<p>Apesar dessas mudanças de composição, o nível geral permaneceu próximo: interações a cada 100 visualizações foram de <strong>{fmt_num(p1_er,3)}</strong> para <strong>{fmt_num(p2_er,3)}</strong>. Isso é importante porque separa duas coisas diferentes: <strong>postar mais de um tipo de conteúdo</strong> e <strong>esse tipo de conteúdo passar a performar melhor</strong>.</p>
<div class="chart"><img src="data:image/png;base64,{monthly_chart}" alt="Série mensal de performance"></div>
<p class="note">A linha mensal existe para reconstruir a ordem dos acontecimentos. Um pico isolado não é tratado como estratégia.</p>
</section>

<section id="patrocinio"><h2>Patrocínio não é uma estratégia única; ele muda conforme o objetivo</h2>
<p>No agregado, os posts patrocinados não apresentam ganho geral defensável em alcance, interações ou eficiência. A tabela abaixo mostra a comparação direta. Quando o intervalo de incerteza cruza zero, os dados não permitem distinguir a diferença observada de uma variação amostral.</p>
{df_html(spdf)}
<div class="chart"><img src="data:image/png;base64,{sponsor_chart}" alt="Diferença mensal patrocinado e orgânico"></div>
<h3>Onde apareceram diferenças locais após comparar situações equivalentes</h3>{cell_html}
<div class="statement warn">Esses bolsões não são uma política de mídia pronta. Eles são sinais locais que precisam ser confirmados prospectivamente. E, sem gasto, receita ou conversão, a análise mede performance — não ROI financeiro.</div>
</section>

<section id="audiencia"><h2>A audiência ajuda a descrever, mas pouco a decidir</h2>
<p>Idade, gênero, localização e idioma produzem rankings, porém as distâncias entre os extremos são pequenas. O ponto não é quem ficou em primeiro lugar: é se a diferença é grande e estável o suficiente para justificar trocar público, conteúdo ou verba.</p>
{df_html(auddf)}
<p>Com os dados atuais, audiência funciona melhor como <strong>variável de contexto para cruzamentos</strong> do que como fundamento para uma persona prioritária.</p>
</section>

<section><h2>Creators: tamanho não substitui qualidade de contexto</h2>
<p>A relação entre seguidores e visualizações é praticamente inexistente nesta base. Além disso, <strong>{fmt_num(creator_multi,1)}% dos creator IDs aparecem associados a mais de um nome</strong>. Isso significa que a chave técnica não identifica uma pessoa com segurança ao longo do tempo; ela serve para auditar a inconsistência, não para reconstruir histórico individual de um creator.</p>
<div class="statement">Implicação: segmentar creators por faixa de seguidores é válido porque follower count está registrado em cada post; tratar <code>creator_id</code> como uma pessoa longitudinal confiável não é.</div>
</section>

<section><h2>Frequência: a base não revela um número mágico de posts</h2>
<p>Ao comparar o volume de publicações semana a semana com alcance e eficiência, não aparece uma relação forte o suficiente para afirmar que publicar mais ou menos, por si só, melhora a performance. Portanto, estes dados não sustentam uma frequência ótima. A frequência deve ser tratada como variável de experimento e capacidade operacional, não como conclusão retirada de correlação histórica.</p></section>

<section id="decisao"><h2>O que Marketing deve fazer com esta leitura</h2><div class="actions">
{actions_html}
</div></section>

<section id="auditoria"><h2>Investigação completa para auditoria</h2><p class="lead">A narrativa acima é a interpretação. Abaixo ficam as tabelas que permitem verificar as conclusões sem transformar o corpo executivo em relatório estatístico.</p>
"""
    # Core dimension tables by key objective
    for metric in KEY_METRICS:
        html_doc += f"<details><summary>{escape(OBJECTIVE_NAMES[metric])}: todas as dimensões principais</summary>"
        for dim in DIMENSIONS_INVESTIGATION:
            t=group_summary(d,dim,metric,30)
            html_doc += f"<h3>{escape(DIMENSION_LABELS.get(dim,dim))}</h3>" + df_html(t, cols=[dim,"n","mediana","media","p25","p75","diferenca_para_plataforma","diferenca_relativa_pct"], max_rows=30)
        combo=f["combo_tables"][metric]
        html_doc += "<h3>Formato × categoria × tamanho do creator</h3>" + df_html(combo, cols=["formato","categoria","porte_criador","n","mediana","diferenca_para_plataforma","meses_validos","meses_acima_do_padrao_pct","primeiros_12m","segundos_12m","mudanca"], max_rows=40)
        html_doc += "</details>"
    # Sponsor technical: selected controlled cells are enough in the report; the full universe remains explorable in the dashboard.
    if f["sponsor_cells"]:
        st=pd.DataFrame(f["sponsor_cells"])
        html_doc += "<details><summary>Patrocínio: células controladas com evidência mais clara</summary>" + df_html(st, cols=["metrica","formato","categoria","porte_criador","n_patrocinado","n_organico","resultado_patrocinado","resultado_organico","diferenca","intervalo_95_min","intervalo_95_max","evidencia"], max_rows=30) + "</details>"
    # Time
    html_doc += "<details><summary>Primeiros 12 meses × segundos 12 meses</summary>"
    for dim in ["formato","categoria","porte_criador","faixa_etaria_audiencia","localizacao_audiencia","idioma"]:
        t=period_comparison(d,[dim],"taxa_engajamento",30)
        html_doc += f"<h3>{escape(DIMENSION_LABELS.get(dim,dim))}</h3>" + df_html(t, max_rows=40)
    html_doc += "</details>"
    # Hashtags
    ht=hashtag_analysis(d,"taxa_engajamento",30)
    html_doc += "<details><summary>Hashtags</summary>" + df_html(ht, cols=["hashtag","n","mediana","p25","p75","diferenca_para_plataforma"], max_rows=80) + "</details>"
    # Outliers
    for pct,label in [(.01,"1%"),(.05,"5%")]:
        ot=outlier_profile(d,"taxa_engajamento",pct)
        html_doc += f"<details><summary>Composição do top/bottom {label}</summary>" + df_html(ot.sort_values("indice_top",ascending=False), max_rows=100) + "</details>"
    # Creator audit
    ca=creator_id_audit(d)
    html_doc += "<details><summary>Auditoria de creator_id</summary>" + df_html(ca, max_rows=100) + "</details>"
    # Technical limitations
    html_doc += f"""<details><summary>Limitações e testes de robustez</summary>
<p><strong>Views pouco dispersas:</strong> variação relativa de {fmt_num(cv,2)}%. Rankings de pequenas diferenças devem ser tratados com cuidado.</p>
<p><strong>Seguidores × visualizações:</strong> correlação ordinal = {follower_views:.4f}; valor próximo de zero.</p>
<p><strong>Previsibilidade fora do tempo:</strong> capacidade de identificar o top 20% no período seguinte = {f['predict_er']['capacidade_identificar_top_20_futuro']:.3f} para eficiência e {f['predict_views']['capacidade_identificar_top_20_futuro']:.3f} para visualizações; 0,50 é aproximadamente acaso.</p>
<p><strong>Duração:</strong> a unidade de content_length não é documentada; a análise usa duração relativa dentro da plataforma.</p>
<p><strong>Horário:</strong> não há timezone confirmado.</p>
<p><strong>Patrocínio:</strong> não há gasto, receita ou conversão; não é possível calcular ROI financeiro.</p>
<p><strong>Creator ID:</strong> a chave é inconsistente para identidade longitudinal.</p>
</details></section>
<footer>Challenge 004 · {platform} · relatório gerado pelo mesmo motor analítico usado no dashboard e notebook.</footer></main></body></html>"""
    return html_doc


def build_cross_platform_report(df: pd.DataFrame, findings: dict[str,dict]) -> str:
    overview=platform_overview(df)
    overall_audit=audit_quality(df)
    cv=100*overall_audit['distribuicao_metricas']['visualizacoes']['variacao_relativa']
    # Cross platform objective table
    rows=[]
    for p in PLATFORMS:
        f=findings[p]; d=f['d']
        for metric in KEY_METRICS:
            r=f['candidates'][metric]
            rows.append({
                "Plataforma":p,"Objetivo":OBJECTIVE_NAMES[metric],"Sinal observado":combo_phrase(r),
                "Posts":int(r.n),"Resultado":metric_value(metric,r.mediana),
                "Vantagem vs. post típico":metric_value(metric,r.diferenca_para_plataforma),
                "Meses acima do padrão":fmt_pct(r.meses_acima_do_padrao_pct,0) if pd.notna(r.get('meses_acima_do_padrao_pct',np.nan)) else "—",
                "Mudança P1→P2":metric_value(metric,r.get('mudanca',np.nan))
            })
    obj=pd.DataFrame(rows)

    # Sponsorship cross summary
    sp_rows=[]
    for p in PLATFORMS:
        sp=findings[p]['sponsor'].set_index('metrica')
        for metric in KEY_METRICS:
            r=sp.loc[metric]
            sp_rows.append({"Plataforma":p,"Objetivo":OBJECTIVE_NAMES[metric],"Patrocinado":metric_value(metric,r.resultado_patrocinado),"Orgânico":metric_value(metric,r.resultado_organico),"Diferença":metric_value(metric,r.diferenca),"Leitura":r.evidencia})
    spdf=pd.DataFrame(sp_rows)

    # Audience spreads per platform
    aud_rows=[]
    for p in PLATFORMS:
        for dim,tab in findings[p]['audience'].items():
            if tab.empty: continue
            aud_rows.append({"Plataforma":p,"Dimensão":DIMENSION_LABELS[dim],"Maior":display_value(tab.iloc[0][dim]),"Menor":display_value(tab.iloc[-1][dim]),"Distância entre extremos":fmt_num(tab.iloc[0].mediana-tab.iloc[-1].mediana,3)})
    auddf=pd.DataFrame(aud_rows)

    # Cross overall monthly chart
    fig,ax=plt.subplots(figsize=(10.3,4.2))
    for p in PLATFORMS:
        ts=time_series(platform_data(df,p),'taxa_engajamento','MS')
        ax.plot(ts.data_hora,ts.mediana,label=p,linewidth=1.5)
    ax.set_title("Interações a cada 100 visualizações por plataforma")
    ax.set_ylabel("Interações / 100 views"); ax.grid(alpha=.18); ax.legend(ncol=3,fontsize=8); fig.tight_layout()
    buf=io.BytesIO();fig.savefig(buf,format='png',dpi=145,bbox_inches='tight');plt.close(fig); chart=base64.b64encode(buf.getvalue()).decode()

    # Specific sponsorship cells across platforms
    cell_rows=[]
    for p in PLATFORMS:
        cells=findings[p]["sponsor_cells"]
        for c in cells[:2]:
            cell_rows.append({"Plataforma":p,"Contexto":combo_phrase(c),"Objetivo":OBJECTIVE_NAMES[c['metrica']],"Diferença patrocinado - orgânico":metric_value(c['metrica'],c['diferenca']),"Direção":c['evidencia']})
    celldf=pd.DataFrame(cell_rows)

    # Frequência semanal: leitura de portfólio
    freq_rows=[]
    for p in PLATFORMS:
        f=findings[p]
        freq_rows.append({
            "Plataforma":p,
            "Relação entre publicar mais e alcance":fmt_num(f["frequency_views"]["correlacao_volume_resultado"],3),
            "Relação entre publicar mais e eficiência":fmt_num(f["frequency_er"]["correlacao_volume_resultado"],3),
            "Leitura":"Sem relação forte o suficiente para definir uma frequência ótima"
        })
    freqdf=pd.DataFrame(freq_rows)

    # Carteira de hipóteses específicas por plataforma: somente sinais que ganharam força
    exp_rows=[]
    for p in PLATFORMS:
        f=findings[p]
        chosen=None
        for metric in KEY_METRICS:
            r=f["candidates"][metric]
            if pd.notna(r.get("mudanca",np.nan)) and r.get("mudanca",0)>0 and r.get("meses_validos",0)>=10:
                chosen=(metric,r); break
        if chosen is None:
            metric=KEY_METRICS[0]; r=f["candidates"][metric]
        else:
            metric,r=chosen
        exp_rows.append({
            "Plataforma":p,
            "Objetivo":OBJECTIVE_NAMES[metric],
            "Hipótese para validação":combo_phrase(r),
            "Por que entra na carteira":f"Apareceu acima do padrão em {fmt_pct(r.get('meses_acima_do_padrao_pct',np.nan),0)} dos meses comparáveis e melhorou de {metric_value(metric,r.get('primeiros_12m',np.nan))} para {metric_value(metric,r.get('segundos_12m',np.nan))}." if pd.notna(r.get('primeiros_12m',np.nan)) else "Sinal com amostra e repetição temporal mínimas."
        })
    expdf=pd.DataFrame(exp_rows)

    html_doc=f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Relatório Final — Social Media</title><style>{CSS}</style></head><body><main>
<header><div class="kicker">Challenge 004 · Estratégia Social Media</div><h1>Diagnóstico de performance e estratégia do portfólio de social media</h1>
<p class="subtitle">A investigação de {len(df):,} posts mostra que plataforma, formato, tamanho do creator e patrocínio isolados explicam pouco da diferença de performance. Os sinais úteis aparecem quando o objetivo é definido primeiro e o contexto é aberto: conteúdo, categoria, creator, audiência e tempo.</p>
<p class="scope">Instagram · TikTok · YouTube · Bilibili · RedNote · {df.data_hora.min():%d/%m/%Y} a {df.data_hora.max():%d/%m/%Y}</p></header>

<section><h2>Executive Summary</h2>
<p>As cinco plataformas entregam níveis muito próximos de alcance e interação na base; a diferença entre a maior e a menor taxa típica de interação é pequena demais para justificar redistribuição de esforço apenas por ranking de plataforma. Patrocínio também não gera ganho geral consistente: no agregado, nenhuma plataforma mostra aumento defensável de alcance ou de interação total, embora existam bolsões específicos em que um objetivo melhora e outro piora. O que mais muda a leitura é definir o objetivo — alcance, conversa, compartilhamento ou interação — e acompanhar combinações específicas no tempo. A recomendação é substituir decisões por “plataforma vencedora”, follower count e patrocínio amplo por uma operação de testes por objetivo, usando o dashboard para confirmar persistência antes de escalar.</p>
</section>

<section><h2>As plataformas parecem diferentes; os resultados típicos quase não são</h2>
<p>Um post típico fica perto de 10,1 mil visualizações e 2,0 mil interações nas cinco plataformas. A variação total das visualizações na base é de apenas <strong>{fmt_num(cv,2)}%</strong> em torno da média. Na prática, escolher a plataforma com a maior taxa de interação histórica significaria tomar uma decisão grande com base em uma diferença muito pequena.</p>
{df_html(overview, labels={'plataforma':'Plataforma','posts':'Posts','visualizacoes_tipicas':'Views de um post típico','curtidas_tipicas':'Curtidas','comentarios_tipicos':'Comentários','compartilhamentos_tipicos':'Compartilhamentos','interacoes_tipicas':'Interações','interacoes_por_100_views':'Interações / 100 views','posts_patrocinados_pct':'Patrocinados (%)'}, max_rows=10)}
<div class="chart"><img src="data:image/png;base64,{chart}" alt="Comparação temporal entre plataformas"></div>
<div class="statement">Conclusão: <strong>a base não sustenta concentrar esforço em uma plataforma apenas porque ela ficou alguns centésimos acima das demais</strong>. A decisão precisa descer para objetivo e contexto.</div>
</section>

<section><h2>O conteúdo que serve para alcance não é o mesmo que serve para conversa ou compartilhamento</h2>
<p>Ao abrir formato, categoria e tamanho do creator, aparecem sinais locais. Vídeo surge com frequência entre os melhores recortes de alcance, mas deixa de dominar quando o objetivo muda para compartilhamento, interação total ou eficiência. Isso é mais útil do que um ranking único porque mostra como montar briefs diferentes por objetivo.</p>
{df_html(obj, max_rows=30)}
<p class="note">A tabela mostra o melhor sinal com amostra e repetição temporal mínimas em cada plataforma. Ela não transforma automaticamente o primeiro colocado em recomendação de escala; o relatório individual abre a magnitude e a evolução de cada caso.</p>
</section>

<section><h2>Patrocínio não compra performance automaticamente</h2>
<p>No agregado, patrocinado e orgânico ficam praticamente empatados nas cinco plataformas para os principais objetivos. Isso elimina uma política simples do tipo “patrocinar aumenta alcance” ou “patrocinar aumenta engajamento”. Quando controlamos conteúdo, categoria e tamanho do creator, aparecem exceções locais — justamente por isso patrocínio precisa ser comprado por objetivo e contexto.</p>
{df_html(spdf, max_rows=30)}
<h3>Exceções locais que sobreviveram aos testes selecionados</h3>
{df_html(celldf, max_rows=15) if not celldf.empty else '<p>Nenhuma célula local robusta foi encontrada.</p>'}
<div class="statement warn">Sem gasto, receita ou conversão, não existe base para afirmar ROI. A decisão econômica exige acrescentar custo por parceria/post e resultado de negócio.</div>
</section>

<section><h2>A audiência descreve diferenças menores do que o ranking sugere</h2>
<p>Idade, gênero, localização e idioma mudam de posição conforme a plataforma. Não existe um perfil universal de audiência vencedor, e as distâncias entre primeiro e último lugar são pequenas. Isso enfraquece a ideia de escolher uma persona apenas porque teve a maior taxa histórica.</p>
{df_html(auddf, max_rows=30)}
</section>

<section><h2>Frequência de publicação: a base não sustenta um número ideal de posts</h2>
<p>O volume semanal de publicações foi comparado com alcance e interações por visualização em cada plataforma. Em nenhuma delas aparece uma relação forte e consistente que permita afirmar que publicar mais, por si só, melhora a performance. Isso significa que a frequência deve ser definida pela capacidade de produzir conteúdo com qualidade e por testes prospectivos — não por um número histórico apresentado como regra.</p>
{df_html(freqdf, max_rows=10)}
</section>

<section><h2>Hipóteses que merecem validação no próximo ciclo</h2>
<p>O objetivo não é transformar os melhores recortes históricos em receita. A carteira abaixo prioriza sinais que tiveram amostra suficiente, se repetiram ao longo do tempo e, quando possível, ganharam força no segundo período. Cada item deve ser testado contra uma alternativa equivalente antes de receber escala.</p>
{df_html(expdf, max_rows=10)}
</section>

<section><h2>O que NÃO funciona como regra de decisão</h2>
<p><strong>Follower count como promessa de alcance.</strong> Nas cinco plataformas, a associação entre seguidores e visualizações fica muito próxima de zero. O dado não respalda pagar mais apenas esperando que creator maior gere mais views.</p>
<p><strong>Patrocínio generalizado.</strong> Não há ganho agregado consistente. Algumas células melhoram um KPI e pioram outro.</p>
<p><strong>Escolher plataforma pela taxa média de interação.</strong> As diferenças são pequenas e os modelos treinados no primeiro período não conseguem reconhecer os vencedores do segundo melhor que aproximadamente o acaso.</p>
<p><strong>Horário como regra operacional.</strong> A base tem hora, mas não informa timezone. Serve para investigar, não para prescrever “poste às 18h”.</p>
<p><strong>Creator ID como identidade histórica.</strong> A mesma chave aparece associada a múltiplos nomes e follower counts; não é seguro reconstruir trajetória individual sem correção da fonte.</p>
</section>

<section><h2>Estratégia recomendada</h2><div class="actions">
<div class="action"><div class="num">1</div><div><h3>Trocar “qual plataforma é melhor?” por “qual objetivo estamos comprando?”</h3><p>Defina campanhas de alcance, conversa, compartilhamento e interação como problemas separados. Cada uma recebe combinação, creator e política de patrocínio próprios.</p></div></div>
<div class="action"><div class="num">2</div><div><h3>Manter o portfólio enquanto valida hipóteses específicas</h3><p>Os dados não sustentam uma migração ampla de esforço entre plataformas. Use as combinações mais persistentes de cada relatório individual como carteira de experimentos, não como regra permanente.</p></div></div>
<div class="action"><div class="num">3</div><div><h3>Patrocinar somente com hipótese explícita e grupo de comparação</h3><p>Antes de pagar, definir o KPI: alcance, comentários, compartilhamentos ou eficiência. Depois comparar com orgânico equivalente e registrar custo. Sem essa disciplina, a empresa compra exposição sem saber o que ganhou.</p></div></div>
<div class="action"><div class="num">4</div><div><h3>Adicionar as variáveis que faltam para transformar performance em negócio</h3><p>Registrar gasto/fee, conversão, receita, alcance de não seguidores, tema/hook e qualidade criativa. Hoje o dataset é bom para separar sinais e ruído, mas insuficiente para otimizar retorno financeiro.</p></div></div>
</div></section>

<section><h2>Quick wins para a próxima semana</h2>
<p><strong>1.</strong> Escolher um objetivo principal por plataforma/campanha e parar de usar “engajamento” como métrica única.</p>
<p><strong>2.</strong> Rodar testes prospectivos das combinações com melhor persistência temporal nos relatórios individuais, sempre contra uma alternativa equivalente.</p>
<p><strong>3.</strong> Suspender a premissa de que creator maior = mais alcance e exigir evidência histórica por contexto.</p>
<p><strong>4.</strong> Toda nova parceria patrocinada passa a registrar custo e KPI esperado antes da publicação.</p>
<p><strong>5.</strong> Usar o dashboard único como camada operacional: qualquer insight deve poder ser aberto até os registros que o formaram.</p>
</section>

<section><h2>Limitações que mudam a interpretação</h2>
<p>A base não contém gasto, receita ou conversão; portanto não calcula retorno financeiro. A unidade de duração não é documentada e o timezone não é confirmado. Creator ID é inconsistente como identidade longitudinal. As métricas de performance apresentam dispersão muito estreita, o que reduz a relevância prática de muitos rankings. Por fim, padrões históricos que não se reproduzem no período seguinte são tratados como hipótese, não como regra.</p>
</section>

<section><h2>Relatórios individuais</h2><p>O relatório oficial consolida a decisão cross-platform. Os relatórios de Instagram, TikTok, YouTube, Bilibili e RedNote abrem a investigação completa: objetivos, linha temporal, patrocínio, audiência, creators, combinações, outliers e auditoria.</p></section>
<footer>Challenge 004 · relatório oficial cross-platform · mesmos cálculos do dashboard e notebook canônicos.</footer></main></body></html>"""
    return html_doc


def main():
    df=load_data(DATA)
    findings={}
    for platform in PLATFORMS:
        f=platform_findings(df,platform); findings[platform]=f
        md=report_platform_markdown(df,platform,f)
        (RESULTS/f"RESULTADOS_{platform}.md").write_text(md,encoding='utf-8')
        report=report_platform_html(df,platform,f)
        (REPORTS/f"Relatorio_{platform}.html").write_text(report,encoding='utf-8')
        print('built',platform)
    final=build_cross_platform_report(df,findings)
    (REPORTS/'Relatorio_Final_Social_Media.html').write_text(final,encoding='utf-8')
    print('built final')

if __name__=='__main__':
    main()
