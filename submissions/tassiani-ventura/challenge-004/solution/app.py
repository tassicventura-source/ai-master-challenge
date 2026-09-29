from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from analysis_engine import (
    load_data, apply_filters, platform_overview, group_summary, time_series,
    combination_analysis, sponsorship_overall, sponsorship_decision_map,
    monthly_sponsorship, audience_profile_candidates, best_time_by_format,
    hashtag_count_profile, weekly_volume_bands, temporal_movers,
    outlier_profile, top_bottom_rows, creator_id_audit, audit_quality,
    organic_objective_playbook, METRICS, DIMENSION_LABELS, OBJECTIVE_METRICS
)

st.set_page_config(page_title='Social Media Performance Intelligence', layout='wide', page_icon='📊')
DATA_PATH = Path(__file__).parent / 'data' / 'social_media_dataset.csv'

@st.cache_data(show_spinner=False)
def get_data():
    return load_data(DATA_PATH)

@st.cache_data(show_spinner=False)
def playbook_cached(platform, metric):
    d = DF if platform == 'Todas' else DF[DF.plataforma.eq(platform)]
    return organic_objective_playbook(d, metric)

@st.cache_data(show_spinner=False)
def sponsor_map_cached(platform, metric):
    d = DF if platform == 'Todas' else DF[DF.plataforma.eq(platform)]
    return sponsorship_decision_map(d, metric, shortlist=3, n_boot=500)

DF = get_data()
PLATFORMS = ['Instagram','TikTok','YouTube','Bilibili','RedNote']
GOALS = {
    'visualizacoes':'Alcance','curtidas':'Curtidas','comentarios':'Comentários / conversa',
    'compartilhamentos':'Compartilhamentos','interacoes_totais':'Interação total',
    'taxa_engajamento':'Eficiência das interações'
}
FMT = {'video':'vídeo','image':'imagem','text':'texto','mixed':'misto'}
CAT = {'beauty':'beleza','lifestyle':'estilo de vida','tech':'tecnologia'}
GENDER = {'female':'feminino','male':'masculino','non-binary':'não binário','unknown':'não informado'}


def br(x, dec=0):
    if x is None or pd.isna(x): return '—'
    s=f'{float(x):,.{dec}f}'
    return s.replace(',','X').replace('.',',').replace('X','.')

def pct(x, dec=1): return f'{br(x,dec)}%'

def combo(r):
    return f"{FMT.get(str(r.formato),str(r.formato))} · {CAT.get(str(r.categoria),str(r.categoria))} · creator {str(r.porte_criador).replace('mil–1 mi','mil–1 milhão')}"

def metric_text(metric, x):
    if metric=='taxa_engajamento': return f'{br(x,2)} interações / 100 views'
    return br(x,0)

def decision_text(metric, r):
    lift=float(r.vantagem_recente_pct)
    if metric=='visualizacoes' and abs(lift)<.5:
        return f'Melhor recorte observado para alcance, mas a vantagem é só {pct(lift,2)}. Use como teste; não pague prêmio por isso.'
    if lift>=2: return f'Sinal relevante (+{pct(lift,2)}). Prioridade alta de teste.'
    if lift>=1: return f'Sinal moderado (+{pct(lift,2)}). Prioridade de teste.'
    if lift>0: return f'Sinal pequeno (+{pct(lift,2)}). Use para desempatar escolhas, não para uma mudança grande.'
    return 'Não supera o padrão recente.'

# ---------- Sidebar ----------
st.title('Social Media Performance Intelligence')
st.caption('Um dashboard para responder “o que funciona, para qual objetivo, em qual contexto e com que evidência” nas cinco plataformas.')

st.sidebar.header('Recorte')
platform = st.sidebar.selectbox('Plataforma', ['Todas'] + PLATFORMS)
base = DF.copy() if platform=='Todas' else DF[DF.plataforma.eq(platform)].copy()
min_date,max_date=base.data_hora.min().date(),base.data_hora.max().date()
dates=st.sidebar.date_input('Período',(min_date,max_date),min_value=min_date,max_value=max_date)
if len(dates)==2: base=apply_filters(base,{'date_range':dates})
for col,label in [('formato','Formato'),('categoria','Categoria'),('porte_criador','Tamanho do creator'),('faixa_etaria_audiencia','Idade'),('genero_audiencia','Gênero'),('localizacao_audiencia','Localização'),('idioma','Idioma'),('duracao_relativa','Duração relativa')]:
    vals=sorted(base[col].dropna().astype(str).unique().tolist())
    chosen=st.sidebar.multiselect(label,vals)
    if chosen: base=base[base[col].astype(str).isin(chosen)]
sponsor=st.sidebar.selectbox('Patrocínio',['Todos','Orgânico','Patrocinado'])
if sponsor=='Orgânico': base=base[~base.patrocinado]
elif sponsor=='Patrocinado': base=base[base.patrocinado]
st.sidebar.caption(f'{len(base):,} posts'.replace(',','.'))
with st.sidebar.expander('Relatórios da entrega'):
    report_dir = Path(__file__).parent / 'reports'
    for report_path in sorted(report_dir.glob('*.html')):
        label = report_path.stem.replace('Relatorio_', '').replace('_', ' ')
        st.download_button(label, data=report_path.read_bytes(), file_name=report_path.name, mime='text/html')

pages=['1 · Mapa executivo','2 · Objetivo por objetivo','3 · Patrocínio','4 · Tempo e mudanças','5 · Audiência','6 · Conteúdo e creators','7 · Cruzamentos livres','8 · Top / bottom','9 · Auditoria','10 · Registros brutos']
page=st.sidebar.radio('Análise',pages)
if base.empty:
    st.error('Nenhum registro atende aos filtros.')
    st.stop()

# ---------- 1 Executive ----------
if page == pages[0]:
    st.subheader('Mapa executivo')
    st.caption('Resultados recalculados conforme os filtros. Rankings orgânicos exploratórios; o período recente corresponde à segunda janela de 12 meses da base.')
    st.write('Comece pelo objetivo. O dashboard não trata “engajamento” como uma única resposta.')
    if platform=='Todas':
        rows=[]
        for p in PLATFORMS:
            d=base[base.plataforma.eq(p)]
            for m in GOALS:
                t=organic_objective_playbook(d,m)
                if t.empty: continue
                r=t.iloc[0]
                rows.append({'Plataforma':p,'Objetivo':GOALS[m],'Melhor aposta orgânica':combo(r),'Vantagem recente (%)':r.vantagem_recente_pct,'Posts':int(r.n)})
        x=pd.DataFrame(rows)
        if x.empty:
            st.info('Amostra insuficiente para comparar combinações orgânicas nos dois períodos. Amplie os filtros.')
            st.stop()
        pivot=x.pivot(index='Plataforma',columns='Objetivo',values='Vantagem recente (%)')
        st.markdown('### Onde cada plataforma apresenta mais sinal')
        fig=px.imshow(pivot,text_auto='.2f',aspect='auto',labels={'color':'Vantagem %'})
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(x,use_container_width=True,hide_index=True)
        st.info('Leitura: alcance tem diferenças muito pequenas em todas as redes; comentários e compartilhamentos apresentam separação maior e, portanto, mais utilidade para decisão editorial.')
    else:
        cols=st.columns(3)
        for i,m in enumerate(GOALS):
            t=organic_objective_playbook(base,m)
            if t.empty: continue
            r=t.iloc[0]
            with cols[i%3]:
                st.markdown(f'**{GOALS[m]}**')
                st.write(combo(r))
                st.metric('Vantagem no período recente',pct(r.vantagem_recente_pct,2))
                st.caption(decision_text(m,r))
        st.markdown('### O que eu faria primeiro')
        share_table=organic_objective_playbook(base,'compartilhamentos')
        comment_table=organic_objective_playbook(base,'comentarios')
        if share_table.empty or comment_table.empty:
            st.info('Amostra insuficiente para uma recomendação orgânica neste recorte. Amplie os filtros.')
            st.stop()
        share=share_table.iloc[0]
        comments=comment_table.iloc[0]
        st.write(f'1. Para compartilhamento, começaria por **{combo(share)}**. 2. Para conversa, começaria por **{combo(comments)}**. 3. Abriria a página de Patrocínio antes de colocar verba, porque o mesmo contexto pode ganhar em um KPI e perder em outro.')

# ---------- 2 Objectives ----------
elif page.startswith('2'):
    st.subheader('Objetivo por objetivo')
    metric=st.selectbox('Qual resultado você quer?',list(GOALS),format_func=lambda m:GOALS[m])
    if platform=='Todas':
        rows=[]
        for p in PLATFORMS:
            d=base[base.plataforma.eq(p)]
            t=organic_objective_playbook(d,metric)
            if t.empty: continue
            r=t.iloc[0]
            rows.append({'Plataforma':p,'Combinação':combo(r),'Resultado recente':metric_text(metric,r.segundos_12m),'Post típico':metric_text(metric,r.resultado_base_recente),'Vantagem %':r.vantagem_recente_pct,'Posts':int(r.n),'Meses acima do padrão %':r.meses_acima_do_padrao_pct})
        tab=pd.DataFrame(rows)
        if tab.empty:
            st.info('Não há amostra suficiente para comparar este objetivo. Amplie os filtros.')
            st.stop()
        tab=tab.sort_values('Vantagem %',ascending=False)
        fig=px.bar(tab,x='Vantagem %',y='Plataforma',orientation='h',text=tab['Vantagem %'].map(lambda x:f'{x:.2f}%'))
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(tab,use_container_width=True,hide_index=True)
    else:
        tab=organic_objective_playbook(base,metric)
        if tab.empty:
            st.info('Não há amostra orgânica suficiente nos dois períodos. Amplie os filtros.')
            st.stop()
        top=tab.head(12).copy()
        top['Combinação']=top.apply(combo,axis=1)
        top['Decisão']=top.apply(lambda r:decision_text(metric,r),axis=1)
        display=top[['Combinação','n','segundos_12m','resultado_base_recente','vantagem_recente_pct','meses_validos','meses_acima_do_padrao_pct','Decisão']].rename(columns={'n':'Posts','segundos_12m':'Resultado recente','resultado_base_recente':'Post típico','vantagem_recente_pct':'Vantagem %','meses_validos':'Meses comparáveis','meses_acima_do_padrao_pct':'Meses acima do padrão %'})
        st.dataframe(display,use_container_width=True,hide_index=True)
        r=tab.iloc[0]
        st.success(f'Primeiro teste recomendado: {combo(r)}. {decision_text(metric,r)}')

# ---------- 3 Sponsorship ----------
elif page.startswith('3'):
    st.subheader('Patrocínio: onde colocar verba e onde parar')
    st.write('A pergunta aqui não é “patrocínio funciona?”. É: **em qual combinação e para qual KPI ele muda o resultado?**')
    metric=st.selectbox('KPI',list(GOALS),format_func=lambda m:GOALS[m])
    if platform=='Todas':
        maps=[]
        for p in PLATFORMS:
            t=sponsorship_decision_map(base[base.plataforma.eq(p)],metric,shortlist=3,n_boot=300)
            if not t.empty:
                t=t.copy(); t['Plataforma']=p; maps.append(t)
        tab=pd.concat(maps,ignore_index=True) if maps else pd.DataFrame()
    else:
        tab=sponsorship_decision_map(base,metric,shortlist=5,n_boot=500)
    if tab.empty:
        st.warning('Nenhuma comparação controlada disponível neste recorte.')
    else:
        tab=tab.copy()
        tab['Combinação']=tab.apply(lambda r:f"{FMT.get(str(r.formato),r.formato)} · {CAT.get(str(r.categoria),r.categoria)} · {r.porte_criador}",axis=1)
        tab['Variação %']=tab['diferenca_relativa_pct']
        positive=tab[tab.evidencia.eq('positivo')].sort_values('Variação %',ascending=False)
        negative=tab[tab.evidencia.eq('negativo')].sort_values('Variação %')
        st.markdown('### 🟢 Onde o pago apresentou resultado maior')
        if positive.empty: st.write('Nenhuma célula com intervalo positivo neste KPI/recorte; não use isso como justificativa para patrocínio genérico.')
        else:
            fig=px.bar(positive,x='Variação %',y='Combinação',orientation='h',text=positive['Variação %'].map(lambda x:f'{x:.2f}%'),hover_data=['n_patrocinado','n_organico'])
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(positive[['Plataforma','Combinação','n_patrocinado','n_organico','resultado_patrocinado','resultado_organico','Variação %']].dropna(axis=1,how='all'),use_container_width=True,hide_index=True)
        st.markdown('### 🔴 Onde o pago apresentou resultado menor')
        if negative.empty: st.write('Nenhuma célula com intervalo negativo neste KPI/recorte.')
        else:
            fig=px.bar(negative,x='Variação %',y='Combinação',orientation='h',text=negative['Variação %'].map(lambda x:f'{x:.2f}%'),hover_data=['n_patrocinado','n_organico'])
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(negative[['Plataforma','Combinação','n_patrocinado','n_organico','resultado_patrocinado','resultado_organico','Variação %']].dropna(axis=1,how='all'),use_container_width=True,hide_index=True)
        st.caption('Comparação exploratória dentro de formato, categoria e porte. Intervalos bootstrap de 95% nas células selecionadas; sem ajuste por múltiplas comparações e sem inferência causal. Performance não é ROI: faltam custo, receita e conversão.')
        with st.expander('Todas as comparações avaliadas e intervalos'):
            st.dataframe(tab, use_container_width=True, hide_index=True)

# ---------- 4 Time ----------
elif page.startswith('4'):
    st.subheader('Tempo: o que mudou e quais janelas merecem teste')
    metric=st.selectbox('Métrica',list(GOALS),format_func=lambda m:GOALS[m])
    ts=time_series(base,metric,'MS')
    fig=px.line(ts,x='data_hora',y='mediana',markers=True,hover_data=['n'],labels={'data_hora':'Mês','mediana':'Resultado típico','n':'Posts'})
    st.plotly_chart(fig,use_container_width=True)
    if platform!='Todas':
        movers=temporal_movers(base,metric)
        if not movers.empty:
            st.markdown('### Ganhando força')
            up=movers.head(8).copy(); up['Combinação']=up.apply(combo,axis=1)
            st.dataframe(up[['Combinação','n','primeiros_12m','segundos_12m','mudanca','vantagem_recente_pct']],use_container_width=True,hide_index=True)
            st.markdown('### Perdendo força')
            down=movers.tail(8).sort_values('mudanca').copy(); down['Combinação']=down.apply(combo,axis=1)
            st.dataframe(down[['Combinação','n','primeiros_12m','segundos_12m','mudanca','vantagem_recente_pct']],use_container_width=True,hide_index=True)
        st.markdown('### Formato × dia × faixa horária')
        tw=best_time_by_format(base,metric,60).head(15).copy()
        if not tw.empty:
            tw['Formato']=tw.formato.map(FMT).fillna(tw.formato.astype(str))
            st.dataframe(tw[['Formato','dia_semana','faixa_horaria','n','mediana','vantagem_pct']],use_container_width=True,hide_index=True)
            st.caption('O horário é o timestamp do dataset; o fuso não está documentado. Use como janela de teste, não como regra definitiva.')
    else:
        st.info('Selecione uma plataforma para ver combinações temporais e estratégias que ganharam/perderam força.')

# ---------- 5 Audience ----------
elif page.startswith('5'):
    st.subheader('Audiência: qual perfil aparece associado a cada comportamento?')
    metric=st.selectbox('Objetivo',list(GOALS),format_func=lambda m:GOALS[m])
    if platform=='Todas':
        rows=[]
        for p in PLATFORMS:
            t=audience_profile_candidates(base[base.plataforma.eq(p)],metric,40)
            if t.empty: continue
            r=t.iloc[0]
            rows.append({'Plataforma':p,'Idade':r.faixa_etaria_audiencia,'Gênero':GENDER.get(str(r.genero_audiencia),str(r.genero_audiencia)),'Localização':r.localizacao_audiencia,'Posts':int(r.n),'Vantagem %':r.vantagem_pct})
        tab=pd.DataFrame(rows)
        if tab.empty:
            st.info('Amostra insuficiente para este perfil de audiência. Amplie os filtros.')
            st.stop()
        st.dataframe(tab.sort_values('Vantagem %',ascending=False),use_container_width=True,hide_index=True)
    else:
        t=audience_profile_candidates(base,metric,40).head(20).copy()
        if t.empty:
            st.info('Amostra insuficiente para este perfil de audiência. Amplie os filtros.')
            st.stop()
        t['Gênero']=t.genero_audiencia.astype(str).map(GENDER).fillna(t.genero_audiencia.astype(str))
        st.dataframe(t[['faixa_etaria_audiencia','Gênero','localizacao_audiencia','n','mediana','vantagem_pct']],use_container_width=True,hide_index=True)
        st.caption('Associação não é causalidade. Use estes perfis para hipóteses de criativo/targeting e valide em campanha.')

# ---------- 6 Content levers ----------
elif page.startswith('6'):
    st.subheader('Conteúdo, creators, duração, hashtags e frequência')
    metric=st.selectbox('Métrica',list(GOALS),format_func=lambda m:GOALS[m])
    col=st.selectbox('Quero comparar',['formato','categoria','porte_criador','duracao_relativa','quantidade_hashtags'],format_func=lambda x:{'quantidade_hashtags':'Quantidade de hashtags',**DIMENSION_LABELS}.get(x,x))
    if col=='quantidade_hashtags':
        t=hashtag_count_profile(base,metric,300)
    else:
        t=group_summary(base,col,metric,60)
    st.dataframe(t,use_container_width=True,hide_index=True)
    if col=='porte_criador':
        st.info('Use follower count como contexto, não como atalho de alcance. Nesta base, aumentar seguidores do creator não produz um ganho consistente de visualizações.')
    if col in ['duracao_relativa','quantidade_hashtags']:
        st.info('As diferenças observadas são pequenas na maior parte dos recortes. Trate esta variável como ajuste fino; priorize formato, categoria, objetivo e contexto de creator.')
    st.markdown('### Volume semanal do ecossistema')
    w=weekly_volume_bands(base,metric)
    st.dataframe(w,use_container_width=True,hide_index=True)
    st.caption('Isto não é frequência de uma conta: a base reúne muitos creators. O uso correto é procurar sinal de saturação do ecossistema; a frequência de uma conta precisa de experimento próprio.')

# ---------- 7 Free combinations ----------
elif page.startswith('7'):
    st.subheader('Cruzamentos livres')
    metric=st.selectbox('Métrica',OBJECTIVE_METRICS,format_func=lambda m:METRICS[m])
    dims=st.multiselect('Dimensões (até 4)',['formato','categoria','porte_criador','patrocinado','faixa_etaria_audiencia','genero_audiencia','localizacao_audiencia','idioma','duracao_relativa','faixa_horaria','dia_semana'],default=['formato','categoria','porte_criador'],max_selections=4)
    min_n=st.slider('Mínimo de posts por célula',20,300,60,10)
    if dims:
        t=combination_analysis(base,dims,metric,min_n=min_n,min_month_n=5,min_months=6)
        st.dataframe(t,use_container_width=True,hide_index=True)
        st.caption('Abra uma combinação e depois use Tempo/Patrocínio para testar se o resultado persiste ou depende de um contexto específico.')

# ---------- 8 Outliers ----------
elif page.startswith('8'):
    st.subheader('Top e bottom performers')
    metric=st.selectbox('Métrica',OBJECTIVE_METRICS,format_func=lambda m:METRICS[m])
    pctcut=st.selectbox('Faixa extrema',[.01,.05],format_func=lambda x:f'{int(x*100)}%')
    top,bottom=top_bottom_rows(base,metric,pctcut)
    c1,c2=st.columns(2)
    with c1:
        st.markdown('### Top')
        st.dataframe(top.head(200),use_container_width=True,hide_index=True)
    with c2:
        st.markdown('### Bottom')
        st.dataframe(bottom.head(200),use_container_width=True,hide_index=True)
    profile=outlier_profile(base,metric,pctcut)
    st.markdown('### O que aparece desproporcionalmente nos extremos')
    st.dataframe(profile.sort_values('indice_top',ascending=False).head(50),use_container_width=True,hide_index=True)

# ---------- 9 Audit ----------
elif page.startswith('9'):
    st.subheader('Auditoria dos dados')
    a=audit_quality(base)
    st.write(f"**Posts:** {a['posts']:,}".replace(',','.'))
    st.write(f"**Creator IDs associados a mais de um nome:** {pct(a['creator_ids_multiplos_nomes_pct'],1)}")
    st.write('Em português: o mesmo código de creator foi reutilizado para pessoas diferentes. Por isso, ele não pode ser usado como identidade histórica confiável.')
    aud=creator_id_audit(base)
    st.dataframe(aud.head(100),use_container_width=True,hide_index=True)
    st.markdown('### Limitações que mudam decisão')
    st.markdown('- O horário não tem timezone confirmado.\n- Duração não tem unidade documentada.\n- Não há custo, receita ou conversão; patrocínio mede performance, não ROI.\n- Creator ID não é uma chave longitudinal confiável.\n- As visualizações variam pouco; diferenças pequenas de ranking não devem ser vendidas como vantagem estratégica.')

# ---------- 10 Raw ----------
else:
    st.subheader('Registros brutos')
    st.write('Use esta página para rastrear qualquer conclusão até os posts que a formaram.')
    st.dataframe(base,use_container_width=True,hide_index=True,height=700)
