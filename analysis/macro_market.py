"""Exploratory monthly US unemployment and S&P 500 return association."""
import pandas as pd
import matplotlib.pyplot as plt
def fred(s):
    return pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id="+s,index_col=0,parse_dates=True)[s].dropna()
u=fred("UNRATE").resample("MS").last().diff().rename("unemployment_change")
p=fred("SP500").resample("MS").last().pct_change().rename("equity_return")
d=pd.concat([u,p],axis=1).dropna()
# Exclude the current incomplete month.
d=d[d.index<pd.Timestamp.today().to_period("M").start_time]
print(d.corr(),len(d))
d.plot.scatter(x="unemployment_change",y="equity_return")
plt.savefig("macro_scatter.png",dpi=160,bbox_inches="tight")
