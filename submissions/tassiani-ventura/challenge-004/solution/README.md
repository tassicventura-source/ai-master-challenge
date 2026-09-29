# Social Media Performance Intelligence

[Voltar à submissão do Challenge 004](../README.md) · [Challenge 001](../../README.md)

Aplicativo analítico em Streamlit para Instagram, TikTok, YouTube, Bilibili e RedNote. Inclui filtros, objetivos, patrocínio, tempo, audiência, cruzamentos, auditoria e registros brutos.

## Aplicativo online

[Abrir Social Media Performance Intelligence](https://ai-master-challenge-m5yj4ywoyiacfym9wcgjrj.streamlit.app/)

## Configuração no Streamlit Community Cloud

| Campo | Valor |
|---|---|
| Repository | `tassicventura-source/ai-master-challenge` |
| Branch | `submission/tassiani-ventura` |
| Main file path | `submissions/tassiani-ventura/challenge-004/solution/app.py` |
| Python | `3.12` |
| Secrets | Não necessários |

O aplicativo está publicado com essa configuração. Para reproduzir o deploy, use esses campos em **Create app → Deploy an app from GitHub** e clique em **Deploy**.

A base está comprimida em gzip, sem alteração de conteúdo; o motor abre o arquivo diretamente. O aplicativo carrega a base incluída em `data/social_media_dataset.csv.gz`. É uma ferramenta de consulta: filtros pertencem à sessão e não há gravação de alterações nem dependência de banco de dados.

## Executar localmente

Na raiz do repositório:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r submissions/tassiani-ventura/challenge-004/solution/requirements.txt
streamlit run submissions/tassiani-ventura/challenge-004/solution/app.py
```

## Entregas

- [Relatório final](reports/Relatorio_Final_Social_Media.html): baixar e abrir no navegador. Os seis relatórios também podem ser baixados na barra lateral do app.
- [Resultados por plataforma](results/).
- [Notebook executado](notebooks/Investigacao_Social_Media_EXECUTADA.ipynb).
- [Motor de cálculo](analysis_engine.py).
- [Mapa de cruzamentos](COMBINACOES_ANALITICAS.md).
- [Protocolo de relatório](PADRAO_RELATORIO.md).
- [Prompt de investigação](PROMPT_MESTRE_ANALISE_PLATAFORMA.md).
- [Validação e limites da integração](VALIDACAO.md).

## Reprodução analítica

Instale as dependências adicionais:

```bash
pip install -r submissions/tassiani-ventura/challenge-004/solution/requirements-analysis.txt
```

Abra o notebook na pasta `notebooks/` e execute as células na ordem. Ele resolve o caminho do motor e do dataset relativamente ao projeto.

`make_notebook.py` recria o notebook de investigação e `build_reports.py` gera relatórios a partir do motor. Esses scripts foram recebidos junto com a entrega. **O gerador de relatórios não corresponde integralmente à versão editorial final dos HTMLs enviados**; executá-lo pode substituir esses documentos. Preserve uma cópia se quiser comparar a reprodução com os relatórios finais. A preparação para GitHub manteve os HTMLs e o notebook recebidos, sem reescrever as conclusões.

## Como interpretar

O dashboard oferece rankings orgânicos exploratórios, comparação de patrocínio por formato/categoria/porte e dados filtráveis. A integração das funções ausentes está documentada em `VALIDACAO.md`. Um ranking filtrado não equivale automaticamente à recomendação editorial dos relatórios.

Não há custos, receita nem conversões; não se estima ROI. As comparações são observacionais, os intervalos de confiança exploratórios não corrigem múltiplas comparações, o fuso e a unidade de duração não estão documentados e `creator_id` não identifica consistentemente uma mesma pessoa ao longo do tempo.

## Teste de integração

Na pasta desta solução, execute `python tests/smoke_app.py`. O teste usa o AppTest do Streamlit, o dataset incluído e as dependências de `requirements.txt`.
