# MVP_CHECKLIST — RavenStack Customer Journey

**Revisão:** 2026-09-27 09:04 (São Paulo). Interface simplificada e fluxo operacional validado em Python, navegador e clone limpo.

| ID | Critério de aceite | Status | Evidência |
|---|---|---|---|
| A01 | Criar cliente, assinatura, responsável e eventos | Concluído | Cadastro nativo criado e aberto na Ficha do cliente; Playwright. |
| A02 | Encontrar ficha com estado, próxima ação e jornada | Concluído | Busca e navegação testadas; título/descrição orientados ao trabalho. |
| A03 | Usar conta importada sem validação total | Concluído | Interação e próxima ação permitidas em conta parcialmente validada. |
| A04 | Confirmar campos legacy seletivamente | Concluído | Plano e seats confirmados sem promover o restante. |
| A05 | Registrar contato na jornada | Concluído | Contato/evento auditável persistidos. |
| A06 | Atribuir próximo passo a responsável | Concluído | Tarefa aparece na fila do responsável. |
| A07 | Concluir tarefa e auditar | Concluído | E2E confirmou saída da fila e evento. |
| A08 | Alterar assinatura com prévia | Concluído | E2E delta +300; teste de inclusão paralela cobre +350. |
| A09 | Registrar perda total confirmada | Concluído | Ação explícita altera etapa da relação, sem inferência histórica. |
| A10 | Encerrar linha sem churn indevido | Concluído | Outra linha ativa mantém a conta ativa. |
| A11 | Tratar alerta sem apagar histórico | Concluído | E2E confirmou tratamento e retenção do histórico. |
| A12 | Auditar ator, data, origem e antes/depois | Concluído | Eventos transacionais e E2E de alteração/conclusão. |
| A13 | Proteger CSVs históricos | Concluído | Hashes antes/depois nos testes; fontes read-only. |
| A14 | Não promover legacy automaticamente | Concluído | Seed idempotente e confirmação explícita dos dados. |
| A15 | Trabalhar sem depender de dashboard | Concluído | Home Minha fila; E2E das rotas e viewport mobile 390×844 sem overflow horizontal. |

## Evidência final

Suíte completa: **88 passed in 207.54s**; testes focados de interface/navegação após os rótulos finais: **33 passed in 171.75s**; Playwright exit 0, A01–A15, 20 rotas abertas e mobile verificado; `compileall`, `pip check` e `git diff --check` passaram. Clone limpo no commit `f9a5cf2` compilou e inicializou com **500 contas históricas e 500 clientes**.

## Limitações reais

PostgreSQL está implementado, mas sem instância para integração; SQLite local não é persistência durável garantida no Streamlit Cloud. Sem SSO/RBAC; responsável/operador é autodeclarado. Não usar dados pessoais reais no demo. `churn_event` não comprova perda econômica.
