# Submissão — Tassiani Ventura — Challenge 001

> **Outra entrega nesta submissão:** [Challenge 004 — Estratégia Social Media](./challenge-004/README.md), com análise das cinco plataformas, relatórios, notebook e aplicativo Streamlit.

## Sobre mim

- **Nome:** Tassiani Ventura
- **LinkedIn:** https://www.linkedin.com/in/tassianiventura/
- **Challenge escolhido:** 001 — Diagnóstico de Churn

Minha trajetória passou por conteúdo, gestão de projetos, liderança, processos e aquisição, dentro do marketing digital. Hoje sigo trabalhando isso, conectando liderança e produtividade. Acredito que pessoas, processos e tecnologia são pilares fundamentais hoje em dia. Foi isso que quis explorar neste desafio.

---

## Executive Summary

Investiguei as cinco bases da RavenStack para entender se o aumento aparente de churn representava perda real de clientes e receita ou se havia um problema de definição e leitura do ciclo de vida. A incidência do primeiro churn_event em até 90 dias sobe de **19,4% em 2023 para 47,2% em 2024**, mas o cruzamento das bases mostra que evento, encerramento de subscription, refund e flags de churn não representam de forma consistente perda econômica definitiva. Ao mesmo tempo, 2024 registra **+20,3% em novas contas e +77,1% em valor inicial**, com Organic concentrando grande parte do crescimento; Produto e Suporte também foram testados e não explicam de forma consistente o fenômeno geral. A recomendação central é reconciliar o desfecho econômico real e a jornada da conta antes de tratar esses eventos como churn — e a entrega transforma esse diagnóstico em relatório, reprodução analítica, plano de ação e uma aplicação operacional.

## Demo online

**RavenStack Customer Journey Intelligence**  
https://ravenstack-customer-journey.streamlit.app/

O aplicativo é uma camada operacional complementar ao diagnóstico: conecta **dado → sinal → contexto → decisão → ação → responsável → acompanhamento → resultado**, sem converter automaticamente evento histórico em churn ou perda financeira.

---

## Solução

### 1. Diagnóstico executivo

- [Relatório Final](./diagnostic/RavenStack_Relatorio_Final.html) — **fonte oficial das conclusões**.
- [Reprodução completa da investigação](./diagnostic/REPRODUCAO_COMPLETA_INVESTIGACAO_ANALITICA.md) — perguntas, cálculos, testes, hipóteses refutadas e rastreabilidade.
- [Plano de Ação](./diagnostic/IMPACTO_ESTIMADO_ACOES.md) — ações por área, prioridade, horizonte e impacto estimado.
- [Customer Value & Revenue Intelligence](./diagnostic/Customer%20Value%20%26%20Revenue%20Intelligence.html) — protótipo estratégico complementar.

### 2. Aplicação operacional

- [Código e instruções](./solution/)
- [Briefing para CEO](./solution/docs/BRIEFING_CEO.md)
- [Treinamento dos funcionários](./solution/docs/TREINAMENTO_FUNCIONARIOS.md)
- [Deploy Streamlit](./solution/docs/DEPLOY_STREAMLIT.md)
- [Modelo operacional de retenção](./solution/docs/RETENTION_OPERATING_MODEL.md)

### 3. Reprodução dos cálculos

O script [reproduce_diagnostic.py](./solution/scripts/reproduce_diagnostic.py) reproduz os principais cálculos e verificações usados no diagnóstico, incluindo coortes, sensibilidade temporal, aquisição, Organic × plano, refunds, continuidade paga e auditorias adicionais de Produto/Suporte.

---

## Abordagem

1. Validar estrutura, chaves, granularidade, temporalidade e significado das cinco bases antes de assumir uma definição de churn.
2. Reconciliar diferentes representações de churn e separar **evento registrado** de **perda econômica confirmada**.
3. Testar o aumento aparente de eventos precoces e sua sensibilidade à janela observável.
4. Separar crescimento em volume de crescimento em valor.
5. Abrir aquisição, planos e segmentos sem transformar associação em causa.
6. Testar Produto, Suporte, refunds/créditos e movimentos de subscription por abordagens alternativas quando a relação temporal original era insuficiente.
7. Converter os achados em plano operacional e em um MVP que preserve incerteza, contexto e rastreabilidade.

---

## Resultados / Findings

- **19,4% → 47,2%:** aumento observado de evento precoce entre coortes comparáveis; não equivale automaticamente a churn econômico.
- **42,9%:** o teste de sensibilidade mostra que grande parte do salto pode ser reproduzida pela estrutura temporal/observacional da base.
- **408 linhas pagas encerradas:** 399 tinham outra linha paga vigente na mesma data; nas 9 restantes, outra linha paga começa depois.
- **500/500 contas:** possuem pelo menos uma linha paga ativa no corte de 31/12/2024.
- **2024:** +20,3% em novas contas e +77,1% em valor inicial registrado versus 2023.
- **Organic:** respondeu por 60,9% do crescimento líquido de novas contas e 64,6% do crescimento de valor inicial; Enterprise/Mixed concentrou 94,3% do aumento de valor de Organic.
- **Produto:** a reanálise dos primeiros 90 dias após signup cobriu 194/195 contas comparáveis de 2024 e não encontrou deterioração consistente de uso que explique o fenômeno geral.
- **Suporte:** a análise dos primeiros 90 dias após signup também não encontrou diferença consistente de volume, resposta, resolução, satisfação ou escalonamento capaz de explicar o fenômeno geral.

---

## Recomendações

As ações completas estão no [Plano de Ação](./diagnostic/IMPACTO_ESTIMADO_ACOES.md). As frentes centrais são:

- **Growth/Comercial:** abrir Organic em origens específicas e reconstruir o contexto de aquisição; investigar Organic × Enterprise sem assumir causalidade.
- **Comercial → CS:** tornar handoff, expectativa, escopo e primeiro valor parte obrigatória da jornada.
- **Finance/RevOps + Dados:** reconciliar eventos, refunds/créditos e movimentos de subscription até chegar ao desfecho econômico real.
- **Produto + Dados:** corrigir o vínculo conta → assinatura → uso e preservar sinais de adoção/erro sem tratá-los automaticamente como churn.
- **Suporte:** registrar etapa da jornada, motivo, solução, pendência, área acionada e próximo passo.
- **Gestão:** acompanhar responsáveis, decisões, aprendizados e resultados em cadência operacional.

---

## Limitações

- Os dados são **sintéticos**; os padrões encontrados descrevem este dataset, não clientes SaaS reais.
- A base não oferece uma definição canônica e reconciliada de churn econômico, MRR atual ou perda financeira por conta.
- Há inconsistências temporais relevantes em Produto e Suporte; elas foram investigadas e contornadas quando possível, mas não devem ser escondidas.
- Refund/crédito registrado não comprova perda líquida de receita.
- O MVP não possui SSO/RBAC e requer banco externo, como PostgreSQL, para persistência durável/compartilhada em produção no Streamlit.
- Sinais do aplicativo são triagem operacional; não são probabilidades de churn nem causalidade.

---

## Process Log — Como usei IA

O Process Log completo está disponível em:

- [PROCESS_LOG.pdf](./process-log/PROCESS_LOG.pdf) — versão principal para avaliação.
- [Process_Log.zip](./process-log/Process_Log.zip) — arquivos-fonte e imagens da documentação.

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| **ChatGPT / ChatGPT Work** | Principal ambiente de investigação, contraponto, análise, programação inicial, construção de relatórios e revisão final. |
| **Manus** | Reconstrução da versão mais recente do aplicativo, com foco em programação, UX, persistência e preparação para GitHub/Streamlit. |
| **Claude** | Segunda perspectiva para confrontar interpretações e resultados. |
| **Python** | Cálculos, cruzamentos, testes e reprodução analítica. |
| **Streamlit** | Construção e publicação da aplicação operacional. |
| **Notion** | Registro cronológico de prompts, prints, decisões, erros e aprendizados. |

### Workflow

1. Estruturei o contexto e as regras de investigação antes de entregar as bases à IA, para reduzir o risco de seguir o primeiro padrão encontrado.
2. Comecei pelo profiling das cinco bases e pela validação do que cada campo e relação realmente permitiam afirmar.
3. Rodei ciclos sucessivos de análise, critiquei resultados, refiz perguntas e voltei aos dados quando uma conclusão dependia de premissa não comprovada.
4. Reconcilei as diferentes representações de churn e passei a separar evento registrado de perda econômica confirmada.
5. Cruzei churn com aquisição, valor, subscriptions, Produto, Suporte e refunds; associações foram testadas antes de virar recomendação.
6. Consolidei o diagnóstico, a reprodução analítica e o plano de ação.
7. Transformei o diagnóstico em uma aplicação operacional, primeiro com ChatGPT/Work e depois com reconstrução no Manus, seguida de testes, revisão de UX, documentação, GitHub e deploy no Streamlit.

### Onde a IA errou e como corrigi

| Problema | Minha intervenção | O que mudou |
|---|---|---|
| A análise começou fragmentada por tabela e métrica. | Pedi uma leitura sistêmica do negócio. | Aquisição, receita, Produto, Suporte e churn passaram a ser analisados em conjunto. |
| churn_flag, churn_event e subscription encerrada apareciam como equivalentes. | Questionei o significado e cruzei as representações. | Churn deixou de ser premissa e virou parte do problema investigado. |
| A IA recomendava análises que ela mesma poderia executar. | Determinei que toda investigação possível fosse executada antes da recomendação. | Recomendações passaram a vir depois da evidência. |
| Associações começaram a ser narradas como causa. | Exigi separação entre fato, cálculo, associação, inferência e hipótese causal. | Produto, Suporte, canais e reason_code deixaram de receber causalidade não sustentada. |
| Refund apareceu inicialmente como perda econômica. | Pedi cruzamentos com subscriptions, temporalidade e continuidade paga. | Refund/crédito deixou de ser tratado automaticamente como receita ou cliente perdido. |
| Primeiras versões do relatório e do sistema geravam carga cognitiva alta. | Usei minha própria dificuldade de leitura e navegação como teste de UX. | A solução foi simplificada e reorganizada em torno de contexto, decisão e próxima ação. |

### O que eu adicionei que a IA sozinha não faria

Meu papel foi principalmente **questionar o enquadramento**, decidir quais perguntas tinham relevância de negócio, exigir contexto econômico, impedir que hipóteses virassem fatos e transformar análises em decisões executáveis. Também usei a experiência real de leitura e navegação para redefinir o produto quando a solução tecnicamente correta ainda estava cognitivamente pesada. A IA ampliou minha capacidade de investigar, calcular, programar e testar alternativas; o julgamento estratégico e a decisão sobre o que deveria ser investigado, descartado, priorizado ou transformado em sistema permaneceram humanos.

### Iterações

Ao final, fiz uma auditoria dos chats e identifiquei **53 ciclos relevantes**: aproximadamente **23 ligados à investigação e análise dos dados, 12 à construção dos relatórios e 18 ao produto, sistema e implementação**.

---

## Evidências

- [x] Screenshots das conversas, prompts e decisões no Process Log
- [x] Narrativa escrita do workflow e das intervenções humanas
- [x] Git history com a evolução da solução
- [x] Código, testes e instruções de reprodução
- [x] Aplicação publicada no Streamlit
- [ ] Screen recording
- [ ] Chat export integral

### Auditabilidade adicional

- cinco bases originais preservadas em [solution/data/raw/](./solution/data/raw/);
- scripts de transformação e reprodução em [solution/scripts/](./solution/scripts/);
- testes automatizados em [solution/tests/](./solution/tests/);
- documentação técnica e operacional em [solution/docs/](./solution/docs/);
- histórico de commits no branch **submission/tassiani-ventura**.

> Em caso de diferença de interpretação entre materiais, prevalece o **Relatório Final**, apoiado pela **Reprodução Completa da Investigação Analítica**.

---

_Submissão enviada em: 27/09/2026_
