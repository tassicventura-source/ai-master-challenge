# Plano de Ação — RavenStack Retention Intelligence

## Resumo estratégico — o que fazer

O plano deve acontecer em **três prioridades**, mas isso **não significa três fases sequenciais**. A RavenStack pode investigar o passado e corrigir a operação atual ao mesmo tempo. A prioridade indica principalmente **quando começar e quanto foco de gestão dedicar**.

### Prioridade 1 — Começar agora

| Área | Ações |
|---|---|
| **Growth** | 1. Abrir “Organic” em origens específicas. 2. Reconstruir a origem das contas Organic de 2024. 3. Passar a registrar origem detalhada em toda nova oportunidade. |
| **Comercial** | 1. Investigar as 22 contas Organic × Enterprise junto com CS. 2. Implantar registro mínimo de necessidade, expectativa, escopo e contexto da venda. 3. Tornar obrigatório o handoff Comercial → CS. |
| **CS** | 1. Comparar a jornada das 14 Organic × Enterprise com evento com as 8 sem evento. 2. Passar a registrar objetivo, primeiro valor, bloqueios e próximo passo das novas contas. |
| **Suporte** | 1. Investigar por que 1.077 tickets aparecem antes do signup. 2. Classificar novos tickets por etapa da jornada e motivo. 3. Registrar solução, pendência, área acionada e próximo passo. |
| **Financeiro / RevOps** | 1. Começar a classificação das 92 contas com evento precoce. 2. Separar refund, crédito e perda financeira efetiva. 3. Registrar valor antes/depois de todo novo movimento econômico relevante. |
| **Dados** | 1. Definir os conceitos mínimos de cliente ativo, churn, expansão, contração, reativação e refund. 2. Preservar as relações corretas entre conta, assinatura, evento e período nos novos registros. |
| **Gestão** | 1. Nomear responsáveis. 2. Fazer acompanhamento semanal curto. 3. Cobrar aprendizado e decisão, e não apenas execução de tarefas. |

**Resultado esperado da Prioridade 1:** parar de aumentar as ambiguidades já identificadas **enquanto** as principais perguntas do diagnóstico continuam sendo investigadas.

### Prioridade 2 — Estruturar nos próximos 30 dias

| Área | Ações |
|---|---|
| **Growth + Comercial** | Transformar origem, qualificação e contexto da venda em padrão operacional; investigar também Event e “Other” depois da abertura de Organic. |
| **Comercial + CS** | Padronizar handoff e acompanhar sua adesão; transformar diferenças encontradas nas 22 jornadas em testes ou mudanças de processo. |
| **CS** | Formalizar os marcos mínimos da jornada: entrada, onboarding, primeiro valor, bloqueio, risco e próximo passo. |
| **Suporte + Produto** | Usar a nova classificação dos tickets para identificar problemas recorrentes, etapas mais afetadas e temas que precisam chegar a Produto, Comercial ou CS. |
| **Produto + Dados** | Corrigir a interpretação temporal do uso e estabelecer como conta, assinatura, uso, funcionalidade e erro devem se relacionar. |
| **Financeiro / RevOps + Dados** | Concluir a reconciliação econômica prioritária e estruturar uma classificação única dos movimentos da conta. |
| **Gestão** | Acompanhar adesão aos novos registros e remover campos/processos que gerem trabalho sem melhorar decisão. |

**Resultado esperado da Prioridade 2:** transformar correções emergenciais em **processo repetível**, reduzindo dependência da memória das pessoas.

### Prioridade 3 — Consolidar nos próximos 60–90 dias

| Frente | Resultado desejado |
|---|---|
| **Jornada integrada** | Conseguir reconstruir aquisição → venda → onboarding → uso → suporte → renovação/expansão/saída. |
| **Revenue Truth** | Medir perda, expansão, contração e reativação com efeito econômico confirmado. |
| **Métricas de retenção** | Passar a acompanhar logo churn, revenue churn, GRR e NRR sobre definições confiáveis. |
| **Inteligência de aquisição** | Comparar canais não apenas por volume adquirido, mas por qualidade e valor que permanece. |
| **Inteligência operacional** | Usar tickets, uso, interações e movimentos financeiros como sinais conectados à jornada — não bases isoladas. |
| **Gestão** | Revisar periodicamente o que está gerando crescimento de qualidade, onde a jornada quebra e quais intervenções funcionam. |
| **Sistema** | Consolidar esse processo no Customer Journey desenvolvido ou nas ferramentas já utilizadas pela empresa. |

**Resultado esperado da Prioridade 3:** sair de uma operação que precisa reconstruir o passado para entender o cliente e chegar a uma operação que **produz essa inteligência enquanto a jornada acontece**.

> **Como ler o restante:** o resumo acima mostra quem precisa fazer o quê e quando. As seções seguintes explicam os dados, hipóteses e razões de negócio por trás de cada ação.

---

## Objetivo

A RavenStack não precisa esperar terminar todas as investigações para começar a operar melhor.

O diagnóstico encontrou dois tipos de problema:

**1. Existem perguntas importantes que ainda precisam ser respondidas.**  
Ex.: o que realmente aconteceu com as contas que possuem `churn_event`? Por que Organic cresceu tanto e, ao mesmo tempo, concentra determinados sinais de risco?

**2. A operação atual não registra informação suficiente para responder algumas dessas perguntas com segurança.**  
Continuar trabalhando da mesma forma significa produzir novos meses de dados que continuarão ambíguos.

Por isso, o plano deve acontecer em **três frentes simultâneas**:

> **Investigar o passado → corrigir o que já sabemos que está errado → melhorar o processo que produzirá os próximos dados.**

---

## 1. Aquisição e Comercial

### O que encontramos

Organic merece atenção não porque tenha sido provado como “causa de churn”, mas porque se tornou economicamente muito relevante.

De 2023 para 2024:

- contas Organic passaram de **43 para 71**;
- o valor inicial dessas contas passou de **US$ 70,7 mil para US$ 321,5 mil**;
- Organic respondeu por aproximadamente **64,6% do crescimento do valor inicial** observado.

O crescimento também mudou de composição. Enterprise + entradas mistas responderam por **25 das 28 novas contas líquidas Organic** e por aproximadamente **94% do aumento de valor** do canal.

Isso muda a pergunta de negócio. Não basta perguntar se “Organic churna mais”. É necessário entender **que tipo de cliente Organic está trazendo, por qual origem, com qual expectativa e o que acontece depois da venda.**

### O que fazer agora

**Growth deve abrir a categoria Organic.**

“Organic” é uma informação insuficiente para gerir aquisição. Para cada nova oportunidade, registrar pelo menos:

**origem específica → conteúdo/página/canal → campanha quando houver → data → oferta/interesse que originou o contato.**

**Comercial deve registrar o contexto da venda antes do handoff para CS.**

No mínimo:

**necessidade principal → objetivo esperado → plano contratado → tamanho/escopo → principais dúvidas ou objeções → promessa/expectativa relevante criada durante a venda → próximo passo combinado.**

Isso pode começar em CRM, formulário ou planilha. **Não depende da implantação do sistema desenvolvido no projeto.**

### Investigação paralela

Comparar as **22 contas Organic × Enterprise de 2024 com janela completa de 90 dias**:

- 14 possuem evento registrado em até 90 dias;
- 8 não possuem;
- juntas representam **US$ 161.986 de valor inicial**.

A comparação deve reconstruir aquisição → negociação → contratação → handoff → onboarding → primeiros sinais de valor → problemas → evento → situação posterior.

A finalidade não é provar que “Organic Enterprise é ruim”. É descobrir **o que diferencia as jornadas que seguem caminhos diferentes dentro do segmento que mais cresceu.**

---

## 2. Handoff Comercial → CS

### Problema

Hoje conseguimos observar o cliente nas bases, mas não reconstruir adequadamente **o que foi vendido e o que CS recebeu para entregar.**

Essa ausência é especialmente importante porque o crescimento de 2024 mudou a composição da carteira.

### Ação imediata

Criar um **handoff mínimo obrigatório** para toda nova conta.

Antes de Comercial considerar a venda entregue, CS deve receber:

**quem é o cliente → por que comprou → resultado que espera → plano/escopo contratado → usuários/seats → expectativa relevante criada → possíveis riscos percebidos → responsável do cliente → primeira ação acordada.**

Não é necessário escrever um relatório.

O objetivo é impedir que informação importante permaneça somente na memória do vendedor, em uma conversa, em uma mensagem ou simplesmente desapareça depois da assinatura.

### Como medir

Primeiro indicador:

> **% das novas contas que chegam ao CS com handoff completo.**

A meta inicial deveria ser operacional: **nenhuma nova conta sem contexto mínimo registrado.**

---

## 3. CS e onboarding

### O problema que precisamos evitar

Se a empresa registra apenas contratação e depois algum problema ou evento, perde justamente a parte mais importante da jornada:

> **o cliente conseguiu chegar ao valor que esperava?**

### Ação imediata

CS deve registrar alguns marcos simples para cada nova conta:

**handoff recebido → onboarding iniciado → principal objetivo confirmado → primeiro valor percebido/entregue → bloqueio relevante → próximo passo → responsável → data da próxima revisão.**

Não recomendo criar dezenas de campos.

O princípio é:

> **registrar aquilo que alguém precisará saber depois para entender por que aquela conta avançou, travou, expandiu ou saiu.**

### Hipótese que merece teste

Uma das perguntas para Organic × Enterprise é se as contas com evento precoce apresentam diferenças sistemáticas entre venda e início do relacionamento, velocidade de implantação, escopo contratado, quantidade de usuários, primeiro valor e problemas iniciais.

Os dados atuais fornecem pistas, mas não informação suficiente para afirmar o mecanismo.

---

## 4. Suporte — aqui existe uma oportunidade maior do que parecia

### O que os 2.000 tickets realmente mostram

A distribuição temporal é incomum:

| Momento do ticket | Tickets |
|---|---:|
| Antes do `signup_date` | **1.077** |
| Entre signup e primeira assinatura paga | **113** |
| Depois do início pago | **810** |

Portanto, **1.190 dos 2.000 tickets aparecem antes da primeira relação paga**.

Mais importante: os 1.077 anteriores ao próprio signup pertencem a **389 contas diferentes**.

Isso é grande demais para ser ignorado.

### O que podemos afirmar

Os tickets não representam exclusivamente suporte pós-venda.

### O que ainda não podemos afirmar

Não podemos chamar automaticamente esses 1.190 registros de “pré-venda”.

Uma hipótese inteligente é que o canal de atendimento esteja sendo usado também para dúvidas antes da compra, avaliação do produto, atendimento durante negociação, preparação para contratação ou outras interações anteriores à formalização.

Mas existe outra hipótese igualmente importante: **a relação temporal entre ticket e cadastro pode estar representando processos ou datas diferentes do que imaginamos.**

Isso precisa ser validado com quem conhece a operação.

### O que Suporte deve fazer agora

Não esperar essa investigação terminar.

Todo novo ticket deve ganhar **contexto de jornada**.

Um conjunto mínimo poderia ser:

**etapa da jornada:** pré-cadastro/lead; negociação; onboarding; cliente ativo; renovação; encerramento; pós-encerramento.

**motivo do contato:** dúvida comercial; configuração/onboarding; dificuldade de uso; erro técnico; cobrança; solicitação de funcionalidade; cancelamento/renovação; outro.

E registrar:

**problema → solução → pendência → área que precisa agir → próximo passo.**

### Por que isso importa

Hoje um ticket pode representar desde uma dúvida comercial até uma falha grave de produto.

Sem essa distinção, “quantidade de tickets” mistura comportamentos completamente diferentes.

Com a classificação, Suporte deixa de ser apenas uma área que **resolve chamados** e passa a gerar inteligência sobre a jornada.

---

## 5. Produto

### O cuidado necessário

Existem **25.000 registros de uso**, mas apenas **5.568** acontecem dentro da janela temporal da própria assinatura à qual estão vinculados.

Isso não torna os outros 19.432 registros inúteis.

Significa que não devemos usá-los automaticamente para afirmar coisas como:

> “baixo uso provoca churn”.

A relação temporal precisa ser entendida primeiro.

### Ação imediata

Produto e Dados devem definir o significado operacional de:

**conta → assinatura → usuário → sessão/uso → funcionalidade → erro → data.**

E novos registros precisam preservar essa relação.

### O que Produto deveria acompanhar

Em vez de apenas volume de uso:

**ativação → funcionalidades relevantes adotadas → erros encontrados → bloqueios recorrentes → evolução do uso → perda de uso → recuperação.**

### Nova oportunidade

Quando Suporte classificar corretamente os tickets, Produto passa a conseguir responder perguntas melhores:

- Quais funcionalidades geram mais dificuldade?
- Quais problemas técnicos impedem onboarding?
- Existem erros repetidos antes de uma conta reduzir uso?
- Algum problema aparece repetidamente em determinado plano ou perfil?

Hoje essa conexão é frágil. O processo futuro deve torná-la possível.

---

## 6. Financeiro e RevOps — definir o que realmente aconteceu com o dinheiro

Esta continua sendo uma frente crítica.

Existem diferentes sinais de encerramento que **não concordam entre si**.

Nas 500 contas, **400 apresentam divergência entre as diferentes representações de churn** utilizadas nas bases.

Além disso:

- existem **600 churn_events** envolvendo 352 contas;
- há assinaturas encerradas em 312 contas;
- apenas 110 contas têm `churn_flag=true` na base de contas.

Portanto:

> **um evento chamado churn não pode ser convertido automaticamente em cliente perdido ou receita perdida.**

### Ação imediata

Financeiro/RevOps deve criar uma classificação econômica única para movimentos da conta.

Quando ocorrer uma mudança relevante, registrar o que aconteceu:

**nova venda → expansão → contração → troca de plano → crédito → refund efetivamente realizado → pausa → encerramento → reativação → nenhuma perda econômica.**

E, quando houver alteração de receita:

**valor antes → valor depois → diferença → data efetiva.**

---

## 7. As 92 contas precisam ser investigadas — mas a empresa não precisa parar enquanto isso

O diagnóstico encontrou **92 contas da coorte comparável de 2024** com evento registrado em até 90 dias.

O valor inicial associado a elas é aproximadamente **US$ 273,8 mil**.

Isso é material.

Mas não significa US$ 273,8 mil perdidos.

### Ação

Financeiro/RevOps + Dados devem classificar as 92 contas uma a uma:

**o cliente realmente saiu? reduziu contrato? mudou plano? recebeu crédito? voltou? permaneceu pagando?**

Ao final, a RavenStack finalmente poderá separar:

**evento registrado** de **perda econômica confirmada**.

### Resultado esperado

A empresa deixa de administrar retenção por um proxy ambíguo e passa a saber quantos clientes realmente perdeu, quanto MRR perdeu, quanto expandiu, quanto contraiu, quanto recuperou e quanto permaneceu.

Só então métricas como **logo churn, revenue churn, GRR e NRR** passam a ter base confiável.

---

## 8. Refund/crédito precisa deixar de ser uma caixa-preta

Existem:

- **142 eventos com refund_amount > 0**;
- envolvendo **120 contas**;
- totalizando **US$ 8.652,25** registrados.

Isso não prova US$ 8.652,25 de receita perdida.

### Ação imediata

Financeiro deve classificar cada novo registro como:

**crédito concedido → refund solicitado → refund liquidado → ajuste financeiro → outro.**

E associá-lo ao motivo.

Isso permitirá responder futuramente:

> Estamos devolvendo dinheiro por falha de produto? erro comercial? cobrança? implantação? concessão de retenção?

Hoje o campo sozinho não responde.

---

## 9. Dados — criar um dicionário operacional, não apenas técnico

A RavenStack não precisa começar construindo uma grande arquitetura de dados.

Precisa primeiro fazer com que as áreas **falem a mesma língua**.

### Definições que precisam existir

Por exemplo:

**Cliente ativo:** qual condição torna uma conta ativa?

**Churn:** quando exatamente a empresa considera que perdeu um cliente?

**Expansão:** qual movimento entra nessa categoria?

**Contração:** o que diferencia redução de contrato de churn?

**Reativação:** quando começa uma nova relação ou continua a anterior?

**Refund:** evento financeiro ou apenas registro de solicitação?

**Primeiro valor:** qual evidência mostra que o cliente começou a receber o resultado esperado?

Cada definição precisa ter:

**significado → responsável → sistema/campo de origem → momento em que é registrada.**

Isso evita que Comercial, CS, Financeiro e Dados usem a mesma palavra para coisas diferentes.

---

## 10. O protocolo mínimo da jornada

Esta é a ação estrutural que conecta tudo.

A RavenStack precisa conseguir reconstruir a história de uma conta sem depender da memória de quem a atendeu.

Não significa documentar tudo.

Significa documentar **mudanças importantes da jornada**.

### Regra operacional

Sempre que acontecer algo que altere significativamente:

**expectativa → etapa da jornada → risco → próximo passo → relação comercial → valor econômico**

alguém precisa registrar.

Exemplos:

**Comercial:** “Cliente comprou Enterprise para resolver X. Principal expectativa: Y.”

**CS:** “Onboarding bloqueado porque falta Z. Responsável: Ana. Próxima ação: 15/01.”

**Suporte:** “Erro técnico impede utilização da funcionalidade X. Produto acionado.”

**Financeiro:** “Contrato caiu de US$ X para US$ Y a partir de determinada data.”

Isso é muito mais valioso do que simplesmente acumular registros.

---

## 11. Quem precisa fazer o quê

| Área | Mudança imediata |
|---|---|
| **Growth** | parar de registrar aquisição apenas como “Organic”; preservar a origem específica |
| **Comercial** | registrar necessidade, expectativa, escopo e contexto da venda |
| **Comercial → CS** | tornar handoff mínimo obrigatório |
| **CS** | registrar objetivo, primeiro valor, bloqueios, risco e próximo passo |
| **Suporte** | classificar ticket por etapa da jornada e motivo |
| **Produto** | conectar uso/erro à conta, assinatura e período correto |
| **Financeiro/RevOps** | registrar o efeito econômico real de cada movimento |
| **Dados** | manter definições, chaves e regras comuns entre áreas |
| **Gestão** | acompanhar adesão ao processo e cobrar decisão sobre os sinais produzidos |

---

## 12. Prioridade: o que começa primeiro

Eu não colocaria tudo em uma fila.

### Começar imediatamente — em paralelo

**Growth + Comercial:** abrir Organic e reconstruir a origem das contas.

**Comercial + CS:** analisar as 22 Organic × Enterprise e implantar handoff mínimo para novas vendas.

**Suporte:** validar o significado dos tickets anteriores ao signup e implantar a nova classificação para tickets novos.

**Financeiro + RevOps:** começar a classificação das 92 contas e estruturar os movimentos econômicos daqui para frente.

**Dados:** definir os primeiros conceitos canônicos e impedir que novos registros continuem aumentando a ambiguidade.

Essas ações podem acontecer simultaneamente porque possuem responsáveis diferentes.

---

## 13. PDCA — como impedir que o plano vire documento

### Plan

Cada área recebe:

**ação → responsável → prazo → indicador → hipótese quando existir.**

### Do

Começar pelos processos mínimos, sem esperar integração perfeita ou novo software.

Uma planilha estruturada é melhor do que continuar sem registro.

### Check

Gestão faz uma revisão semanal curta.

Não para perguntar apenas “fizeram?”.

Mas para responder:

**O que aprendemos? O que foi confirmado? O que foi refutado? Que risco apareceu? Que decisão precisa ser tomada?**

### Act

Se a prática funcionar, ela vira padrão.

Se gerar burocracia sem produzir informação ou decisão, é simplificada ou eliminada.

Se uma hipótese for refutada, a empresa não insiste nela.

---

## 14. Como o sistema desenvolvido entra nisso

O **RavenStack Customer Journey** não precisa ser adotado para que esse modelo funcione.

O valor principal do sistema é mostrar **como essas informações podem viver juntas**:

> conta → contexto → interação → sinal → decisão → responsável → próxima ação → resultado → impacto econômico.

Se a empresa utilizar CRM, ferramenta de suporte, billing e outros sistemas, o mesmo modelo pode ser implementado neles.

Portanto, a recomendação não é:

> “use o aplicativo”.

É:

> **adote o processo operacional; use o aplicativo como uma implementação possível desse processo.**

---

## Resultado esperado

O plano não busca apenas explicar por que clientes aparentemente churnaram no dataset.

Ele muda a capacidade da RavenStack de administrar a carteira.

No curto prazo, a empresa investiga **Organic, os 92 casos, tickets e refunds**.

Ao mesmo tempo, para de produzir parte das ambiguidades que tornaram essa investigação difícil.

E, progressivamente, passa a conseguir responder perguntas mais importantes:

- **Quem está gerando crescimento de qualidade?**
- **Onde clientes encontram fricção?**
- **Onde estamos prometendo algo que depois não conseguimos entregar?**
- **Quem está recebendo valor e quem está travando antes disso?**
- **Onde estamos perdendo receita — e quanto?**
- **Que intervenção funcionou?**

Esse é o ponto em que retenção deixa de ser apenas uma análise de churn e passa a ser **gestão da jornada e do valor do cliente**.

---

## Nota de mensuração

Alguns valores dimensionam materialidade, mas **não podem ser tratados como perda financeira confirmada**:

- **US$ 161.986** do grupo Organic × Enterprise não é receita em risco;
- **US$ 273,8 mil** das 92 contas não é MRR perdido;
- **US$ 8.652,25** de refund/crédito registrado não é automaticamente caixa perdido.

O impacto financeiro deverá ser calculado após a reconciliação econômica. Os cálculos centrais já possuem reprodução em `solution/scripts/reproduce_diagnostic.py`; a reprodução analítica completa deve registrar também hipóteses testadas, confirmadas, refutadas e inconclusivas.
