from pathlib import Path
import sys,json
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from streamlit.testing.v1 import AppTest
from analysis_engine import load_data,combination_analysis,top_bottom_rows
D=load_data(root/'data/social_media_dataset.csv');print('Dates',D.data_hora.min(),D.data_hora.max(),flush=True)
for dims in [['formato','patrocinado'],['formato','categoria','idioma','dia_semana']]:
 t=combination_analysis(D,dims);print('Cross',dims,len(t),flush=True)
for metric in ['taxa_curtidas','taxa_comentarios','taxa_compartilhamentos']:
 a,b=top_bottom_rows(D,metric);assert len(a)>0
at=AppTest.from_file(str(root/'app.py'),default_timeout=120).run()
for platform in ['Todas', 'Instagram']:
 at.sidebar.selectbox[0].select(platform).run()
 for page in at.sidebar.radio[0].options:
  at.sidebar.radio[0].set_value(page).run()
  assert not at.exception, [e.message for e in at.exception]
at.sidebar.selectbox[0].select('Todas').run()
lo=D.data_hora.min().date()
at.sidebar.date_input[0].set_value((lo,lo)).run()
print('Small sample caption',[c.value for c in at.sidebar.caption],flush=True)
results=[]
for page in at.sidebar.radio[0].options:
 at.sidebar.radio[0].set_value(page).run();e=[x.message for x in at.exception];print('Small',page,e,flush=True);results.append(e)
at.sidebar.date_input[0].set_value((lo,D.data_hora.max().date())).run()
at.sidebar.selectbox[1].select('Patrocinado').run()
for page in at.sidebar.radio[0].options[:3]:
 at.sidebar.radio[0].set_value(page).run();e=[x.message for x in at.exception];print('Sponsored only',page,e,flush=True);results.append(e)
assert not any(results)
print('EDGE TESTS PASSED',flush=True)
