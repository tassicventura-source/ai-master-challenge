# Diagnóstico e protótipo exploratório

Esta pasta reúne dois materiais complementares do Challenge 001.

## 1. Relatório Final

[`RavenStack_Relatorio_Final.html`](./RavenStack_Relatorio_Final.html)

É a **fonte oficial das conclusões do diagnóstico**. Deve ser lido primeiro. Nele estão a interpretação final dos dados, os limites do dataset e as recomendações priorizadas.

## 2. Torre de Retenção — protótipo exploratório

[`RavenStack_Torre_Retencao_Exploratoria.html`](./RavenStack_Torre_Retencao_Exploratoria.html)

A Torre foi criada durante a fase documentada no Process Log como **Customer Value & Revenue Intelligence (dados atuais)**. Seu objetivo é demonstrar como a investigação poderia sair de um relatório estático e ganhar uma camada interativa para:

- filtrar sinais por período, canal e plano;
- localizar contas e segmentos para investigação;
- consultar definições e limitações junto às métricas;
- transformar achados em uma fila de análise e próximas ações.

Ela é um **protótipo de exploração e triagem**, não o sistema final e não um modelo preditivo de churn. O `churn_event`, o `accounts.churn_flag` e valores de subscriptions não são tratados como perda econômica comprovada sem reconciliação.

A aplicação atual está em [`../solution/`](../solution/) e a demo online está indicada no README principal da submissão.

> Em caso de qualquer diferença de interpretação entre os materiais, prevalece o **Relatório Final**.
