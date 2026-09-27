# Impacto e priorização das ações — RavenStack

Este documento transforma os achados do diagnóstico em uma sequência de decisão e execução. A ordem não é definida apenas pelo maior número observado: considera **impacto, urgência/risco, esforço e dependências**, usando a lógica da matriz de priorização localizada no material de gestão do projeto.

> **Importante:** a planilha original traz os campos Impacto, Urgência/Risco, Esforço, Dependências e Pontuação, mas não define escala nem fórmula de pontuação. Para não criar precisão artificial, esta versão aplica os quatro critérios de forma explícita e mantém a decisão justificável sem inventar um score numérico.

## 1. O que muda na priorização

A primeira versão colocava a reconciliação das 92 contas automaticamente como P0 por materialidade. A revisão muda essa lógica.

A frente **Organic** deve começar imediatamente em paralelo porque combina:
- 60,9% do crescimento líquido de contas em 2024;
- 64,6% do aumento do valor de entrada;
- crescimento fortemente concentrado em Enterprise e entradas mistas;
- sinais diferentes dentro do mesmo canal: Enterprise concentra crescimento; Basic/Pro concentram proporcionalmente mais refund/crédito precoce;
- uma população pequena o suficiente para investigação rápida e comparável.

Isso não significa que Organic "causa churn". Significa que é o motor de crescimento com maior retorno potencial de aprendizado no curto prazo.

## 2. Evidência que sustenta a frente Organic

### Organic cresceu em valor — não deve ser cortado por causa do churn_event

De 2023 para 2024:
- contas Organic: **43 → 71** (+28);
- valor de entrada: **US$ 70.748 → US$ 321.475** (+US$ 250.727);
- Organic respondeu por **64,6%** do crescimento total do valor de entrada.

### O crescimento não foi homogêneo

| Primeira entrada paga | Contas 2023 | Contas 2024 | Valor 2023 | Valor 2024 | Leitura |
|---|---:|---:|---:|---:|---|
| Basic | 14 | 12 | US$ 6.764 | US$ 5.871 | caiu em contas e valor |
| Pro | 18 | 23 | US$ 22.393 | US$ 37.583 | crescimento moderado |
| Enterprise | 11 | 33 | US$ 41.591 | US$ 217.507 | principal motor |
| Misto | 0 | 3 | US$ 0 | US$ 60.514 | novo e material |

Enterprise + Misto explicam **25 das 28 contas líquidas adicionais** de Organic e **94,3% do valor adicional**.

### Organic × Enterprise é a comparação de maior valor informacional

Entre as contas Organic × Enterprise de 2024 com 90 dias completos:
- **22 contas** comparáveis;
- **14** com evento em até 90 dias;
- **8** sem evento;
- **US$ 161.986** de valor inicial registrado no grupo.

Novos descritivos da revisão:
- mediana de valor inicial: **US$ 6.368** nas 14 com evento vs **US$ 8.258,50** nas 8 sem evento;
- mediana de seats: **32** vs **41,5**;
- mediana de tempo até primeira linha paga: **10,5 dias** vs **19 dias**;
- refund/crédito precoce: **4/14** nas contas com evento e **0/8** nas sem evento.

Essas diferenças são pistas para investigação, não causas demonstradas. Produto e suporte são esparsos e temporalmente problemáticos, portanto não devem receber causalidade a partir desses números.

### Organic × Basic aponta para outro problema

Na coorte comparável de 2024:
- **10 contas Organic × Basic**;
- **7** têm evento em até 90 dias;
- **5/10** têm refund/crédito precoce.

Em Pro, são **4/16**; em Enterprise, **4/22**.

Logo, a investigação não deve tratar "Organic" como um bloco único:
- **Enterprise:** qualidade e permanência do principal motor de crescimento;
- **Basic/Pro:** maior concentração relativa de refund/crédito precoce;
- **Misto:** materialidade alta, mas população ainda muito pequena.

## 3. Matriz de priorização por área

| Área / iniciativa | Resultado esperado | Impacto | Urgência / risco | Esforço | Dependências | Decisão |
|---|---|---|---|---|---|---|
| **Growth + Comercial — reconstruir origem de Organic** | separar conteúdo, página, campanha, oportunidade, vendedor e promessa comercial | Muito alto: canal responde por 64,6% do crescimento de valor | Alta: decisões de aquisição podem ser tomadas com categoria ampla demais | Baixo–médio | CRM/origem comercial | **Começar agora** |
| **Comercial + CS — comparar 22 jornadas Organic × Enterprise** | descobrir diferenças entre 14 contas com evento e 8 sem | Muito alto: US$ 161.986 de valor inicial no grupo e principal motor de crescimento | Alta | Médio | histórico de venda, handoff e onboarding | **Começar agora, em paralelo** |
| **Finance + RevOps — investigar refund/crédito em Organic Basic/Pro** | distinguir crédito, refund liquidado, concessão comercial e continuidade | Alto: sinal proporcionalmente concentrado e acionável | Alta | Baixo–médio | cobrança/pagamento | **Começar agora** |
| **Finance + RevOps + Dados — reconciliar as 92 contas dos 47,2%** | classificar desfecho econômico e calcular perda real | Muito alto: resolve a principal ambiguidade do diagnóstico | Muito alta | Alto | contrato, fatura, pagamento e MRR antes/depois | **Iniciar em paralelo; não esperar Organic terminar** |
| **Dados + RevOps — construir lifecycle econômico canônico** | tornar logo churn, revenue churn, GRR e NRR mensuráveis | Estrutural / muito alto | Alta | Alto | definição de eventos + integração de sistemas | **Projeto estrutural** |
| **Growth — abrir Event por campanha/origem** | explicar +8 contas com apenas +US$ 4.412 de valor e queda de mediana | Médio | Média | Baixo | metadados de campanha | **Quick win após abertura de Organic** |
| **Dados + Growth — eliminar “Other” como categoria residual** | recuperar origem útil para decisão | Médio | Média | Baixo | taxonomia de aquisição | **Quick win de dados** |

### Ordem operacional

Não existe uma fila única. Há três trilhas que devem andar em paralelo:

1. **Aprendizado rápido:** Organic — origem + 22 jornadas Enterprise + refund/crédito Basic/Pro.
2. **Verdade econômica:** reconciliação das 92 contas e dos refunds/créditos.
3. **Correção estrutural:** lifecycle canônico e granularidade permanente de aquisição.

## 4. 5W2H das ações imediatas

| What | Why | Who | When | Where | How | How much / métrica |
|---|---|---|---|---|---|---|
| Abrir Organic em origem real | Organic concentra crescimento, mas a categoria não explica mecanismo | Growth + Comercial | início imediato; primeira leitura em 5 dias úteis | CRM + fontes de aquisição | reconstruir conteúdo/página/campanha/oportunidade/vendedor e promessa | cobertura de origem das 71 contas Organic de 2024; % sem origem explicada |
| Comparar 22 jornadas Organic × Enterprise | é o principal motor de valor e há 14 casos com evento contra 8 controles naturais | Comercial + CS; Produto entra onde houver evidência | até 10 dias úteis | CRM + onboarding + interações + produto válido | roteiro único de comparação entre venda, handoff, primeiro valor, bloqueios, evento e continuidade | 22/22 jornadas reconstruídas; diferenças repetidas e verificáveis |
| Reconciliar refund/crédito Organic Basic/Pro | o sinal é proporcionalmente maior nesses grupos | Finance + RevOps | até 10 dias úteis | billing/financeiro | vincular evento a cobrança, pagamento, concessão e estado posterior | % dos casos classificados; valor financeiro confirmado |
| Reconciliar 92 eventos precoces de 2024 | 47,2% não é churn econômico demonstrado | Finance + RevOps + Dados | começar imediatamente; fechamento progressivo | contrato + billing + subscriptions | classificar perda, contração, expansão, pausa, troca, reativação, crédito/refund ou sem perda comprovada | 92/92 classificados; MRR antes/depois confirmado |

## 5. PDCA

### Plan
Executar as três trilhas acima com definições comuns de conta, evento, valor inicial e desfecho econômico. Registrar hipótese antes da investigação para evitar reinterpretar o resultado depois.

### Do
Rodar primeiro os grupos pequenos e informativos — 22 Organic × Enterprise e Organic Basic/Pro — enquanto Finance/RevOps inicia a reconciliação dos 92 casos.

### Check
Revisão semanal por área:
- Growth/Comercial: cobertura de origem e padrões de promessa/qualificação;
- CS: diferenças de onboarding, primeiro valor, bloqueios e continuidade;
- Produto: apenas evidências temporalmente válidas;
- Finance/RevOps: casos reconciliados, refund/crédito confirmado e MRR antes/depois;
- Dados: divergências ainda abertas e qualidade das chaves/eventos.

A pergunta de controle não é "o churn caiu?". Primeiro é: **a hipótese investigada foi confirmada, refutada ou continua inconclusiva?**

### Act
- hipótese confirmada → transformar em mudança operacional e acompanhar resultado;
- hipótese refutada → encerrar ou redirecionar a investigação;
- inconclusiva por dado ausente → corrigir captura/integração antes de ampliar a conclusão;
- padrão econômico confirmado → incorporar ao Revenue Truth e às métricas de retenção.

## 6. Como o aplicativo entra

O aplicativo é a camada de execução, não a fonte da verdade econômica. Ele deve registrar:
- conta e contexto;
- responsável e área;
- hipótese/achado;
- próxima ação e prazo;
- MRR antes/depois quando reconciliado;
- resultado da ação;
- evidência que confirmou ou refutou a hipótese.

Assim, diagnóstico → ação → acompanhamento → resultado passam a fazer parte da mesma trilha.

## 7. O que ainda não pode ser chamado de impacto financeiro

- **US$ 161.986** do grupo Organic × Enterprise não é receita em risco.
- **US$ 273.827** das 92 contas prioritárias não é MRR perdido.
- **US$ 8.652,25** de refund/crédito registrado não é automaticamente caixa perdido.

O impacto financeiro só deve ser calculado depois da reconciliação. Até lá, esses números dimensionam **materialidade e escopo de decisão**.

Os cálculos centrais são reproduzíveis em `solution/scripts/reproduce_diagnostic.py`; o inventário analítico completo será ampliado separadamente para registrar também hipóteses testadas e descartadas.
