# Validação — RavenStack Customer Journey

**Execução:** 2026-09-27 · sandbox Python 3.12 / Streamlit 1.64.

## Revisão de linguagem e navegação

A navegação diária usa nomes orientados à tarefa: **Minha fila**, **Clientes**, **Ficha do cliente**, **Tarefas e alertas**, **Vendas e oportunidades**, **Prioridades da carteira** e **Acompanhamento da equipe**. **Consulta histórica (dados até 2024)** agrupa registros congelados; páginas técnicas de jornada e arquitetura ficam fora do menu diário. Filtros e estados operacionais são exibidos em português, mantendo valores internos compatíveis com o banco.

## Python e integridade

- `python -m compileall -q app.py pages src scripts tests`: passou.
- Suíte completa `python -m pytest -q -W error::DeprecationWarning`: **88 passed in 207.54s**.
- Testes focados de interface/navegação após a revisão final: **33 passed in 171.75s**.
- `python -m pip check`: sem dependências quebradas.
- `git diff --check`: passou.

## E2E

Comando: `RAVEN_PYTHON=python RAVEN_BROWSER_EXECUTABLE=/usr/bin/chromium npm run test:browser` — **exit 0** após a revisão final dos rótulos.

Cobertura: A01–A15; cadastro e Ficha do cliente, contatos, tarefa atribuída e concluída, alerta tratado e auditado, alteração e encerramento de contratos, uso legacy com validação parcial, ação ligada a evidência histórica; **20 rotas abertas** e viewport **390×844 sem overflow horizontal**. Evidência: `docs/browser-results.json`; capturas em `docs/screenshots/`.

## Integridade e limitações

SQLAlchemy suporta SQLite e configuração PostgreSQL; os CSVs permanecem somente leitura. Dados importados não são promovidos a contrato atual sem confirmação explícita. Nenhum sinal histórico, `churn_event`, ticket, erro, refund informado ou encerramento administrativo prova sozinho churn ou perda econômica.

Não há instância para teste de integração PostgreSQL, Alembic ou migração automática do SQLite antigo. SQLite demo não é persistência durável garantida no Streamlit Community Cloud. Sem SSO/RBAC; nomes de operador/responsável são autodeclarados.
