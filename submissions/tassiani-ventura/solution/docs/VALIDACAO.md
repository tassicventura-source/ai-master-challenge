# Validação — RavenStack Customer Journey

**Execução:** 2026-09-27 · Python 3.12 / Streamlit 1.64 · sandbox atual. A prévia Streamlit temporária está disponível no link compartilhado no handoff.

## E2E Playwright aprovado

Comando: `RAVEN_PYTHON=python RAVEN_BROWSER_EXECUTABLE=/usr/bin/chromium npm run test:browser`.

Resultado: **exit 0**, cobrindo cadastro nativo e Cliente 360 (A01/A02), interação e follow-up atribuído (A05/A06), concluir tarefa com evento (A07), tratar alerta conservando histórico (A11), alteração de MRR com delta +300 (A08/A12), encerramento administrativo sem churn e perda total explicitamente confirmada (A09/A10), ação de sinal persistida, uso e validação parcial de conta legacy sem mudar fontes (A03/A04/A13/A14), 22 rotas e viewport **390×844 sem overflow horizontal** (A15). Evidência detalhada em `docs/browser-results.json`; capturas em `docs/screenshots/`.

O E2E revelou e levou à correção de um bug real: `preview_subscription_change` exigia ID de assinatura a substituir mesmo quando `create_parallel=True`. A prévia agora soma linhas vigentes e não confunde inclusão paralela com substituição; regressão dedicada cobre delta +350. Também ajustados flash após rerun e roteiro Playwright (menus React Aria, expander, viewport/hrefs mobile).

## Testes Python

- Suíte completa pós-correções: **88 passed em 212.36s**, com `-W error::DeprecationWarning`.
- Após fix de assinatura paralela e lifecycle: **2 testes direcionados passaram**.
- `python -m compileall -q app.py pages src scripts tests`, três AppTests, `pip check` e `git diff --check`: passaram após os fixes.

## Integridade e regras preservadas

SQLAlchemy com SQLite local e suporte de configuração PostgreSQL. Seed idempotente de 500 registros legacy; campos/estado contratual só ficam atuais após confirmação operacional. Testes preservam SHA-256 das cinco fontes. `churn_event`, uso/ticket, refund informado e fechamento administrativo não são considerados por si só prova de churn ou perda econômica. Arquivos históricos permanecem read-only.

## Limitações

- Sem instância/credenciais Postgres para teste de integração; não há Alembic nem migração automática dos bancos SQLite antigos.
- SQLite local persiste enquanto o arquivo existe, mas pode desaparecer/não ser compartilhado no Streamlit Community Cloud; usar Postgres gerenciado nos Secrets (`DATABASE_URL`) para dados duráveis.
- Não há autenticação/SSO/RBAC; ator e responsável são autodeclarados. Não usar PII em deployment público.
- Preview desta sessão é temporária, sem promessa de permanência após encerramento do sandbox. Push/clone limpo ainda pendentes.
