# Manifesto dos arquivos atuais

Este diretório contém apenas a versão canônica da solução. Arquivos `FINAL_v2`, `v3`, relatórios antigos e dashboards anteriores foram deliberadamente excluídos.

| Arquivo | Função | Status |
|---|---|---|
| `data/social_media_dataset.csv.gz` | Base original completa | Fonte factual |
| `analysis_engine.py` | Motor analítico único para as cinco plataformas | Canônico |
| `app.py` | Dashboard Analítico Completo cross-platform | Canônico |
| `requirements.txt` | Dependências do projeto | Canônico |
| `README.md` | Execução, arquitetura e deploy | Canônico |
| `COMBINACOES_ANALITICAS.md` | Arquitetura de perguntas e cruzamentos | Canônico |
| `PADRAO_RELATORIO.md` | Padrão de comunicação executiva | Canônico |
| `PROMPT_MESTRE_ANALISE_PLATAFORMA.md` | Prompt de execução padronizada por plataforma | Canônico |
| `notebooks/Investigacao_Social_Media_EXECUTADA.ipynb` | Reprodução das análises das cinco plataformas | Canônico |
| `results/RESULTADOS_Instagram.md` | Respostas completas — Instagram | Atual |
| `results/RESULTADOS_TikTok.md` | Respostas completas — TikTok | Atual |
| `results/RESULTADOS_YouTube.md` | Respostas completas — YouTube | Atual |
| `results/RESULTADOS_Bilibili.md` | Respostas completas — Bilibili | Atual |
| `results/RESULTADOS_RedNote.md` | Respostas completas — RedNote | Atual |
| `reports/Relatorio_Instagram.html` | Relatório individual — Instagram | Atual |
| `reports/Relatorio_TikTok.html` | Relatório individual — TikTok | Atual |
| `reports/Relatorio_YouTube.html` | Relatório individual — YouTube | Atual |
| `reports/Relatorio_Bilibili.html` | Relatório individual — Bilibili | Atual |
| `reports/Relatorio_RedNote.html` | Relatório individual — RedNote | Atual |
| `reports/Relatorio_Final_Social_Media.html` | Relatório oficial cross-platform | Atual |
| `build_reports.py` | Reprodução automatizada dos relatórios a partir do motor | Suporte válido |
| `make_notebook.py` | Reprodução do notebook canônico | Suporte válido |

Não há necessidade de usar bases filtradas por plataforma: o motor filtra diretamente a base original e evita duplicação de fonte.
