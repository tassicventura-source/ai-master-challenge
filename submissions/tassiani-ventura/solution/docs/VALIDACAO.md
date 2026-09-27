# Validação final — Sistema Operacional de Retenção e CRM demo

**Execução desta revisão:** 26/09/2026, Linux/Python 3.12.14. Este relatório distingue a linha de base histórica do resultado nesta cópia local da branch.

## Linha de base antes da camada operacional

O Streamlit existente respondeu ao endpoint de saúde; sua suíte original tinha **35 testes aprovados**. O smoke test anterior percorria as páginas da análise, baixava recortes e verificava Conta 360/drill-down em viewport de 390 px. Documentos, CSVs e regras analíticas recebidos permaneceram preservados.

## Resultado desta revisão

- `python scripts/build_data.py`: aprovado; reconstruiu 500 accounts, 5.000 subscriptions, 25.000 eventos de uso, 2.000 tickets, 600 eventos legados, 500 Account 360 e oito linhas de quality summary.
- `python -m pytest -q -W error::DeprecationWarning`: **55 testes aprovados, sem warnings**. Inclui os testes anteriores, CRUD/auditoria para CRM, atividades/follow-ups e a página CRM no AppTest.
- `python -m compileall -q app.py pages src scripts tests`: aprovado.
- `python -m pip check`: `No broken requirements found.`
- `git diff --check`: aprovado.
- Chromium Playwright: servidor local health `ok`; 10 rotas; drill-down Finance → Conta 360; cadastro de lead, responsável comercial, atividade e follow-up; atividade do lead visível na Conta 360; criação de ação de retenção desktop/mobile; download de CSV; zero erros de página; todos os viewports de 390×844 com largura do documento = 390 (sem overflow horizontal). Veja `browser-results.json` e as capturas de `screenshots/`.
- Reinício de processo real: conta, etapa e atividade/follow-up foram recuperados do SQLite no novo processo Python.
- Streamlit Community Cloud: push/rebuild do commit `49582cf` na branch `submission/tassiani-ventura` concluído; logs mostraram dependências instaladas e Uvicorn iniciado com Python 3.14.7. A URL pública e a rota `/Operacao_CRM` foram abertas e exibiram cadastro/pipeline sem erro. Não foi cadastrado dado de cliente no deployment público.

| Cobertura | Resultado |
|---|---|
| Quatro áreas e regras determinísticas com IDs estáveis | Aprovado; 939 sinais do recorte histórico derivado das fontes (sem score ou estado atual inferido) |
| Coorte Growth 2024 × Organic × Enterprise × D90 | Aprovado; 22 casos, 14 com e 8 sem evento legado |
| Produto | Aprovado; erros dentro da janela e limiar explícito ≥ 5 por conta × feature |
| CS/Suporte | Aprovado; somente urgent/escalated em ou após signup |
| Finance/RevOps | Aprovado; 600 linhas no grão de evento, sem transformar `churn_event` em perda econômica |
| Central, quatro filas e Conta 360 | Aprovado; filas filtráveis, paginação de 25, detalhes e ações |
| CRM demo | Aprovado; cadastro, associação por ID, pipeline/owner/valor estimado e atividades atribuídas a área/responsável |
| Follow-up e resultado | Aprovado; próxima ação precisa de prazo; concluir atividade exige resultado declarado; Conta 360 liga interação ao mesmo ID |
| Auditoria e persistência | Aprovado no SQLite de demo; eventos de criação/alteração e leitura após reiniciar processo |
| Browser desktop/mobile | Aprovado em 1440×1000 e 390×844; navegação, cadastro, atuação/follow-up, ações, downloads e drill-down |
| Cinco fontes originais | SHA-256 após build idênticos aos CSVs recebidos; detalhes em `data/audit/` |

## Critérios analíticos preservados

A regra de elegibilidade D90 e a flag legada `is_reactivation` mantêm a semântica anterior. Permanecem explícitos os 400/500 registros divergentes entre indicadores de churn, 531/600 eventos com linha paga vigente, 67 antes do primeiro pagamento, 2 entre linhas, 5.568/25.000 usos dentro da janela e 1.077/2.000 tickets pré-signup. São dados sintéticos com cutoff em 31/12/2024; erro/uso/ticket não prova churn, e crédito/reembolso informado não confirma caixa ou perda.

O CRM standalone não altera fontes, Conta 360 canônica, regras históricas ou sistemas externos. Um lead novo não recebe histórico ou valor de receita inventado. Owners/resultados são dados informados pelo operador demo; “Concluída” é status declarado, não outcome econômico verificado.

## Capturas e artefatos

- `browser-results.json` registra as dez rotas, drill-down, downloads, fluxo CRUD e largura dos viewports.
- `screenshots/crm-e-opera--o-comercial-desktop.png` e `screenshots/crm-e-opera--o-comercial-mobile.png` mostram o CRM em desktop e mobile após o fluxo de teste.
- `screenshots/00-central-desktop.png` e `screenshots/00-central-mobile.png` mostram a Central.
- As outras capturas guardam a revisão visual das páginas existentes.
- Os CSVs originais foram comparados por SHA-256 antes do empacotamento; conteúdo idêntico.

## Limites

A validação é automatizada/técnica e inspeção visual; não é pesquisa de usabilidade com operadores reais, homologação de especialistas, teste de carga multiusuário, teste de segurança, acessibilidade completa ou certificação de resultados. Windows não foi executado. Não há autenticação/RBAC, provedor compartilhado persistente, sincronização por API, histórico de imports CRM, nem escrita em CRM/billing/helpdesk.

O SQLite local demonstra persistência enquanto o arquivo e disco persistirem. Streamlit Community Cloud pode apagar/recriar o armazenamento e não o compartilha de forma garantida entre réplicas. **Não usar a URL pública com dados reais ou confidenciais.** O deployment verificado demonstra a execução do fluxo CRUD, mas não é um CRM de produção seguro/system of record até conectar autenticação e armazenamento persistente compartilhado.
