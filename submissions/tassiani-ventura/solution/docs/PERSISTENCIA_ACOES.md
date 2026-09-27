# Persistência das ações: demo e arquitetura de produção

## Modo demo implementado

O Streamlit grava em SQLite, separado do banco analítico: `data/retention_actions.sqlite` (ou caminho definido por `RETENTION_DB_PATH`). As tabelas são criadas automaticamente por `src/action_store.py`.

- `retention_actions`: estado atual de cada tarefa, com sinal/conta/área, dono, prioridade, prazo, status, observação, resultado, timestamps e snapshot JSON da evidência usada.
- `retention_action_events`: evento append-only por criação/edição com timestamp UTC, tipo e JSON dos campos alterados.
- Transação `BEGIN IMMEDIATE`, constraints de status, validação de campos obrigatórios, bloqueio contra reassociar uma tarefa a outro sinal e prazo no formato ISO.
- Uma ação concluída exige resultado informado; o banco não verifica se esse resultado é verdadeiro.
- Atualizar/refazer deploy do banco analítico (`ravenstack.sqlite`) não sobrescreve o arquivo de ações demo.

Teste local:

```bash
python -m streamlit run app.py
# Criar uma ação na Central; reiniciar o processo; confirmar que continua listada.
```

`RETENTION_DB_PATH=/caminho/persistente/acoes.sqlite` permite apontar para volume montado localmente. O modo demo não deve receber dados pessoais ou de cliente real: responsável é texto livre, não há login, autorização, isolamento multi-tenant ou criptografia gerenciada.

### Limite de deploy Streamlit

SQLite valida o ciclo funcional e é persistente entre reruns/reinício **quando o mesmo disco persiste**, mas não é banco compartilhado escalável. O armazenamento local do Streamlit Community Cloud pode ser efêmero/recriado em deploy ou reboot e réplicas podem ter discos separados. Então essa implantação serve a demo, não ao system of record operacional. O volume de dados de amostra é sintético; para um piloto de produção escolha serviço com filesystem persistente ou, recomendado, banco gerenciado.

## Arquitetura recomendada para produção

```text
Browser/Streamlit UI
    │ SSO OIDC + RBAC; sessão curta, CSRF e auditoria de identidade
    ▼
Retention API (stateless; valida esquema, acesso a conta e transições)
    ├── PostgreSQL gerenciado (source of truth de ações/snapshots/eventos)
    ├── job idempotente que lê fontes analíticas e grava versão de sinais
    └── integrações de CRM/helpdesk/billing por API, somente após contrato/owner de campos
         (sem publicar mudança automática de churn ou receita)
```

### Tabelas/entidades sugeridas

- `signal_definition`: `rule_id`, versão, descrição, denominador/filtro/limiar, proprietário, `valid_from/to`, checks de qualidade.
- `signal_instance`: `signal_id` (estável ou UUID), `rule_id/version`, `account_id`, área, campos de prioridade e explicação, `evidence_snapshot`, `source_refs`, `observed_at`, cutoff e versão/hash da fonte.
- `retention_action`: `action_id`, `signal_id`, `account_id`, área, texto, owner como FK para diretório/CRM, prioridade, `due_at`, status, observação, resultado, criador/atualizador e timestamps.
- `retention_action_event`: evento append-only, action/version, ator autenticado, instante, estado anterior/novo e motivo.
- `outcome_reconciliation`: registro independente e aprovado por Finance/RevOps para ligar contrato, fatura, pagamento, movimento, MRR antes/depois e classificação econômica. `churn_event` só é evidência de origem, nunca resultado automático.

Migrar com migrations numeradas e compatibilidade para trás; chaves estrangeiras, constraints de status, índice por área/status/prazo/conta e controle otimista de versão. Se necessário, particione o event log por data depois de medir volume.

### Segurança e confiabilidade

1. OIDC/SSO; papéis por área, autorização por conta/tenant e segregação de organizações antes de habilitar dados de cliente real.
2. Segredos apenas no secret manager do ambiente; TLS em trânsito; criptografia/backup do serviço gerenciado; princípio de menor privilégio e rotações.
3. API valida owners ativos, prazos, transições de estado, acesso à conta, limite do corpo e valores dos enums. Não confiar em nome de usuário digitado no form.
4. Eventos de auditoria não editáveis por operação de usuário; correções via novo evento com ator/motivo; trilha exportável e monitorada.
5. Backup criptografado, PITR, política de retenção, teste periódico de restauração e objetivos RPO/RTO aprovados antes do go-live.
6. Outbox/idempotência para integrações, dead-letter/retry, rate limits, monitoramento de falhas e reconciliação; nunca usar retry para duplicar ações externas.
7. Observabilidade: logs estruturados sem feedback sensível, métricas de latência/erros, alertas de fila atrasada e monitoramento de freshness/quality dos dados.
8. Aprovação humana antes de escrita em CRM/billing/helpdesk; Finance valida qualquer outcome econômico. Nenhum bulk write até testar permissões, rollback e auditoria.

### Passagem do demo para produção

- O provider de dados de ações deve ser interface independente do Streamlit; adapte `src/action_store.py` para uma API autenticada/repositório PostgreSQL.
- A API emite `actor_id` de claims OIDC e troca owner livre por ID de diretório; migre status/observações/resultados com IDs e timestamps, sem fabricar quem operou historicamente.
- Mantenha `signal_snapshot_json`/IDs/hashes dos registros originais; deixe clara a regra/versão aplicada e a data de corte.
- Execute uma migração e reconciliação somente depois de aprovação do dono de dados. Não importa prioridade P1/P2/P3 como churn nem MRR em risco.
- Valide concorrência, permissões, privacidade, backup/restauração, idempotência e disponibilidade antes da primeira gravação real.
