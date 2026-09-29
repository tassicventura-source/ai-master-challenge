from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats

# -----------------------------------------------------------------------------
# Canonical schema and business labels
# -----------------------------------------------------------------------------
RAW_TO_PT = {
    "platform": "plataforma",
    "content_id": "id_conteudo",
    "creator_id": "id_criador",
    "creator_name": "nome_criador",
    "content_url": "url_conteudo",
    "content_type": "formato",
    "content_category": "categoria",
    "post_date": "data_publicacao",
    "language": "idioma",
    "content_length": "comprimento_duracao",
    "content_description": "descricao_conteudo",
    "views": "visualizacoes",
    "likes": "curtidas",
    "shares": "compartilhamentos",
    "comments_count": "comentarios",
    "comments_text": "texto_comentarios",
    "follower_count": "seguidores_criador",
    "is_sponsored": "patrocinado",
    "disclosure_type": "tipo_divulgacao",
    "sponsor_name": "nome_patrocinador",
    "sponsor_category": "categoria_patrocinador",
    "disclosure_location": "local_divulgacao",
    "audience_age_distribution": "faixa_etaria_audiencia",
    "audience_gender_distribution": "genero_audiencia",
    "audience_location": "localizacao_audiencia",
}

METRICS = {
    "visualizacoes": "Visualizações",
    "curtidas": "Curtidas",
    "comentarios": "Comentários",
    "compartilhamentos": "Compartilhamentos",
    "interacoes_totais": "Interações totais",
    "taxa_curtidas": "Curtidas a cada 100 visualizações",
    "taxa_comentarios": "Comentários a cada 100 visualizações",
    "taxa_compartilhamentos": "Compartilhamentos a cada 100 visualizações",
    "taxa_engajamento": "Interações a cada 100 visualizações",
    "visualizacoes_por_seguidor": "Visualizações por seguidor",
    "interacoes_por_seguidor": "Interações por seguidor",
}

OBJECTIVE_METRICS = [
    "visualizacoes", "curtidas", "comentarios", "compartilhamentos",
    "interacoes_totais", "taxa_curtidas", "taxa_comentarios",
    "taxa_compartilhamentos", "taxa_engajamento"
]

DIMENSION_LABELS = {
    "plataforma": "Plataforma",
    "formato": "Formato",
    "categoria": "Categoria",
    "porte_criador": "Tamanho do creator",
    "patrocinado": "Patrocínio",
    "faixa_etaria_audiencia": "Idade predominante da audiência",
    "genero_audiencia": "Gênero predominante da audiência",
    "localizacao_audiencia": "Localização predominante da audiência",
    "idioma": "Idioma",
    "duracao_relativa": "Duração relativa",
    "faixa_horaria": "Faixa horária",
    "dia_semana": "Dia da semana",
    "mes_num": "Mês do ano",
    "trimestre_calendario": "Trimestre",
    "quantidade_hashtags": "Quantidade de hashtags",
}

CORE_DIMENSIONS = [
    "formato", "categoria", "porte_criador", "patrocinado",
    "faixa_etaria_audiencia", "genero_audiencia", "localizacao_audiencia",
    "idioma", "duracao_relativa", "faixa_horaria", "dia_semana"
]

CREATOR_BINS = [0, 10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000, np.inf]
CREATOR_LABELS = ["<10 mil", "10–50 mil", "50–100 mil", "100–250 mil", "250–500 mil", "500 mil–1 mi", "1 mi+"]

WEEKDAY_MAP = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}


# -----------------------------------------------------------------------------
# Loading / preparation
# -----------------------------------------------------------------------------
def _parse_date(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, format="%m/%d/%y %I:%M %p", errors="coerce")
    if parsed.isna().mean() > 0.01:
        parsed = pd.to_datetime(series, errors="coerce")
    return parsed


def _relative_duration_quintile(group: pd.Series) -> pd.Series:
    labels = ["Muito curta", "Curta", "Média", "Longa", "Muito longa"]
    valid = group.notna()
    result = pd.Series(index=group.index, dtype="object")
    if valid.sum() < 10 or group[valid].nunique() < 5:
        result.loc[valid] = "Sem faixa confiável"
        return result
    # Rank first avoids duplicate-edge failures in qcut.
    ranked = group[valid].rank(method="first")
    result.loc[valid] = pd.qcut(ranked, q=5, labels=labels).astype(str)
    return result


def prepare_data(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.rename(columns=RAW_TO_PT).copy()
    required = ["plataforma", "data_publicacao", "visualizacoes", "curtidas", "comentarios", "compartilhamentos", "seguidores_criador"]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    d["data_hora"] = _parse_date(d["data_publicacao"])
    d = d[d["data_hora"].notna()].copy()
    for c in ["visualizacoes", "curtidas", "comentarios", "compartilhamentos", "seguidores_criador", "comprimento_duracao"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")

    d["interacoes_totais"] = d[["curtidas", "comentarios", "compartilhamentos"]].sum(axis=1, min_count=1)
    views = d["visualizacoes"].replace(0, np.nan)
    d["taxa_curtidas"] = d["curtidas"] / views * 100
    d["taxa_comentarios"] = d["comentarios"] / views * 100
    d["taxa_compartilhamentos"] = d["compartilhamentos"] / views * 100
    d["taxa_engajamento"] = d["interacoes_totais"] / views * 100
    followers = d["seguidores_criador"].replace(0, np.nan)
    d["visualizacoes_por_seguidor"] = d["visualizacoes"] / followers
    d["interacoes_por_seguidor"] = d["interacoes_totais"] / followers
    d["porte_criador"] = pd.cut(
        d["seguidores_criador"], CREATOR_BINS, labels=CREATOR_LABELS,
        right=False, include_lowest=True
    )

    # Duration has no documented unit. Analyze only relative position within platform.
    d["duracao_relativa"] = d.groupby("plataforma", group_keys=False)["comprimento_duracao"].apply(_relative_duration_quintile)

    dt = d["data_hora"]
    d["ano"] = dt.dt.year
    d["mes"] = dt.dt.to_period("M").astype(str)
    d["mes_num"] = dt.dt.month
    d["trimestre"] = dt.dt.to_period("Q").astype(str)
    d["trimestre_calendario"] = "T" + dt.dt.quarter.astype(str)
    d["semana_inicio"] = (dt - pd.to_timedelta(dt.dt.weekday, unit="D")).dt.normalize()
    d["semana_iso"] = dt.dt.isocalendar().week.astype(int)
    d["semana_do_mes"] = ((dt.dt.day - 1) // 7 + 1).astype(int)
    d["dia"] = dt.dt.date.astype(str)
    d["dia_semana"] = dt.dt.weekday.map(WEEKDAY_MAP)
    d["hora"] = dt.dt.hour
    d["faixa_horaria"] = pd.cut(
        d["hora"], [-1, 5, 11, 17, 23],
        labels=["00–05", "06–11", "12–17", "18–23"]
    )

    # Two equivalent 12-month windows for every platform use the global dataset start.
    start = dt.min().normalize()
    split = start + pd.DateOffset(months=12)
    d["periodo_12m"] = np.where(dt < split, "Primeiros 12 meses", "Segundos 12 meses")
    d["dias_desde_inicio"] = (dt - start).dt.days

    def count_hashtags(value) -> int:
        if pd.isna(value) or not str(value).strip():
            return 0
        return len([t for t in re.split(r"[,#]+", str(value)) if t.strip()])

    d["quantidade_hashtags"] = d["hashtags"].apply(count_hashtags)
    return d


def load_data(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists() and path.suffix == ".csv":
        path = path.with_suffix(".csv.gz")
    return prepare_data(pd.read_csv(path))


def platform_data(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    return df[df["plataforma"].astype(str).str.lower() == str(platform).lower()].copy()


def apply_filters(df: pd.DataFrame, filters: dict | None = None) -> pd.DataFrame:
    if not filters:
        return df.copy()
    d = df.copy()
    for col, value in filters.items():
        if value is None:
            continue
        if col == "date_range":
            lo, hi = value
            lo, hi = pd.Timestamp(lo), pd.Timestamp(hi) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            d = d[(d["data_hora"] >= lo) & (d["data_hora"] <= hi)]
        elif isinstance(value, (list, tuple, set, pd.Index, np.ndarray)):
            if len(value):
                d = d[d[col].isin(value)]
        else:
            d = d[d[col] == value]
    return d.copy()


# -----------------------------------------------------------------------------
# Descriptive / robustness utilities
# -----------------------------------------------------------------------------
def platform_overview(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("plataforma", observed=True).agg(
        posts=("id", "size"),
        inicio=("data_hora", "min"),
        fim=("data_hora", "max"),
        visualizacoes_tipicas=("visualizacoes", "median"),
        curtidas_tipicas=("curtidas", "median"),
        comentarios_tipicos=("comentarios", "median"),
        compartilhamentos_tipicos=("compartilhamentos", "median"),
        interacoes_tipicas=("interacoes_totais", "median"),
        interacoes_por_100_views=("taxa_engajamento", "median"),
        posts_patrocinados_pct=("patrocinado", lambda s: 100 * s.mean()),
    ).reset_index()


def audit_quality(df: pd.DataFrame) -> dict:
    metrics = ["visualizacoes", "curtidas", "comentarios", "compartilhamentos", "interacoes_totais", "taxa_engajamento"]
    desc = {}
    for c in metrics:
        s = df[c].dropna()
        desc[c] = {
            "n": int(s.size), "media": float(s.mean()), "mediana": float(s.median()),
            "desvio": float(s.std()), "variacao_relativa": float(s.std() / s.mean()) if s.mean() else np.nan,
            "min": float(s.min()), "p01": float(s.quantile(.01)), "p05": float(s.quantile(.05)),
            "p95": float(s.quantile(.95)), "p99": float(s.quantile(.99)), "max": float(s.max())
        }
    creators = df.groupby("id_criador", dropna=False).agg(
        posts=("id", "size"), nomes=("nome_criador", "nunique"),
        contagens_seguidores=("seguidores_criador", "nunique"),
        min_seguidores=("seguidores_criador", "min"), max_seguidores=("seguidores_criador", "max")
    ).reset_index()
    return {
        "posts": int(len(df)), "inicio": df["data_hora"].min(), "fim": df["data_hora"].max(),
        "linhas_duplicadas": int(df.duplicated().sum()),
        "ids_conteudo_duplicados": int(df["id_conteudo"].duplicated().sum()) if "id_conteudo" in df else 0,
        "distribuicao_metricas": desc,
        "creator_ids": int(len(creators)),
        "creator_ids_multiplos_nomes_pct": float(100 * (creators["nomes"] > 1).mean()),
        "creator_ids_multiplas_contagens_pct": float(100 * (creators["contagens_seguidores"] > 1).mean()),
    }


def bootstrap_diff_median(a: Sequence[float], b: Sequence[float], n_boot: int = 500, seed: int = 42) -> tuple[float, float, float]:
    a = np.asarray(pd.Series(a).dropna(), dtype=float)
    b = np.asarray(pd.Series(b).dropna(), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    observed = float(np.median(a) - np.median(b))
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        diffs[i] = np.median(rng.choice(a, len(a), replace=True)) - np.median(rng.choice(b, len(b), replace=True))
    lo, hi = np.quantile(diffs, [.025, .975])
    return observed, float(lo), float(hi)


def rank_biserial(a: Sequence[float], b: Sequence[float]) -> float:
    a = np.asarray(pd.Series(a).dropna(), dtype=float)
    b = np.asarray(pd.Series(b).dropna(), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return np.nan
    u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic
    return float(2 * u / (len(a) * len(b)) - 1)


def group_summary(df: pd.DataFrame, group_cols: str | list[str], metric: str = "taxa_engajamento", min_n: int = 20) -> pd.DataFrame:
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    if df.empty:
        return pd.DataFrame()
    g = df.dropna(subset=[metric]).groupby(group_cols, dropna=False, observed=True)[metric]
    out = g.agg(
        n="size", media="mean", mediana="median", desvio="std",
        p05=lambda s: s.quantile(.05), p25=lambda s: s.quantile(.25),
        p75=lambda s: s.quantile(.75), p95=lambda s: s.quantile(.95)
    ).reset_index()
    out["amplitude_central"] = out["p75"] - out["p25"]
    base = df[metric].median()
    out["diferenca_para_plataforma"] = out["mediana"] - base
    out["diferenca_relativa_pct"] = np.where(base != 0, 100 * (out["mediana"] / base - 1), np.nan)
    return out[out["n"] >= min_n].sort_values(["mediana", "n"], ascending=[False, False]).reset_index(drop=True)


def objective_matrix(df: pd.DataFrame, dimensions: Iterable[str] | None = None, min_n: int = 60) -> pd.DataFrame:
    dimensions = list(dimensions or CORE_DIMENSIONS)
    rows = []
    for dim in dimensions:
        for metric in OBJECTIVE_METRICS:
            tab = group_summary(df, dim, metric, min_n=min_n)
            if tab.empty:
                continue
            best, worst = tab.iloc[0], tab.iloc[-1]
            rows.append({
                "dimensao": dim, "metrica": metric,
                "melhor_segmento": str(best[dim]), "n_melhor": int(best.n),
                "resultado_melhor": float(best.mediana), "diferenca_melhor": float(best.diferenca_para_plataforma),
                "pior_segmento": str(worst[dim]), "n_pior": int(worst.n),
                "resultado_pior": float(worst.mediana), "diferenca_pior": float(worst.diferenca_para_plataforma)
            })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Time
# -----------------------------------------------------------------------------
def time_series(df: pd.DataFrame, metric: str = "taxa_engajamento", freq: str = "MS") -> pd.DataFrame:
    g = df.set_index("data_hora").groupby(pd.Grouper(freq=freq))[metric]
    out = g.agg(n="size", mediana="median", media="mean", p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75)).reset_index()
    return out[out.n > 0]


def time_grain_table(df: pd.DataFrame, metric: str = "taxa_engajamento", grain: str = "mes") -> pd.DataFrame:
    if grain == "mes":
        keys = ["mes"]
    elif grain == "trimestre":
        keys = ["trimestre"]
    elif grain == "semana":
        keys = ["semana_inicio"]
    elif grain == "dia":
        keys = ["dia"]
    elif grain == "dia_semana":
        keys = ["dia_semana"]
    elif grain == "faixa_horaria":
        keys = ["faixa_horaria"]
    else:
        raise ValueError(f"Grão temporal desconhecido: {grain}")
    return group_summary(df, keys, metric, min_n=1)



def frequency_performance(df: pd.DataFrame, metric: str = "taxa_engajamento", grain: str = "semana") -> dict:
    """Relates posting volume to typical performance over time; association only, not causality."""
    if grain == "semana":
        key = "semana_inicio"
    elif grain == "mes":
        key = "mes"
    elif grain == "dia":
        key = "dia"
    else:
        raise ValueError("grain must be semana, mes or dia")
    tab = df.groupby(key).agg(posts=("id","size"), resultado=(metric,"median")).reset_index()
    valid = tab.dropna(subset=["posts","resultado"])
    if len(valid) < 5 or valid.posts.nunique() < 2:
        rho = p = np.nan
    else:
        rho, p = stats.spearmanr(valid.posts, valid.resultado)
    return {"grao":grain,"metrica":metric,"periodos":len(valid),"correlacao_volume_resultado":float(rho) if pd.notna(rho) else np.nan,"p_value":float(p) if pd.notna(p) else np.nan,"tabela":tab}

def period_comparison(df: pd.DataFrame, group_cols: list[str], metric: str = "taxa_engajamento", min_n: int = 40) -> pd.DataFrame:
    rows = []
    for keys, g in df.groupby(group_cols, dropna=False, observed=True):
        p1 = g[g.periodo_12m == "Primeiros 12 meses"][metric].dropna()
        p2 = g[g.periodo_12m == "Segundos 12 meses"][metric].dropna()
        if len(p1) < min_n or len(p2) < min_n:
            continue
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, map(str, keys)))
        row.update({
            "n_primeiros_12m": len(p1), "n_segundos_12m": len(p2),
            "primeiros_12m": float(p1.median()), "segundos_12m": float(p2.median()),
            "mudanca": float(p2.median() - p1.median()),
            "efeito_ordinal": rank_biserial(p2, p1)
        })
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("mudanca", ascending=False).reset_index(drop=True)


def mix_shift(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    tab = pd.crosstab(df["periodo_12m"], df[dimension], normalize="index").T
    p1, p2 = "Primeiros 12 meses", "Segundos 12 meses"
    out = tab.reset_index()
    if p1 in out.columns and p2 in out.columns:
        out["mudanca_pontos_percentuais"] = 100 * (out[p2] - out[p1])
        out[p1] *= 100
        out[p2] *= 100
    return out.sort_values("mudanca_pontos_percentuais", ascending=False) if "mudanca_pontos_percentuais" in out else out


def monthly_segment_path(df: pd.DataFrame, group_cols: list[str], metric: str = "taxa_engajamento", min_month_n: int = 8, min_months: int = 10) -> pd.DataFrame:
    base_month = df.groupby("mes")[metric].median().rename("padrao_mes")
    rows = []
    for keys, g in df.groupby(group_cols, dropna=False, observed=True):
        gm = g.groupby("mes")[metric].agg(n="size", resultado="median").join(base_month)
        gm = gm[gm.n >= min_month_n].copy()
        if len(gm) < min_months:
            continue
        gm["diferenca_mes"] = gm.resultado - gm.padrao_mes
        x = np.arange(len(gm))
        slope = float(stats.linregress(x, gm["diferenca_mes"]).slope) if len(gm) >= 3 else np.nan
        signs = np.sign(gm["diferenca_mes"].to_numpy())
        longest, current, previous = 0, 0, 0
        for sign in signs:
            if sign == 0:
                current, previous = 0, 0
            elif sign == previous:
                current += 1
            else:
                current, previous = 1, sign
            longest = max(longest, current)
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, map(str, keys)))
        row.update({
            "meses_validos": len(gm), "posts_nesses_meses": int(gm.n.sum()),
            "diferenca_mediana_mensal": float(gm.diferenca_mes.median()),
            "meses_acima_do_padrao_pct": float(100 * (gm.diferenca_mes > 0).mean()),
            "tendencia_mensal": slope,
            "maior_sequencia_mesmo_sinal": int(longest),
            "primeiro_mes_diferenca": float(gm.diferenca_mes.iloc[0]),
            "ultimo_mes_diferenca": float(gm.diferenca_mes.iloc[-1])
        })
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["diferenca_mediana_mensal", "meses_acima_do_padrao_pct"], ascending=False).reset_index(drop=True)


def regime_scan(df: pd.DataFrame, metric: str = "taxa_engajamento", window_months: int = 3) -> pd.DataFrame:
    ts = time_series(df, metric, "MS").copy()
    ts["antes"] = ts["mediana"].rolling(window_months, min_periods=window_months).mean().shift(1)
    ts["depois"] = ts["mediana"][::-1].rolling(window_months, min_periods=window_months).mean()[::-1].shift(-1)
    ts["mudanca_de_nivel"] = ts["depois"] - ts["antes"]
    return ts.sort_values("mudanca_de_nivel", key=lambda s: s.abs(), ascending=False)


# -----------------------------------------------------------------------------
# Sponsorship
# -----------------------------------------------------------------------------
def sponsorship_overall(df: pd.DataFrame, metrics: Iterable[str] | None = None, n_boot: int = 400) -> pd.DataFrame:
    metrics = list(metrics or OBJECTIVE_METRICS)
    rows = []
    for metric in metrics:
        sponsored = df.loc[df.patrocinado == True, metric].dropna()
        organic = df.loc[df.patrocinado == False, metric].dropna()
        observed, lo, hi = bootstrap_diff_median(sponsored, organic, n_boot=n_boot)
        rows.append({
            "metrica": metric, "n_patrocinado": len(sponsored), "n_organico": len(organic),
            "resultado_patrocinado": float(sponsored.median()), "resultado_organico": float(organic.median()),
            "diferenca": observed, "intervalo_95_min": lo, "intervalo_95_max": hi,
            "efeito_ordinal": rank_biserial(sponsored, organic),
            "evidencia": "vantagem observável" if lo > 0 else ("desvantagem observável" if hi < 0 else "diferença não separada de zero")
        })
    return pd.DataFrame(rows)


def sponsorship_controlled(df: pd.DataFrame, metric: str = "taxa_engajamento", controls: list[str] | None = None, min_each: int = 25, with_ci: bool = False, n_boot: int = 160) -> pd.DataFrame:
    controls = controls or ["formato", "categoria", "porte_criador"]
    rows = []
    for keys, g in df.groupby(controls, dropna=False, observed=True):
        sponsored = g.loc[g.patrocinado == True, metric].dropna()
        organic = g.loc[g.patrocinado == False, metric].dropna()
        if len(sponsored) < min_each or len(organic) < min_each:
            continue
        observed = float(sponsored.median() - organic.median())
        lo = hi = np.nan
        if with_ci:
            _, lo, hi = bootstrap_diff_median(sponsored, organic, n_boot=n_boot)
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(controls, map(str, keys)))
        row.update({
            "n_patrocinado": len(sponsored), "n_organico": len(organic),
            "resultado_patrocinado": float(sponsored.median()), "resultado_organico": float(organic.median()),
            "diferenca": observed, "intervalo_95_min": lo, "intervalo_95_max": hi,
            "efeito_ordinal": rank_biserial(sponsored, organic),
            "evidencia": ("positivo" if lo > 0 else ("negativo" if hi < 0 else "não conclusivo")) if with_ci else "comparação descritiva controlada"
        })
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("diferenca", ascending=False).reset_index(drop=True)


def sponsorship_strata_with_ci(df: pd.DataFrame, metric: str, rows: pd.DataFrame, controls: list[str] | None = None, n_boot: int = 500) -> pd.DataFrame:
    """Add bootstrap intervals only to selected controlled rows."""
    controls = controls or ["formato", "categoria", "porte_criador"]
    enriched = []
    for _, r in rows.iterrows():
        mask = pd.Series(True, index=df.index)
        for c in controls:
            mask &= df[c].astype(str).eq(str(r[c]))
        g = df[mask]
        sponsored = g.loc[g.patrocinado == True, metric].dropna()
        organic = g.loc[g.patrocinado == False, metric].dropna()
        observed, lo, hi = bootstrap_diff_median(sponsored, organic, n_boot=n_boot)
        rr = r.to_dict()
        rr.update({"diferenca": observed, "intervalo_95_min": lo, "intervalo_95_max": hi,
                   "evidencia": "positivo" if lo > 0 else ("negativo" if hi < 0 else "não conclusivo")})
        enriched.append(rr)
    return pd.DataFrame(enriched)


def monthly_sponsorship(df: pd.DataFrame, metric: str = "taxa_engajamento", min_each: int = 20) -> pd.DataFrame:
    rows = []
    for month, g in df.groupby("mes"):
        sponsored = g.loc[g.patrocinado == True, metric].dropna()
        organic = g.loc[g.patrocinado == False, metric].dropna()
        if len(sponsored) < min_each or len(organic) < min_each:
            continue
        rows.append({
            "mes": month, "n_patrocinado": len(sponsored), "n_organico": len(organic),
            "resultado_patrocinado": float(sponsored.median()), "resultado_organico": float(organic.median()),
            "diferenca": float(sponsored.median() - organic.median()),
            "share_patrocinado_pct": float(100 * g.patrocinado.mean())
        })
    return pd.DataFrame(rows)


def lag_sponsorship_test(df: pd.DataFrame, metric: str = "taxa_engajamento") -> dict:
    organic = df[~df.patrocinado].groupby("mes")[metric].median().rename("resultado_organico")
    share = df.groupby("mes").patrocinado.mean().rename("share_patrocinio")
    x = pd.concat([organic, share], axis=1).sort_index()
    x["share_mes_seguinte"] = x["share_patrocinio"].shift(-1)
    valid = x.dropna()
    if len(valid) < 5:
        return {"meses": len(valid), "correlacao": np.nan, "p_value": np.nan, "tabela": x.reset_index()}
    rho, p = stats.spearmanr(valid["resultado_organico"], valid["share_mes_seguinte"])
    return {"meses": len(valid), "correlacao": float(rho), "p_value": float(p), "tabela": x.reset_index()}


def sponsorship_simpson_scan(df: pd.DataFrame, metric: str = "taxa_engajamento", controls: list[str] | None = None, min_each: int = 20) -> dict:
    controls = controls or ["formato", "categoria", "porte_criador"]
    overall = sponsorship_overall(df, [metric], n_boot=250).iloc[0]
    strata = sponsorship_controlled(df, metric, controls=controls, min_each=min_each, with_ci=False)
    if strata.empty:
        return {"overall_difference": float(overall.diferenca), "valid_strata": 0, "positive_strata_pct": np.nan, "negative_strata_pct": np.nan, "possible_composition_effect": False, "strata": strata}
    pos = float(100 * (strata.diferenca > 0).mean())
    neg = float(100 * (strata.diferenca < 0).mean())
    overall_sign = np.sign(overall.diferenca)
    majority_sign = 1 if pos > 60 else (-1 if neg > 60 else 0)
    return {
        "overall_difference": float(overall.diferenca), "valid_strata": int(len(strata)),
        "positive_strata_pct": pos, "negative_strata_pct": neg,
        "possible_composition_effect": bool(overall_sign != 0 and majority_sign != 0 and overall_sign != majority_sign),
        "strata": strata
    }


# -----------------------------------------------------------------------------
# Combinations, outliers, hashtags, creators
# -----------------------------------------------------------------------------
def combination_analysis(df: pd.DataFrame, dimensions: list[str], metric: str = "taxa_engajamento", min_n: int = 80, min_month_n: int = 8, min_months: int = 8) -> pd.DataFrame:
    if not dimensions:
        return pd.DataFrame()
    df = df.copy()
    for dimension in dimensions:
        df[dimension] = df[dimension].astype(str)
    base = float(df[metric].median())
    agg = df.groupby(dimensions, observed=True, dropna=False)[metric].agg(
        n="size", mediana="median", media="mean", desvio="std",
        p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75)
    ).reset_index()
    agg = agg[agg.n >= min_n].copy()
    if agg.empty:
        return agg
    agg["diferenca_para_plataforma"] = agg.mediana - base
    agg["diferenca_relativa_pct"] = np.where(base != 0, 100 * (agg.mediana / base - 1), np.nan)
    path = monthly_segment_path(df, dimensions, metric, min_month_n=min_month_n, min_months=min_months)
    if not path.empty:
        agg = agg.merge(path, on=dimensions, how="left")
    period = period_comparison(df, dimensions, metric, min_n=max(20, min_n // 3))
    if not period.empty:
        keep = dimensions + ["n_primeiros_12m", "n_segundos_12m", "primeiros_12m", "segundos_12m", "mudanca"]
        agg = agg.merge(period[keep], on=dimensions, how="left")
    return agg.sort_values(["mediana", "n"], ascending=[False, False]).reset_index(drop=True)


def outlier_profile(df: pd.DataFrame, metric: str = "taxa_engajamento", pct: float = .05, dimensions: Iterable[str] | None = None) -> pd.DataFrame:
    dimensions = list(dimensions or CORE_DIMENSIONS)
    s = df[metric].dropna()
    lo, hi = s.quantile(pct), s.quantile(1 - pct)
    top, bottom = df[df[metric] >= hi], df[df[metric] <= lo]
    rows = []
    for dim in dimensions:
        base = df[dim].astype(str).value_counts(normalize=True, dropna=False)
        tp = top[dim].astype(str).value_counts(normalize=True, dropna=False)
        bt = bottom[dim].astype(str).value_counts(normalize=True, dropna=False)
        for segment in base.index.union(tp.index).union(bt.index):
            b, t, bo = base.get(segment, 0), tp.get(segment, 0), bt.get(segment, 0)
            rows.append({
                "metrica": metric, "faixa_extrema": pct, "dimensao": dim, "segmento": segment,
                "participacao_base_pct": 100 * b, "participacao_top_pct": 100 * t, "participacao_bottom_pct": 100 * bo,
                "indice_top": t / b if b else np.nan, "indice_bottom": bo / b if b else np.nan,
                "top_n": int((top[dim].astype(str) == segment).sum()),
                "bottom_n": int((bottom[dim].astype(str) == segment).sum())
            })
    return pd.DataFrame(rows)


def top_bottom_rows(df: pd.DataFrame, metric: str = "taxa_engajamento", pct: float = .01) -> tuple[pd.DataFrame, pd.DataFrame]:
    lo, hi = df[metric].quantile(pct), df[metric].quantile(1 - pct)
    cols = [
        "id", "id_conteudo", "plataforma", "nome_criador", "formato", "categoria", "data_publicacao",
        "visualizacoes", "curtidas", "comentarios", "compartilhamentos", "interacoes_totais", "taxa_engajamento",
        "seguidores_criador", "patrocinado", "faixa_etaria_audiencia", "genero_audiencia", "localizacao_audiencia", "idioma", "hashtags"
    ]
    return (
        df[df[metric] >= hi][list(dict.fromkeys(cols + [metric]))].sort_values(metric, ascending=False),
        df[df[metric] <= lo][list(dict.fromkeys(cols + [metric]))].sort_values(metric)
    )


def hashtag_analysis(df: pd.DataFrame, metric: str = "taxa_engajamento", min_n: int = 30) -> pd.DataFrame:
    rows = []
    for _, r in df[["id", metric, "hashtags"]].dropna(subset=[metric]).iterrows():
        raw = "" if pd.isna(r.hashtags) else str(r.hashtags)
        tokens = [t.strip().lower() for t in re.split(r"[,#]+", raw) if t.strip()]
        for token in set(tokens):
            rows.append((r.id, token, r[metric]))
    if not rows:
        return pd.DataFrame()
    x = pd.DataFrame(rows, columns=["id", "hashtag", "resultado"])
    out = x.groupby("hashtag").resultado.agg(
        n="size", media="mean", mediana="median", p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75)
    ).reset_index()
    out = out[out.n >= min_n].copy()
    out["diferenca_para_plataforma"] = out.mediana - df[metric].median()
    return out.sort_values(["mediana", "n"], ascending=[False, False]).reset_index(drop=True)


def creator_id_audit(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("id_criador", dropna=False).agg(
        posts=("id", "size"), nomes_distintos=("nome_criador", "nunique"),
        seguidores_distintos=("seguidores_criador", "nunique"),
        min_seguidores=("seguidores_criador", "min"), max_seguidores=("seguidores_criador", "max"),
        nomes_exemplo=("nome_criador", lambda s: ", ".join(map(str, pd.unique(s)[:8])))
    ).reset_index().sort_values(["nomes_distintos", "seguidores_distintos", "posts"], ascending=False)


def numeric_correlations(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "visualizacoes", "curtidas", "comentarios", "compartilhamentos", "interacoes_totais",
        "taxa_curtidas", "taxa_comentarios", "taxa_compartilhamentos", "taxa_engajamento",
        "seguidores_criador", "comprimento_duracao", "quantidade_hashtags", "hora"
    ]
    return df[cols].corr(method="spearman")


# -----------------------------------------------------------------------------
# Predictability / stress tests
# -----------------------------------------------------------------------------
def temporal_predictability(df: pd.DataFrame, metric: str = "taxa_engajamento", top_quantile: float = .8, random_state: int = 42) -> dict:
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import Ridge, LogisticRegression
    from sklearn.metrics import r2_score, roc_auc_score

    categorical = [
        "formato", "categoria", "porte_criador", "patrocinado", "faixa_etaria_audiencia",
        "genero_audiencia", "localizacao_audiencia", "idioma", "faixa_horaria", "dia_semana", "duracao_relativa"
    ]
    numeric = ["seguidores_criador", "comprimento_duracao", "quantidade_hashtags", "hora", "mes_num"]
    cols = categorical + numeric
    train = df[df.periodo_12m == "Primeiros 12 meses"].dropna(subset=[metric]).copy()
    test = df[df.periodo_12m == "Segundos 12 meses"].dropna(subset=[metric]).copy()
    Xtr, Xte = train[cols], test[cols]
    ytr, yte = train[metric], test[metric]
    pre = ColumnTransformer([
        ("categorias", OneHotEncoder(handle_unknown="ignore"), categorical),
        ("numeros", StandardScaler(), numeric)
    ])
    reg = Pipeline([("pre", pre), ("modelo", Ridge(alpha=10.0))])
    reg.fit(Xtr, ytr)
    pred = reg.predict(Xte)
    r2 = float(r2_score(yte, pred))

    threshold = float(ytr.quantile(top_quantile))
    ctr, cte = (ytr >= threshold).astype(int), (yte >= threshold).astype(int)
    clf = Pipeline([
        ("pre", pre),
        ("modelo", LogisticRegression(C=.3, max_iter=500, class_weight="balanced", random_state=random_state))
    ])
    clf.fit(Xtr, ctr)
    probability = clf.predict_proba(Xte)[:, 1]
    auc = float(roc_auc_score(cte, probability)) if cte.nunique() > 1 else np.nan
    return {
        "metrica": metric, "posts_treino": len(train), "posts_teste": len(test),
        "capacidade_explicar_resultado_futuro": r2,
        "capacidade_identificar_top_20_futuro": auc,
        "limiar_top_20_treino": threshold
    }


# -----------------------------------------------------------------------------
# Canonical analytic architecture
# -----------------------------------------------------------------------------
def cross_universe() -> list[dict]:
    return [
        {"familia": "Objetivos", "cruzamentos": [
            "visualizações", "curtidas", "comentários", "compartilhamentos", "interações totais",
            "curtidas/comentários/compartilhamentos por 100 visualizações", "interações por 100 visualizações"
        ]},
        {"familia": "Conteúdo", "cruzamentos": [
            "formato", "categoria", "formato × categoria", "formato × categoria × tamanho do creator",
            "formato × categoria × patrocínio", "formato × duração relativa", "categoria × duração relativa"
        ]},
        {"familia": "Creators", "cruzamentos": [
            "tamanho do creator", "tamanho × formato", "tamanho × categoria", "tamanho × patrocínio",
            "creator_id somente para auditoria de consistência"
        ]},
        {"familia": "Patrocínio", "cruzamentos": [
            "patrocinado × todos os objetivos", "patrocinado × formato/categoria/tamanho/audiência/tempo/duração",
            "formato × categoria × tamanho × patrocínio", "trajetória mensal do ganho/perda do patrocinado",
            "resultado orgânico em um mês × participação patrocinada no mês seguinte"
        ]},
        {"familia": "Audiência", "cruzamentos": [
            "idade/gênero/localização/idioma", "audiência × formato", "audiência × categoria",
            "audiência × tamanho", "audiência × patrocínio", "audiência × formato × categoria"
        ]},
        {"familia": "Tempo", "cruzamentos": [
            "mês", "trimestre", "semana", "dia", "dia da semana", "hora/faixa horária",
            "primeiros 12 meses × segundos 12 meses", "mudança de mix", "mudança de resultado dentro do mesmo segmento",
            "trajetória mensal de combinações", "possíveis mudanças de regime"
        ]},
        {"familia": "Criativo / proxies", "cruzamentos": [
            "duração relativa × formato/categoria/tamanho/patrocínio", "hashtags × formato/categoria",
            "quantidade de hashtags × resultados"
        ]},
        {"familia": "Robustez", "cruzamentos": [
            "top/bottom 1%", "top/bottom 5%", "média × mediana", "agregado × controlado",
            "efeito de composição / possível paradoxo de Simpson", "primeiro período × segundo período",
            "persistência mês a mês", "teste fora do tempo"
        ]},
        {"familia": "Cross-platform", "cruzamentos": [
            "plataforma × objetivo", "plataforma × formato", "plataforma × categoria", "plataforma × tamanho",
            "plataforma × audiência", "plataforma × patrocínio", "plataforma × tempo",
            "mesma combinação em plataformas diferentes"
        ]}
    ]


def analyze_platform(df: pd.DataFrame, platform: str) -> dict:
    d = platform_data(df, platform)
    if d.empty:
        raise ValueError(f"Plataforma não encontrada: {platform}")
    return {
        "plataforma": platform,
        "dados": d,
        "auditoria": audit_quality(d),
        "objetivos": objective_matrix(d, min_n=60),
        "mensal_engajamento": time_series(d, "taxa_engajamento", "MS"),
        "mensal_visualizacoes": time_series(d, "visualizacoes", "MS"),
        "patrocinio_geral": sponsorship_overall(d),
        "patrocinio_engajamento_controlado": sponsorship_controlled(d, "taxa_engajamento", with_ci=False),
        "patrocinio_visualizacoes_controlado": sponsorship_controlled(d, "visualizacoes", with_ci=False),
        "patrocinio_mensal_engajamento": monthly_sponsorship(d, "taxa_engajamento"),
        "patrocinio_mensal_visualizacoes": monthly_sponsorship(d, "visualizacoes"),
        "patrocinio_lag": lag_sponsorship_test(d, "taxa_engajamento"),
        "combinacoes_engajamento": combination_analysis(d, ["formato", "categoria", "porte_criador"], "taxa_engajamento"),
        "combinacoes_visualizacoes": combination_analysis(d, ["formato", "categoria", "porte_criador"], "visualizacoes"),
        "combinacoes_comentarios": combination_analysis(d, ["formato", "categoria", "porte_criador"], "comentarios"),
        "combinacoes_compartilhamentos": combination_analysis(d, ["formato", "categoria", "porte_criador"], "compartilhamentos"),
        "combinacoes_interacoes": combination_analysis(d, ["formato", "categoria", "porte_criador"], "interacoes_totais"),
        "periodo_formato_engajamento": period_comparison(d, ["formato"], "taxa_engajamento", 40),
        "periodo_categoria_engajamento": period_comparison(d, ["categoria"], "taxa_engajamento", 40),
        "periodo_porte_engajamento": period_comparison(d, ["porte_criador"], "taxa_engajamento", 40),
        "hashtags_engajamento": hashtag_analysis(d, "taxa_engajamento", 30),
        "creator_audit": creator_id_audit(d),
        "correlacoes": numeric_correlations(d),
        "outliers_1": outlier_profile(d, "taxa_engajamento", .01),
        "outliers_5": outlier_profile(d, "taxa_engajamento", .05),
        "regimes_engajamento": regime_scan(d, "taxa_engajamento"),
    }


# Dashboard integration: compose the existing calculations without changing
# the original report/notebook methodology. See VALIDACAO.md.
def organic_objective_playbook(df, metric):
    organic = df.loc[~df.patrocinado].copy()
    table = combination_analysis(organic, ["formato", "categoria", "porte_criador"],
                                 metric, min_n=80, min_month_n=8, min_months=8)
    if table.empty or "segundos_12m" not in table:
        return pd.DataFrame()
    recent = organic.loc[organic.periodo_12m.eq("Segundos 12 meses"), metric].median()
    if pd.isna(recent) or recent == 0:
        return pd.DataFrame()
    table = table.dropna(subset=["segundos_12m"]).copy()
    table["resultado_base_recente"] = recent
    table["vantagem_recente_pct"] = 100 * (table.segundos_12m / recent - 1)
    for column in ["meses_validos", "meses_acima_do_padrao_pct"]:
        if column not in table:
            table[column] = np.nan
    return table.sort_values(["vantagem_recente_pct", "n"], ascending=False).reset_index(drop=True)


def sponsorship_decision_map(df, metric, shortlist=3, n_boot=500):
    table = sponsorship_controlled(df, metric, min_each=25)
    if table.empty:
        return table
    # Descriptive shortlist, then exploratory bootstrap on both extremes.
    selected = pd.concat([table.head(shortlist), table.tail(shortlist)]).drop_duplicates(
        ["formato", "categoria", "porte_criador"])
    table = sponsorship_strata_with_ci(df, metric, selected, n_boot=n_boot)
    table["diferenca_relativa_pct"] = 100 * table.diferenca / table.resultado_organico.replace(0, np.nan)
    table["Plataforma"] = ", ".join(sorted(df.plataforma.dropna().unique()))
    return table


def audience_profile_candidates(df, metric, min_n=40):
    table = group_summary(df, ["faixa_etaria_audiencia", "genero_audiencia", "localizacao_audiencia"], metric, min_n)
    if not table.empty:
        table["vantagem_pct"] = table.diferenca_relativa_pct
    return table


def best_time_by_format(df, metric, min_n=60):
    table = group_summary(df, ["formato", "dia_semana", "faixa_horaria"], metric, min_n)
    if not table.empty:
        table["vantagem_pct"] = table.diferenca_relativa_pct
    return table


def hashtag_count_profile(df, metric, min_n=300):
    return group_summary(df, "quantidade_hashtags", metric, min_n)


def weekly_volume_bands(df, metric):
    return frequency_performance(df, metric, "semana")["tabela"]


def temporal_movers(df, metric):
    table = combination_analysis(df, ["formato", "categoria", "porte_criador"], metric)
    if table.empty or "mudanca" not in table:
        return pd.DataFrame()
    recent = df.loc[df.periodo_12m.eq("Segundos 12 meses"), metric].median()
    table["vantagem_recente_pct"] = 100 * (table.segundos_12m / recent - 1) if recent else np.nan
    return table.dropna(subset=["mudanca"]).sort_values("mudanca", ascending=False)
