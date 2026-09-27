# HANDOFF — RavenStack Customer Journey

**Atualizado:** 2026-09-27 09:04 (São Paulo). Repositório `tassicventura-source/ai-master-challenge`, branch `submission/tassiani-ventura`, commit `f9a5cf2`. Projeto: `submissions/tassiani-ventura/solution`.

## Estado

O MVP operacional foi implementado sobre o app e os dados existentes. A camada transacional SQLAlchemy suporta SQLite e está preparada para PostgreSQL; os CSVs históricos originais permanecem somente leitura. A navegação diária é **Minha fila**, **Clientes**, **Ficha do cliente**, **Tarefas e alertas**, **Vendas e oportunidades**, **Prioridades da carteira** e **Acompanhamento da equipe**. A consulta anterior a 2025 fica agrupada em **Consulta histórica (dados até 2024)**; páginas técnicas saíram do menu diário. Estados e chamadas de ação visíveis estão em português, mantendo valores internos compatíveis com o banco.

A prévia temporária foi reiniciada e respondeu `ok` local e publicamente: https://8501-i7c7zs0wmld8y3izrwr79-c06a848f.us4.manus.computer. O processo vive somente durante este sandbox. O README contém instruções locais e de publicação no Streamlit.

## Testes e pacote

`compileall` passou. Suíte completa: **88 passed in 207.54s**. Testes focados de interface/navegação após os últimos rótulos: **33 passed in 171.75s**. `pip check` não encontrou dependências quebradas. Playwright E2E terminou com exit 0, verificando A01–A15, 20 rotas e viewport 390×844 sem overflow horizontal; evidências em `docs/browser-results.json` e `docs/screenshots/`.

Validação de clone limpo em `/tmp/ravenstack-clean-clone` no commit `f9a5cf2`: compilação e `pip check` passaram; o store operacional inicializou e retornou 500 contas históricas e 500 clientes.

## Persistência e limitações reais

Sem `DATABASE_URL`, SQLite local/demo grava em disco, mas não é durável nem compartilhado garantidamente no Streamlit Community Cloud. Configure PostgreSQL gerenciado em Streamlit Secrets para retenção após reinício. PostgreSQL não foi testado contra uma instância; não há Alembic nem migração automática do SQLite anterior. Ainda não existe login/SSO/RBAC; ator e responsável são autodeclarados. Não usar PII no demo público. Eventos históricos não comprovam churn ou perda econômica.

## GitHub

A revisão de UX está publicada na branch informada. Os fontes estão dentro de `submissions/tassiani-ventura/solution`; o `.gitignore` da raiz ignora outras submissões, então mudanças futuras neste projeto devem usar `git add -f` apenas nos arquivos revisados, evitando diretórios com bancos ou caches.
