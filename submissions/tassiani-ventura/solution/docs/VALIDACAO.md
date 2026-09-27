# Validação final — Sistema Operacional de Retenção

**Execução:** 26/09/2026, no ambiente Linux/Python 3.12.14. Este relatório diferencia a linha de base da implementação final.

## Linha de base, antes das alterações

O Streamlit existente respondeu ao endpoint de saúde; sua suíte tinha **35 testes aprovados**. O smoke test original percorreu as oito páginas anteriores em Chromium, baixou recortes e verificou Conta 360/drill-down em viewport de 390 px. As leituras e limitações analíticas preexistentes foram preservadas.

## Resultado final

- `python scripts/build_data.py`: aprovado; reconstruiu 500 accounts, 5.000 subscriptions, 25.000 eventos de uso, 2.000 tickets, 600 eventos legados, 500 Account 360 e oito linhas de quality summary.
- `python -m pytest -q -W error::DeprecationWarning`: **47 testes aprovados em 63,62 s, sem warnings**; inclui dez testes dedicados de retenção/ações, um AppTest da Central e a nova rota na navegação parametrizada.
- `python -m compileall -q app.py pages src scripts tests`: aprovado.
- `python -m pip check`: `No broken requirements found.`
- Chromium Playwright: health `ok`; nove páginas navegadas; drill-down Finance → Conta 360; formulários criaram tarefas no desktop e no mobile; documento e viewport de 390 px sem overflow horizontal; zero erros de página. Relatório de execução: `browser-results.json`; capturas: `screenshots/`.
- Teste separado cria ação num processo Python e a carrega num novo processo, conservando responsável, observação e ID. Testes adicionais cobrem transação, update/event log, snapshot, bloqueio de reassociação, campos obrigatórios e resultado ao concluir.

| Cobertura | Resultado |
|---|---|
| Quatro áreas e regras determinísticas com IDs estáveis | Aprovado; 939 sinais do recorte histórico derivado das fontes (sem score ou estado atual inferido) |
| Coorte Growth 2024 × Organic × Enterprise × D90 | Aprovado; 22 casos, 14 com e 8 sem evento legado |
| Produto | Aprovado; apenas erros dentro da janela e limiar explícito >= 5 por conta × feature |
| CS/Suporte | Aprovado; somente urgent/escalated em ou após signup |
| Finance/RevOps | Aprovado; 600 linhas no grão de evento, sem transformar `churn_event` em perda econômica |
| Central, quatro filas e Conta 360 | Aprovado; filas filtráveis, paginação de 25 e formulário de ação |
| Ação, status, prazo, dono, observação, resultado e auditoria | Aprovado em SQLite demo; concluir sem resultado é bloqueado |
| Browser desktop/mobile | Aprovado em 1440×1000 e 390×844; ações, downloads e drill-down verificados |
| Cinco fontes originais | SHA-256 após o build idênticos aos CSVs recebidos; detalhes em `data/audit/` |

## Critérios preservados

A regra de elegibilidade D90 e a flag legada `is_reactivation` mantêm a semântica da versão anterior. Continuam explícitos os 400/500 registros divergentes entre indicadores de churn, 531/600 eventos com linha paga vigente, 67 antes do primeiro pagamento, 2 entre linhas, 5.568/25.000 usos dentro da janela e 1.077/2.000 tickets pré-signup. São dados sintéticos com cutoff em 31/12/2024; erro/uso/ticket não prova churn e crédito/reembolso informado não confirma caixa ou perda.

A camada de ações **não** altera as cinco fontes, a Account 360 canônica, as definições históricas ou os sistemas externos. Owners e resultados são informados manualmente, snapshot e histórico ficam no SQLite local de demo. “Concluída” significa status declarado pelo operador, não outcome econômico verificado.

## Capturas e arquivos de auditoria

- `browser-results.json` registra rotas, drill-down, downloads, ações desktop/mobile e largura medida.
- `screenshots/00-central-desktop.png` e `screenshots/00-central-mobile.png` registram a Central.
- Capturas adicionais preservam a revisão visual de cada rota em desktop/mobile.
- Os CSVs originais foram comparados diretamente por SHA-256 antes do empacotamento; conteúdo idêntico.

## Limites e fora do escopo

Esta é uma validação automatizada/técnica com inspeção visual; não é pesquisa de usabilidade com operadores reais, homologação por especialistas, teste de carga multiusuário, teste de segurança ou certificação de resultados. Windows foi revisado mas não executado. GitHub Actions está preparado, mas requer push para rodar no hosted runner. Não houve criação/publicação de repositório remoto nem deploy em Streamlit Community Cloud.

SQLite local demonstra persistência, inclusive em novo processo, **somente enquanto o arquivo e seu disco persistirem**. Streamlit Community Cloud não garante armazenamento compartilhado/estável entre redeploy/reboots/réplicas. Use o modo demo somente com dados sintéticos; consulte `PERSISTENCIA_ACOES.md` antes de ligar identidades, dados de clientes ou sistemas externos. Não existe risco/health score, atualização por API, autenticação/RBAC nem escrita de CRM/billing/helpdesk.
