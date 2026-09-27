# RavenStack Customer Journey — Sistema Operacional de Retenção

Aplicação Streamlit de trabalho diário para Comercial, CS/Suporte, Finance/RevOps e Gestão. A pessoa pode localizar ou criar clientes, registrar conversas e tarefas, confirmar progressivamente campos históricos, movimentar subscriptions/lifecycle, tratar alertas e acompanhar a jornada auditada — sem depender das bases brutas.

> **Dado → sinal → contexto → decisão → ação → responsável → acompanhamento → resultado.** O sistema preserva o projeto analítico existente como apoio secundário; a camada operacional é a referência para estado futuro confirmado.

## Começar localmente

Requer Python 3.12+. A partir desta pasta:

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

O app constrói/valida as saídas analíticas e cria o store operacional na primeira execução. A tela inicial é **Meu trabalho**. A primeira utilização importa, de forma idempotente, os 500 clientes históricos como `legacy / not_validated`, sem promover churn, assinatura, seats ou MRR antigos a estado atual.

Para reconstruir explicitamente os dados analíticos e rodar a suíte:

```bash
python scripts/build_data.py
python -m pip install -r requirements-dev.txt
python -m pytest -q

# E2E com Chromium (requer Node.js)
npm ci
npx playwright install chromium
npm run test:browser
```

## Fluxo operacional

- **Meu trabalho:** tarefas de hoje, vencidas, próximas, renovações confirmadas, alertas e ações históricas atribuídas a quem está operando.
- **Clientes:** pesquisa/filtros por lifecycle, responsável, origem e qualidade; cadastro nativo cria cliente, owner, assinatura inicial, eventos e tarefa na mesma transação.
- **Cliente 360:** resumo/próxima ação, interações, jornada com antes/depois e autoria, subscriptions, prévia de movimentos econômicos, tarefas/alertas, ações ligadas a sinais e evidências/fonte histórica.
- **Tarefas & alertas:** criar/atualizar/concluir tarefas; ver alertas abertos/tratados/resolvidos sem apagar o histórico.
- **Comercial · pipeline:** cadastrar lead sem fingir que oportunidade é cliente/receita atual, mover etapa e registrar atuações.
- **Inteligência e Gestão:** regras determinísticas/alertas atuais e resumo da carteira; não substituem o fluxo operacional.
- **Central de Retenção histórica e análises por área:** investigações existentes, em navegação secundária, mantidas com suas regras documentadas.

As mudanças econômicas exigem confirmação humana e registram o movimento. A prévia deixa o delta desconhecido quando falta confirmação ou quando moedas não são comparáveis. `churn_event`, fim administrativo de linha, erro, ticket, refund informado e ausência de uso não são convertidos em churn ou perda econômica confirmada.

## Persistência, auditoria e segurança

O modelo transacional `src/operating_store.py` usa SQLAlchemy e mantém entidades operacionais separadas das fontes históricas: clientes, subscriptions, interações, tarefas, alertas, eventos de jornada, cópias-fonte e metadados de importação. Ações ligadas aos sinais históricos guardam snapshot, área, conta, ação, owner, prioridade, prazo, status, observação, resultado e trilha. Por compatibilidade com o store anterior, SQLite usa `retention_actions`/`retention_action_events`; PostgreSQL usa `op_retention_actions`/`op_retention_action_events`. Alterações relevantes são transacionais e guardam ator informado, timestamp, origem e valores antes/depois.

### Modo demo/local

Sem `DATABASE_URL`, a aplicação usa SQLite no arquivo `data/retention_actions.sqlite` (ou o caminho de `RETENTION_DB_PATH`). O arquivo está ignorado no Git. Isso é persistência real em disco local, mas **não é persistência durável/compartilhada no Streamlit Community Cloud**: reboot, redeploy ou réplica diferente pode não manter/compartilhar o arquivo. O app avisa quando roda nesse modo.

### Streamlit Community Cloud com banco persistente

Configure um PostgreSQL gerenciado acessível pela aplicação e adicione em **App → Settings → Secrets**:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Também se aceitam as variáveis de ambiente `DATABASE_URL`/`RAVENSTACK_DATABASE_URL`. Use TLS, credencial de privilégio mínimo, backup/PITR e rotacione secrets fora do código. O app normaliza a URL `postgresql://` e usa o driver `psycopg`. Tabelas são criadas pelo schema SQLAlchemy ao inicializar; este MVP ainda não traz Alembic nem migração automática dos registros da antiga SQLite para o PostgreSQL. Confirme o schema e faça backup antes de atualizar um banco já em uso.

> **Não use esta instância demo pública com PII ou dados reais.** Ainda não há login/SSO, RBAC nem identidade autenticada; o campo de responsável/ator é texto informado pela pessoa. SQLite local e credenciais de banco não substituem controle de acesso, API autenticada, política de dados, auditoria imutável ou restauração testada.

Veja [`docs/PERSISTENCIA_ACOES.md`](docs/PERSISTENCIA_ACOES.md) e [`docs/VALIDACAO.md`](docs/VALIDACAO.md) para arquitetura, limites e evidências.

## Publicar no Streamlit

Este projeto está em um repositório que contém outras submissões. No [Streamlit Community Cloud](https://share.streamlit.io/), selecione o repositório `tassicventura-source/ai-master-challenge`, branch `submission/tassiani-ventura` e caminho do app `submissions/tassiani-ventura/solution/app.py`. Escolha Python 3.12; o `requirements.txt` ao lado do app contém as dependências de runtime. Configure `DATABASE_URL` nos Secrets antes de depender das gravações após reinício.

Para usar como repositório separado, copie o **conteúdo** desta pasta para a raiz e selecione `app.py`.

## Dados e limites preservados

- São dados sintéticos: 500 contas e corte analítico em 31/12/2024. Crédito obrigatório do dataset: River @ Rivalytics.
- As cinco fontes CSV originais ficam em `data/raw/`, são importadas como snapshot somente leitura e checadas por SHA-256 nos testes.
- Há conflitos históricos em flags de churn/assinatura; subscriptions podem se sobrepor. MRR atual não é inferido somando linhas históricas.
- Telemetria e tickets são filtrados conforme as janelas temporais já documentadas. Refund/crédito informado não confirma liquidação ou caixa.
- Sinais da Central são evidência histórica para triagem, não monitoramento atual nem score de risco.

As regras, grãos e limitações analíticas estão em [`docs/RETENTION_OPERATING_MODEL.md`](docs/RETENTION_OPERATING_MODEL.md), [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) e `data/audit/`.

## Estrutura principal

- `app.py` — entrada Streamlit e navegação.
- `src/operating_store.py` — persistência transacional e regras canônicas.
- `src/operational_ui.py` — Meu trabalho, Clientes, Cliente 360, tarefas, pipeline, inteligência e gestão.
- `src/action_store.py` — ações da Central, SQLite demo/PostgreSQL e trilha.
- `src/retention.py`, `src/retention_ui.py` — regras de sinalização histórica explicável.
- `data/raw/`, `data/processed/`, `data/audit/` — fontes preservadas, saídas analíticas e verificações.
- `tests/` — regras do store, ação, navegação/AppTest e regressões.
