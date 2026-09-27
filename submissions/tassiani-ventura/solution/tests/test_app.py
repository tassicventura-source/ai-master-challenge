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
    assert at.title[0].value=='CRM e Operação Comercial'
    assert any('Cadastrar conta' in t.label for t in at.tabs)
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
    assert at.selectbox(key='account_choice').value==aid

@pytest.mark.parametrize('page',['01_Conta_360.py','03_Produto.py','04_Suporte_e_CS.py','05_Growth_e_Comercial.py','06_Finance_RevOps.py'])
def test_account_filters(page):
    at=app(page)
    for idx in range(2):
        for option in at.multiselect[idx].options:
            at.multiselect[idx].set_value([option]).run(); assert_ok(at)
        at.multiselect[idx].set_value([]).run(); assert_ok(at)


def test_account_timeline_empty_and_anomalies():
    at=app('01_Conta_360.py')
    types=next(w for w in at.multiselect if w.label=='Tipos de registro')
    types.set_value([]).run(); assert_ok(at)
    assert any('Nenhum registro' in i.value for i in at.info)
    types=next(w for w in at.multiselect if w.label=='Tipos de registro')
    types.set_value(list(types.options)).run()
    count=len(at.dataframe[0].value)
    at.checkbox[0].check().run()
    assert len(at.dataframe[0].value)>=count


def test_every_account_opens():
    at=app('01_Conta_360.py')
    for option in at.selectbox(key='account_choice').options:
        at.selectbox(key='account_choice').select(option).run()
        assert_ok(at)
        assert len(at.dataframe[0].value)>=1


def test_journey_table_headers_match_content():
    at=app('02_Jornada_e_Areas.py')
    assert list(at.dataframe[0].value.columns)==['Área','Etapa','Registra','Base']
    assert at.dataframe[0].value.iloc[0]['Área']=='Growth/Marketing'


def test_architecture_table_headers_match_content():
    at=app('07_Dados_e_Arquitetura.py')
    assert list(at.dataframe[0].value.columns)==['Base atual','Base nova','Função','Mudança principal']
    assert at.dataframe[0].value.iloc[3]['Base atual']=='support_tickets'
    assert at.dataframe[0].value.iloc[3]['Base nova']=='customer_interactions'
