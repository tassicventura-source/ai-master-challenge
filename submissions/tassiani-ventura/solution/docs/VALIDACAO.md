# Validação — RavenStack Customer Journey

**Execução:** 2026-09-27 · sandbox Python 3.12 / Streamlit 1.64.

## Revisão de linguagem e navegação

A navegação diária usa nomes orientados à tarefa: **Minha fila**, **Clientes**, **Ficha do cliente**, **Tarefas e alertas**, **Vendas e oportunidades**, **Prioridades da carteira** e **Acompanhamento da equipe**. **Consulta histórica (dados até 2024)** agrupa registros congelados; páginas técnicas de jornada e arquitetura ficam fora do menu diário. Filtros e estados operacionais são exibidos em português, mantendo valores internos compatíveis com o banco.

## Python e integridade

`python -m compileall -q app.py pages src scripts tests` passou. A suíte completa `python -m pytest -q -W error::DeprecationWarning` teve **88 passed in 207.54s**; os testes focados de interface/navegação após a revisão final tiveram **33 passed in 171.75s**. `python -m pip check` não encontrou dependências quebradas, e `git diff --check` passou.

## E2E e clone limpo

Comando do browser: `RAVEN_PYTHON=python RAVEN_BROWSER_EXECUTABLE=/usr/bin/chromium npm run test:browser` — **exit 0**. Cobertura A01–A15: cadastro e ficha, contatos, tarefa atribuída/concluída, alerta tratado/auditado, alteração e encerramento de contratos, conta histórica com validação parcial e ação sobre sinal; **20 rotas abertas** e viewport **390×844 sem overflow horizontal**. Evidências: `docs/browser-results.json` e `docs/screenshots/`.

O branch publicado foi clonado limpo em `/tmp/ravenstack-clean-clone` no commit `f9a5cf2`. `compileall`, `pip check`, inicialização da camada operacional e leitura dos dados passaram; resultado: **500 contas históricas e 500 clientes operacionais**. A prévia do Streamlit respondeu `ok` em localhost e pela URL pública temporária informada no HANDOFF.

## Integridade e limitações

SQLAlchemy suporta SQLite e configuração PostgreSQL; os CSVs permanecem somente leitura. Dados importados não são promovidos a contrato atual sem confirmação explícita. Nenhum sinal histórico, `churn_event`, ticket, erro, refund informado ou encerramento administrativo prova sozinho churn ou perda econômica.

Não há instância para teste de integração PostgreSQL, Alembic ou migração automática do SQLite antigo. SQLite demo não é persistência durável garantida no Streamlit Community Cloud. Sem SSO/RBAC; nomes de operador/responsável são autodeclarados.
