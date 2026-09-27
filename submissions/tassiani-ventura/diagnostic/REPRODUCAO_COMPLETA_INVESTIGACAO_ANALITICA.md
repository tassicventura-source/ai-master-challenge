# Reprodução completa da investigação analítica — RavenStack

## Finalidade

Este documento registra **como o diagnóstico foi construído, testado, refutado e transformado em decisão**. Ele não substitui o relatório executivo. Sua função é permitir que outra pessoa refaça o raciocínio a partir das cinco bases originais e entenda por que algumas interpretações foram mantidas e outras foram descartadas.

A investigação usa dados sintéticos com corte em **31/12/2024**. Portanto, os padrões descritos valem para este dataset e não devem ser generalizados automaticamente para empresas SaaS reais.

### Fontes primárias

| Base | Linhas | Grão |
|---|---:|---|
| accounts | 500 | uma conta |
| subscriptions | 5.000 | uma linha de assinatura |
| feature_usage | 25.000 | um registro de uso |
| support_tickets | 2.000 | um ticket |
| churn_events | 600 | um evento registrado como churn |

O README foi usado como documentação, mas **não como verdade superior aos dados**. Quando documentação e dados divergem, a divergência é registrada como achado.

---

# 1. Antes de procurar a causa: validar o que os dados representam

## Pergunta

As cinco bases podem ser cruzadas diretamente e os campos significam o que seus nomes sugerem?

## Teste

Foram validados volume, chaves, relacionamentos, cardinalidade e temporalidade antes de interpretar churn.

## Resultado

As relações entre tabelas não possuem registros órfãos: subscriptions, tickets e churn_events apontam para contas existentes; feature_usage aponta para subscriptions existentes.

Entretanto, a documentação afirma que os IDs são chaves primárias únicas e que os intervalos temporais foram validados. Os dados mostram duas divergências importantes:

- **21 valores de usage_id estão duplicados**, representando 42 linhas distintas; não são duplicatas exatas.
- **19.142 dos 25.000 registros de uso acontecem antes do início da assinatura à qual estão ligados**.
- Outros 290 registros de uso ficam depois do encerramento da assinatura.
- Apenas **5.568 registros de uso** estão dentro da janela temporal da própria assinatura.
- Entre os 19.142 registros anteriores à assinatura vinculada, **4.689 acontecem durante outra assinatura paga da mesma conta**. Isso mostra que parte do problema está na associação do uso à linha de assinatura, e não necessariamente no uso em si.
- Em Suporte, **1.077 dos 2.000 tickets aparecem antes do signup_date da conta**.

## Interpretação

A integridade referencial existe, mas **integridade referencial não significa coerência temporal ou semântica**.

## Decisão

Uso e Suporte não seriam descartados. A decisão foi separar duas perguntas: **a linha de assinatura vinculada é temporalmente confiável?** e **a atividade da conta ainda pode ser analisada por outra referência temporal?**. Por isso, além da validação da subscription_id, Produto e Suporte foram reanalisados no nível da conta e da jornada, usando o signup como referência alternativa quando a pergunta permitia. Qualquer interpretação dos tickets anteriores ao cadastro permaneceu como hipótese.

**Status:** documentação parcialmente refutada pelos próprios dados.

---

# 2. O primeiro sinal: 19,4% → 47,2%

## Pergunta

Os registros de churn realmente ficaram muito mais frequentes em 2024?

## Definição

Para evitar comparar contas com tempos de observação diferentes:

- evento precoce = primeiro churn_event entre 0 e 90 dias após signup;
- entram no denominador apenas contas com pelo menos 90 dias completos até 31/12/2024.

## Resultado

| Coorte | Contas comparáveis | Primeiro evento ≤90 dias | Taxa |
|---|---:|---:|---:|
| 2023 | 227 | 44 | **19,4%** |
| 2024 | 195 | 92 | **47,2%** |

O aumento do **evento registrado** é real no dataset.

## O que isso permite afirmar

Em 2024, churn_events passaram a aparecer muito mais cedo na jornada registrada.

## O que não permite afirmar

Não permite dizer que 47,2% dos clientes foram perdidos nem que 47,2% da receita churnou.

Essa distinção abriu a investigação seguinte.

---

# 3. O churn_event representa saída real?

## Hipótese inicial

Se churn_event representa saída, o evento deveria normalmente ocorrer quando a relação paga termina e deveria ser seguido por ausência de continuidade paga.

## Testes

Os 600 eventos foram posicionados em relação às linhas pagas.

## Resultado

| Contexto do churn_event | Eventos |
|---|---:|
| Enquanto existe linha paga vigente | **531** |
| Antes da primeira linha paga | **67** |
| Entre relações pagas | **2** |
| Total | **600** |

Os dois eventos que aparecem entre relações pagas pertencem a contas que voltam a ter linha paga depois.

A própria tabela de eventos contém sinais de que o nome "churn" agrega movimentos diferentes:

- **61 dos 600 eventos** estão marcados como reativação;
- **123** possuem upgrade precedente;
- **53** possuem downgrade precedente.

Também foram examinadas as linhas pagas encerradas:

- **408 linhas pagas** têm end_date;
- **399** possuem outra linha paga vigente na mesma data;
- nas **9 restantes**, uma nova linha paga começa entre **3 e 157 dias depois**;
- a soma do MRR das 408 linhas encerradas é **US$ 1.179.139**;
- no corte de 31/12/2024, **todas as 500 contas possuem pelo menos uma linha paga ativa**.

Isso não prova ausência de perda econômica ao longo da jornada. Prova que encerramento de linha e churn_event não podem ser convertidos automaticamente em perda definitiva da conta.

## Teste adicional: três representações de churn

Foram comparados:

1. accounts.churn_flag;
2. existência de churn_event;
3. existência de subscription encerrada.

Resultados:

- 352 contas possuem pelo menos um churn_event;
- 312 contas possuem alguma subscription encerrada;
- 110 contas possuem accounts.churn_flag = true;
- **400 das 500 contas** não recebem a mesma classificação nas três representações.

## Interpretação

O campo chamado churn está registrando **movimentos do ciclo de vida**, não uma definição econômica única de perda.

Somar o MRR das linhas encerradas e chamá-lo de receita perdida produziria uma conclusão incorreta.

## Decisão

O projeto deixou de perguntar apenas “por que os clientes churnam?” e passou a perguntar primeiro:

> **Quais eventos representam perda real de cliente ou de receita?**

**Status da hipótese “churn_event = cliente perdido”: refutada.**

---

# 4. O que acontece depois do evento?

## Pergunta

Mesmo que o evento aconteça durante uma linha paga, a conta sai logo depois?

## Teste

Nas 92 contas comparáveis de 2024 com evento precoce, foi observada a continuidade posterior.

## Resultado

Das contas com 90 dias completos disponíveis depois do evento:

- **67 de 68** ainda tinham uma linha paga ativa no dia +90.

Além disso:

- **89 das 92 contas** com evento precoce apresentam uso temporalmente válido depois do evento.

## Interpretação

O comportamento posterior é incompatível com tratar automaticamente o evento como encerramento definitivo da relação.

## Decisão

O relatório passou a chamar 47,2% de **incidência de evento registrado**, e não de churn econômico.

**Status:** evidência adicional contra a equivalência entre churn_event e perda definitiva.

---

# 5. Quanto do salto para 47,2% pode ser efeito da janela do dataset?

## Problema

O dataset termina em 31/12/2024. Contas abertas em 2024 possuem menos tempo total de observação. Isso pode alterar onde o primeiro evento aparece em relação ao cadastro.

## Teste de sensibilidade

O teste não “corrige” os dados.

Procedimento:

1. medir em 2023 a incidência de contas que tiveram algum evento observado;
2. entre as contas de 2023 com evento, normalizar o tempo até o evento pela janela total disponível;
3. aplicar essa distribuição temporal às janelas disponíveis das contas elegíveis de 2024;
4. calcular qual parcela projetada cairia nos primeiros 90 dias;
5. multiplicar pela incidência de algum evento observada em 2023.

## Resultado reproduzido

- incidência de algum evento em 2023: **71,81%**;
- parcela projetada em ≤90 dias, condicionada a evento: **59,72%**;
- taxa projetada para 2024: **42,8849%**, aproximadamente **42,9%**.

Testes complementares:

- Mann–Whitney para tempo normalizado até o evento entre 2023 e 2024: **p ≈ 0,404**;
- associação entre janela disponível e tempo absoluto até o evento: **Spearman ρ ≈ 0,645**.

## Interpretação

Os 47,2% observados continuam sendo um fato. Porém, o teste mostra que **grande parte do salto de 19,4% para 47,2% pode ser reproduzida pela estrutura temporal do dataset**.

## Decisão

Não atribuir todo o aumento a deterioração de retenção.

**Status da hipótese “o salto prova piora equivalente do negócio”: refutada.**

---

# 6. Crescimento: volume e valor contam a mesma história?

## Pergunta

Enquanto os eventos aumentavam, o negócio estava encolhendo ou crescendo?

## Métrica

Foi criada a régua **valor de entrada**:

> soma do MRR das linhas pagas iniciadas na primeira data em que a conta aparece paga.

Ela serve para comparar aquisição. **Não é MRR atual, receita reconhecida nem receita perdida.**

## Resultado geral

| Ano | Novos cadastros | Valor de entrada |
|---|---:|---:|
| 2023 | 227 | US$ 503.575 |
| 2024 | 273 | US$ 891.676 |

Variação:

- cadastros: **+20,3%**;
- valor de entrada: **+77,1%**;
- aumento absoluto de valor: **US$ 388.101**.

## Interpretação

2024 não é apenas um ano de “mais churn_event”. É também um ano de crescimento muito mais forte em valor.

Isso levou a uma nova pergunta:

> **de onde veio esse crescimento e qual é a qualidade de sua composição?**

---

# 7. Aquisição: onde o crescimento realmente aconteceu?

## Resultado por canal

| Canal | Contas 2023 → 2024 | Valor de entrada 2023 → 2024 | Leitura |
|---|---|---|---|
| Organic | 43 → 71 | US$ 70.748 → US$ 321.475 | principal motor de volume e valor |
| Event | 44 → 52 | US$ 112.955 → US$ 117.367 | ganhou volume, quase não ganhou valor |
| Partner | 45 → 44 | US$ 99.617 → US$ 132.651 | volume estável, valor maior |
| Ads | 48 → 50 | US$ 144.778 → US$ 181.446 | pouco volume adicional, valor maior |
| Other | 47 → 56 | US$ 75.477 → US$ 138.737 | crescimento material escondido em categoria ampla |

Organic adicionou:

- **28 contas**, 60,9% do crescimento líquido da base;
- **US$ 250.727** de valor de entrada;
- **64,6%** de todo o aumento de valor.

Event adicionou 8 contas, mas somente **US$ 4.412** de valor; a mediana de entrada caiu de US$ 1.200 para US$ 882.

## Interpretação

Avaliar aquisição somente por número de clientes esconderia diferenças importantes de qualidade econômica.

## Decisão

Organic deveria ser investigado e protegido, não cortado por associação simples com churn_event. Event e Other também deveriam ganhar granularidade.

**Status da hipótese “mais contas = melhor crescimento”: refutada como regra suficiente.**

---

# 8. O que existe dentro de Organic?

## Pergunta

Organic cresceu de forma homogênea?

## Resultado

| Primeira entrada paga | Contas 2023 | Contas 2024 | Valor 2023 | Valor 2024 |
|---|---:|---:|---:|---:|
| Basic | 14 | 12 | US$ 6.764 | US$ 5.871 |
| Pro | 18 | 23 | US$ 22.393 | US$ 37.583 |
| Enterprise | 11 | 33 | US$ 41.591 | US$ 217.507 |
| Misto | 0 | 3 | US$ 0 | US$ 60.514 |

Enterprise + Misto explicam:

- **25 das 28 contas líquidas adicionais** de Organic;
- **US$ 236.430 dos US$ 250.727 adicionais**, ou **94,3%** do novo valor.

## Interpretação

“Organic” não é uma causa nem um segmento homogêneo. O crescimento mudou de composição.

## Decisão

Separar pelo menos:

- Organic × Enterprise: qualidade do principal motor de crescimento;
- Organic × Basic/Pro: investigar sinais de refund/crédito;
- Misto: acompanhar materialidade, reconhecendo a amostra pequena.

---

# 9. Organic × Enterprise: comparação de maior valor informacional

## Pergunta

Dentro do principal motor de crescimento, o que diferencia contas com e sem evento precoce?

## População comparável

Contas de 2024:

- origem Organic;
- primeira entrada paga Enterprise;
- pelo menos 90 dias completos de observação.

Resultado:

- **22 contas**;
- **14** com evento precoce;
- **8** sem evento;
- **US$ 161.986** de valor de entrada no grupo.

Contas com evento:
A-0a282f, A-592832, A-526d93, A-117171, A-71615e, A-1619f8, A-b9eed8, A-0cc442, A-0baac2, A-09316c, A-50bb9f, A-751c58, A-bb1eaa, A-781cc0.

Contas sem evento:
A-30b4ca, A-6f8ad2, A-faa28c, A-adc1f3, A-4ef964, A-fd9422, A-560d27, A-940b8b.

## Pistas adicionais

Usando as linhas da primeira entrada paga:

- mediana de valor inicial: **US$ 6.368** com evento vs **US$ 8.258,50** sem evento;
- mediana de seats na entrada: **32** vs **41,5**;
- mediana entre signup e primeira linha paga: **10,5 dias** vs **19 dias**;
- refund/crédito precoce: **4/14** vs **0/8**.

## Interpretação

São **pistas**, não mecanismos demonstrados. Por exemplo, fechar mais rápido não pode ser chamado de causa do evento apenas porque a mediana é menor.

## Decisão

Reconstruir as 22 jornadas, comparando aquisição, promessa, venda, handoff, onboarding, primeiro valor, bloqueios, suporte, produto e continuidade econômica.

**Status causal: inconclusivo; grupo priorizado por valor + comparabilidade + potencial de aprendizado.**

---

# 10. Refund/crédito: perda financeira ou outro movimento?

## Pergunta

Refund_amount_usd mede dinheiro definitivamente perdido?

## Resultado

- **142 eventos** possuem refund_amount_usd > 0;
- pertencem a **120 contas**;
- total registrado: **US$ 8.652,25**;
- 13 ocorrem antes da primeira linha paga;
- 129 ocorrem enquanto existe linha paga vigente.

Entre os 81 eventos de refund/crédito com 90 dias completos depois:

- **81/81** ainda possuem linha paga ativa no dia +90;
- **64/81** iniciam nova linha paga nesse intervalo.

Frequência de refund/crédito precoce:

| Coorte | Contas |
|---|---:|
| 2023 | 6/227 = **2,6%** |
| 2024 | 31/195 = **15,9%** |

Na coorte comparável de 2024:

- Organic: **13/48 = 27,1%**;
- fora de Organic: **18/147 = 12,2%**.

Dentro de Organic:

- Basic: **5/10**;
- Pro: **4/16**;
- Enterprise: **4/22**.

## Interpretação

O mecanismo ficou mais frequente, mas o campo não está ligado a uma fatura/transação e a documentação admite refund ou credit.

## Decisão

Financeiro/RevOps deve reconciliar crédito, refund solicitado, refund liquidado, ajuste e continuidade econômica.

**Status da hipótese “US$ 8.652,25 = receita perdida”: não sustentada.**

---

# 11. Produto explica o fenômeno?

## Hipótese

Problemas de uso, erros ou baixa adoção poderiam explicar os eventos.

## Primeiro teste: qualidade do vínculo com assinatura

Dos 25.000 registros:

- **19.142** precedem o início da subscription associada;
- **5.568** ficam dentro da janela da subscription;
- **290** ficam depois do fim;
- **4.689 dos 19.142 registros anteriores** coincidem com outra assinatura paga da mesma conta;
- existem **21 identificadores de uso repetidos**, envolvendo 42 das 25.000 linhas (0,17%). Isso não altera os principais resultados, mas confirma uma falha de chave que precisa ser corrigida.

A conclusão correta não é "19.432 registros são inúteis". É que a **subscription_id não é uma âncora temporal confiável para toda a base**.

## Segundo teste: recuperar a análise no nível da conta

Como cada subscription aponta para uma conta existente, o uso foi reanalisado pela jornada da conta, sem exigir que a data estivesse dentro da linha de assinatura originalmente vinculada.

Para as 195 contas comparáveis de 2024, foi observado o uso nos **primeiros 90 dias após o signup**:

- **2.940 registros de uso** entram nessa janela;
- **194 das 195 contas** possuem pelo menos um registro;
- mediana de registros: **6 com evento vs 6 sem evento**;
- mediana de usage_count acumulado: **61 vs 60**;
- duração acumulada mediana: **17.755 vs 18.258 segundos**;
- funcionalidades distintas: **6 vs 6**;
- dias distintos de uso: **6 vs 6**;
- erros acumulados: **3 vs 4**.

## Interpretação

A inconsistência da subscription_id não impediu toda análise de Produto. A abordagem alternativa recuperou cobertura quase completa da coorte comparável e **não mostrou uma deterioração consistente de adoção, intensidade, variedade ou frequência de uso nas contas com evento precoce**.

Isso não prova que Produto nunca cause perda em contas específicas. Mostra apenas que, neste dataset, os indicadores disponíveis não sustentam Produto como explicação geral do aumento de eventos.

## Decisão

- não descartar a base de uso;
- corrigir a relação conta → assinatura → uso para análises futuras;
- manter Produto como sinal operacional e hipótese por conta;
- não transformar uso em causa geral nem treinar modelo de churn enquanto o desfecho econômico continuar ambíguo.

**Status: hipótese geral não confirmada; análise recuperada por uma referência temporal alternativa.**

---

# 12. Suporte explica o fenômeno?

## Hipótese

Volume, lentidão, escalonamento ou satisfação de suporte poderiam anteceder os eventos.

## Primeiro teste: entender a temporalidade

Dos 2.000 tickets:

| Momento | Tickets |
|---|---:|
| Antes do signup | **1.077** |
| Entre signup e primeira linha paga | **113** |
| A partir da primeira linha paga | **810** |

Outros fatos:

- 492 contas possuem tickets;
- os 1.077 tickets anteriores ao signup atingem 389 contas;
- 825 tickets não possuem satisfaction_score.

Isso impede chamar automaticamente os tickets anteriores ao cadastro de "pré-venda". Eles podem refletir atendimento anterior à formalização, backfill, outro significado de signup_date ou problema de data. A base não distingue essas explicações.

## Segundo teste: suporte nos primeiros 90 dias após signup

Para evitar depender dos tickets anteriores ao cadastro, a coorte comparável de 2024 foi reanalisada usando somente tickets entre signup e signup + 90 dias.

Resultado:

- **89 tickets**, distribuídos por **75 das 195 contas**;
- mediana de tickets por conta: **0 com evento vs 0 sem evento**;
- entre contas com ticket, resolução mediana: **36h vs 34,5h**;
- primeira resposta mediana: **67 min vs 93 min**;
- satisfação mediana: **4 vs 4**;
- mediana de escalonamento: **0 vs 0**.

## Interpretação

Não aparece um padrão consistente em que contas com evento precoce recebam sistematicamente mais tickets, atendimento mais lento, pior satisfação ou mais escalonamentos.

A descoberta material de Suporte é dupla: **não há evidência para tratá-lo como causa geral** e **a base mistura momentos da jornada que hoje não conseguimos interpretar com segurança**.

## Decisão

Para o histórico, validar a semântica temporal antes de classificar os 1.077 tickets. Para novos tickets, registrar etapa da jornada, motivo, solução, pendência, área acionada e próximo passo.

**Status causal: hipótese geral não confirmada; problema de captura/semântica confirmado.**

---

# 13. Os reason_codes explicam saída?

## Hipótese

pricing, competitor, features, support ou budget poderiam ser tratados como causas diretas de perda.

## Teste

Entre eventos com 90 dias completos de acompanhamento, foi medida a existência de nova linha paga em até 90 dias.

| Motivo | Eventos com 90d | Nova linha paga ≤90d |
|---|---:|---:|
| pricing | 58 | **87,9%** |
| competitor | 61 | **83,6%** |
| features | 61 | **83,6%** |
| support | 63 | **81,0%** |
| budget | 57 | **80,7%** |
| unknown | 52 | **76,9%** |

## Interpretação

Os motivos podem explicar fricções ou perdas específicas, mas não se comportam como rótulos confiáveis de encerramento definitivo.

## Decisão

Não ranquear reason_code como “causa raiz de churn econômico” antes da reconciliação do desfecho.

**Status da hipótese geral: não confirmada.**

---

# 14. O que foi deliberadamente descartado

A investigação produziu decisões negativas tão importantes quanto os achados positivos.

Não foram aceitas as seguintes conclusões:

1. **47,2% = taxa real de clientes perdidos.**  
   Refutada pela continuidade paga, conflito entre representações e efeito de janela.

2. **US$ 1.179.139 de MRR encerrado = receita perdida.**  
   Refutada pela sobreposição e continuidade das linhas pagas.

3. **Organic deve receber menos investimento porque concentra eventos.**  
   Não sustentada: Organic é o principal motor de crescimento em valor e precisa ser aberto em suborigens/jornadas.

4. **Produto ou Suporte são a causa geral.**  
   Não demonstrado. As análises alternativas nos primeiros 90 dias após signup recuperaram Produto e Suporte sem depender das relações temporais problemáticas e não mostraram deterioração consistente nas contas com evento precoce.

5. **Reason_code pode ser usado diretamente como causa raiz de perda.**  
   Não sustentado pela continuidade posterior.

6. **Refund_amount_usd = churn de receita.**  
   Não demonstrado sem cobrança, pagamento e estado econômico posterior.

7. **Treinar imediatamente um modelo preditivo de churn.**  
   Rejeitado: o alvo ainda não representa um desfecho econômico canônico. Um modelo poderia aprender a prever inconsistências do processo em vez de perda real.

---

# 15. Como a investigação virou decisão

A conclusão central não foi “descobrimos a causa única do churn”.

Foi:

> **Com as cinco bases atuais, a causa comercial do churn econômico não é identificável com segurança porque o próprio desfecho econômico não está reconciliado.**

Isso gerou três frentes simultâneas:

### Investigar o passado
- reconciliar as 92 contas por trás dos 47,2%;
- reconstruir 22 jornadas Organic × Enterprise;
- abrir refund/crédito;
- validar tickets e granularidade de aquisição.

### Corrigir o presente
- parar de registrar aquisição apenas em categorias amplas;
- criar handoff Comercial → CS;
- classificar tickets por etapa/motivo;
- registrar movimentos econômicos com valor antes/depois;
- definir conceitos comuns de churn, expansão, contração, reativação e refund.

### Construir o futuro
- produzir uma jornada reconstruível enquanto ela acontece;
- conectar aquisição → venda → onboarding → uso → suporte → movimento econômico;
- medir depois logo churn, revenue churn, GRR e NRR sobre uma verdade econômica reconciliada.

O detalhamento operacional está em **IMPACTO_ESTIMADO_ACOES.md**.

---

# 16. Rastreabilidade entre achado e entrega

| Achado | Evidência principal | Decisão gerada | Entrega |
|---|---|---|---|
| 19,4% → 47,2% de eventos precoces | accounts + churn_events | investigar sem chamar de churn econômico | Relatório Final |
| 42,9% no teste de sensibilidade | accounts + churn_events + cutoff | não atribuir todo o salto a piora | Relatório Final + script |
| 531 eventos durante linha paga; 61 reativações; 123 upgrades; 53 downgrades precedentes | churn_events + subscriptions | separar evento de perda | Relatório Final |
| 500/500 contas com linha paga ativa no corte | subscriptions | não tratar encerramento de linha como perda definitiva | Relatório + Plano |
| 2.940 usos nos primeiros 90d; cobertura 194/195 | usage + accounts + subscriptions | Produto não explica o fenômeno geral; preservar e corrigir vínculo temporal | Relatório + Reprodução |
| 89 tickets em 75/195 contas nos primeiros 90d | support + accounts | Suporte não explica o fenômeno geral; corrigir contexto de jornada | Relatório + Plano |
| 400/500 contas em desacordo | três representações de churn | Revenue Truth | Relatório + Plano de Ação |
| Organic = 64,6% do novo valor | accounts + subscriptions | proteger e abrir canal | Relatório + Plano |
| 14/22 Organic × Enterprise | aquisição + assinatura + evento | reconstruir jornadas | Relatório + Plano |
| Refund/crédito 2,6% → 15,9% | churn_events + coortes | reconciliar mecanismo financeiro | Relatório + Plano |
| 5.568/25.000 usos temporalmente válidos | usage + subscriptions | não inferir causalidade geral | Relatório |
| 1.077/2.000 tickets antes do signup | tickets + accounts | corrigir captura e investigar significado | Plano de Ação |
| 21 usage_id duplicados | feature_usage | reforçar controle de qualidade | esta reprodução |

---

# 17. Cinco testes finais de validação antes da publicação

Antes de este documento ser incluído no repositório, a reprodução foi executada novamente diretamente sobre os cinco CSVs originais.

## Teste 1 — Integridade estrutural e chaves: PASS

Validado:

- volumes 500 / 5.000 / 25.000 / 2.000 / 600;
- ausência de FKs órfãs;
- unicidade das chaves principais de accounts, subscriptions, tickets e churn_events;
- divergência documentada: 21 usage_id duplicados.

## Teste 2 — Reprodução dos números executivos: PASS

Recalculados:

- 227 → 273 cadastros;
- US$ 503.575 → US$ 891.676 de valor de entrada;
- 44/227 = 19,4%;
- 92/195 = 47,2%;
- sensibilidade = **42,8849%**.

## Teste 3 — Reconciliação semântica de churn: PASS

Recalculados:

- 531 / 67 / 2 contextos dos 600 eventos;
- 408 linhas pagas encerradas;
- 399 com outra linha paga vigente;
- 400/500 contas com desacordo entre representações.

## Teste 4 — Validade temporal de Uso e Suporte: PASS

Recalculados:

- 19.142 usos antes da assinatura;
- 5.568 usos dentro da janela;
- 1.077 tickets antes do signup;
- 113 entre signup e primeira linha paga;
- 810 a partir da primeira linha paga.

## Teste 5 — Segmentos, refunds e estatística: PASS

Recalculados:

- 22 Organic × Enterprise comparáveis, 14 com evento;
- US$ 161.986 de valor de entrada no grupo;
- 142 eventos de refund/crédito, 120 contas, US$ 8.652,25;
- refund precoce 6/227 → 31/195;
- Mann–Whitney p≈0,404;
- Spearman ρ≈0,645.

**Resultado final: 5/5 testes aprovados.**

---

# 18. Como reproduzir

O script principal está em:

`solution/scripts/reproduce_diagnostic.py`

Execução a partir de `submissions/tassiani-ventura/solution`:

```bash
python scripts/reproduce_diagnostic.py
```

O script usa apenas as cinco bases originais em `data/raw`, sem corrigir ou imputar registros.

## Regra de interpretação

A reprodução confirma **cálculos e relações presentes no dataset**. Ela não transforma associação em causalidade e não resolve campos cujo significado de negócio não está disponível nas bases.

Quando um resultado depende de informação inexistente — por exemplo, fatura efetivamente liquidada, promessa comercial, categoria real do ticket ou motivo operacional do movimento — o documento encerra a análise como **inconclusiva** e registra o dado necessário para avançar.

---

## Conclusão auditável

A investigação começou procurando uma causa de churn e terminou mostrando que a primeira decisão correta era **não confundir movimentação registrada com perda econômica**.

A partir daí, o problema ficou mais amplo e mais útil para o negócio:

- 2024 cresceu em volume e, principalmente, em valor;
- esse crescimento mudou de composição e se concentrou fortemente em Organic/Enterprise;
- churn_event, encerramento de linha e churn_flag não formam uma única verdade;
- refunds, Produto, Suporte e reason_codes fornecem sinais, mas não uma causa geral comprovada;
- a maior oportunidade é combinar **reconciliação do passado com melhoria imediata da captura da jornada futura**.

Esse encadeamento — inclusive as hipóteses refutadas — é o que sustenta o Relatório Final, o Plano de Ação e o desenho do RavenStack Customer Journey.
