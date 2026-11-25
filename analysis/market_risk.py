import pandas as pd
import numpy as np
url = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
df = pd.read_csv(url).sort_values("Date")
p = df["AAPL.Adjusted"]
r = p.pct_change().dropna()
print("Observations", len(p))
print("Total return", p.iloc[-1]/p.iloc[0]-1)
print("Annualized volatility", r.std()*np.sqrt(252))
print("Maximum drawdown", (p/p.cummax()-1).min())
