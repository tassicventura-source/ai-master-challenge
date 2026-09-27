# Impacto estimado das ações — RavenStack

Este documento complementa o Relatório Final e conecta cada recomendação ao impacto que **pode ser estimado com as cinco bases atuais**.

## Regra de leitura

Os dados não permitem estimar com segurança "MRR salvo", ROI de retenção ou redução esperada de churn, porque não existe churn econômico canônico nem MRR atual confiável por conta. Por isso, o impacto abaixo separa:

- **escopo quantificável agora**: contas, eventos e valor comercial registrado que entram na ação;
- **resultado que a ação deve destravar**: métrica que passa a ser mensurável depois da reconciliação;
- **impacto financeiro futuro**: só deve ser calculado quando contrato, cobrança, pagamento e MRR antes/depois estiverem reconciliados.

Isso evita transformar exposição em benefício previsto.

| Prioridade | Ação | Escopo quantificável agora | Impacto esperado / métrica de sucesso | Entregável que operacionaliza |
|---|---|---|---|---|
| P0 | Reconciliar as 92 contas de 2024 por trás dos 47,2% | 92 contas com janela completa e evento em até 90 dias; **US$ 273.827** de valor inicial registrado nessas contas | Converter 92 casos ambíguos em desfechos econômicos classificados; medir pela primeira vez quantas perdas totais/contrações ocorreram e qual MRR foi efetivamente perdido | Relatório Final + app: Finance/RevOps, Conta 360 e registro de movimentos econômicos |
| P1 | Investigar a qualidade do crescimento Organic × Enterprise | 22 contas comparáveis; 14 com evento e 8 sem; **US$ 161.986** de valor inicial registrado no grupo | Identificar diferenças de origem, promessa, handoff, onboarding e fricção entre jornadas equivalentes. Sucesso = hipóteses convertidas em evidência e ações por conta; não "redução de churn" presumida | Relatório Final + app: Growth/Comercial, Cliente 360 e tarefas |
| P1 | Reconciliar refund/crédito com cobrança e continuidade | **US$ 8.652,25** registrados em 142 eventos de 120 contas | Separar crédito, refund efetivamente liquidado e casos sem perda econômica; medir valor financeiro confirmado em vez de usar o campo bruto como perda | Relatório Final + app: Finance/RevOps e trilha de evidências |
| P2 | Criar uma verdade operacional de lifecycle e receita | 500 contas; hoje as três representações de churn discordam em 400/500 contas, e todas as contas têm múltiplas subscriptions abertas no histórico | Cobertura progressiva de lifecycle, contrato e MRR confirmados. Métricas-alvo após reconciliação: logo churn, revenue churn, GRR, NRR, expansão e contração | Aplicação + modelo operacional + treinamento + briefing CEO |

## Como transformar isso em impacto financeiro depois da reconciliação

Quando os 92 casos prioritários estiverem classificados, o sistema poderá calcular sem inferência:

- **MRR perdido confirmado** = soma dos deltas negativos de MRR em perdas/contrações confirmadas;
- **MRR expandido confirmado** = soma dos deltas positivos em expansões confirmadas;
- **MRR retido após ação** = MRR confirmado antes da intervenção que permanece ativo após a janela definida;
- **impacto líquido observado** = expansão confirmada + MRR retido atribuível a casos acompanhados − contração/perda confirmada;
- **ROI operacional** = impacto financeiro observado / custo incremental da intervenção, somente se o custo também for registrado.

A aplicação já possui a estrutura para registrar MRR antes/depois, delta, responsável, ação e resultado. O que falta para transformar isso em impacto econômico real não é uma fórmula adicional: é a reconciliação com os sistemas de origem.

## Limite importante

**US$ 273.827 e US$ 161.986 não são receita em risco nem receita salva.** São valores de entrada registrados nas populações priorizadas. Servem para dimensionar a materialidade comercial das ações, não para prometer retorno.

Os cálculos deste documento são reproduzidos por `solution/scripts/reproduce_diagnostic.py`.
