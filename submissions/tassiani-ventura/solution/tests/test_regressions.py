from pathlib import Path
import pandas as pd
import pytest
from src.data_access import load_table
from src.transform import load_raw, validate_raw, build_all
from src.analytics import growth_by_source

ROOT=Path(__file__).resolve().parents[1]

def test_mature_cohorts_match_independently_computed_source():
    raw=load_raw(ROOT/'data/raw')
    a=raw['accounts'][['account_id','signup_date']].copy()
    a['first_event']=a.account_id.map(raw['churn_events'].groupby('account_id').churn_date.min())
    a=a[(pd.Timestamp('2024-12-31')-a.signup_date).dt.days.ge(90)]
    a['event90']=(a.first_event-a.signup_date).dt.days.between(0,90)
    expected=a.groupby(a.signup_date.dt.year).event90.agg(['count','sum'])
    actual=load_table('account_360')
    eligible=actual[actual.eligible_90d]
    got=eligible.groupby(eligible.signup_date.dt.year).recorded_event_within_90d.agg(['count','sum'])
    assert expected.astype(int).equals(got.astype(int).rename_axis(expected.index.name))
    assert got['count'].tolist()==[227,195]
    assert got['sum'].tolist()==[44,92]
    assert actual.loc[~actual.eligible_90d,'recorded_event_within_90d'].isna().all()
    g=growth_by_source(actual)
    assert g.eligible_90d.sum()==422


def test_legacy_flag_never_retypes_event():
    d=load_table('lifecycle_events')
    assert d.recorded_event_type.eq('churn_recorded').all()
    assert d.legacy_reactivation_flag.sum()>0
    assert d.canonical_event_type.isna().all()
    assert d.mrr_before.isna().all()


def test_no_usage_and_no_tickets_are_zero_observed_counts():
    a=load_table('account_360')
    cols=['valid_usage_count','valid_interactions','recorded_lifecycle_events']
    assert a[cols].notna().all().all()
    raw=load_raw(ROOT/'data/raw')
    assert a.refunds_recorded.sum()==pytest.approx(raw['churn_events'].refund_amount_usd.sum())


def test_reject_duplicate_keys_and_orphans():
    raw=load_raw(ROOT/'data/raw')
    raw['accounts']=pd.concat([raw['accounts'],raw['accounts'].iloc[:1]])
    with pytest.raises(ValueError,match='duplicada'): validate_raw(raw)
    raw=load_raw(ROOT/'data/raw')
    raw['subscriptions'].loc[0,'account_id']='missing'
    with pytest.raises(ValueError,match='inexistente'): validate_raw(raw)


def test_table_names_are_allowlisted():
    with pytest.raises(ValueError): load_table('accounts"; DROP TABLE accounts; --')


def test_clean_rebuild_and_missing_database(tmp_path,monkeypatch):
    import src.data_access as access
    monkeypatch.setattr(access,'DB_PATH',tmp_path/'ravenstack.sqlite')
    monkeypatch.setattr(access,'ROOT',tmp_path)
    import shutil
    shutil.copytree(ROOT/'data/raw',tmp_path/'data/raw')
    got=access.load_table('account_360')
    assert len(got)==500 and got.account_id.is_unique
    assert len(access.load_table('feature_usage'))==25000
    access._load_table.clear()
