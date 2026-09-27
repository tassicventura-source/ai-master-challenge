# Diagnóstico e materiais de decisão

Esta pasta reúne os materiais analíticos do Challenge 001. Todos usam as cinco bases sintéticas com corte em 31/12/2024 e distinguem evento registrado de perda econômica confirmada.

## Ordem de leitura

1. [RavenStack_Relatorio_Final.html](./RavenStack_Relatorio_Final.html) — **fonte oficial das conclusões executivas**.
2. [REPRODUCAO_COMPLETA_INVESTIGACAO_ANALITICA.md](./REPRODUCAO_COMPLETA_INVESTIGACAO_ANALITICA.md) — perguntas, testes, hipóteses refutadas, cálculos e rastreabilidade.
3. [IMPACTO_ESTIMADO_ACOES.md](./IMPACTO_ESTIMADO_ACOES.md) — plano operacional por área, prioridade e horizonte.
4. [Customer Value & Revenue Intelligence.html](./Customer%20Value%20%26%20Revenue%20Intelligence.html) — protótipo estratégico complementar.

## Leitura correta dos dados

A revisão final confirmou que a tabela de uso não deve ser descartada apesar dos problemas de vínculo temporal. A análise foi recuperada no nível da conta/jornada, e Produto e Suporte foram retestados em janelas comparáveis. Os resultados não sustentam nenhum dos dois como explicação geral do aumento de eventos precoces, mas preservam ambos como fontes de sinais operacionais e hipóteses por conta.

O protótipo estratégico conecta:

- **Revenue Truth** — reconciliar o desfecho econômico real por conta;
- **Customer Value Journey** — reconstruir a jornada que levou ao desfecho;
- **Action Layer** — definir responsável, próxima ação, prazo e evidência necessária.

Nenhum material trata `churn_event`, `accounts.churn_flag`, refund/crédito ou encerramento de subscription como perda econômica comprovada sem reconciliação.

> Em caso de diferença de interpretação, prevalece o **Relatório Final**, apoiado pela reprodução analítica.
