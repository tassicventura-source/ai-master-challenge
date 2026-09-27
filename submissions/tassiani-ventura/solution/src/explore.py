"""Shared exploration controls; technical keys stay in CSV exports."""
import pandas as pd
import streamlit as st

CONTEXTS = {
    'paid_line_active': 'Linha paga vigente na data',
    'before_first_paid': 'Antes da primeira linha paga',
    'previously_paid_no_active_line': 'Histórico pago, sem linha vigente',
    'no_paid_history_observed': 'Sem histórico pago observado',
}
LABELS = {
    'account_id':'ID da conta', 'account_name':'Conta', 'industry':'Setor', 'country':'País',
    'referral_source':'Origem', 'first_paid_plan':'Primeiro plano pago', 'signup_year':'Ano de cadastro',
    'initial_value_registered':'Valor inicial (US$)', 'initial_value':'Valor inicial (US$)',
    'median_initial_value':'Mediana do valor inicial (US$)', 'accounts':'Contas',
    'eligible_90d':'Contas com 90 dias completos', 'events_90d':'Contas com evento em 90 dias',
    'recorded_event_90d':'Incidência em 90 dias', 'valid_usage_count':'Usos registrados',
    'valid_features_used':'Funcionalidades usadas', 'valid_errors':'Erros registrados',
    'valid_interactions':'Atendimentos pós-cadastro', 'refunds_recorded':'Reembolsos registrados (US$)',
    'median_usage':'Mediana de usos', 'median_features':'Mediana de funcionalidades',
    'median_errors':'Mediana de erros', 'priority':'Prioridade', 'interactions':'Atendimentos',
    'median_first_response_min':'Resposta mediana (min)', 'median_resolution_h':'Resolução mediana (h)',
    'escalation_rate':'Proporção escalada', 'csat_response_rate':'Cobertura de satisfação',
    'csat_mean':'Satisfação média (1–5)', 'event_id':'ID do evento', 'event_date':'Data do evento',
    'reason_code':'Motivo informado', 'paid_context_at_event':'Contexto pago na data',
    'refund_amount_usd':'Reembolso registrado (US$)', 'next_paid_start_date':'Próxima linha paga',
    'recorded_lifecycle_events':'Eventos legados', 'feature_name':'Funcionalidade',
    'usage':'Usos registrados', 'errors':'Erros registrados', 'events':'Registros',
    'errors_per_100_usage':'Erros / 100 usos', 'date':'Data', 'type':'Tipo', 'detail':'Detalhe',
    'validity':'Contexto temporal', 'source_id':'ID de origem',
}

def display_frame(df):
    out = df.copy()
    if 'paid_context_at_event' in out:
        out['paid_context_at_event'] = out['paid_context_at_event'].replace(CONTEXTS)
    if 'priority' in out:
        out['priority'] = out['priority'].replace({'low':'Baixa','medium':'Média','high':'Alta','urgent':'Urgente'})
    for col in ['recorded_event_90d','escalation_rate','csat_response_rate']:
        if col in out:
            out[col] = out[col].map(lambda v: '—' if pd.isna(v) else f'{v:.1%}')
    return out.rename(columns=LABELS)


def table(df, filename=None):
    if df.empty:
        st.info('Nenhum registro neste recorte. Ajuste os filtros.')
    else:
        shown = display_frame(df)
        config = {col: st.column_config.DatetimeColumn(col, format="DD/MM/YYYY HH:mm")
                  for col in shown if pd.api.types.is_datetime64_any_dtype(shown[col])}
        for col in shown:
            if pd.api.types.is_float_dtype(shown[col]):
                config[col] = st.column_config.NumberColumn(col, format='%.2f')
        st.dataframe(shown, hide_index=True, width='stretch', column_config=config)
    if filename:
        st.download_button('Baixar este recorte em CSV', df.to_csv(index=False).encode('utf-8-sig'),
                           file_name=filename, mime='text/csv', disabled=df.empty)


def account_filters(accounts, prefix):
    with st.expander('Filtrar contas'):
        c1, c2 = st.columns(2)
        origins = c1.multiselect('Origem', sorted(accounts.referral_source.dropna().unique()), key=prefix+'_origins')
        plans = c2.multiselect('Primeiro plano pago', sorted(accounts.first_paid_plan.dropna().unique()), key=prefix+'_plans')
    out=accounts.copy()
    if origins: out=out[out.referral_source.isin(origins)]
    if plans: out=out[out.first_paid_plan.isin(plans)]
    st.caption(f'{len(out)} de {len(accounts)} contas · todo o histórico disponível para o recorte')
    return out


def open_account(accounts, key):
    if accounts.empty: return
    names=accounts.set_index('account_id')['account_name'].to_dict()
    aid=st.selectbox('Escolher conta para ver detalhes', accounts.account_id.tolist(),
                     format_func=lambda x: f'{names[x]} · {x}', key=key)
    if st.button('Abrir ficha do cliente', key=key+'_open'):
        st.session_state['requested_account_id']=aid
        st.switch_page('pages/01_Conta_360.py')
