# HANDOFF — RavenStack Customer Journey

**Estado em 2026-09-27 08:10 (America/Sao_Paulo).** Projeto: `/home/ubuntu/work/github/ai-master-challenge/submissions/tassiani-ventura/solution`. Repo Git raiz: `/home/ubuntu/work/github/ai-master-challenge`; branch `submission/tassiani-ventura`, remote `origin` = `tassicventura-source/ai-master-challenge`.

## Implementado
- MVP operacional Streamlit sobre a base existente, sem reconstrução do histórico: `app.py`, `src/operating_store.py` (SQLAlchemy, SQLite/Postgres), `src/operational_ui.py`, `src/action_store.py`, `src/retention_ui.py`.
- Cadastro nativo, CRM/pipeline, 500 contas legacy pré-carregadas sem estado atual inferido, validação parcial, interações/follow-up, tarefas/alertas, Cliente 360/jornada, movimentos de assinatura/lifecycle com proteção de moeda, Central de Retenção e Gestão.
- Autor de sessão persistente entre páginas; abas operacionais agora têm `on_change="rerun"` para não retornarem à primeira tab após reruns (correção recém-aplicada; ainda precisa validar).
- README, requisitos, docs de persistência, AppTests/unit tests e Playwright desktop/mobile estão no projeto.

## Evidência confirmada
- Suíte completa antes da última mudança de tabs: **87 passed** (`python -m pytest -q -W error::DeprecationWarning`, 203.34s).
- Após a alteração de tabs: `compileall` e **3 AppTests** (home, identidade entre páginas, tabs/Cliente 360) passaram em 2.61s. `pip check`/`git diff --check` precisam ser repetidos.
- E2E já percorreu cadastro/interação/follow-up e fila; foi ampliado para A03–A11/rotas/mobile. Última falha: Playwright não encontrou `Motivo da mudança *` visível após clicar o checkbox de assinatura paralela. Causa provável: `st.tabs` não preservava a seleção no rerun; corrigido com keys + `on_change="rerun"`. **E2E completo pendente.**
- Logs de tentativas ficam em `/home/ubuntu/terminal_full_output/` e scripts em `tests/browser_smoke.cjs`. DB temporário em `test-results/operating-e2e.sqlite`; não incluir no Git/ZIP.
- Snapshot de transferência já empacotado em `/home/ubuntu/work/github/ai-master-challenge/RavenStack_Customer_Journey_HANDOFF.zip` (106 arquivos; sem banco, cache, node_modules ou segredos). Ele não substitui o pacote final: regenerar após E2E, validação clone limpo e push.

## Próximos passos — execute em ordem
1. `cd /home/ubuntu/work/github/ai-master-challenge/submissions/tassiani-ventura/solution`.
2. `python -m compileall -q app.py pages src scripts tests && python -m pytest -q -W error::DeprecationWarning`.
3. E2E isolado (não rode duas cópias simultaneamente): `RAVEN_PYTHON=python RAVEN_BROWSER_EXECUTABLE=/usr/bin/chromium npm run test:browser`. Use `shell://` output. Primeiro verifique se `on_change="rerun"` mantém a tab Assinatura após checkbox; corrija apenas falhas concretas. Se passar, atualizar `docs/browser-results.json` e `docs/screenshots/` são automáticos.
4. Atualizar `MVP_CHECKLIST.md` e `docs/VALIDACAO.md` com resultados verdadeiros; nunca marque E2E aprovado se falhou.
5. `python -m pip check && git diff --check`; verifique `git status --short --ignored`. A regra `.gitignore` da raiz ignora `submissions/`; adicionar explicitamente arquivos novos/modificados com `git add -f submissions/tassiani-ventura/solution/...` (não adicionar `.sqlite`, `node_modules`, cache nem `test-results`).
6. Confirmar `git diff --cached --check`, commit e `git push origin submission/tassiani-ventura`. GitHub CLI já autenticado; o usuário autorizou push.
7. Validar clone limpo em `/tmp` e gerar ZIP via `git archive` do commit, fora da pasta de solução. Entregar o link absoluto.

## Limitações reais (documentar, não tentar esconder)
- PostgreSQL está implementado via `DATABASE_URL`/Streamlit Secrets, mas sem instância/credenciais para teste de integração; não há Alembic nem migração automática do SQLite legado.
- SQLite local persiste em disco, mas pode ser apagado/não compartilhado pelo Streamlit Community Cloud; conectar banco PostgreSQL para persistência durável.
- Sem SSO/RBAC; owner/ator é autodeclarado. Não usar dados reais/PII em deployment público.
- Fontes históricas ficam read-only; `churn_event`, ticket, erro, refund informado ou encerramento administrativo não provam perda econômica.
