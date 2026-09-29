from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

ROOT=Path(__file__).parent
NB=ROOT/'notebooks'/'Investigacao_Social_Media_EXECUTADA.ipynb'

cells=[]
cells.append(nbf.v4.new_markdown_cell('''# Investigação Social Media — Execução Canônica\n\nNotebook de auditoria do Challenge 004. Os cálculos usam o mesmo `analysis_engine.py` do dashboard e dos relatórios.\n\n**Plataformas:** Instagram, TikTok, YouTube, Bilibili e RedNote.\n\n**Regra de leitura:** rankings são sempre contextualizados com amostra, magnitude, tempo e controles. Performance de patrocínio não é chamada de ROI sem custo/receita/conversão.'''))

cells.append(nbf.v4.new_code_cell('''from pathlib import Path\nimport sys, pandas as pd, numpy as np\nfrom IPython.display import display, Markdown\n\n# Funciona dentro da pasta do projeto; em Colab, faça upload/clone do projeto inteiro.\nroot = Path.cwd()\nif not (root / "analysis_engine.py").exists():\n    candidates = [root.parent, root.parent.parent, Path('/content')]\n    for c in candidates:\n        if (c / "analysis_engine.py").exists():\n            root = c; break\nsys.path.insert(0, str(root))\nfrom analysis_engine import *\nDATA = root / "data" / "social_media_dataset.csv"\ndf = load_data(DATA)\nprint(f"Base carregada: {len(df):,} posts | {df.data_hora.min():%d/%m/%Y} a {df.data_hora.max():%d/%m/%Y}")'''))

cells.append(nbf.v4.new_markdown_cell('## 1. Panorama cross-platform'))
cells.append(nbf.v4.new_code_cell('''display(platform_overview(df))'''))

cells.append(nbf.v4.new_markdown_cell('## 2. Universo de cruzamentos definido antes das conclusões'))
cells.append(nbf.v4.new_code_cell('''for bloco in cross_universe():\n    display(Markdown(f"### {bloco['familia']}"))\n    display(pd.DataFrame({'Cruzamento / pergunta': bloco['cruzamentos']}))'''))

cells.append(nbf.v4.new_markdown_cell('## 3. Auditoria da base e dos creator IDs'))
cells.append(nbf.v4.new_code_cell('''rows=[]\nfor p in sorted(df.plataforma.unique()):\n    d=platform_data(df,p); a=audit_quality(d)\n    rows.append({\n        'plataforma':p,'posts':a['posts'],\n        'variação relativa de views (%)':100*a['distribuicao_metricas']['visualizacoes']['variacao_relativa'],\n        'creator IDs com múltiplos nomes (%)':a['creator_ids_multiplos_nomes_pct'],\n        'creator IDs com múltiplas contagens (%)':a['creator_ids_multiplas_contagens_pct']\n    })\ndisplay(pd.DataFrame(rows))'''))

cells.append(nbf.v4.new_markdown_cell('## 4. Objetivos separados: alcance, conversa, compartilhamento, interação e eficiência'))
cells.append(nbf.v4.new_code_cell('''metricas=['visualizacoes','comentarios','compartilhamentos','interacoes_totais','taxa_engajamento']\nfor p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:\n    display(Markdown(f"### {p}"))\n    d=platform_data(df,p)\n    out=[]\n    for m in metricas:\n        t=combination_analysis(d,['formato','categoria','porte_criador'],m,80,8,8)\n        stable=t[(t.meses_validos>=10)&(t.meses_acima_do_padrao_pct>=60)] if 'meses_validos' in t else pd.DataFrame()\n        r=(stable.iloc[0] if not stable.empty else t.iloc[0])\n        out.append({\n            'objetivo':METRICS[m], 'formato':r.formato,'categoria':r.categoria,'porte_criador':r.porte_criador,\n            'posts':int(r.n),'resultado':r.mediana,'diferença_plataforma':r.diferenca_para_plataforma,\n            'meses_válidos':r.get('meses_validos',np.nan),'meses_acima_padrão_%':r.get('meses_acima_do_padrao_pct',np.nan),\n            'primeiros_12m':r.get('primeiros_12m',np.nan),'segundos_12m':r.get('segundos_12m',np.nan)\n        })\n    display(pd.DataFrame(out))'''))

cells.append(nbf.v4.new_markdown_cell('## 5. Reconstrução temporal: o que mudou entre janelas equivalentes'))
cells.append(nbf.v4.new_code_cell('''for p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:\n    d=platform_data(df,p)\n    display(Markdown(f"### {p}"))\n    period=d.groupby('periodo_12m').agg(posts=('id','size'),views=('visualizacoes','median'),interacoes=('interacoes_totais','median'),interacoes_por_100_views=('taxa_engajamento','median'),patrocinio_pct=('patrocinado',lambda s:100*s.mean()))\n    display(period)\n    display(Markdown('**Mudança de mix — categoria**'))\n    display(mix_shift(d,'categoria'))\n    display(Markdown('**Mudança de mix — formato**'))\n    display(mix_shift(d,'formato'))'''))

cells.append(nbf.v4.new_markdown_cell('## 6. Patrocínio: agregado e controlado'))
cells.append(nbf.v4.new_code_cell('''for p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:\n    d=platform_data(df,p)\n    display(Markdown(f"### {p} — comparação geral"))\n    display(sponsorship_overall(d,['visualizacoes','comentarios','compartilhamentos','interacoes_totais','taxa_engajamento'],n_boot=300))\n    display(Markdown('**Exemplos controlados por formato × categoria × tamanho do creator (taxa de engajamento)**'))\n    ctrl=sponsorship_controlled(d,'taxa_engajamento',['formato','categoria','porte_criador'],25,with_ci=False)\n    display(pd.concat([ctrl.head(5),ctrl.tail(5)]).drop_duplicates())'''))

cells.append(nbf.v4.new_markdown_cell('## 7. Audiência'))
cells.append(nbf.v4.new_code_cell('''for p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:\n    d=platform_data(df,p)\n    display(Markdown(f"### {p}"))\n    rows=[]\n    for dim in ['faixa_etaria_audiencia','genero_audiencia','localizacao_audiencia','idioma']:\n        t=group_summary(d,dim,'taxa_engajamento',30)\n        if not t.empty:\n            rows.append({'dimensão':DIMENSION_LABELS[dim],'melhor':t.iloc[0][dim],'resultado_melhor':t.iloc[0].mediana,'pior':t.iloc[-1][dim],'resultado_pior':t.iloc[-1].mediana,'distância':t.iloc[0].mediana-t.iloc[-1].mediana})\n    display(pd.DataFrame(rows))'''))

cells.append(nbf.v4.new_markdown_cell('## 8. Outliers — top/bottom 1% e 5%'))
cells.append(nbf.v4.new_code_cell('''for p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:\n    d=platform_data(df,p)\n    display(Markdown(f"### {p}"))\n    for pct in [.01,.05]:\n        x=outlier_profile(d,'taxa_engajamento',pct)\n        display(Markdown(f"**Top/bottom {int(pct*100)}% — segmentos mais super-representados no topo**"))\n        display(x.sort_values('indice_top',ascending=False).head(12))'''))

cells.append(nbf.v4.new_markdown_cell('## 9. Hashtags e duração relativa'))
cells.append(nbf.v4.new_code_cell('''for p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:\n    d=platform_data(df,p)\n    display(Markdown(f"### {p}"))\n    display(Markdown('**Duração relativa**'))\n    display(group_summary(d,'duracao_relativa','taxa_engajamento',30))\n    display(Markdown('**Hashtags com pelo menos 30 ocorrências**'))\n    display(hashtag_analysis(d,'taxa_engajamento',30).head(20))'''))

cells.append(nbf.v4.new_markdown_cell('## 10. Frequência semanal'))
cells.append(nbf.v4.new_code_cell('''rows=[]
for p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:
    d=platform_data(df,p)
    for m in ['visualizacoes','taxa_engajamento']:
        r=frequency_performance(d,m)
        rows.append({'plataforma':p,'métrica':METRICS[m],'relação volume semanal × resultado':r['correlacao_volume_resultado']})
display(pd.DataFrame(rows))
print('Leitura: valores próximos de zero indicam que o histórico não sustenta uma frequência semanal ótima por si só.')'''))

cells.append(nbf.v4.new_markdown_cell('## 11. Stress test fora do tempo'))
cells.append(nbf.v4.new_code_cell('''rows=[]\nfor p in ['Instagram','TikTok','YouTube','Bilibili','RedNote']:\n    d=platform_data(df,p)\n    for m in ['taxa_engajamento','visualizacoes']:\n        r=temporal_predictability(d,m)\n        rows.append({'plataforma':p,'métrica':METRICS[m],**r})\ndisplay(pd.DataFrame(rows))\nprint('Leitura: AUC perto de 0,50 significa que as características disponíveis no primeiro período não reconhecem os posts de maior performance no segundo melhor que aproximadamente o acaso.')'''))

cells.append(nbf.v4.new_markdown_cell('''## 12. Síntese metodológica\n\n- Os cálculos deste notebook são os mesmos do dashboard e dos relatórios.\n- As tabelas completas continuam exploráveis no Streamlit até o registro bruto.\n- O relatório traduz os resultados para linguagem de negócio; este notebook preserva a camada de auditoria.\n- A falta de gasto/receita/conversão impede ROI financeiro.\n- Creator ID inconsistente não é usado como identidade longitudinal.\n- Horário não vira prescrição sem timezone.\n- Content length é interpretado relativamente, sem assumir unidade.'''))

nb=nbf.v4.new_notebook(cells=cells, metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3"}})
nbf.write(nb,NB)
client=NotebookClient(nb, timeout=300, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}})
executed=client.execute()
nbf.write(executed,NB)
print(NB)
