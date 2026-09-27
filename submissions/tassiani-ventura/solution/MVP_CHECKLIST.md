> **Checkpoint histórico.** Esta checklist registra uma etapa intermediária do desenvolvimento. O estado final validado da entrega está em [`docs/VALIDACAO.md`](docs/VALIDACAO.md), que substitui os checkpoints e pendências abaixo.

# MVP_CHECKLIST — RavenStack Customer Journey

**Última revisão:** 2026-09-27 08:10, São Paulo. **Atenção:** core funcional e suíte Python aprovados; E2E browser ainda NÃO aprovado. Status reflete a evidência disponível, não apenas a presença de código.

| ID | Critério do blueprint | Status | Evidência |
|---|---|---|---|
| A01 | Criar cliente com conta, assinatura, owner e eventos | Parcial | Store transacional e testes/AppTest; E2E de cadastro executado até fluxo posterior. |
| A02 | Buscar/abrir Cliente 360 com estado, próxima ação e jornada | Parcial | AppTest abre clientes/drilldowns; revisar no E2E final. |
| A03 | Operar legacy sem validação total | Parcial | Teste de store verifica interação/task em legacy; smoke inclui operação parcial, E2E falhou depois. |
| A04 | Validar apenas plano e seats no legacy | Parcial | Unit/AppTest cobre validação seletiva; E2E ainda precisa concluir e confirmar fonte preservada. |
| A05 | Interação aparece na jornada | Parcial | Testes do store; E2E alcançou jornada, mas a rodada total terminou depois em outro ponto. |
| A06 | Follow-up aparece em Meu Trabalho do responsável | Parcial | Teste de domínio e validação manual Chromium mostram owner/fila; E2E final pendente. |
| A07 | Concluir tarefa, sair da fila e auditar | Parcial | Unit + trecho executado no E2E antes de A11. |
| A08 | Prévia/alteração de subscription e evento | Parcial | Teste unitário e trecho E2E chegaram a delta +300 antes da falha posterior. |
| A09 | Perda total explícita muda lifecycle e registra impacto | Parcial | Coberto por unitário; roteiro E2E adicionado, ainda não confirmado até o fim. |
| A10 | Encerramento administrativo de linha não causa churn indevido | Parcial | Unitário cobre duas subscriptions; roteiro E2E adicionado, ainda não confirmado até o fim. |
| A11 | Tratar alerta sem apagar histórico | Parcial | Store/AppTest e roteiro browser adicionados; verificar sucesso total no E2E. |
| A12 | Auditoria quem/quando/origem/antes/depois | Parcial | Eventos e testes do store; fechar com resultado E2E. |
| A13 | CSVs históricos protegidos | Concluído (teste) | SHA-256 antes/depois de operações no teste de store. |
| A14 | Sem promoção silenciosa de estado legacy | Concluído (teste) | Import idempotente e confirmação explícita; suíte completa passou. |
| A15 | Fluxo funciona sem depender de dashboard | Parcial | Home Meu Trabalho e rotas AppTest; verificar navegação E2E desktop/mobile. |

## Última suíte aprovada
`python -m pytest -q -W error::DeprecationWarning`: **87 passed em 203,34 s**. Esta execução foi antes da alteração mais recente de `st.tabs(on_change="rerun")`; reexecutar.

## Bloqueio exato
Último E2E terminou em `tests/browser_smoke.cjs` tentando preencher `Motivo da mudança *` depois de marcar assinatura paralela; o campo foi desmontado/ficou invisível por mudança de tab/rerun. Correção aplicada: chaves estáveis e `on_change="rerun"` às tabs em `src/operational_ui.py`. Falta reexecutar para validar essa correção.

## Entrega pendente
- E2E Chromium desktop/mobile completo; conferir capturas e `docs/browser-results.json`.
- Reexecutar compilação, pytest completo, `pip check`, `git diff --check` após correção de tabs.
- Atualizar `docs/VALIDACAO.md`; não usar evidências antigas sobre página pública.
- Git add explícito (a raiz ignora `submissions/`), commit/push para `origin/submission/tassiani-ventura`.
- Clone limpo e ZIP final sem banco SQLite, cache, `node_modules` ou `test-results`.

## Limitações
SQLite demo não é persistência durável no Streamlit Cloud. Postgres implementado, sem instância para smoke de integração e sem migração/Alembic. Sem login/SSO/RBAC; ator/owner é texto autodeclarado. Dados sintéticos; não inserir PII. Histórico raw read-only e sem tratar `churn_event` como perda econômica confirmada.
