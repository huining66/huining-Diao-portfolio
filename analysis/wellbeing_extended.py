import json, pathlib, urllib.request
import numpy as np
import pandas as pd
import statsmodels.api as sm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'data/wellbeing';out.mkdir(parents=True,exist_ok=True)
def fetch(url):
    with urllib.request.urlopen(url,timeout=90) as f:return json.load(f)
a=pd.read_csv(root/'matched-data.csv')
url='https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.PP.KD?date=2023&format=json&per_page=400'
raw=fetch(url)
g={d['countryiso3code']:d['value'] for d in raw[1] if d['value'] is not None and d['value']>0}
a['gdp_ppp']=a.Code.map(g)
b=a.dropna(subset=['gdp_ppp']).copy()
assert len(b)>=80
def model(d,controls):
    X=pd.DataFrame({'hours100':d.hours/100},index=d.index)
    if controls:
        X['log_gdp']=np.log(d.gdp_ppp)
        X=pd.concat([X,pd.get_dummies(d.region,drop_first=True,dtype=float)],axis=1)
    fit=sm.OLS(d.score,sm.add_constant(X)).fit(cov_type='HC3',use_t=True)
    ci=fit.conf_int().loc['hours100']
    return dict(n=int(fit.nobs),slope=float(fit.params.hours100),lo=float(ci.iloc[0]),hi=float(ci.iloc[1]),r2=float(fit.rsquared))
models={'full_unadjusted':model(a,False),'matched_unadjusted':model(b,False),'matched_adjusted':model(b,True)}
geo=fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
features=[]
for f in geo['features']:
    p=f['properties'];code=p.get('ISO3166-1-Alpha-3',p.get('ISO_A3'))
    if code and code!='-99':
        features.append({'type':'Feature','properties':{'code':code},'geometry':f['geometry']})
assert len(features)>100
(out/'countries.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')))
(out/'models.json').write_text(json.dumps({'models':models,'source':url,'excluded':a.loc[a.gdp_ppp.isna(),'Entity'].tolist()},indent=2))
b.to_csv(out/'matched-gdp.csv',index=False)
styles=getSampleStyleSheet()
story=[Paragraph('Working Hours &amp; Global Well-being',styles['Title']),Paragraph('Cross-country econometric research | Huining Diao | 2023 observations',styles['Normal']),Spacer(1,18),Paragraph('Executive summary',styles['Heading2']),Paragraph('The archived sample contains 120 observations. The models below compare the full sample with the GDP-matched subset and a specification controlling for log GDP per capita (PPP, constant international dollars) and broad region indicators. All intervals use HC3 robust standard errors.',styles['BodyText']),Spacer(1,12)]
rows=[['Model','N','Slope / 100h','95% CI','R squared']]
for k,v in models.items():rows.append([k.replace('_',' '),str(v['n']),f"{v['slope']:.3f}",f"{v['lo']:.3f} to {v['hi']:.3f}",f"{v['r2']:.3f}"])
t=Table(rows,colWidths=[145,35,85,125,65]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#14283e')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
story.extend([t,Spacer(1,16),Paragraph('Interpretation and limitations',styles['Heading2']),Paragraph('These estimates describe associations, not causal effects. Missing GDP observations change the sample. National averages cannot establish individual effects; omitted variables and spatial dependence remain possible. Countries receive equal weight.',styles['BodyText']),Paragraph('Sources and reproducibility',styles['Heading2']),Paragraph('Our World in Data: annual working hours and Cantril ladder life satisfaction. World Bank: NY.GDP.PCAP.PP.KD, 2023. The portfolio provides the archived CSV, GDP-matched CSV and Python scripts. AI assisted with analysis implementation and presentation.',styles['BodyText'])])
SimpleDocTemplate(str(out/'report.pdf'),pagesize=letter).build(story)
print(models)
