# RavenStack — Briefing executivo para o CEO

## Resumo executivo

O painel enviado tem uma base funcional forte e apresenta melhor organização da rotina em algumas áreas. A versão reestruturada preserva esses pontos e corrige o principal problema: a **Visão do cliente** não deve exigir interpretação técnica para que alguém saiba o que fazer.

A proposta do RavenStack é ser um sistema operacional de relacionamento com o cliente, não apenas um conjunto de relatórios.

> O diferencial não é mostrar mais dados. É transformar dados em decisão, ação, responsável e acompanhamento.

## O que foi aproveitado do painel enviado

| Melhoria observada | Como foi incorporada |
|---|---|
| Navegação orientada à rotina | Grupos como Rotina da equipe, Consulta histórica e Análises por equipe |
| Separação entre operação atual e material técnico | Jornada e Dados/Arquitetura ficam fora do menu principal |
| Linguagem mais direta | Minha fila, Ficha do cliente, Vendas e oportunidades e Acompanhamento da equipe |
| Melhor tratamento de sinais históricos | Sinais são apresentados como evidência para revisão, não como churn automático |
| Priorização por área | Growth/Comercial, Produto, Suporte/CS e Financeiro/RevOps mantêm suas análises específicas |

## Por que a Visão do cliente foi reestruturada

A versão anterior misturava quatro conceitos diferentes:

1. saúde e risco;
2. situação do relacionamento;
3. qualidade dos dados;
4. histórico técnico.

Isso fazia um usuário interpretar “Dados” como saúde da conta ou confundir “situação da conta” com etapa de venda.

A nova ficha separa explicitamente:

- **Saúde e risco:** exige atenção ou está normal?
- **Situação da conta:** implantação, ativa, pausada ou encerrada.
- **Confiança dos dados:** o quanto foi confirmado.
- **Próxima ação:** o que precisa ser feito, por quem e até quando.

Essa separação reduz erro de interpretação e diminui o tempo para decidir.

## Por que este sistema é melhor que um painel somente analítico

### 1. Um painel explica o passado; o RavenStack também conduz o próximo passo

Relatórios são úteis para entender tendências, origens e eventos. Porém, um relatório normalmente termina na observação:

> “Esta conta teve um sinal de risco.”

O RavenStack continua o fluxo:

> “O sinal foi entendido, o responsável foi definido, existe um prazo e o resultado será registrado.”

### 2. A operação atual não é confundida com dado histórico

O sistema preserva os dados históricos, mas não promove automaticamente uma linha antiga, um ticket, um erro ou um evento de churn a uma verdade atual.

Isso evita decisões indevidas como:

- encerrar uma conta por causa de um evento antigo;
- somar linhas históricas como se fossem o MRR atual;
- tratar ausência de uso como cancelamento;
- confundir reembolso informado com perda de caixa.

### 3. Ações têm rastreabilidade

Mudanças relevantes registram:

- quem fez;
- quando fez;
- origem;
- motivo;
- valores antes e depois;
- resultado.

Assim, a gestão deixa de depender de memória, planilhas paralelas e conversas dispersas.

### 4. Cada área usa a mesma conta como referência

Comercial, CS, Suporte, Produto, Financeiro e Gestão passam a trabalhar sobre a mesma ficha e a mesma jornada.

Isso reduz a passagem de contexto entre áreas e evita que cada departamento mantenha uma versão diferente da realidade do cliente.

## Por que manter o plano de ação

O plano de ação não é burocracia adicional. Ele é o mecanismo que converte informação em resultado.

Sem plano de ação:

- o alerta é visto, mas não tratado;
- a reunião acontece, mas ninguém sabe o próximo passo;
- a renovação se aproxima sem dono;
- o risco aparece no relatório e se perde na rotina;
- a gestão cobra pessoas, mas não consegue ver o compromisso registrado.

Com plano de ação:

- toda pendência tem responsável;
- toda ação tem prazo;
- tarefas vencidas aparecem na fila;
- o gestor pode acompanhar a execução;
- o resultado fica associado ao cliente e ao sinal que originou a ação;
- a empresa cria memória operacional.

### O plano de ação também protege a empresa

Ele evita que uma decisão de alto impacto seja tomada sem contexto. Para pausa, redução, encerramento ou perda total, o sistema exige confirmação e registra o motivo.

Isso cria uma camada de governança sem impedir a operação.

## Comparação de valor

| Critério | Painel somente analítico | RavenStack reestruturado |
|---|---|---|
| Ver indicadores | Sim | Sim |
| Consultar histórico | Sim | Sim, separado do estado atual |
| Saber o que fazer agora | Limitado | Minha fila e próxima ação |
| Definir responsável e prazo | Normalmente externo | Dentro do sistema |
| Registrar resultado | Parcial ou manual | Associado à tarefa e à conta |
| Evitar churn inferido indevidamente | Nem sempre | Regra explícita e confirmação humana |
| Auditar mudanças | Limitado | Ator, data, origem e antes/depois |
| Integrar áreas | Por exportação ou reunião | Ficha e jornada compartilhadas |
| Apoiar gestão | Relatório posterior | Acompanhamento da execução |

## Benefícios esperados

### Para a receita

- maior visibilidade de renovações;
- menor risco de tarefas esquecidas;
- melhor registro de expansão, contração e encerramento;
- menos decisões baseadas em dados históricos mal interpretados.

### Para a operação

- menos planilhas paralelas;
- menos reuniões para reconstruir contexto;
- clareza de responsável e prazo;
- histórico de decisões acessível.

### Para a gestão

- acompanhamento da carga e dos atrasos;
- contas ativas sem próxima ação identificadas;
- separação entre problema de execução e problema de qualidade de dados;
- evidência para cobrar resultado sem depender apenas de percepção.

## Limitações honestas do MVP

O sistema ainda não substitui:

- CRM corporativo com SSO e RBAC;
- sistema financeiro oficial;
- data warehouse governado;
- ferramenta de suporte;
- política de aprovação formal para alterações financeiras.

O MVP usa dados sintéticos, e a identidade do operador ainda é informada na sessão. Para uso real, o próximo passo é conectar autenticação, permissões, PostgreSQL persistente, integração com CRM/billing e política de aprovação.

## Recomendação executiva

Manter o plano de ação e adotar o RavenStack como camada operacional sobre os sistemas existentes.

A decisão recomendada é:

1. utilizar o painel enviado como referência de navegação e análise;
2. utilizar a Visão do cliente reestruturada como ponto central de trabalho;
3. exigir que renovações, riscos e decisões relevantes tenham responsável e prazo;
4. medir adoção por tarefas concluídas, contas sem próxima ação e renovações acompanhadas;
5. evoluir o MVP para autenticação e persistência corporativa antes de usar dados reais.

## Conclusão

O valor do RavenStack não está em ter mais uma tela de indicadores. Está em fechar o ciclo que normalmente fica quebrado:

> **sinal → contexto → decisão → ação → responsável → prazo → resultado.**

É esse ciclo que justifica manter o plano de ação e diferencia o sistema de um painel que apenas informa o que já aconteceu.
