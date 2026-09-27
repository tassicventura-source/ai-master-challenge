# MVP_CHECKLIST — RavenStack Customer Journey

**Última revisão:** 2026-09-27 08:34 (São Paulo). E2E Playwright e suíte Python completa passaram; resultado E2E em `docs/browser-results.json`.

| ID | Critério do blueprint | Status | Evidência confirmada |
|---|---|---|---|
| A01 | Criar cliente com conta, assinatura, owner e eventos | Concluído | Cadastro nativo persistiu, ficou validado e abriu Cliente 360 no E2E. |
| A02 | Buscar/abrir Cliente 360 com estado, próxima ação e jornada | Concluído | Seleção e deep-link abertos pelo E2E; testes AppTest cobrem opções de contas. |
| A03 | Operar legacy sem validação total | Concluído | Interação e follow-up persistidos numa legacy parcialmente validada. |
| A04 | Validar apenas plano e seats no legacy | Concluído | E2E confirmou esses campos, conservou os demais sem validação. |
| A05 | Interação aparece na jornada | Concluído | Interação operacional e evento de jornada gravados no E2E. |
| A06 | Follow-up aparece em Meu Trabalho do responsável | Concluído | Tarefa atribuída ao ator QA percorreu o fluxo; AppTest/store cobrem ownership. |
| A07 | Concluir tarefa, sair da fila e auditar | Concluído | Conclusão confirmada e evento de auditoria verificado no E2E. |
| A08 | Prévia/alteração de subscription e evento | Concluído | E2E confirmou delta +300; teste de regressão cobre preview de linha paralela (+350). |
| A09 | Perda total explícita muda lifecycle e registra impacto | Concluído | Movimento `total_loss` explícito confirmou lifecycle `churned` no E2E. |
| A10 | Encerramento administrativo não causa churn indevido | Concluído | Encerrar uma linha preservou outra ativa e lifecycle `active` no E2E/unitário. |
| A11 | Tratar alerta sem apagar histórico | Concluído | Alerta vencido marcado tratado e histórico preservado no E2E. |
| A12 | Auditoria quem/quando/origem/antes/depois | Concluído | Evento de conclusão/movimentos e testes de store verificam ator e valores anteriores/novos. |
| A13 | CSVs históricos protegidos | Concluído | SHA-256 antes/depois validado no teste do store; fontes ficam read-only. |
| A14 | Sem promoção silenciosa de estado legacy | Concluído | Import idempotente e atualização somente dos campos confirmados; suíte/teste de domínio. |
| A15 | Fluxo funciona sem depender de dashboard | Concluído | Home Meu Trabalho, 22 rotas e viewport mobile sem overflow no E2E. |

## Validações pendentes

- Clone limpo e push/commit da branch; não foram feitos nesta sessão.
- `pip check` e `git diff --check` passaram após as alterações finais.

## Limitações reais

SQLite demo não é persistência durável no Streamlit Community Cloud. Postgres implementado, sem instância para smoke de integração e sem migração/Alembic. Sem login/SSO/RBAC; ator/owner é texto autodeclarado. Dados sintéticos; não inserir PII. Histórico raw read-only; `churn_event` não confirma perda econômica.
