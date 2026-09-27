# Persistência operacional: CRM, atividades e retenção

## O que funciona no modo demo

O Streamlit grava na base SQLite `data/retention_actions.sqlite` (ou no caminho definido por `RETENTION_DB_PATH`), separada do banco analítico reconstruído. O schema é criado automaticamente por `src/action_store.py`.

| Tabela | Uso |
|---|---|
| `crm_accounts` | Cadastro standalone de lead/cliente, origem do registro, atributos informados, owner textual, etapa de jornada/pipeline, valor estimado e moeda, previsão e próxima ação. |
| `crm_interactions` | Diário de ligação, reunião, proposta, suporte ou outra atuação por conta/área, com responsável, resultado, status e follow-up/prazo. |
| `crm_events` | Trilha de criação/alterações de contas e interações, com timestamp UTC e JSON dos campos alterados. |
| `retention_actions` | Ação vinculada a conta/sinal, área, owner, prioridade, prazo, status, observação, resultado e snapshot da evidência. |
| `retention_action_events` | Trilha das alterações das ações de retenção. |

O fluxo disponível em **CRM e operação comercial** permite:

1. Cadastrar um lead/cliente ou associar um registro analítico pelo ID já existente.
2. Definir etapa, responsável, segmento, canal e valor **estimado** da oportunidade (não receita realizada).
3. Atualizar a etapa e o owner no Pipeline.
4. Registrar a atuação comercial/CS/Suporte por tipo, área, resumo e resultado.
5. Manter atividade planejada, próxima ação e prazo; concluir ou cancelar sem apagar o histórico.
6. Abrir a Conta 360 operacional, consultar atividades e trilha de mudanças.

O ID de uma conta associada ao dataset é reutilizado, mas os campos comerciais são armazenados em camada separada. Um lead `CRM-*` não recebe telemetria, receita, assinatura ou histórico inventado. Cadastro/interação não altera os CSVs nem sincroniza com CRM, billing ou helpdesk externo.

As gravações da demonstração usam transação SQLite (`BEGIN IMMEDIATE`), validações de owner/campos/etapas e eventos de auditoria da aplicação. Atividade concluída exige resultado declarado; uma próxima ação exige prazo. A aplicação registra o que a pessoa informou — não verifica que a atividade ou resultado realmente ocorreu. Um usuário de banco com acesso ao arquivo ainda pode alterar tabelas/eventos diretamente; não se trata de auditoria criptograficamente imutável.

Teste local:

```bash
python -m streamlit run app.py
# CRM e operação comercial → Cadastrar conta → Pipeline → atividade/follow-up
# Reinicie o processo local e confira as contas e atividades registradas.
```

`RETENTION_DB_PATH=/caminho/persistente/operacao.sqlite` seleciona outro arquivo local. Responsáveis são texto livre, não associados a diretório de usuários.

## Limites de uso do Streamlit Community Cloud

O Community Cloud pode descartar/recriar o armazenamento local em deploy ou reboot; réplicas podem não compartilhar o mesmo disco. A URL existente foi publicada sem autenticação de aplicação. Embora o CRUD funcione para demonstrar o fluxo, a URL pública **não deve receber nomes, e-mails, contatos, notas comerciais, dados reais de cliente ou informações confidenciais**. O aviso de segurança é exibido dentro do app.

Para um teste com dados não públicos, primeiro restrinja a visibilidade do app no Cloud e confirme quem tem acesso. A opção de tornar o repositório/app privado é uma configuração da conta que deve ser verificada no workspace antes de inserir dados reais; este código não implementa login ou autorização.

## Arquitetura recomendada para produção

```text
Usuário autenticado (SSO/OIDC)
        │ sessão e papel verificados
        ▼
UI Streamlit (sem segredos nem credenciais compartilhadas)
        │ API autenticada; validação de acesso por conta/tenant
        ▼
API de operações (stateless, esquema e transições controladas)
        ├── PostgreSQL gerenciado — cadastro, pipeline, atividades, ações e eventos
        ├── diretório/CRM — IDs de operador/conta e permissões autorizadas
        ├── job idempotente — leitura das fontes aprovadas e versão/corte dos sinais
        └── integrações CRM/helpdesk/billing — apenas após contrato e aprovação do owner
```

### Entidades para o banco compartilhado

- `crm_account`: `account_id`, `record_origin`, atributos de cadastro, `owner_id` de diretório, etapa, valor estimado/moeda, data esperada e versionamento.
- `crm_interaction`: conta, tipo/área, data, resumo, ator autenticado, resultado declarado, status e follow-up/prazo.
- `crm_event`: entidade/versionamento, estado anterior/novo, ator autenticado, timestamp e motivo; escrita append-only pela API.
- `retention_action` / `retention_action_event`: sinal imutável/snapshot, conta, owner de diretório, prazo/status/resultado e trilha.
- `outcome_reconciliation`: registro separado, aprovado por Finance/RevOps, para ligar contrato, fatura, pagamento, MRR antes/depois e classificação econômica.

### Requisitos antes do piloto real

1. SSO/OIDC e RBAC; autorizar cada conta/tenant/área e usar identidade do operador, nunca confiar em owner digitado.
2. PostgreSQL gerenciado via API autenticada, TLS, secrets manager, criptografia e backups/PITR testados.
3. Migrações versionadas, constraints de domínio, controle de concorrência e auditoria imutável, exportável e monitorada.
4. Política de dados/privacidade, retenção e deleção aprovada; campos de notas e PII minimizados.
5. Acesso de menor privilégio, alertas/observabilidade, objetivos RPO/RTO e procedimento de restauração.
6. Integrações externas com outbox/idempotência, retry com dead-letter e aprovação humana antes de qualquer escrita em sistemas de origem.
7. Não importar P1/P2/P3 como churn nem atribuir resultado econômico automaticamente. `churn_event`, valor de refund informado e valor inicial continuam não reconciliados.

A passagem do demo para produção exige substituir o provider SQLite por API/repositório PostgreSQL e testar migração, isolamento, permissões, privacidade, concorrência e restauração. Configurar apenas uma variável/secret de banco não torna o app seguro nem converte a SQLite atual em banco de produção.
