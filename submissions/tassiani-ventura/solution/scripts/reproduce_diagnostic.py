"""Reproduz os principais cálculos do diagnóstico RavenStack.

Execute a partir de submissions/tassiani-ventura/solution:
    python scripts/reproduce_diagnostic.py

Usa somente as cinco bases originais em data/raw. Não corrige nem imputa registros.
O objetivo é tornar auditáveis os números centrais do relatório, inclusive o
teste de sensibilidade que produz ~42,9% para eventos em até 90 dias em 2024.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CUTOFF = pd.Timestamp("2024-12-31")


def load():
    accounts = pd.read_csv(RAW / "ravenstack_accounts.csv", parse_dates=["signup_date"])
    subscriptions = pd.read_csv(
        RAW / "ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"]
    )
    churn = pd.read_csv(RAW / "ravenstack_churn_events.csv", parse_dates=["churn_date"])
    usage = pd.read_csv(RAW / "ravenstack_feature_usage.csv", parse_dates=["usage_date"])
    tickets = pd.read_csv(
        RAW / "ravenstack_support_tickets.csv", parse_dates=["submitted_at", "closed_at"]
    )
    return accounts, subscriptions, churn, usage, tickets


def account_frame(accounts, subscriptions, churn):
    first_event = churn.groupby("account_id")["churn_date"].min().rename("first_event_date")
    a = accounts.merge(first_event, on="account_id", how="left")
    a["signup_year"] = a["signup_date"].dt.year
    a["observation_days"] = (CUTOFF - a["signup_date"]).dt.days
    a["days_to_first_event"] = (a["first_event_date"] - a["signup_date"]).dt.days
    a["eligible_90d"] = a["observation_days"].ge(90)
    a["event_within_90d"] = a["days_to_first_event"].between(0, 90, inclusive="both")

    paid = subscriptions[(~subscriptions["is_trial"]) & (subscriptions["mrr_amount"] > 0)].copy()
    first_paid_date = paid.groupby("account_id")["start_date"].min().rename("first_paid_date")
    first_rows = paid.merge(first_paid_date, on="account_id", how="left")
    first_rows = first_rows[first_rows["start_date"].eq(first_rows["first_paid_date"])]

    initial = first_rows.groupby("account_id").agg(
        initial_value=("mrr_amount", "sum"),
        initial_paid_lines=("subscription_id", "count"),
    )
    first_plan = first_rows.groupby("account_id")["plan_tier"].agg(
        lambda s: sorted(set(s.dropna().astype(str)))
    ).map(lambda plans: plans[0] if len(plans) == 1 else "mixed_same_day").rename("first_paid_plan")

    return a.merge(initial, on="account_id", how="left").merge(first_plan, on="account_id", how="left")


def early_event_sensitivity(a):
    """Reproduz o ~42,9% citado no relatório.

    1) Em 2023, mede a fração de contas elegíveis que teve algum evento observado.
    2) Entre as contas de 2023 com evento, transforma o tempo até o evento em fração
       da janela total disponível até 31/12/2024.
    3) Aplica essa distribuição temporal às janelas disponíveis das contas elegíveis
       de 2024 e calcula a fração que cairia nos primeiros 90 dias.
    4) Multiplica pela incidência de "algum evento" observada em 2023.

    É teste de sensibilidade, não estimativa de churn econômico.
    """
    c23 = a[(a["signup_year"] == 2023) & a["eligible_90d"]].copy()
    c24 = a[(a["signup_year"] == 2024) & a["eligible_90d"]].copy()

    any_event_rate_2023 = c23["first_event_date"].notna().mean()
    with_event_2023 = c23[c23["first_event_date"].notna()].copy()
    normalized_time_2023 = (
        with_event_2023["days_to_first_event"] / with_event_2023["observation_days"]
    ).to_numpy()
    horizons_2024 = c24["observation_days"].to_numpy()

    projected_days = normalized_time_2023[:, None] * horizons_2024[None, :]
    projected_early_share_given_event = (projected_days <= 90).mean()
    expected_early_rate_2024 = any_event_rate_2023 * projected_early_share_given_event

    return {
        "any_event_rate_2023": any_event_rate_2023,
        "projected_early_share_given_event": projected_early_share_given_event,
        "expected_early_rate_2024": expected_early_rate_2024,
    }


def paid_context_counts(subscriptions, churn):
    paid = subscriptions[(~subscriptions["is_trial"]) & (subscriptions["mrr_amount"] > 0)].copy()
    counts = {"paid_line_active": 0, "before_first_paid": 0, "between_paid_relationships": 0}
    for row in churn.itertuples(index=False):
        s = paid[paid["account_id"].eq(row.account_id)]
        first_paid = s["start_date"].min()
        active = s[
            s["start_date"].le(row.churn_date)
            & (s["end_date"].isna() | s["end_date"].ge(row.churn_date))
        ]
        if not active.empty:
            counts["paid_line_active"] += 1
        elif pd.notna(first_paid) and row.churn_date < first_paid:
            counts["before_first_paid"] += 1
        else:
            counts["between_paid_relationships"] += 1
    return counts




def extended_quality_and_journey_checks(accounts, subscriptions, churn, usage, tickets, a):
    """Audita os achados adicionais usados na revisão final do diagnóstico."""
    paid = subscriptions[(~subscriptions["is_trial"]) & (subscriptions["mrr_amount"] > 0)].copy()

    active_cutoff = paid[
        paid["start_date"].le(CUTOFF)
        & (paid["end_date"].isna() | paid["end_date"].ge(CUTOFF))
    ]
    print("\n=== VALIDAÇÃO ADICIONAL DE CICLO DE VIDA ===")
    print(f"Contas com linha paga ativa em 31/12/2024: {active_cutoff['account_id'].nunique()}/{len(accounts)}")
    print(
        "Eventos marcados como reativação / upgrade precedente / downgrade precedente: "
        f"{int(churn['is_reactivation'].sum())} / "
        f"{int(churn['preceding_upgrade_flag'].sum())} / "
        f"{int(churn['preceding_downgrade_flag'].sum())}"
    )
    end_matches_flag = (
        subscriptions["churn_flag"].astype(bool).eq(subscriptions["end_date"].notna())
    ).all()
    print(
        f"subscription.churn_flag coincide com end_date em todas as linhas: {end_matches_flag} "
        f"({int(subscriptions['churn_flag'].sum())} linhas)"
    )

    u = usage.merge(
        subscriptions[["subscription_id", "account_id", "start_date", "end_date"]],
        on="subscription_id",
        how="left",
    )
    in_linked = (
        u["usage_date"].ge(u["start_date"])
        & (u["end_date"].isna() | u["usage_date"].le(u["end_date"]))
    )
    before = u[u["usage_date"].lt(u["start_date"])].reset_index().rename(columns={"index": "usage_row"})
    candidates = before[["usage_row", "account_id", "usage_date"]].merge(
        paid[["account_id", "start_date", "end_date"]], on="account_id", how="left"
    )
    overlaps_other_paid = (
        candidates["usage_date"].ge(candidates["start_date"])
        & (candidates["end_date"].isna() | candidates["usage_date"].le(candidates["end_date"]))
    )
    recovered_rows = candidates.loc[overlaps_other_paid, "usage_row"].nunique()

    print("\n=== QUALIDADE E RECUPERAÇÃO DA BASE DE PRODUTO ===")
    print(f"Dentro da subscription vinculada: {int(in_linked.sum()):,}")
    print(f"Fora da subscription vinculada: {int((~in_linked).sum()):,}")
    print(f"Registros anteriores que coincidem com outra linha paga da conta: {recovered_rows:,}")
    dup_rows = int(usage["usage_id"].duplicated(keep=False).sum())
    dup_ids = int(usage.loc[usage["usage_id"].duplicated(keep=False), "usage_id"].nunique())
    print(f"IDs de uso repetidos: {dup_ids}; linhas envolvidas: {dup_rows}")

    c24 = a[(a["signup_year"] == 2024) & a["eligible_90d"]][
        ["account_id", "signup_date", "event_within_90d"]
    ].copy()
    account_usage = usage.merge(
        subscriptions[["subscription_id", "account_id"]], on="subscription_id", how="left"
    ).merge(accounts[["account_id", "signup_date"]], on="account_id", how="left")
    u90 = account_usage[
        account_usage["usage_date"].ge(account_usage["signup_date"])
        & account_usage["usage_date"].le(account_usage["signup_date"] + pd.Timedelta(days=90))
        & account_usage["account_id"].isin(c24["account_id"])
    ]
    print(
        "Uso nos primeiros 90d da coorte comparável de 2024: "
        f"{len(u90):,} registros; {u90['account_id'].nunique()}/{len(c24)} contas"
    )

    ticket90 = tickets.merge(accounts[["account_id", "signup_date"]], on="account_id", how="left")
    ticket90 = ticket90[
        ticket90["submitted_at"].ge(ticket90["signup_date"])
        & ticket90["submitted_at"].le(ticket90["signup_date"] + pd.Timedelta(days=90))
        & ticket90["account_id"].isin(c24["account_id"])
    ]
    print("\n=== SUPORTE NOS PRIMEIROS 90 DIAS ===")
    print(f"{len(ticket90)} tickets; {ticket90['account_id'].nunique()}/{len(c24)} contas")


def main():
    accounts, subscriptions, churn, usage, tickets = load()
    a = account_frame(accounts, subscriptions, churn)

    print("=== COORTES COM 90 DIAS COMPLETOS ===")
    for year in (2023, 2024):
        c = a[(a["signup_year"] == year) & a["eligible_90d"]]
        n = len(c)
        events = int(c["event_within_90d"].sum())
        print(f"{year}: {events}/{n} = {events/n:.1%}")

    print("\n=== TESTE DE SENSIBILIDADE DA JANELA ===")
    s = early_event_sensitivity(a)
    print(f"Incidência de algum evento em 2023: {s['any_event_rate_2023']:.4%}")
    print(
        "Parcela projetada <=90d, condicionada a evento: "
        f"{s['projected_early_share_given_event']:.4%}"
    )
    print(f"Taxa esperada 2024: {s['expected_early_rate_2024']:.4%} (~42,9%)")

    print("\n=== CONTEXTO DOS 600 EVENTOS ===")
    print(paid_context_counts(subscriptions, churn))

    print("\n=== DESACORDO ENTRE TRÊS REPRESENTAÇÕES DE CHURN ===")
    event_accounts = set(churn["account_id"])
    ended_accounts = set(subscriptions.loc[subscriptions["end_date"].notna(), "account_id"])
    flag_accounts = set(accounts.loc[accounts["churn_flag"], "account_id"])
    disagree = sum(
        len({aid in event_accounts, aid in ended_accounts, aid in flag_accounts}) > 1
        for aid in accounts["account_id"]
    )
    print(f"{disagree}/{len(accounts)} = {disagree/len(accounts):.1%}")

    print("\n=== ESCOPO ECONÔMICO/OPERACIONAL DAS AÇÕES ===")
    c92 = a[(a["signup_year"] == 2024) & a["eligible_90d"] & a["event_within_90d"]]
    print(
        f"Reconciliação prioritária: {len(c92)} contas; "
        f"valor inicial registrado = US$ {c92['initial_value'].sum():,.0f}"
    )
    oe = a[
        (a["signup_year"] == 2024)
        & a["eligible_90d"]
        & a["referral_source"].eq("organic")
        & a["first_paid_plan"].eq("Enterprise")
    ]
    print(
        f"Organic x Enterprise comparável: {len(oe)} contas; "
        f"{int(oe['event_within_90d'].sum())} com evento; "
        f"valor inicial registrado = US$ {oe['initial_value'].sum():,.0f}"
    )
    print(
        f"Refund/crédito registrado: US$ {churn['refund_amount_usd'].sum():,.2f}; "
        f"{churn.loc[churn['refund_amount_usd'].gt(0), 'account_id'].nunique()} contas"
    )

    extended_quality_and_journey_checks(accounts, subscriptions, churn, usage, tickets, a)

    print("\nNota: valores acima são exposição/escopo observável, não benefício financeiro previsto.")
    print("Churn econômico, MRR perdido e ROI dependem da reconciliação contrato-fatura-pagamento.")


if __name__ == "__main__":
    main()
