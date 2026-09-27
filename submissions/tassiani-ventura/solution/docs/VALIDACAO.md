# Validação da versão reestruturada — 27/09/2026

Validação executada sobre o ZIP `RavenStack_Customer_Journey_reestruturado.zip`, antes de publicar esta versão.

- Instalação em ambiente virtual novo com Python 3.12.14 e `requirements-dev.txt`: concluída.
- `python -m pip check`: nenhuma dependência incompatível.
- Regras de negócio, persistência local, CRM, transformação e regressões: **54 testes aprovados** em 29,90 s.
- Interface com Streamlit AppTest: **33 testes aprovados** em 130,91 s, incluindo as 16 rotas e abertura dos 500 clientes históricos.
- Total: **87 testes aprovados**. Bancos de testes isolados, sem incorporar os registros de teste à entrega.
- Inicialização de `submissions/tassiani-ventura/solution/app.py` a partir da raiz do repositório: tela **Minha fila** carregada sem exceções.
- As cinco fontes CSV conferidas byte a byte com os arquivos originais do projeto: idênticas.
- `BRIEFING_CEO.md` e `TREINAMENTO_FUNCIONARIOS.md`: as cópias do ZIP são idênticas aos documentos enviados separadamente.
- Cache Python e arquivos SQLite temporários WAL/SHM excluídos do pacote publicado.

## Limites desta verificação

AppTest executa a interface Python, mas não substitui uma avaliação visual em navegador. O roteiro Playwright incluído ainda contém seletores da interface anterior; não foi executado nesta validação. As imagens e `browser-results.json` recebidos são evidências históricas, não evidências novas.

Não foi fornecido banco PostgreSQL externo. Sua conexão, gravação e restauração no Streamlit continuam pendentes. Sem `DATABASE_URL`, o aplicativo permanece em demonstração com SQLite local, sujeito a perda após reinício/redeploy. Não há autenticação/SSO/RBAC.

A instalação local e os testes não constituem confirmação de publicação online. O deploy deve ser reconhecido pela tela inicial **Minha fila**, conforme [instruções](DEPLOY_STREAMLIT.md).

---

## Registro histórico recebido no ZIP

O conteúdo abaixo preserva o checkpoint anterior; os resultados da validação desta versão estão acima.

# Validação — RavenStack Customer Journey (handoff)

**Execução:** 2026-09-27 · sandbox Python 3.12 / Streamlit 1.64. Este é um checkpoint de transferência, não uma declaração de aceite final.

## Resultado confirmado

- `python -m pytest -q -W error::DeprecationWarning`: **87 passed em 203,34 s**. Executado após a camada operacional, testes AppTest e testes de persistência/negócio, mas **antes** da última alteração de `st.tabs`.
- `python -m compileall -q app.py pages src scripts tests`: passou antes da última alteração das tabs; rerodar.
- `python -m pip check`: `No broken requirements found`.
- `git diff --check`: passou antes da última alteração.
- Smoke Chromium parcial percorreu cadastro nativo, interação/follow-up, Cliente 360/jornada e fila atribuída. Os eventos e tarefas foram conferidos no SQLite de teste após falhas de seletor. Foram adicionados cenários para alertas, subscription, perda explícita, legacy parcial e viewport mobile.

## Bloqueio E2E conhecido

A última execução terminou ao tentar preencher `Motivo da mudança *` após selecionar “Adicionar uma nova assinatura em paralelo”. O checkbox causa rerun; `st.tabs` por padrão não preservava a aba selecionada e o campo saiu da página ativa. Alteração recém-aplicada em `src/operational_ui.py`: chaves estáveis e `on_change="rerun"` nos grupos de abas operacionais. **Essa correção ainda não foi validada por pytest/E2E**. Reexecute primeiro os comandos de teste indicados em `HANDOFF.md`; corrija qualquer falha concreta antes de marcar os A01–A15 como concluídos.

Tentativas e falhas anteriores estão em `/home/ubuntu/terminal_full_output/`; a falha mais recente conhecida também consta no histórico da tarefa. `tests/browser_smoke.cjs` contém a suite Playwright. O processo E2E sempre usa `test-results/operating-e2e.sqlite`, arquivo temporário que não deve ser publicado nem empacotado.

## Cobertura e regras preservadas

A camada SQLAlchemy opera com SQLite local e está preparada para PostgreSQL. Testes cobrem seed idempotente dos 500 clientes legacy sem promover estado contratual, persistência transacional, operações, eventos antes/depois e hash das cinco fontes. `churn_event`, uso/ticket, refund informado e fechamento administrativo não são automaticamente classificados como churn ou perda econômica confirmada. As bases CSV continuam somente leitura.

## Limitações

- Sem instância/credenciais Postgres disponíveis para teste de integração; não há Alembic nem migração automática de registros do arquivo SQLite antigo.
- SQLite local persiste enquanto o arquivo existe, mas pode ser removido/não compartilhado no Streamlit Community Cloud. Para dados duráveis, conectar Postgres gerenciado nos Secrets (`DATABASE_URL`).
- Não há autenticação/SSO/RBAC; ator e responsável são valores autodeclarados. Não inserir PII em deployment público.
- Nenhum deployment/push desta sessão foi validado após as alterações locais.
