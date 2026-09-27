# Submissão — Tassiani Ventura — Challenge 001

## Sobre a entrega

**Challenge:** Diagnóstico de Churn — RavenStack  
**Objetivo:** descobrir o que os dados realmente permitem afirmar sobre churn, identificar segmentos e movimentos relevantes para o negócio e transformar o diagnóstico em decisões e operação.

## Executive Summary

A investigação começou pelo aumento aparente de eventos precoces: entre contas com pelo menos 90 dias observáveis, a incidência de primeiro `churn_event` em até 90 dias passa de **19,4% em 2023 para 47,2% em 2024**. O cruzamento das cinco bases mostrou, porém, que `churn_event`, encerramento de subscription, refund e flags de churn **não representam de forma consistente perda definitiva de cliente ou receita**. A própria tabela de eventos mistura movimentos de jornada: há reativações, upgrades e downgrades precedentes, e todas as 500 contas possuem pelo menos uma linha paga ativa no corte da base.

Ao mesmo tempo, 2024 não representa simplesmente piora do negócio: novas contas cresceram **20,3%** e o valor inicial registrado cresceu **77,1%**. Organic concentrou grande parte desse crescimento, especialmente em Enterprise/Mixed, tornando **aquisição + qualidade do crescimento + handoff** uma frente prioritária de investigação, sem tratar Organic como causa de churn.

Produto e Suporte também foram testados. Problemas temporais impedem usar parte dos vínculos brutos como verdade, mas análises alternativas no nível da conta/jornada recuperaram cobertura suficiente e **não mostraram deterioração consistente capaz de explicar o fenômeno geral**. A principal conclusão é que a RavenStack precisa primeiro reconciliar o desfecho econômico real e melhorar a captura da jornada; caso contrário, continuará produzindo eventos ambíguos e decisões baseadas em definições incompatíveis.

## Demo online

**RavenStack Customer Journey Intelligence**  
https://ravenstack-customer-journey.streamlit.app/

O aplicativo é uma camada operacional complementar ao diagnóstico: conecta **dado → sinal → contexto → decisão → ação → responsável → acompanhamento → resultado**, sem converter automaticamente evento histórico em churn ou perda financeira.

## Solução

### 1. Diagnóstico executivo

- [Relatório Final](./diagnostic/RavenStack_Relatorio_Final.html) — **fonte oficial das conclusões**.
- [Reprodução completa da investigação](./diagnostic/REPRODUCAO_COMPLETA_INVESTIGACAO_ANALITICA.md) — perguntas, cálculos, testes, hipóteses refutadas e rastreabilidade.
- [Plano de Ação](./diagnostic/IMPACTO_ESTIMADO_ACOES.md) — ações por área, prioridade e horizonte.
- [Customer Value & Revenue Intelligence](./diagnostic/Customer%20Value%20%26%20Revenue%20Intelligence.html) — protótipo estratégico complementar.

### 2. Aplicação operacional

- [Código e instruções](./solution/)
- [Briefing para CEO](./solution/docs/BRIEFING_CEO.md)
- [Treinamento dos funcionários](./solution/docs/TREINAMENTO_FUNCIONARIOS.md)
- [Deploy Streamlit](./solution/docs/DEPLOY_STREAMLIT.md)
- [Modelo operacional de retenção](./solution/docs/RETENTION_OPERATING_MODEL.md)

### 3. Reprodução dos cálculos

O script [`reproduce_diagnostic.py`](./solution/scripts/reproduce_diagnostic.py) reproduz os principais cálculos e verificações usados no diagnóstico, incluindo coortes, sensibilidade temporal, aquisição, Organic × plano, refunds, continuidade paga e auditorias adicionais de Produto/Suporte.

## Abordagem

1. Validar estrutura, chaves, granularidade, temporalidade e significado das cinco bases antes de assumir uma definição de churn.
2. Reconciliar diferentes representações de churn e separar **evento registrado** de **perda econômica confirmada**.
3. Testar o aumento aparente de eventos precoces e sua sensibilidade à janela observável.
4. Separar crescimento em volume de crescimento em valor.
5. Abrir aquisição, planos e segmentos sem transformar associação em causa.
6. Testar Produto, Suporte, refunds/créditos e movimentos de subscription por abordagens alternativas quando a relação temporal original era insuficiente.
7. Converter os achados em plano operacional e em um MVP que preserve incerteza, contexto e rastreabilidade.

## Principais resultados

- **19,4% → 47,2%:** aumento observado de evento precoce entre coortes comparáveis; não equivale automaticamente a churn econômico.
- **42,9%:** o teste de sensibilidade mostra que grande parte do salto pode ser reproduzida pela estrutura temporal/observacional da base.
- **408 linhas pagas encerradas:** 399 tinham outra linha paga vigente na mesma data; nas 9 restantes, outra linha paga começa depois.
- **500/500 contas:** possuem pelo menos uma linha paga ativa no corte de 31/12/2024.
- **2024:** +20,3% em novas contas e +77,1% em valor inicial registrado versus 2023.
- **Organic:** respondeu por 60,9% do crescimento líquido de novas contas e 64,6% do crescimento de valor inicial; Enterprise/Mixed concentrou 94,3% do aumento de valor de Organic.
- **Produto:** a reanálise dos primeiros 90 dias após signup cobriu 194/195 contas comparáveis de 2024 e não encontrou deterioração consistente de uso que explique o fenômeno geral.
- **Suporte:** a análise dos primeiros 90 dias após signup também não encontrou diferença consistente de volume, resposta, resolução, satisfação ou escalonamento capaz de explicar o fenômeno geral.

## Recomendações

As ações completas estão no [Plano de Ação](./diagnostic/IMPACTO_ESTIMADO_ACOES.md). As frentes centrais são:

- **Growth/Comercial:** abrir Organic em origens específicas e reconstruir o contexto de aquisição; investigar Organic × Enterprise sem assumir causalidade.
- **Comercial → CS:** tornar handoff, expectativa, escopo e primeiro valor parte obrigatória da jornada.
- **Finance/RevOps + Dados:** reconciliar eventos, refunds/créditos e movimentos de subscription até chegar ao desfecho econômico real.
- **Produto + Dados:** corrigir o vínculo conta → assinatura → uso e preservar sinais de adoção/erro sem tratá-los automaticamente como churn.
- **Suporte:** registrar etapa da jornada, motivo, solução, pendência, área acionada e próximo passo.
- **Gestão:** acompanhar responsáveis, decisões, aprendizados e resultados em cadência operacional.

## Limitações

- Os dados são **sintéticos**; os padrões encontrados descrevem este dataset, não clientes SaaS reais.
- A base não oferece uma definição canônica e reconciliada de churn econômico, MRR atual ou perda financeira por conta.
- Há inconsistências temporais relevantes em Produto e Suporte; elas foram investigadas e contornadas quando possível, mas não devem ser escondidas.
- Refund/crédito registrado não comprova perda líquida de receita.
- O MVP não possui SSO/RBAC e requer banco externo, como PostgreSQL, para persistência durável/compartilhada em produção no Streamlit.
- Sinais do aplicativo são triagem operacional; não são probabilidades de churn nem causalidade.

## Process Log

O Process Log é obrigatório e será a última peça consolidada antes do envio final.

Arquivos atualmente presentes:

- [PROCESS_LOG.pdf](./process-log/PROCESS_LOG.pdf)
- [Process_Log.zip](./process-log/Process_Log.zip)

A versão final deve refletir também as últimas iterações, correções e decisões documentadas nesta entrega.

## Evidências e auditabilidade

- cinco bases originais preservadas em [`solution/data/raw/`](./solution/data/raw/);
- scripts de transformação e reprodução em [`solution/scripts/`](./solution/scripts/);
- testes automatizados em [`solution/tests/`](./solution/tests/);
- documentação técnica e operacional em [`solution/docs/`](./solution/docs/);
- histórico de commits no branch `submission/tassiani-ventura`.

> Em caso de diferença de interpretação entre materiais, prevalece o **Relatório Final**, apoiado pela **Reprodução Completa da Investigação Analítica**.
