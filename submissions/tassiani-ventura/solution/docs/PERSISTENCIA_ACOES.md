# Persistência operacional e arquitetura de produção

## O que persiste no MVP

`src/operating_store.py` implementa o estado canônico com SQLAlchemy. Raw/analytics são somente leitura; `op_source_records` preserva payload, linha e hash importados. A carga histórica é idempotente: só `accounts` fornece ID/nome/atributos estáveis ao cliente `legacy`; planos, status, churn e receita históricos não são promovidos a situação atual.

Entidades operacionais: `op_customers`, `op_subscriptions`, `op_interactions`, `op_tasks`, `op_alerts`, `op_journey_events`, `op_source_records` e `op_source_imports`. Cadastro/assinatura/tarefa inicial, interações/follow-up, alterações de assinatura/lifecycle, tarefas/alertas e eventos relacionados são gravados em transações. Eventos guardam ator informado, origem, horário, resumo, antes/depois e entidade relacionada. Campos históricos só entram no agregado atual quando confirmados explicitamente.

A Central histórica persiste snapshot do sinal, área, conta, ação, owner, prioridade, prazo, status, observação, resultado e trilha. Para compatibilidade, SQLite usa `retention_actions`/`retention_action_events`; PostgreSQL usa `op_retention_actions`/`op_retention_action_events`. O mesmo registro aparece em Minha fila por responsável, Gestão e Conta 360 da conta correspondente. Resultado é informação declarada pelo operador; não é reconciliação automática de outcome econômico.

### SQLite local / modo demo

Sem `DATABASE_URL`, ambos os stores usam `data/retention_actions.sqlite` por padrão; `RETENTION_DB_PATH` escolhe outro arquivo local. O banco é criado no primeiro uso. Para validar persistência local, crie cliente/ação, reinicie o processo Streamlit e reabra Cliente 360 / Minha fila. Os testes usam bancos temporários para isolamento.

O botão de reset da Gestão exige digitar `RESETAR DEMO` e só funciona em SQLite; recarrega as 500 contas históricas e mantém os CSVs analíticos intactos. **Não use reset em dados de trabalho.**

### PostgreSQL para persistência compartilhada

O app aceita `DATABASE_URL`/`RAVENSTACK_DATABASE_URL` por variável de ambiente ou Streamlit Secrets. Ações da Central consultam ambos os nomes também em env/Secrets. Use uma URL PostgreSQL com TLS e psycopg, por exemplo:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

No primeiro arranque são criadas as tabelas SQLAlchemy para dados operacionais e ações de retenção. O seed das fontes é idempotente por cliente/identificador/hash de arquivo. Todas as escritas da UI usam transações do banco. Para deploy real, testar previamente connectivity, permissões, backup e transições em uma base de staging.

O modo PostgreSQL é implementado, mas não pôde ser conectado/validado nesta entrega porque não havia instância ou credenciais PostgreSQL disponíveis no sandbox. O MVP ainda não inclui Alembic/versionamento de schema nem migração automática de dados do arquivo SQLite pré-existente, incluindo o histórico `retention_actions`. Faça export/backup e um plano de migração antes de trocar uma base em uso; não aponte uma atualização incompatível para registros de produção.

## Limites do Streamlit Community Cloud

Sem PostgreSQL, o SQLite local pode ser apagado em reboot/redeploy e não é compartilhado de forma confiável entre réplicas. O app exibe aviso quando essa configuração está ativa. Por isso, o modo SQLite é para clone/local e demonstração com dados sintéticos, não para tratar ações importantes como duráveis no Cloud.

Não há autenticação, SSO, RBAC, tenant isolation ou ator verificado. `Quem está usando?` e owners são textos autodeclarados. Uma pessoa com acesso ao banco pode alterar os dados/eventos diretamente; o histórico é auditável na camada da aplicação, não criptograficamente imutável.

**Não insira informação real de clientes ou PII no app demo/público.** Antes de um piloto real, restrinja acesso e implemente SSO/RBAC e política de dados.

## Recomendação de arquitetura de produção

```text
Usuário autenticado (SSO/OIDC)
        │ identidade verificada / papel
        ▼
UI Streamlit
        │ API autenticada, schema versionado, autorização por conta
        ▼
Serviço de operações
        ├── PostgreSQL gerenciado (cadastro, assinatura, interação, tarefa, alertas, ações, eventos)
        ├── diretório/CRM (IDs e permissões)
        ├── job de importação somente leitura (hash/versão/source refs)
        └── integrações externas com outbox, retry e idempotência
```

Pré-requisitos para piloto: SSO/RBAC e princípio de menor privilégio; TLS e secrets manager; migrações versionadas; auditoria de identidade controlada pelo servidor; backups/PITR com restauração testada; concorrência/constraints; política de retenção e minimização de texto/PII; observabilidade e alertas; APIs com outbox/idempotência; reconciliação aprovada por Finance antes de declarar impacto de receita.

O MVP não sincroniza com CRM/billing/helpdesk. `churn_event`, erro de uso, ticket, fim administrativo de subscription e refund informado não são convertidos automaticamente em churn ou perda econômica.
