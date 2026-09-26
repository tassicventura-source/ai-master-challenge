# RavenStack Customer Journey Intelligence

Aplicação Streamlit que conecta aquisição, assinaturas, produto, suporte e eventos de jornada em uma visão por cliente. Continuação do projeto original, com navegação simplificada e testes de todas as oito telas.

**Dados sintéticos · 500 contas · período 2023–2024.** Autor do dataset: **River @ Rivalytics**. Esta versão é de análise e investigação: não grava tarefas, não altera os sistemas de origem e não confirma perdas econômicas sem conciliação externa.

## Rodar

Requer Python **3.12**. No Windows, execute `run_local.bat`. No macOS/Linux, execute `bash run_local.sh`. Os scripts funcionam mesmo quando chamados a partir de outra pasta.

Ou, no diretório do projeto:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build_data.py
python -m streamlit run app.py
```

A aplicação abre no endereço local informado no terminal. As dependências diretas estão fixadas nas versões testadas. `requirements-lock.txt` registra também as dependências transitivas do ambiente validado em Python 3.12/Linux; use `python -m pip install -r requirements-lock.txt` para reproduzi-lo.

## Como navegar

- **Visão executiva:** o que exige atenção, valores, denominadores e acesso às evidências.
- **Conta 360:** seleção por nome/ID, filtros, jornada, contexto temporal e CSV.
- **Growth e Comercial:** alternância entre volume, valor inicial e incidência em 90 dias; acesso à conta.
- **Produto:** funcionalidades, erros e contas com uso na janela da assinatura.
- **Suporte e CS:** prioridades, escaladas e contas atendidas; o histórico contém somente suporte.
- **Finance e RevOps:** fila de eventos por contexto pago e reembolso, com acesso à conta.
- **Jornada e áreas:** responsabilidades e proposta de captura.
- **Dados e arquitetura:** fontes, campos e qualidade; diagramas disponíveis sob demanda.

Filtros são locais à página e descritos no recorte. Ao abrir uma conta a partir de uma área, a Conta 360 exibe a conta selecionada e limpa filtros incompatíveis. CSVs preservam as chaves técnicas para auditoria.

## GitHub e Streamlit Community Cloud

O arquivo `app.py` deve estar na raiz do repositório, junto de `requirements.txt`, `src/`, `pages/`, `.streamlit/`, `assets/` e `data/`. Não suba a pasta externa que contém o projeto como um nível adicional sem ajustar o caminho do app.

1. Crie um repositório GitHub e envie o conteúdo deste diretório. Inclua os cinco CSVs em `data/raw/`. O banco pronto está incluído; se ausente, o app o reconstrói automaticamente a partir dessas fontes.
2. No [Streamlit Community Cloud](https://share.streamlit.io/), selecione o repositório, a branch `main` e o arquivo principal **`app.py`**.
3. Nas configurações avançadas, selecione **Python 3.12**. O arquivo `.python-version` documenta a versão local; não substitui a seleção no painel de deploy.
4. Faça o deploy. Esta demonstração não exige chaves de API ou secrets.
5. Confirme a abertura das oito páginas e teste um caminho de uma área até Conta 360.

Se ainda não houver um repositório Git local, execute `git init -b main`, `git add .` e `git commit -m "Prepare RavenStack Customer Journey"`. Depois adicione a URL real do seu repositório como `origin` e faça `git push -u origin main`.

O workflow em `.github/workflows/ci.yml` reconstrói as bases e roda os testes em cada push/PR. Nenhum repositório remoto ou deploy foi criado por este pacote.

Referências oficiais consultadas: [deploy](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [dependências](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) e [testes em CI](https://docs.streamlit.io/develop/concepts/app-testing/automate-tests).

## Validar e atualizar os dados

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_data.py
python -m pytest -q
```

Depois de atualizar CSVs, rode o build antes de commitar. Uma instância que já contém banco não reprocessa os arquivos a cada navegação. O cache de leitura é invalidado pela versão do arquivo SQLite. O banco é escrito em arquivo temporário e substituído apenas ao concluir; as conexões da aplicação são somente leitura.

## Definições que protegem a análise

- **Valor inicial registrado:** soma de `mrr_amount` das linhas não trial e positivas na primeira data paga da conta. Não equivale a caixa, faturamento ou MRR atual. A primeira linha paga não comprova pagamento liquidado.
- **Incidência em 90 dias:** primeiro evento legado entre o cadastro e o 90º dia, somente em contas com janela completa. Corte: maior data de evento, 31/12/2024 nesta base; a completude até essa data é uma premissa explícita. Contas imaturas ficam com indicador nulo, sem serem tratadas como zero.
- **Linha vigente na data:** início ≤ evento ≤ fim; fim vazio representa linha aberta. Os limites são inclusivos e não resolvem sobreposição contratual.
- **Flag de reativação:** preservada como atributo legado; não determina o tipo nem a data de um evento de reativação.
- **Uso na janela:** entre início e fim da assinatura. Não prova ativação, retenção ou causalidade. Registros fora da janela são preservados.
- **Interação pós-cadastro:** ticket em data igual ou posterior ao signup. Demais tickets permanecem auditáveis.
- **Zero observado:** sem usos ou tickets no recorte válido; não significa ausência de atividade real.
- **Reembolso registrado:** valor informado na origem, sem comprovação bancária.

## Estrutura e auditoria

`data/raw/` preserva as cinco fontes; `data/processed/` contém bases canônicas e Conta 360; `data/audit/` contém campos legados e verificações. `src/` implementa transformações e leitura; `tests/` cobre integridade, métricas e navegação. Consulte `docs/VALIDACAO.md` para o resultado dos testes e limites da revisão.

Nenhum dado ausente é inventado. Campos futuros de contrato, responsável, ação, impacto e etapa permanecem vazios. Não há integração autenticada com CRM/billing/helpdesk, nem módulo de IA ou modelo preditivo nesta versão.

### Conferência opcional no navegador

Requer Node.js 20+ apenas para QA; Node não é dependência do deploy Streamlit.

```bash
npm ci
npx playwright install chromium
npm run test:browser
```

O script inicia uma instância temporária na porta 8502, percorre as telas, testa downloads e navegação até a conta, registra capturas em `docs/screenshots/` e encerra o servidor. `RAVEN_PYTHON` permite indicar outro interpretador; `RAVEN_BROWSER_EXECUTABLE` permite indicar um Chromium já instalado.
