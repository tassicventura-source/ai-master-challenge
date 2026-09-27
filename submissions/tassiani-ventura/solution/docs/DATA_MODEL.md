# RavenStack — Modelo de dados proposto

## Princípio

O projeto não cria cinco novas fontes operacionais. Ele mantém os sistemas atuais como fontes e muda a **semântica das cinco saídas de dados** para que a jornada seja reconstruível.

## 1. accounts

**Função:** cadastro mestre e atributos estáveis da conta.

Mantém: `account_id`, nome, industry, country, signup e origem macro.

Sai do canônico: `plan_tier`, `seats`, `is_trial`, `churn_flag`, porque o histórico atual não demonstra que sejam estado inicial/atual confiável da conta.

Entra: `referral_detail`, `icp_segment`, `owner_id`, `journey_stage`.

## 2. subscriptions

**Função:** registros de assinatura no grão da linha. A identificação de contrato ainda depende de captura e reconciliação.

Mantém plano, seats, MRR/ARR, trial, billing, auto-renew e datas.

Sai do canônico: flags de upgrade/downgrade/churn sem timestamp.

Entra: `contract_id`, `record_state`, `movement_type`, `movement_effective_date`.

## 3. feature_usage

**Função:** telemetria de produto.

Preserva todas as linhas. `source_usage_id` mantém o ID original; `usage_event_id` cria chave canônica única sem apagar registros conflitantes.

Entra: `account_id`, `temporal_status`, `signup_temporal_status`, `user_id`, `action_name`, `event_success`, `context`.

## 4. customer_interactions

Substitui a visão estreita de `support_tickets` por uma estrutura comum de interação.

Histórico atual: todas as linhas têm `area=Support` e `interaction_type=support_ticket`.

Futuro: Comercial, Onboarding, CS e Suporte usam a mesma espinha comum, com campos condicionais.

Campos mínimos: área, tipo, tópico, feature, problema, impacto, causa, recorrência, resultado, próxima ação e prazo. Métricas de SLA permanecem específicas de suporte.

## 5. lifecycle_events

Substitui `churn_events` como nome canônico.

O evento legado é preservado em `recorded_event_type`, porém `canonical_event_type` e impacto econômico começam vazios até reconciliação.

Tipos futuros: sale, activation, renewal, expansion, contraction, cancellation, logo_churn, reactivation.

Campos econômicos: MRR, seats e plano antes/depois.

## Regra de auditoria

Nada é apagado do histórico bruto. Campos retirados do modelo canônico ficam preservados em `data/raw` e nos arquivos de auditoria em `data/audit`.

## Camada operacional de retenção (demo)

`src/retention.py` deriva sinais determinísticos das cinco saídas canônicas; os sinais guardam regra, prioridade explicada, incerteza e referências às linhas de origem. Os IDs de origem continuam disponíveis para Conta 360. A prioridade P1/P2/P3 direciona trabalho, sem score preditivo e sem outcome econômico inferido.

As ações vivem em `data/retention_actions.sqlite`, separado do banco de análise: owner informado, tarefa, prioridade, prazo, status, observação, resultado declarado, snapshot da evidência e eventos append-only de auditoria. Essa base demonstra persistência local; não adiciona campos retroativamente às fontes nem altera CRM/billing/helpdesk. SQLite local não é system of record compartilhado de produção; veja `PERSISTENCIA_ACOES.md`.

## Correções da versão de desenvolvimento

- `legacy_reactivation_flag` preserva a flag original sem transformar automaticamente o evento em reativação.
- `account_360.observation_end` explicita o corte; `eligible_90d` identifica a janela completa.
- `recorded_event_within_90d` é nulo em contas sem 90 dias completos.
- Contagens sem registros válidos são zero observado; datas, planos e valores desconhecidos permanecem nulos.
- Ausências de chaves, chaves duplicadas nas entidades e referências órfãs interrompem o build com erro explícito. IDs de uso conflitantes continuam preservados conforme a regra original.
- O SQLite é reconstruído em arquivo temporário, com índices por conta e substituição ao final. A leitura usa tabelas permitidas e conexões somente leitura.
