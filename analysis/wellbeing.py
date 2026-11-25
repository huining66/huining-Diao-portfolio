"""Reproduce portfolio statistics from the archived matched CSV; no network required."""
import csv, statistics as st, math
from pathlib import Path
rows=list(csv.DictReader((Path(__file__).resolve().parents[1]/"matched-data.csv").open()))
assert len(rows)==120 and len({r["Code"] for r in rows})==120
x=[float(r["hours"]) for r in rows]
y=[float(r["score"]) for r in rows]
assert all(r["Year"]=="2023" for r in rows)
assert all(h>0 and 0<=s<=10 for h,s in zip(x,y))
def fit(x,y):
    b=st.covariance(x,y)/st.variance(x)
    r=st.correlation(x,y)
    se=math.sqrt(sum((v-st.mean(y)-b*(u-st.mean(x)))**2 for u,v in zip(x,y))/(len(x)-2)/sum((u-st.mean(x))**2 for u in x))
    return b*100,r,((b-1.98*se)*100,(b+1.98*se)*100)
def ranks(x):
    return [1+sum(v<u for v in x)+(sum(v==u for v in x)-1)/2 for u in x]
b,r,ci=fit(x,y)
groups={g:[i for i,row in enumerate(rows) if row["region"]==g] for g in sorted({r["region"] for r in rows})}
dx=x.copy();dy=y.copy()
for g,idx in groups.items():
    mx=st.mean(x[i] for i in idx);my=st.mean(y[i] for i in idx)
    print(g,len(idx),round(mx,2),round(my,3))
    for i in idx: dx[i]-=mx;dy[i]-=my
within=st.covariance(dx,dy)/st.variance(dx)*100
rho=st.correlation(ranks(x),ranks(y))
print("OLS slope per 100 hours",b,"Pearson",r,"R squared",r*r,"95% classical CI",ci,"Spearman",rho,"Region FE slope",within)
assert abs(r+0.4762407074)<1e-8
assert abs(b+0.1718735583)<1e-8
assert abs(rho+0.5114782675)<1e-8
assert abs(within+0.0678901297)<1e-8

# HC3 sandwich standard error for the simple regression slope.
z=[u/100-st.mean(x)/100 for u in x]
ss=sum(u*u for u in z)
e=[v-st.mean(y)-b*u for u,v in zip(z,y)]
lev=[1/len(z)+u*u/ss for u in z]
hc3=math.sqrt(sum(u*u*v*v/(1-h)**2 for u,v,h in zip(z,e,lev)))/ss
print("HC3 SE",hc3,"approximate 95% CI",(b-1.98*hc3,b+1.98*hc3),"max leverage",max(lev))
