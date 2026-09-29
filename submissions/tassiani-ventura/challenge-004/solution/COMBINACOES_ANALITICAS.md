# Arquitetura Analítica Canônica — Challenge 004 Social Media

Este documento define **o universo de perguntas que o motor analítico deve ser capaz de responder**. Ele não é uma lista de gráficos obrigatórios. A profundidade de cada cruzamento depende de amostra, magnitude, estabilidade temporal e potencial de decisão.

## 1. Validação antes da análise

- Cobertura temporal por plataforma.
- Duplicidades de linha e de conteúdo.
- Ausências e valores impossíveis.
- Distribuição de views, curtidas, comentários, compartilhamentos e seguidores.
- Relação matemática entre métricas derivadas e campos originais.
- Consistência de `creator_id`, nomes e follower count.
- Validade de `content_length`: a unidade não é presumida; duração é tratada relativamente dentro da plataforma.
- Validade do horário: sem timezone, hora é exploratória.
- Limites de patrocínio: sem gasto, receita e conversão, não se chama performance de ROI.

## 2. Objetivos de Marketing

Cada pergunta deve ser respondida separadamente para:

- alcance: visualizações;
- curtidas;
- comentários/conversa;
- compartilhamentos;
- interações totais;
- curtidas a cada 100 visualizações;
- comentários a cada 100 visualizações;
- compartilhamentos a cada 100 visualizações;
- interações a cada 100 visualizações.

A mesma combinação pode servir para um objetivo e prejudicar outro. O relatório deve mostrar essas divergências.

## 3. Análises de uma variável

Para cada objetivo:

- plataforma;
- formato;
- categoria;
- tamanho do creator;
- orgânico/patrocinado;
- idade predominante da audiência;
- gênero predominante;
- localização predominante;
- idioma;
- duração relativa;
- quantidade de hashtags;
- dia da semana;
- faixa horária;
- mês/trimestre.

## 4. Cruzamentos de duas variáveis

### Conteúdo
- formato × categoria;
- formato × tamanho do creator;
- formato × patrocínio;
- formato × audiência;
- formato × duração;
- formato × dia/faixa horária;
- formato × idioma;
- formato × hashtag.

### Categoria
- categoria × tamanho do creator;
- categoria × patrocínio;
- categoria × audiência;
- categoria × duração;
- categoria × dia/faixa horária;
- categoria × hashtag.

### Creator
- tamanho × patrocínio;
- tamanho × audiência;
- tamanho × duração;
- tamanho × dia/faixa horária.

### Audiência
- idade × formato/categoria/tamanho/patrocínio;
- gênero × formato/categoria/tamanho/patrocínio;
- localização × formato/categoria/tamanho/patrocínio;
- idioma × formato/categoria/tamanho/patrocínio.

### Tempo
- mês × formato/categoria/tamanho/patrocínio/audiência;
- trimestre × formato/categoria/tamanho/patrocínio/audiência;
- dia da semana × formato/categoria/tamanho/patrocínio/audiência;
- faixa horária × formato/categoria/tamanho/patrocínio/audiência.

## 5. Cruzamentos de três ou mais variáveis

Executar quando houver amostra suficiente, especialmente:

- formato × categoria × tamanho do creator;
- formato × categoria × patrocínio;
- formato × tamanho × patrocínio;
- categoria × tamanho × patrocínio;
- formato × categoria × tamanho × patrocínio;
- audiência × formato × categoria;
- audiência × categoria × tamanho;
- audiência × formato × patrocínio;
- tempo × formato × categoria;
- tempo × categoria × tamanho;
- tempo × formato × patrocínio;
- duração × formato × categoria;
- plataforma × formato × categoria;
- plataforma × categoria × tamanho;
- plataforma × formato × patrocínio.

## 6. Reconstrução temporal

Não analisar os dois anos como fotografia única.

Para cada objetivo e para os principais segmentos:

- mês a mês;
- trimestre;
- semana;
- dia;
- dia da semana;
- faixa horária;
- primeiros 12 meses × segundos 12 meses;
- períodos equivalentes;
- janelas móveis;
- mudança do mix de publicação;
- mudança de performance dentro do mesmo segmento;
- surgimento/desaparecimento de combinações;
- perda/ganho progressivo de vantagem;
- potenciais mudanças de regime.

Perguntas obrigatórias:

1. O mix mudou antes da performance?
2. A performance mudou antes do mix?
3. Um segmento melhorou porque passou a aparecer mais ou porque realmente performou melhor?
4. Patrocínio cresceu depois de bons resultados orgânicos?
5. O efeito do patrocínio mudou ao longo dos meses?
6. Alguma combinação boa no primeiro período perdeu força no segundo?
7. Alguma combinação apareceu apenas recentemente?
8. O resultado agregado esconde direções opostas dentro dos segmentos?

## 7. Patrocínio

Para cada objetivo:

- patrocinado × orgânico no agregado;
- controlado por formato;
- controlado por categoria;
- controlado por tamanho do creator;
- controlado simultaneamente por formato × categoria × tamanho;
- audiência;
- duração relativa;
- período;
- mês;
- dia/faixa horária (exploratório);
- evolução do ganho/perda do patrocinado;
- teste de efeito de composição / possível paradoxo de Simpson.

Sempre mostrar:

- quantidade de posts orgânicos e patrocinados;
- resultado típico dos dois grupos;
- diferença observada;
- incerteza quando calculada;
- se a diferença permanece após controle;
- comportamento temporal;
- objetivo beneficiado e objetivo eventualmente prejudicado.

Sem custo, receita ou conversão: **não usar ROI, ROAS, CPA ou CPE financeiro**.

## 8. Audiência

Investigar idade, gênero, localização e idioma:

- isoladamente;
- por plataforma;
- por objetivo;
- por formato;
- por categoria;
- por tamanho do creator;
- por patrocínio;
- por período;
- em combinações com amostra suficiente.

Diferença pequena não deve virar persona prioritária apenas porque ficou em primeiro lugar.

## 9. Duração e hashtags

### Duração
A unidade de `content_length` não é documentada. Portanto:

- analisar posição relativa dentro de cada plataforma (muito curta → muito longa);
- cruzar com formato, categoria, tamanho e patrocínio;
- não chamar de segundos/minutos sem evidência.

### Hashtags

- quantidade de hashtags;
- hashtags individuais com amostra mínima;
- hashtag × formato;
- hashtag × categoria;
- evolução temporal quando houver volume suficiente;
- verificar dependência de outliers.

## 10. Outliers e não óbvio

Para cada objetivo:

- top 1%;
- bottom 1%;
- top 5%;
- bottom 5%;
- composição desses extremos versus base completa;
- segmentos raros super-representados;
- segmentos mais previsíveis entre os piores;
- média × mediana;
- efeito com e sem extremos;
- mudança de sinal após controle;
- possível paradoxo de Simpson;
- efeito de composição.

## 11. Stress test de cada conclusão

Para qualquer conclusão importante:

**Pergunta → cálculo → amostra → resultado → magnitude → dispersão → trajetória temporal → explicações alternativas → evidência contraditória → limitação → implicação de Marketing.**

Perguntas de destruição:

- Depende de poucos posts?
- Some na mediana?
- Some sem top 1%?
- Permanece no segundo período?
- Permanece quando controlo formato/categoria/tamanho/audiência?
- O resultado pode ser explicado por mudança de mix?
- Há outro segmento que conta história oposta?
- Um modelo treinado no primeiro período consegue reconhecer o padrão no segundo?

## 12. Comparação cross-platform

O relatório oficial deve comparar as cinco plataformas sem transformar diferenças microscópicas em ranking estratégico.

Para cada objetivo:

- tamanho da diferença entre plataformas;
- diferenças de formato dentro de cada plataforma;
- categorias;
- creators;
- audiência;
- patrocínio;
- temporalidade;
- combinações que se repetem entre plataformas;
- combinações exclusivas;
- estratégias que parecem universais versus locais.

A conclusão deve responder: **onde o dado realmente sustenta concentração de esforço, onde só sustenta teste e onde não sustenta decisão.**
