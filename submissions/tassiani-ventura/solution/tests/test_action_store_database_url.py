from datetime import date, timedelta

import pytest

from src.action_store import list_actions, list_events, save_action


@pytest.mark.parametrize("env_key", ["DATABASE_URL", "RAVENSTACK_DATABASE_URL"])
def test_signal_actions_use_database_url_aliases_and_keep_audit(monkeypatch, tmp_path, env_key):
    for key in ("DATABASE_URL", "RAVENSTACK_DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    url = f"sqlite:///{tmp_path / (env_key + '-actions.sqlite')}"
    monkeypatch.setenv(env_key, url)
    signal = {
        "signal_id": "SIG-QA-1", "account_id": "ACC-QA-1", "account_name": "Conta QA",
        "area": "Produto", "title": "Erros acima do limiar", "next_action": "Revisar erros",
    }
    action_id = save_action(signal=signal, action_text="Investigar com Produto", owner="Marta",
        priority="P2 — próxima execução", due_date=date.today()+timedelta(days=2),
        status="Aberta", observation="Primeira verificação")
    rows = list_actions(account_id="ACC-QA-1", open_only=True)
    assert len(rows) == 1 and rows[0]["action_id"] == action_id
    assert rows[0]["signal_snapshot_json"]
    save_action(signal=signal, action_text="Investigar com Produto", owner="Marta",
        priority="P2 — próxima execução", due_date=date.today()+timedelta(days=2),
        status="Em andamento", observation="Contato com engenharia", action_id=action_id)
    events = list_events(action_id)
    assert [x["event_type"] for x in events] == ["created", "updated"]
    assert '"status"' in events[-1]["changed_fields_json"]
