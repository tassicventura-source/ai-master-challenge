"""Exercise every route and its controls against the same entrypoint used in deploy."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
PAGES=sorted(p.name for p in (ROOT/'pages').glob('*.py'))

def app(page):
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.switch_page('pages/'+page).run()
    assert not at.exception, [e.message for e in at.exception]
    return at

def assert_ok(at):
    assert not at.exception, [e.message for e in at.exception]


def test_my_work_is_the_operational_home():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert_ok(at)
    assert at.title[0].value=='Meu trabalho'
    assert any(t.label=='Ações de sinais' for t in at.tabs)


def test_operator_identity_persists_across_multipage_navigation():
    at=app('01_Conta_360.py')
    at.text_input(key='current_actor_input').set_value('Responsável QA').run()
    assert_ok(at)
    assert at.session_state['actor_identity']=='Responsável QA'
    at.switch_page('pages/00_Meu_Trabalho.py').run()
    assert_ok(at)
    assert at.session_state['actor_identity']=='Responsável QA'


def test_retention_central_renders_prioritized_cases_and_action_fields():
    at=app('08_Central_de_Retencao.py')
    assert at.title[0].value=='Central de Retenção'
    assert any('Sinais para triagem' in m.label for m in at.metric)
    assert any(w.label=='Responsável' for w in at.text_input)
    assert any(w.label=='Ação a executar' for w in at.text_area)
    assert any(w.label=='Prazo' for w in at.date_input)
    assert any(w.label=='Status' for w in at.selectbox)
    assert_ok(at)

def test_crm_workspace_exposes_registration_pipeline_and_activity_forms():
    at=app('09_Operacao_CRM.py')
    assert at.title[0].value=='Comercial · pipeline e atuação'
    assert any('Cadastrar lead' in t.label for t in at.tabs)
    assert any('Pipeline' in t.label for t in at.tabs)
    assert_ok(at)

@pytest.mark.parametrize('page',PAGES)
def test_every_route_and_widget_options(page):
    at=app(page)
    for idx in range(len(at.selectbox)):
        # Account options are covered separately across all accounts.
        if idx >= len(at.selectbox): continue
        widget=at.selectbox[idx]
        if 'conta' in widget.label.lower() or 'situação para decidir' in widget.label.lower() or 'sinal desta conta' in widget.label.lower(): continue
        for option in list(widget.options):
            at.selectbox[idx].select(option).run()
            assert_ok(at)
    for idx in range(len(at.radio)):
        for option in list(at.radio[idx].options):
            at.radio[idx].set_value(option).run(); assert_ok(at)
    for idx in range(len(at.checkbox)):
        at.checkbox[idx].check().run(); assert_ok(at)
        at.checkbox[idx].uncheck().run(); assert_ok(at)

@pytest.mark.parametrize('page',['03_Produto.py','04_Suporte_e_CS.py','05_Growth_e_Comercial.py','06_Finance_RevOps.py'])
def test_drilldown_preserves_account(page):
    at=app(page)
    widget=next(w for w in at.selectbox if w.label=='Investigar conta')
    aid=widget.value
    next(b for b in at.button if b.label=='Abrir Conta 360').click().run()
    assert_ok(at)
    assert at.selectbox(key='operational_customer_picker').value==aid

@pytest.mark.parametrize('page',['03_Produto.py','04_Suporte_e_CS.py','05_Growth_e_Comercial.py','06_Finance_RevOps.py'])
def test_account_filters(page):
    at=app(page)
    for idx in range(2):
        for option in at.multiselect[idx].options:
            at.multiselect[idx].set_value([option]).run(); assert_ok(at)
        at.multiselect[idx].set_value([]).run(); assert_ok(at)


def test_account_timeline_empty_and_anomalies():
    at=app('01_Conta_360.py')
    assert at.title[0].value=='Cliente 360'
    assert [t.label for t in at.tabs]==['Visão geral','Jornada','Assinatura & receita','Produto & suporte','Histórico / fonte']
    assert any(w.label=='Buscar / selecionar cliente' for w in at.selectbox)
    assert_ok(at)


def test_interaction_toggle_reveals_followup_inputs_immediately():
    at=app('01_Conta_360.py')
    customer_id=at.selectbox(key='operational_customer_picker').value
    key=f'interaction_create_next_overview_{customer_id}'
    at.checkbox(key=key).check().run()
    assert_ok(at)
    assert any(w.label=='Próxima ação *' for w in at.text_input)
    assert any(w.label=='Responsável pela próxima ação *' for w in at.text_input)
    assert any(w.label=='Prazo *' for w in at.date_input)


def test_every_account_opens():
    at=app('01_Conta_360.py')
    for option in at.selectbox(key='operational_customer_picker').options:
        at.selectbox(key='operational_customer_picker').select(option).run()
        assert_ok(at)
        assert any('Cliente 360' in x.value for x in at.title)


def test_journey_table_headers_match_content():
    at=app('02_Jornada_e_Areas.py')
    assert list(at.dataframe[0].value.columns)==['Área','Etapa','Registra','Base']
    assert at.dataframe[0].value.iloc[0]['Área']=='Growth/Marketing'


def test_architecture_table_headers_match_content():
    at=app('07_Dados_e_Arquitetura.py')
    assert list(at.dataframe[0].value.columns)==['Base atual','Base nova','Função','Mudança principal']
    assert at.dataframe[0].value.iloc[3]['Base atual']=='support_tickets'
    assert at.dataframe[0].value.iloc[3]['Base nova']=='customer_interactions'
