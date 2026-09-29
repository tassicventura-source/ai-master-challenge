# Preparação para GitHub e Streamlit — 28/09/2026

## Origem e preservação

Arquivos obtidos da pasta Drive fornecida pela autora. O dataset original acompanha a aplicação. Relatórios HTML, resultados Markdown, notebook executado e Process Log foram preservados. As análises antigas por plataforma anexadas ao projeto não foram misturadas ao pacote atual, identificado pelo manifesto recebido.

## Problemas encontrados e correções

- O app importava sete funções ausentes de `analysis_engine.py`. Foram implementadas composições sobre as funções existentes: objetivos orgânicos, mapa de patrocínio, audiência, janelas por formato, hashtags, volume semanal e mudanças temporais.
- A comparação orgânica considera apenas posts orgânicos, exige 80 posts por combinação e dados nos dois períodos; ordena a vantagem da mediana do segundo período sobre a mediana orgânica do mesmo recorte. A persistência mensal usa os parâmetros originais (8 posts por mês, 8 meses). É um ranking exploratório; não reproduz necessariamente a seleção editorial dos relatórios.
- Patrocínio usa comparações por formato, categoria e porte com pelo menos 25 posts em cada grupo. Calcula intervalos bootstrap nos extremos descritivos selecionados (3 por extremo na visão geral; 5 por extremo na plataforma). Não há correção por múltiplas comparações, nem causalidade ou ROI.
- A rota “10 · Registros brutos” era capturada pela condição da página 1. A seleção agora é exata.
- A visão executiva geral ignorava filtros ao usar o dataset integral. Agora usa o recorte selecionado.
- Resultados vazios geravam acesso à primeira linha ou a colunas inexistentes. Agora há mensagem de amostra insuficiente.
- A tabela de patrocínio podia acessar uma coluna de plataforma inexistente. A identificação acompanha o resultado.
- Top/bottom por métricas derivadas podia falhar por falta da coluna usada na ordenação. A métrica escolhida agora é incluída.
- Linguagem causal na tela de patrocínio foi substituída por descrição de resultados observados.
- Downloads dos relatórios foram adicionados à barra lateral.
- Dependências para reprodução de notebooks/relatórios foram separadas em `requirements-analysis.txt`.

## Limite de reprodução dos documentos recebidos

O `build_reports.py` recebido e os HTMLs finais usam apresentações e seleções editoriais diferentes. Não foi assumido que regenerar esse script reproduza exatamente os HTMLs finais. A integração corrige a execução do aplicativo, sem certificar equivalência integral entre seus rankings e todas as conclusões dos documentos originais.

## Testes

- Streamlit AppTest: abertura e navegação pelas dez páginas na visão geral e no Instagram, sem exceções.
- Dez páginas com recorte de um único dia: sem exceções; telas sem amostra suficiente encerram com mensagem informativa.
- Páginas de objetivos e patrocínio com filtro “somente patrocinados”: sem exceções.
- Cruzamentos com dimensão booleana (`patrocinado`) e com quatro dimensões; top/bottom por três métricas derivadas: sem exceções.
- Servidor Streamlit iniciado localmente; endpoint de saúde respondeu `ok`.
- Links relativos dos READMEs verificados; todos os destinos existem.
- Notebook recebido: 25 células, 12 células executadas, nenhum output de erro. O notebook completo não foi reexecutado nesta preparação.
- Integridade da base gzip verificada byte a byte contra o CSV original.

Essas verificações validam os fluxos exercitados; não substituem uma auditoria estatística completa nem o teste do deploy remoto no Streamlit Community Cloud.

## Integridade do dataset

O CSV de 23.290.049 bytes excedeu o limite de 16 MiB por requisição da integração de upload. Foi incluído em gzip, sem perda: a descompressão foi comparada byte a byte com o original. O motor lê automaticamente `.csv.gz` quando o caminho `.csv` não existe. SHA-256 do CSV original: `693a2df6e609d1c099f3430d9a5b894b224fe12b2420c0d93e6defe90d15f18e`.
