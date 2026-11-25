"""Download, validate and summarize historical AAPL data."""
import pandas as pd
from pathlib import Path
URL="https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
def main():
    df=pd.read_csv(URL,parse_dates=["Date"]).sort_values("Date")
    assert df.Date.is_unique and df["AAPL.Adjusted"].notna().all()
    assert (df["AAPL.Adjusted"]>0).all()
    df["daily_return"]=df["AAPL.Adjusted"].pct_change()
    df["drawdown"]=df["AAPL.Adjusted"]/df["AAPL.Adjusted"].cummax()-1
    out=Path("output");out.mkdir(exist_ok=True)
    df.to_csv(out/"prices.csv",index=False)
    df.groupby(df.Date.dt.to_period("M")).agg(close=("AAPL.Adjusted","last"),volatility=("daily_return","std")).to_csv(out/"monthly.csv")
if __name__=="__main__": main()
