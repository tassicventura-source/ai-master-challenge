# RavenStack — Sistema Operacional de Retenção

Aplicação Streamlit para converter **dado → sinal → contexto → decisão → ação → responsável → acompanhamento → resultado**. Além da Central de Retenção, há cadastro de leads/clientes, pipeline comercial editável, diário de interações por área, follow-ups com owner/prazo e Conta 360 operacional.

**Base preservada:** projeto Customer Journey Intelligence existente, cinco tabelas originais, transformações canônicas, Conta 360, filtros, análises por área, exportações e testes anteriores. **Dados sintéticos · 500 contas · período 2023–2024.** Crédito obrigatório do dataset: **River @ Rivalytics**.

> Os sinais são filas de triagem, não um modelo preditivo. `churn_event` não é perda de cliente nem perda de receita confirmada. O CRM local é um sistema operacional **standalone** em modo demo: ele não sincroniza com CRM, billing ou helpdesk externos.

## Executar localmente

Requer Python **3.12**. No Windows, use `run_local.bat`; no macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/build_data.py
python -m streamlit run app.py
```

A `Central de Retenção` é a página inicial; **CRM e operação comercial** está logo abaixo no menu lateral. O banco operacional demo é criado em `data/retention_actions.sqlite` no primeiro uso; esse arquivo é runtime e está ignorado no Git. Para escolher outro caminho persistente, configure `RETENTION_DB_PATH`.

## Como operar

1. **Central de Retenção:** veja a fila priorizada em páginas de 25, filtre por área/prioridade e busque conta ou situação. O histórico termina em 31/12/2024; confirme o status atual em sistemas oficiais antes de intervir.
2. Selecione um sinal para consultar **o que aconteceu, por que importa, evidência/IDs, incerteza e próxima ação sugerida**.
3. Abra **Conta 360** para cruzar sinais, registros temporais, ações e resultado.
4. Em **CRM e operação comercial → Cadastrar conta**, crie um lead/cliente ou associe uma conta histórica pelo ID existente. Preencha responsável e etapa do pipeline; o valor é apenas estimativa de oportunidade.
5. Em **Pipeline**, filtre por etapa/owner, atualize a etapa, registre ligação/reunião/proposta e informe o resultado. Em **Atividades e follow-ups**, atualize atividades planejadas para concluídas/canceladas e mantenha próxima ação e prazo.
6. **Conta 360** combina o histórico observado (se houver) com owner, etapa, atividades e sinais operacionais. Leads novos sem presença no dataset aparecem sem métricas históricas inventadas.
7. Na Central/filas, registre ações de retenção separadas do diário de atividades comercial. Conclusão exige resultado informado.
8. Alterações de conta/interação são adicionadas à trilha de auditoria demo; tarefas e recortes podem ser exportados em CSV.

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

O modo demo usa SQLite local com transações e as entidades `crm_accounts`, `crm_interactions`, `crm_events`, além de `retention_actions` e `retention_action_events`. Cadastros têm origem explícita, owner, etapa, valor estimado/moeda, previsão e próxima ação; interações têm área, tipo, responsável, resultado, status e follow-up. Atualizações deixam eventos de auditoria da aplicação. Não há login, permissões, identidade verificada do operador nem sincronização externa.

**Não coloque informações reais de clientes neste deployment público.** A interface mostra o aviso: o arquivo SQLite do Streamlit Community Cloud pode ser apagado em reboot/deploy e não é compartilhado com confiabilidade entre réplicas. Para um piloto real, primeiro restrinja o acesso e migre cadastro/interações/ações a PostgreSQL gerenciado atrás de API autenticada, SSO/RBAC, backups e trilha de auditoria com ator autenticado; detalhes estão em `docs/PERSISTENCIA_ACOES.md`. Não há segredos nem integração com um CRM externo neste pacote.

## GitHub e Streamlit Community Cloud

Esta submissão fica dentro de um repositório com vários desafios. Não mova os arquivos para o topo nem selecione o `app.py` de outro desafio. O caminho desta aplicação no GitHub é `submissions/tassiani-ventura/solution/app.py`; `requirements.txt`, `src/`, `pages/`, e os cinco arquivos de `data/raw/` estão ao lado dele. O app calcula paths a partir da própria pasta e foi verificado iniciando-o desde a raiz do repositório.

1. Conecte o fork `tassicventura-source/ai-master-challenge` ao [Streamlit Community Cloud](https://share.streamlit.io/).
2. Clique **Create app** e escolha branch **`submission/tassiani-ventura`** e arquivo **`submissions/tassiani-ventura/solution/app.py`**. Se os menus não oferecerem a subpasta, informe esse caminho relativo manualmente.
3. Em **Advanced settings**, selecione **Python 3.12**. As dependências vêm de `submissions/tassiani-ventura/solution/requirements.txt`; não crie outro `requirements.txt` na raiz do repositório.
4. Clique **Deploy**. Ao terminar, teste Central, quatro filas, Conta 360, drill-downs e exportações. Commits novos nessa branch acionam atualização do app.
5. Alternativamente, para publicar esta pasta como um repositório separado, copie **o conteúdo** de `solution/` para a raiz daquele repositório e selecione `app.py` na raiz.

Para esta entrega, um workflow dentro de uma subpasta não seria detectado pelo GitHub Actions; validações reproduzíveis ficam em `docs/VALIDACAO.md`. O modo demo usa dados sintéticos. O arquivo SQLite de ações não é incluído no Git e o armazenamento local do Community Cloud é efêmero: não use o app hospedado para guardar ações importantes ou dados reais sem migrar para uma base persistente.

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

O smoke test navega pelas páginas, cria lead sintético, registra responsável/atividade/follow-up no Pipeline, confirma a mesma atividade na Conta 360, cria ações de retenção no desktop e mobile, percorre todas as rotas nos dois viewports e verifica ausência de overflow horizontal. Testes Python confirmam recuperação de CRM e ações após reiniciar o processo. Os detalhes ficam em `docs/browser-results.json` e capturas em `docs/screenshots/`.

## Estrutura

- `src/retention.py` — sinais determinísticos e explicáveis.
- `src/retention_ui.py` — Central, filas, detalhes e formulário.
- `src/crm_ui.py` — cadastro, pipeline, atividades, follow-ups e visão operacional da conta.
- `src/action_store.py` — SQLite demo, CRUD operacional e trilhas de auditoria.
- `data/raw/`, `data/processed/`, `data/audit/` — fontes preservadas, bases e checks de qualidade.
- `tests/` — suíte original mais testes de sinal/ação/navegação.
- `docs/PERSISTENCIA_ACOES.md` — arquitetura de produção; `docs/RETENTION_OPERATING_MODEL.md` — regras e fluxo de decisão.
