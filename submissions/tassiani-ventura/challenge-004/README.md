# Submissão — Tassiani Ventura — Challenge 004

## Sobre mim

- **Nome:** Tassiani Sevidanis Ventura da Silva
- **LinkedIn:** https://www.linkedin.com/in/tassianiventura/
- **Challenge escolhido:** Challenge 004 — Estratégia Social Media

Minha trajetória passou por conteúdo, gestão de projetos, liderança, processos e aquisição, dentro do marketing digital. Hoje sigo trabalhando isso, conectando liderança e produtividade. Acredito que pessoas, processos e tecnologia são pilares fundamentais hoje em dia. Foi isso que quis explorar neste desafio.

---

## Executive Summary

Analisei os dados das cinco plataformas de forma separada, com uma arquitetura de questionários “base” que fiz para enxergar o que cada uma trazia. Inclusive sendo dois anos de análises, busquei considerar o tempo para entender resultados e orientar decisões. Os dados podem enganar, principalmente por serem muito semelhantes. Ainda assim, minha recomendação é trocar regras amplas por uma validação de testes por objetivo, com comparação orgânico × patrocinado, e formatos específicos, além do acompanhamento contínuo no dashboard construído para isso.

---

## Aplicativo online

[Abrir Social Media Performance Intelligence](https://ai-master-challenge-m5yj4ywoyiacfym9wcgjrj.streamlit.app/)

## Acesso às entregas

| Entrega | Link |
|---|---|
| Relatório estratégico final | [Baixar HTML](./solution/reports/Relatorio_Final_Social_Media.html) |
| Aplicativo Streamlit | [Abrir aplicativo online](https://ai-master-challenge-m5yj4ywoyiacfym9wcgjrj.streamlit.app/) · [Código e execução](./solution/README.md) |
| Notebook executado | [Investigação das cinco plataformas](./solution/notebooks/Investigacao_Social_Media_EXECUTADA.ipynb) |
| Process Log | [PROCESS_LOG.pdf](./process-log/PROCESS_LOG.pdf) |
| Validação técnica | [Correções e testes de preparação para publicação](./solution/VALIDACAO.md) |
| Challenge 001 — Diagnóstico de Churn | [Entrega anterior e aplicativo RavenStack](../README.md) |

Os arquivos HTML devem ser baixados e abertos no navegador; o GitHub exibe seu código. Também estão disponíveis para download na barra lateral do aplicativo.

### Detalhamento por plataforma

| Plataforma | Relatório | Resultados |
|---|---|---|
| Instagram | [HTML](./solution/reports/Relatorio_Instagram.html) | [Análise](./solution/results/RESULTADOS_Instagram.md) |
| TikTok | [HTML](./solution/reports/Relatorio_TikTok.html) | [Análise](./solution/results/RESULTADOS_TikTok.md) |
| YouTube | [HTML](./solution/reports/Relatorio_YouTube.html) | [Análise](./solution/results/RESULTADOS_YouTube.md) |
| Bilibili | [HTML](./solution/reports/Relatorio_Bilibili.html) | [Análise](./solution/results/RESULTADOS_Bilibili.md) |
| RedNote | [HTML](./solution/reports/Relatorio_RedNote.html) | [Análise](./solution/results/RESULTADOS_RedNote.md) |

## Solução

Construí uma investigação analítica reproduzível e uma ferramenta para que o time não dependa apenas de um relatório estático.

A entrega reúne:

- um **motor analítico único em Python**;
- um **notebook executado**, com a investigação das cinco plataformas;
- um **dashboard interativo em Streamlit**, para explorar dados, combinações e registros brutos;
- análises individuais de Instagram, TikTok, YouTube, Bilibili e RedNote;
- um **relatório final estratégico**

### Abordagem

Fiz a análise por plataforma, preferi entender uma a uma. Separei performance por objetivo: alcance, curtidas, comentários, compartilhamentos, interação total e eficiência. Também pedi que a análise fosse reconstruída no tempo e cruzasse formato, categoria, creator, audiência, patrocínio, duração, hashtags e demais variáveis sempre que houvesse amostra suficiente.

Ao longo do processo, fui questionando conclusões que pareciam rasas apenas porque estavam fáceis. Isso levou a testes de estabilidade temporal, outliers, comparações controladas e tentativas de derrubar os próprios achados antes de transformá-los em recomendação.

A IA executou os cálculos, cruzamentos e programação do motor, notebook, dashboard. Meu papel foi definir a forma de conduzir, as perguntas, questionar, analisar, pensar e decidir quais conclusões poderiam ou não virar estratégia.

### Resultados / Findings

- **O conteúdo ideal depende do objetivo.** Alcance, curtidas, comentários e compartilhamentos respondem a combinações diferentes. A pergunta certa passou a ser: **“o que eu quero que esse conteúdo gere?”**
- **Compartilhamento trouxe um padrão mais claro entre plataformas.** Instagram, YouTube, Bilibili e RedNote tiveram entre as melhores combinações **imagem + Lifestyle + creators entre 250 mil e 1 milhão**. O TikTok fugiu do padrão, com **texto + Beauty + creators de 500 mil a 1 milhão**.
- **Mais seguidores não significaram mais alcance.** O tamanho do creator fez mais diferença quando combinado com **tipo de conteúdo e objetivo**, principalmente em comentários e compartilhamentos.
- **Patrocínio não funciona como regra geral.** Em alguns recortes ele melhora uma métrica e piora outra. A decisão precisa ser: **patrocinar o quê, para qual objetivo e com qual perfil de creator**.
- **Os melhores padrões mudam ao longo do tempo.** Algumas combinações ganharam força e outras perderam. Isso mostrou que resultado histórico não deveria virar regra permanente sem acompanhamento.

### Recomendações

1. **Definir o objetivo antes de definir o conteúdo:** alcance, conversa, compartilhamento e interação precisam de briefs e métricas próprios.
2. **Patrocinar apenas com KPI definido e comparação com um grupo orgânico equivalente.**
3. **Registrar custo, conversão, receita e variáveis do criativo nas próximas campanhas**, porque sem esses dados é possível medir performance, mas não retorno financeiro.
4. **Usar o dashboard como camada contínua de decisão**, permitindo que qualquer conclusão seja aberta até os posts que a originaram.

### Limitações

- O mesmo `creator_id` aparece associado a diferentes nomes e quantidades de seguidores. Não consegui validar o motivo; o ID não sustenta uma análise histórica individual de creators.
- Sem custos, receita e conversões, a análise compara performance, não ROI financeiro.
- O fuso horário e a unidade de duração não estão documentados; janelas e duração são hipóteses para teste.
- Rankings e comparações observacionais não comprovam causalidade. Os intervalos exploratórios de patrocínio não corrigem a seleção de múltiplas combinações.
- A preparação para deploy corrigiu incompatibilidades entre o aplicativo e o motor disponível. Os relatórios originais foram preservados; o dashboard usa rankings exploratórios recalculados conforme os filtros, como documentado na [validação](./solution/VALIDACAO.md).

---

## Process Log — Como usei IA

[Leia o Process Log completo em PDF](./process-log/PROCESS_LOG.pdf).


### Ferramentas usadas

| **Ferramenta** | **Para que usou** |
| --- | --- |
| *ChatGPT* | Estruturação e execução da investigação, contraponto das hipóteses, análise estatística, programação, construção do dashboard, notebook e relatórios. |
| *Streamlit* | Construção da ferramenta interativa para exploração e acompanhamento dos dados. |
| *Google Colab* | Análise do cruzamento de dados |
| *Notion* | Organização da documentação e do processo. |

### Workflow

1. Defini blocos de tempo de 60 minutos e um temporizador de 4 horas, porque meu objetivo era usar o mínimo de tempo possível e orientar meus passos com o tempo. Basicamente analisei nos primeiros 15 minutos o que tínhamos e pedi pra IA uma primeira estruturação dos dados e criação de um notebook.
2. Enquanto analisava, construí uma arquitetura lógica para investigarmos, ou seja, perguntas específicas, divididas por categorias.
3. A IA fez esse processo, e junto construiu um dashboard para qualquer pessoa conseguir analisar e cruzar dados também
4. Tanto eu, quanto a IA analisamos e cruzamos os dados antes de decidir o que viraria estratégia
5. A partir dos principais insights finalizei os entregáveis finais.

### Onde a IA errou e como corrigi

A primeira análise caiu exatamente no risco que eu queria evitar: trouxe rankings e respostas tecnicamente corretas, mas sem investigar suficientemente o motivo, a evolução temporal ou a relevância prática das diferenças.

Também houve momentos em que a IA transformou pequenas vantagens numéricas em possíveis estratégias sem explicar por que aquilo mereceria um teste. Eu pressionei a análise para abrir os períodos, cruzar outras variáveis, procurar evidência contraditória e distinguir um padrão real de um resultado que apenas ficou em primeiro lugar.

### O que eu adicionei que a IA sozinha não faria

Meu principal papel foi não aceitar a primeira resposta.

Eu defini quais perguntas realmente mudariam uma decisão de Marketing, percebi quando a análise estava confundindo ranking com insight, trouxe a necessidade de reconstruir o comportamento ao longo dos dois anos e insisti que toda recomendação pudesse ser rastreada até a evidência que a sustenta.

Também decidi transformar a análise em uma ferramenta de investigação contínua. Em vez de entregar apenas minhas conclusões, quis que outra pessoa pudesse entrar no dashboard, fazer novos cruzamentos e questionar os mesmos dados.

Há a relação da comunicação. Termos estatísticos e combinações como “formato × categoria × creator” apareciam sem contexto de negócio. Eu redefini a regra: **a técnica comprova; o relatório explica; a estratégia decide.**

A IA ampliou minha capacidade de calcular, programar e testar centenas de combinações. O julgamento sobre o que investigar, quando desconfiar, o que aprofundar e o que deveria virar decisão foi meu. A IA tende a enxergar o dado cru e superficial, sem trazer ou perceber o significado e conexões, que em teoria são normais.

---

## Iterações

Ao longo do processo foram **15 iterações com a IA**.

## Evidências

- [x] [Aplicativo publicado no Streamlit](https://ai-master-challenge-m5yj4ywoyiacfym9wcgjrj.streamlit.app/)
- [x] [Screenshots e narrativa do processo](./process-log/PROCESS_LOG.pdf)
- [x] [Notebook executado com a investigação das cinco plataformas](./solution/notebooks/Investigacao_Social_Media_EXECUTADA.ipynb)

---

*Submissão enviada em: 28/09/2026*
