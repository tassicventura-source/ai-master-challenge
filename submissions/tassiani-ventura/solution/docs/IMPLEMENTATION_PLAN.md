# Plano de implementação enxuto

## Fase 0 — MVP deste repositório

- 5 CSVs brutos preservados.
- transformação reproduzível para 5 bases canônicas;
- Account 360 no grão conta;
- banco SQLite local;
- aplicação Streamlit por área;
- mapa de mudanças de schema;
- testes automatizados.

## Fase 1 — Configurar sistemas existentes

Não trocar CRM, helpdesk, billing ou analytics. Primeiro configurar campos e nomenclaturas.

1. CRM/Marketing: `referral_detail`, ICP, owner e stage.
2. CRM/Sales/CS: registrar interações com `area` e `interaction_type`.
3. Helpdesk: topic, feature, impact, root cause e recurrence.
4. Produto/analytics: user_id, action_name, event_success e contexto.
5. Billing/RevOps: contract_id, movement_type/date, MRR antes/depois.

## Fase 2 — Automatizar ingestão

Trocar arquivos CSV por extrações agendadas/API sem mudar o modelo canônico.

## Fase 3 — Governança

- owner de cada campo;
- catálogo de valores permitidos;
- SLA de preenchimento;
- regras de qualidade;
- versionamento de schema.

## Fase 4 — Inteligência

Somente depois de o outcome econômico estar reconciliado:

- health/risk score;
- detecção de oportunidade de expansão;
- cost-to-serve;
- priorização de backlog por contas e valor afetados;
- avaliação de ações de CS.

## Atualização — camada operacional entregue (26/09/2026)

Acrescentados na Fase 0 a Central paginada, sinais determinísticos com regras/evidência/incerteza, filas das quatro áreas, integração Conta 360 e registro local de ações com responsáveis, prazo, status, resultado e trilha de alterações. O SQLite mantém modo demo e a evidência sintética; é uma camada operacional de demonstração, não autorização para tratar essa base como system of record.

As Fases 1–3 continuam necessárias para operações reais: validar os sistemas oficiais atuais, instrumentar os campos do dono de dados, identificar operadores por SSO/RBAC e obter persistência compartilhada/auditoria operacional. Fase 4 permanece condicionada a outcomes econômicos reconciliados e avaliação específica; não faz parte desta entrega.
