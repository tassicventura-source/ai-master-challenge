# Validação da revisão

Revisão em 26/09/2026 (horário de São Paulo). Ambiente: Python 3.12.14/Linux, versões fixadas em requirements.txt.

## Resultado

**35 testes automatizados aprovados em 43,25 segundos.** `pip check` sem dependências quebradas; compilação Python e `git diff --check` sem erros. A aplicação foi iniciada pelo servidor Streamlit e respondeu ao endpoint de saúde.

| Cobertura | Resultado |
|---|---|
| Oito telas e opções de seleção, filtros e alternâncias | Aprovado com Streamlit AppTest |
| Abertura individual das 500 contas | Aprovado |
| Growth, Produto, Suporte e Finance → Conta 360 | Conta selecionada preservada |
| Timeline sem tipos selecionados e inclusão de anomalias | Estado vazio e recorte tratados |
| Fila sem eventos no contexto escolhido | Exibição vazia e download desabilitado |
| Banco ausente | Reconstrução automática em diretório temporário aprovada |
| Integridade das cinco fontes | SHA-256 idênticos aos anexos originais |
| Cálculo independente da janela completa | 2023: 44/227; 2024: 92/195 |
| Flag legada de reativação | Preservada; não classifica evento canônico |
| Cabeçalhos de Jornada e Arquitetura | Alinhamento entre rótulos e conteúdo corrigido e testado |

## Navegador e UX

As oito telas foram percorridas no Chromium. Downloads CSV foram recebidos e conferidos em Conta 360, Growth, Produto, Suporte e Finance. O caminho Finance → Conta 360 foi executado no navegador. A interface foi conferida em 1440×1000 e 390×844; detalhes e resultados estão em `browser-results.json` e `screenshots/`.

A revisão removeu indicadores redundantes da entrada, agrupou o menu, recolheu diagramas, limitou as escolhas iniciais da timeline e aproximou as análises da conta investigada. Barras de ferramentas de gráficos foram ocultadas e os gráficos ficaram mais compactos. Tabelas largas preservam rolagem local para auditoria.

## Correções com impacto analítico

1. Contas sem 90 dias completos deixaram de entrar como ausência de evento no denominador.
2. A flag `is_reactivation` não converte mais o registro em evento de reativação.
3. Contagens sem registros observáveis são zero, mas datas e atributos desconhecidos continuam vazios.
4. Reembolsos preservam centavos na leitura executiva; não são descritos como caixa conciliado.

## Limites da validação

A revisão foi automatizada e técnica, com inspeção visual; não é pesquisa de usabilidade com usuários reais nem homologação por especialistas externos. Windows não foi executado neste ambiente; o script .bat foi revisado. GitHub Actions está preparado, mas só será executado após push. Streamlit Community Cloud não foi publicado nem testado em produção. Não foram feitos testes de carga multiusuário.

A aplicação continua somente leitura. Conciliação financeira, tarefas persistentes, dados atualizados por API, autenticação e modelos de IA não estão implementados. A adequação dessas funções depende de escopo posterior. A base sintética permite demonstração e verificação técnica, sem provar mecanismos causais de negócios reais.

## Revisão final de premissas

A interface não deve induzir o gestor a confundir valor inicial com receita atual, ausência de uso válido com inatividade, nem evento com perda. Essas distinções acompanham os recortes. A premissa de completude até 31/12/2024 está explícita; caso a janela de extração mude, a análise deve ser reconstruída e as definições revisadas.

Uma oportunidade preservada na experiência é investigar eventos com reembolso junto ao histórico da conta. Isso conecta um valor financeiro registrado à jornada sem inventar churn econômico ou atribuir causalidade a suporte/produto.
