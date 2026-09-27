# RavenStack — Sistema Operacional de Retenção

Aplicação Streamlit para converter **dado → sinal → contexto → decisão → ação → responsável → acompanhamento → resultado**. A Central prioriza situações por regras explícitas, mostra a evidência/limitação, roteia para quatro áreas e grava tarefas com trilha de auditoria no modo demo.

**Base preservada:** projeto Customer Journey Intelligence existente, cinco tabelas originais, transformações canônicas, Conta 360, filtros, análises por área, exportações e testes anteriores. **Dados sintéticos · 500 contas · período 2023–2024.** Crédito obrigatório do dataset: **River @ Rivalytics**.

> Os sinais são filas de triagem, não um modelo preditivo. `churn_event` não é perda de cliente nem perda de receita confirmada. Ações do modo demo não atualizam CRM, billing ou helpdesk.

## Executar localmente

Requer Python **3.12**. No Windows, use `run_local.bat`; no macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/build_data.py
python -m streamlit run app.py
```

A `Central de Retenção` é a página inicial. O banco de ações demo é criado em `data/retention_actions.sqlite` no primeiro uso; esse arquivo é runtime e está ignorado no Git. Para escolher outro caminho persistente, configure `RETENTION_DB_PATH`.

## Como operar

1. **Central de Retenção:** veja a fila priorizada em páginas de 25, filtre por área/prioridade e busque conta ou situação. O histórico termina em 31/12/2024; confirme o status atual em sistemas oficiais antes de intervir.
2. Selecione um sinal para consultar **o que aconteceu, por que importa, evidência/IDs, incerteza e próxima ação sugerida**.
3. Abra **Conta 360** para cruzar sinais, registros temporais, ações e resultado.
4. Registre ou edite a ação, pessoa responsável, prioridade, prazo, status, observação e resultado. Conclusão exige resultado informado.
5. Use as filas **Growth/Comercial**, **Produto**, **CS/Suporte** e **Finance/RevOps**. As análises originais continuam abaixo das novas filas.
6. O histórico de mudanças é acrescentado à trilha de auditoria local; ações e recortes podem ser exportados em CSV.

### Priorização: regras e limites

Não há score composto, modelo de risco ou pesos ocultos. A ordenação é `P1 → P2 → P3`, depois data observada mais antiga primeiro e ID estável; ela representa triagem operacional, não probabilidade de churn.

- **P1 — verificar primeiro:** ticket `urgent` ou escalado; e evento Finance com valor `refund_amount_usd > 0` registrado enquanto existe linha paga na data. O segundo caso apenas antecipa a verificação; valor não prova transação nem perda.
- **P2 — próxima execução:** `error_count` somado **≥ 5 por conta × feature**, somente em eventos dentro da janela da subscription (limiar acima do p95 observado por registro, 4); e eventos Finance com linha paga vigente sem refund positivo.
- **P3 — revisão planejada:** as 22 contas comparáveis da coorte **2024 × Organic × primeiro plano pago Enterprise × D90 completo**. A origem documenta 14/22 com e 8/22 sem evento legado precoce. Pertencer ao grupo não é sinal de risco individual.
- Os demais eventos Finance seguem em P3, pois ainda precisam de reconciliação. Nenhuma razão declarada vira causa causal.

Cada item explica a regra, usa o grão correto e registra IDs de origem. Um sinal pode aparecer repetidamente quando múltiplas evidências independentes existem; a fila não é deduplicada por uma hipótese de “risco da conta”. Veja `docs/RETENTION_OPERATING_MODEL.md`.

## Definições e limitações preservadas

- `churn_event`, `accounts.churn_flag` e encerramento de linha são representações divergentes; **400/500 contas** apresentam discordância entre os três sinais.
- **531/600** eventos coexistem com uma linha paga vigente; **67** ocorrem antes da primeira linha paga e **2** entre linhas pagas. Nenhum evento é convertido automaticamente em perda.
- `subscriptions` se sobrepõem; MRR/ARR atuais por conta não são inferidos somando linhas abertas.
- Só **5.568/25.000** eventos de uso estão dentro da janela da subscription; eventos fora da janela permanecem auditáveis e não viram evidência válida de uso/erro na fila de Produto.
- **1.077/2.000** tickets antecedem o signup; filas de suporte usam apenas registros pós-cadastro. `submitted_at` tem precisão diária.
- Ausência de uso, ticket, CSAT, owner ou resultado não é imputada. CSAT observado cobre respondentes e valores de 3–5 apenas.
- Refund/crédito informado não está ligado a fatura, pagamento ou caixa liquidado.
- Corte observado: **31/12/2024**. Dados sintéticos não demonstram comportamento universal de clientes SaaS.

As regras completas e as premissas de uso permanecem também em `docs/DATA_MODEL.md`, `docs/VALIDACAO.md` e `docs/RETENTION_OPERATING_MODEL.md`.

## Persistência e arquitetura

O modo demo usa SQLite local com transações, ação com dono/prazo/status/observação/resultado, snapshot do sinal no momento do registro e tabela append-only de eventos de criação/alteração. Não há autenticação/segregação por usuário; portanto, não conecte dados reais de clientes nem use o SQLite local como persistência de produção.

O disco do Streamlit Community Cloud pode ser efêmero e não deve ser tratado como banco compartilhado entre réplicas. Para produção, a arquitetura recomendada é PostgreSQL gerenciado persistente atrás de API autenticada, SSO/RBAC e trilha imutável; detalhes, migração de schema, backup, segurança e operações estão em `docs/PERSISTENCIA_ACOES.md`. Não há segredos ou integrações externas neste pacote.

## GitHub e Streamlit Community Cloud

O repositório deve conter `app.py` na raiz, mais `requirements.txt`, `src/`, `pages/`, `.streamlit/`, `assets/` e `data/`. Inclua os cinco CSVs em `data/raw/` para que o banco analítico possa ser reconstruído.

1. Crie um repositório GitHub e envie o conteúdo deste diretório, sem a pasta externa do projeto.
2. No Streamlit Community Cloud, selecione o repositório/branch e `app.py`; configure Python 3.12.
3. Não trate o deploy público simples como backend de tarefas em produção: escolha PostgreSQL gerenciado antes de armazenar trabalho operacional real.
4. Teste Central, quatro filas, Conta 360, drill-downs e exportações.

O projeto inclui workflow GitHub Actions. Nenhum repositório remoto ou deploy foi criado/publicado neste pacote.

## Validar

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_data.py
python -m pytest -q
pip check
```

Teste de navegador desktop/mobile (requer Node.js 20+, Chromium e Playwright):

```bash
npm ci
RAVEN_PYTHON=python RAVEN_BROWSER_EXECUTABLE=/usr/bin/chromium npm run test:browser
```

O smoke test navega pelas páginas, valida drill-down, cria ação pelos formulários desktop/mobile, percorre todas as rotas em viewport desktop e móvel e verifica ausência de overflow horizontal. Teste unitário confirma recuperação da ação em novo processo Python. Os detalhes são gravados em `docs/browser-results.json` e capturas em `docs/screenshots/`.

## Estrutura

- `src/retention.py` — sinais determinísticos e explicáveis.
- `src/retention_ui.py` — Central, filas, detalhes e formulário.
- `src/action_store.py` — SQLite demo e trilha de auditoria.
- `data/raw/`, `data/processed/`, `data/audit/` — fontes preservadas, bases e checks de qualidade.
- `tests/` — suíte original mais testes de sinal/ação/navegação.
- `docs/PERSISTENCIA_ACOES.md` — arquitetura de produção; `docs/RETENTION_OPERATING_MODEL.md` — regras e fluxo de decisão.
