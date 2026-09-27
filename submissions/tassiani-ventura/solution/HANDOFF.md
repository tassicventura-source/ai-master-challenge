# HANDOFF — RavenStack Customer Journey

**Atualizado:** 2026-09-27 09:02 (São Paulo). Repositório: `/home/ubuntu/work/github/ai-master-challenge`; branch `submission/tassiani-ventura`; projeto em `submissions/tassiani-ventura/solution`.

## Estado

- MVP operacional implementado sobre o app e os dados existentes. Persistência transacional via SQLAlchemy em SQLite e preparado para PostgreSQL; CSVs históricos originais preservados como somente leitura.
- Navegação diária usa **Minha fila**, **Clientes**, **Ficha do cliente**, **Tarefas e alertas**, **Vendas e oportunidades**, **Prioridades da carteira** e **Acompanhamento da equipe**. A consulta antiga fica em **Consulta histórica (dados até 2024)**; páginas técnicas ficam fora do menu diário.
- Estados e chamadas de ação visíveis em português. Valores internos preservados para manter compatibilidade do banco.
- README contém execução local, publicação Streamlit, configuração de banco e limitações de segurança/persistência.

## Testes finais

- `python -m compileall -q app.py pages src scripts tests`: passou.
- Suíte completa: **88 passed in 207.54s** (`python -m pytest -q -W error::DeprecationWarning`).
- Testes focados de UI/navegação, após últimos rótulos: **33 passed in 171.75s**.
- `python -m pip check`: sem dependências quebradas; `git diff --check`: passou.
- Playwright E2E: **exit 0**, A01–A15, criação/atendimento/tarefas/alertas/assinatura/legacy/auditoria, 20 rotas abertas e viewport 390×844 sem overflow horizontal. Evidência em `docs/browser-results.json` e `docs/screenshots/`.

## Persistência e limitações reais

Sem `DATABASE_URL`, SQLite local/demo grava em disco, mas não é durável nem compartilhado garantidamente no Streamlit Community Cloud. Para uso persistente, configure PostgreSQL gerenciado em Streamlit Secrets. PostgreSQL não foi testado contra uma instância; não há Alembic nem migração automática do SQLite anterior. Ainda não existe login/SSO/RBAC; ator e responsável são autodeclarados. Não usar PII no demo público. Dados históricos não provam churn/perda econômica.

## Git e pacote

As mudanças finais de UX/documentação precisam ser commitadas e publicadas em `origin/submission/tassiani-ventura`. Como o `.gitignore` raiz ignora `submissions/`, usar `git add -f` apenas nos arquivos do projeto revisados, nunca adicionar diretórios inteiros com bancos ou caches. Gerar ZIP limpo com `git archive` após o commit e validar em clone/extrato limpo.
