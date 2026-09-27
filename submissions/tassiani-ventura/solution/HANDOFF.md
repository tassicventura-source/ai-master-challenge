# HANDOFF — RavenStack Customer Journey

**Estado em 2026-09-27 08:34 (America/Sao_Paulo).** Projeto: `/home/ubuntu/work/github/ai-master-challenge/submissions/tassiani-ventura/solution`. Repo Git raiz: `/home/ubuntu/work/github/ai-master-challenge`; branch `submission/tassiani-ventura`, remote `origin` = `tassicventura-source/ai-master-challenge`.

## Implementado
- MVP operacional Streamlit sobre a base existente, sem reconstrução do histórico: `app.py`, `src/operating_store.py` (SQLAlchemy, SQLite/Postgres), `src/operational_ui.py`, `src/action_store.py`, `src/retention_ui.py`.
- Cadastro nativo, CRM/pipeline, 500 contas legacy pré-carregadas sem estado atual inferido, validação parcial, interações/follow-up, tarefas/alertas, Cliente 360/jornada, movimentos de assinatura/lifecycle com proteção de moeda, Central de Retenção e Gestão.
- Autor de sessão persistente entre páginas; tabs preservam a rota selecionada nos reruns.
- README, requisitos, docs de persistência, AppTests/unit tests e Playwright desktop/mobile estão no projeto.

## Evidência confirmada
- Suíte completa após correções: **88 passed em 212.36s** (`python -m pytest -q -W error::DeprecationWarning`). Compilação, `pip check` e `git diff --check` passaram.
- E2E Playwright: **exit 0**. A01–A15 cobertos em cadastro, jornada, tarefas, ações, alertas, assinatura/lifecycle, legacy parcial, integridade histórica, 22 rotas e viewport mobile 390×844 sem overflow. Resultado em `docs/browser-results.json`, screenshots em `docs/screenshots/`.
- Corrigido bug real na preview da inclusão paralela de subscription; regressão dedicada incluída. Também corrigido flash de ação pós-rerun. Os últimos outros erros foram apenas seletores/expander/viewport no script E2E e foram resolvidos.
- Prévia visual temporária publicada nesta sessão: `https://8501-i7c7zs0wmld8y3izrwr79-c06a848f.us4.manus.computer` (health local/público `ok`, raiz HTTP 200). Manter o serviço vivo enquanto o usuário revisa; o armazenamento é SQLite demo e não é durável no Cloud.
- Logs de tentativas ficam em `/home/ubuntu/terminal_full_output/` e scripts em `tests/browser_smoke.cjs`. DB temporário em `test-results/operating-e2e.sqlite`; não incluir no Git/ZIP.
- Snapshot de transferência em `/home/ubuntu/work/github/ai-master-challenge/RavenStack_Customer_Journey_HANDOFF.zip`; regenerar depois desta atualização. Sem banco local/cache/node_modules/segredos.

## Próximos passos — execute em ordem
1. `cd /home/ubuntu/work/github/ai-master-challenge/submissions/tassiani-ventura/solution`.
2. `python -m compileall -q app.py pages src scripts tests && python -m pytest -q -W error::DeprecationWarning`.
3. Testes já aprovados nesta sessão; ao retomar, evite repetir salvo mudanças no código.
4. Fazer stage explícito, commit e push da branch autorizada; validar clone limpo e ZIP final.
5. `python -m pip check && git diff --check`; verifique `git status --short --ignored`. A regra `.gitignore` da raiz ignora `submissions/`; adicionar explicitamente arquivos novos/modificados com `git add -f submissions/tassiani-ventura/solution/...` (não adicionar `.sqlite`, `node_modules`, cache nem `test-results`).
6. Confirmar `git diff --cached --check`, commit e `git push origin submission/tassiani-ventura`. GitHub CLI já autenticado; o usuário autorizou push.
7. Validar clone limpo em `/tmp` e gerar ZIP via `git archive` do commit, fora da pasta de solução. Entregar o link absoluto.

## Limitações reais (documentar, não tentar esconder)
- PostgreSQL está implementado via `DATABASE_URL`/Streamlit Secrets, mas sem instância/credenciais para teste de integração; não há Alembic nem migração automática do SQLite legado.
- SQLite local persiste em disco, mas pode ser apagado/não compartilhado pelo Streamlit Community Cloud; conectar banco PostgreSQL para persistência durável.
- Sem SSO/RBAC; owner/ator é autodeclarado. Não usar dados reais/PII em deployment público.
- Fontes históricas ficam read-only; `churn_event`, ticket, erro, refund informado ou encerramento administrativo não provam perda econômica.
