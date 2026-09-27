from __future__ import annotations

"""Deterministic operational signals; these are routing cues, not churn predictions."""

from hashlib import sha256
from typing import Any

import pandas as pd

AREAS = ("Growth/Comercial", "Produto", "CS/Suporte", "Finance/RevOps")
PRIORITIES = ("P1 — verificar primeiro", "P2 — próxima execução", "P3 — revisão planejada")
PRIORITY_ORDER = {label: index for index, label in enumerate(PRIORITIES)}
OBSERVATION_CUTOFF = "2024-12-31"

RULES = {
    "growth": "Conta da coorte cadastrada em 2024, origem Organic e primeiro plano pago Enterprise, com 90 dias completos. São os 22 casos comparáveis descritos no diagnóstico (14 com/8 sem evento legado em D90). É revisão de jornada, não risco de churn.",
    "product": "Soma de error_count >= 5 na mesma conta e funcionalidade, apenas em registros dentro da janela da subscription. Cinco supera o percentil 95 observado por registro (4); é um limiar de triagem, não uma taxa de falha ou churn.",
    "support": "Ticket em/apos o cadastro com prioridade urgent OU flag de escalada. submitted_at tem precisão diária; escalar/urgente é evidência de atendimento, não causa de churn.",
    "finance": "Cada churn_event legado precisa de reconciliação. P1 somente quando o campo refund_amount_usd > 0 e existe linha paga que abrange a data, para verificar contrato/cobrança primeiro; o valor não comprova transação nem perda.",
}


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _stable(prefix: str, *parts: Any) -> str:
    raw = "|".join(_text(x) for x in parts)
    suffix = sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{suffix}"


def _account_map(accounts: pd.DataFrame) -> dict[str, dict[str, Any]]:
    return accounts.set_index("account_id").to_dict("index")


def build_signals(accounts: pd.DataFrame, usage: pd.DataFrame,
                  interactions: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    """Build reproducible case signals from canonical processed tables.

    No score or inferred economic outcome is created. Each row includes the
    rule, source IDs, a plain-language explanation, limitations, and next step.
    """
    account_rows = _account_map(accounts)
    records: list[dict[str, Any]] = []

    def add(*, sid: str, area: str, priority: str, account_id: str,
            signal_type: str, title: str, occurred_at: Any, what: str,
            why: str, evidence_summary: str, evidence: dict[str, Any],
            uncertainty: str, next_action: str, source_refs: list[str],
            priority_reason: str) -> None:
        account = account_rows.get(account_id, {})
        records.append({
            "signal_id": sid,
            "area": area,
            "priority": priority,
            "priority_order": PRIORITY_ORDER[priority],
            "priority_reason": priority_reason,
            "account_id": account_id,
            "account_name": account.get("account_name", account_id),
            "industry": account.get("industry", ""),
            "referral_source": account.get("referral_source", ""),
            "signal_type": signal_type,
            "title": title,
            "signal_date": _text(occurred_at),
            "what_happened": what,
            "why_it_matters": why,
            "evidence_summary": evidence_summary,
            "evidence": evidence,
            "uncertainty": uncertainty,
            "next_action": next_action,
            "source_refs": source_refs,
        })

    # Growth: a defined, mature 2024 acquisition cohort. Each member is a
    # review case, not an account-level risk classification.
    cohort = accounts[
        pd.to_datetime(accounts["signup_date"], errors="coerce").le(pd.Timestamp(OBSERVATION_CUTOFF))
        & pd.to_datetime(accounts["first_paid_date"], errors="coerce").le(pd.Timestamp(OBSERVATION_CUTOFF))
        & pd.to_datetime(accounts["signup_date"], errors="coerce").dt.year.eq(2024)
        & accounts["referral_source"].eq("organic")
        & accounts["first_paid_plan"].eq("Enterprise")
        & accounts["eligible_90d"].fillna(False).astype(bool)
    ]
    for row in cohort.itertuples(index=False):
        event = getattr(row, "recorded_event_within_90d")
        event_label = "sim" if pd.notna(event) and bool(event) else "não"
        plan = _text(getattr(row, "first_paid_plan"))
        aid = _text(getattr(row, "account_id"))
        evidence = {
            "coorte": "signup 2024 / origem organic / primeiro plano pago Enterprise",
            "first_paid_date": _text(getattr(row, "first_paid_date")),
            "first_paid_plan": plan,
            "initial_value_registered_usd": getattr(row, "initial_value_registered"),
            "eligible_90d": bool(getattr(row, "eligible_90d")),
            "recorded_event_within_90d": event_label,
            "valid_usage_events": int(getattr(row, "valid_usage_events")),
            "valid_interactions": int(getattr(row, "valid_interactions")),
        }
        add(
            sid=f"GRO-{aid}-2024-organic-enterprise",
            area="Growth/Comercial", priority="P3 — revisão planejada",
            account_id=aid, signal_type="revisar_coorte_aquisicao",
            title="Revisar jornada Organic × Enterprise (2024)",
            occurred_at=getattr(row, "first_paid_date"),
            what=(f"A conta integra a coorte comparável de 2024; primeiro plano pago: {plan}. "
                  f"Evento legado nos primeiros 90 dias: {event_label}."),
            why="A coorte foi destacada no diagnóstico para comparar aquisição, handoff e valor inicial.",
            evidence_summary=(f"signup 2024 · organic · {plan} · janela D90 completa · evento registrado: {event_label}"),
            evidence=evidence,
            uncertainty=("Pertencer à coorte não classifica a conta como em risco. churn_event não é outcome econômico; "
                         "valor inicial não é MRR atual. A leitura é descritiva e restrita a estes dados sintéticos."),
            next_action="Reconstruir a jornada histórica de origem, promessa e handoff com Comercial/CS; antes de agir sobre retenção atual, confirmar o estado presente da conta nos sistemas oficiais.",
            source_refs=[f"account_360:{aid}"],
            priority_reason="P3 é revisão de jornada por coorte; não indica urgência nem propensão a churn.",
        )

    # Product: aggregate before joining at account × feature grain.
    valid_usage = usage[
        usage["temporal_status"].eq("within_subscription")
        & pd.to_datetime(usage["usage_date"], errors="coerce").le(pd.Timestamp(OBSERVATION_CUTOFF))
    ].copy()
    if not valid_usage.empty:
        product_groups = valid_usage[valid_usage["error_count"].gt(0)].groupby(
            ["account_id", "feature_name"], as_index=False
        ).agg(
            errors=("error_count", "sum"),
            usage_count=("usage_count", "sum"),
            records=("usage_event_id", "size"),
            first_date=("usage_date", "min"),
            last_date=("usage_date", "max"),
            source_ids=("usage_event_id", lambda s: list(s.astype(str))),
        )
        for row in product_groups[product_groups["errors"].ge(5)].itertuples(index=False):
            aid, feature = str(row.account_id), str(row.feature_name)
            evidence = {
                "feature_name": feature,
                "error_count_sum_in_subscription_window": int(row.errors),
                "usage_count_sum": int(row.usage_count),
                "source_records": int(row.records),
                "first_usage_date": _text(row.first_date),
                "last_usage_date": _text(row.last_date),
                "threshold": "error_count somado >= 5 por conta × funcionalidade",
                "source_usage_event_ids": row.source_ids,
            }
            add(
                sid=_stable("PRD", aid, feature), area="Produto",
                priority="P2 — próxima execução", account_id=aid,
                signal_type="erros_repetidos_na_funcionalidade",
                title=f"Validar erros registrados em {feature}", occurred_at=row.last_date,
                what=f"{int(row.errors)} erros foram registrados em {int(row.records)} evento(s) válido(s) de {feature} nesta conta.",
                why="Um volume agregado >= 5 ultrapassa o percentil 95 (4 erros) observado por linha de uso e merece inspeção técnica.",
                evidence_summary=f"{feature} · {int(row.errors)} erros / {int(row.records)} registros válidos · {row.first_date} a {row.last_date}",
                evidence=evidence,
                uncertainty=("Registros de uso são esparsos e a unidade de usage_count/error_count não está definida. "
                             "Apenas 5.568/25.000 linhas estão dentro da janela da subscription; não prova falha por usuário, causa ou churn."),
                next_action="Conferir logs/versão da época e reproduzir a ocorrência histórica com Produto; confirmar nos dados atuais se o problema ainda persiste antes de agir sobre a conta.",
                source_refs=[f"feature_usage:{x}" for x in row.source_ids],
                priority_reason="P2 decorre do limiar explícito por grupo; não é um score de risco de conta.",
            )

    # Support: only post-signup observations with an objectively urgent or
    # escalated label. Submitted timestamps are daily precision in the source.
    support = interactions[
        interactions["lifecycle_temporal_status"].eq("on_or_after_signup")
        & pd.to_datetime(interactions["occurred_at"], errors="coerce").le(pd.Timestamp(OBSERVATION_CUTOFF))
        & (interactions["priority"].eq("urgent") | interactions["escalation_flag"].fillna(False).astype(bool))
    ]
    for row in support.itertuples(index=False):
        aid = str(row.account_id)
        priority_name = "Urgente" if str(row.priority) == "urgent" else "Escalado"
        evidence = {
            "ticket_id": str(row.interaction_id),
            "submitted_at_date": _text(row.occurred_at),
            "priority": str(row.priority),
            "escalation_flag": bool(row.escalation_flag),
            "first_response_time_minutes": int(row.first_response_time_minutes),
            "resolution_time_hours": float(row.resolution_time_hours),
            "satisfaction_score": None if pd.isna(row.satisfaction_score) else float(row.satisfaction_score),
            "lifecycle_temporal_status": str(row.lifecycle_temporal_status),
        }
        add(
            sid=f"SUP-{row.interaction_id}", area="CS/Suporte",
            priority="P1 — verificar primeiro", account_id=aid,
            signal_type="ticket_urgente_ou_escalado",
            title=f"Atendimento {priority_name.lower()} para acompanhamento",
            occurred_at=row.occurred_at,
            what=f"Ticket {row.interaction_id}: prioridade {row.priority}; escalado: {'sim' if row.escalation_flag else 'não' }.",
            why="Sinal operacional de atendimento que merece verificar resolução e comunicação com a conta.",
            evidence_summary=f"ticket {row.interaction_id} · {priority_name} · {row.occurred_at}",
            evidence=evidence,
            uncertainty=("Histórico cobre tickets de Suporte, não contatos de CS. submitted_at contém apenas data; "
                         "prioridade/escalada não provam causa, insatisfação nem churn."),
            next_action="Revisar o ticket histórico e, se ainda aplicável, confirmar com o cliente o estado atual da resolução; registrar impacto percebido e follow-up.",
            source_refs=[f"customer_interactions:{row.interaction_id}"],
            priority_reason="P1 por rótulo explícito urgent ou escalated no ticket; não significa risco financeiro confirmado.",
        )

    # Finance: one row per legacy event, preserving its event grain. Never
    # infer revenue impact or relabel the record as customer loss.
    in_cutoff_lifecycle = lifecycle[
        pd.to_datetime(lifecycle["event_date"], errors="coerce").le(pd.Timestamp(OBSERVATION_CUTOFF))
    ]
    for row in in_cutoff_lifecycle.itertuples(index=False):
        aid = str(row.account_id)
        raw_refund = row.refund_amount_usd
        refund = 0.0 if pd.isna(raw_refund) else float(raw_refund)
        paid_active = str(row.paid_context_at_event) == "paid_line_active"
        priority = "P1 — verificar primeiro" if paid_active and refund > 0 else (
            "P2 — próxima execução" if paid_active else "P3 — revisão planejada"
        )
        evidence = {
            "event_id": str(row.event_id),
            "event_date": _text(row.event_date),
            "recorded_event_type": str(row.recorded_event_type),
            "reason_code_as_recorded": str(row.reason_code),
            "paid_context_at_event": str(row.paid_context_at_event),
            "refund_amount_usd_as_recorded": refund,
            "economic_outcome": str(row.economic_outcome),
            "reconciliation_status": str(row.reconciliation_status),
            "next_paid_start_date": _text(row.next_paid_start_date),
        }
        add(
            sid=f"FIN-{row.event_id}", area="Finance/RevOps", priority=priority,
            account_id=aid, signal_type="evento_legacy_a_reconciliar",
            title="Confirmar o resultado contratual e econômico do evento registrado",
            occurred_at=row.event_date,
            what=(f"Evento legado {row.event_id} ({row.reason_code}) em {_text(row.event_date)}; "
                  f"contexto: {row.paid_context_at_event}; valor indicado como crédito/reembolso: US$ {refund:,.2f}."),
            why="É necessário reconciliar contrato, assinatura e cobrança para classificar o movimento antes de tomar decisão comercial.",
            evidence_summary=(f"{row.event_id} · {row.paid_context_at_event} · "
                              f"refund/crédito informado US$ {refund:,.2f} · outcome não reconciliado"),
            evidence=evidence,
            uncertainty=("churn_event não é perda confirmada. refund_amount_usd não está ligado a fatura/transação. "
                         "Subscriptions se sobrepõem; linha paga vigente não comprova pagamento liquidado nem receita atual."),
            next_action="Cruzar historicamente contrato, fatura e pagamento; confirmar o status atual nos sistemas oficiais; registrar tipo de movimento e MRR antes/depois somente após reconciliação.",
            source_refs=[f"lifecycle_events:{row.event_id}"],
            priority_reason=("P1 somente para verificar primeiro o valor registrado junto a contexto de linha paga vigente; "
                             "não confirma refund, churn ou perda econômica." if priority.startswith("P1") else
                             "P2 para evento com linha paga vigente; P3 para demais contextos que também exigem reconciliação."),
        )

    columns = [
        "signal_id", "area", "priority", "priority_order", "priority_reason",
        "account_id", "account_name", "industry", "referral_source", "signal_type",
        "title", "signal_date", "what_happened", "why_it_matters",
        "evidence_summary", "evidence", "uncertainty", "next_action", "source_refs",
    ]
    result = pd.DataFrame(records, columns=columns)
    if result.empty:
        return result
    result["_date_sort"] = pd.to_datetime(result["signal_date"], errors="coerce")
    return result.sort_values(
        ["priority_order", "_date_sort", "signal_id"],
        ascending=[True, True, True], na_position="last",
    ).drop(columns="_date_sort").reset_index(drop=True)


def signal_snapshot(signal: pd.Series | dict[str, Any]) -> dict[str, Any]:
    """Small, JSON-safe decision snapshot stored with a demo action."""
    data = signal.to_dict() if isinstance(signal, pd.Series) else dict(signal)
    allowed = (
        "signal_id", "area", "priority", "priority_reason", "account_id", "account_name",
        "signal_type", "title", "signal_date", "what_happened", "why_it_matters",
        "evidence_summary", "evidence", "uncertainty", "next_action", "source_refs",
    )
    return {key: data.get(key) for key in allowed}
