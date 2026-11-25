"""Download, validate and summarize historical Apple equity prices."""
import json
import pandas as pd
import numpy as np
from pathlib import Path

URL = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"

def main():
    df = pd.read_csv(URL, parse_dates=["Date"]).sort_values("Date")
    if df.empty or not df.Date.is_unique or df["AAPL.Adjusted"].isna().any() or not (df["AAPL.Adjusted"] > 0).all():
        raise ValueError("Historical price input failed validation")
    df["daily_return"] = df["AAPL.Adjusted"].pct_change()
    df["drawdown"] = df["AAPL.Adjusted"] / df["AAPL.Adjusted"].cummax() - 1
    out = Path("output"); out.mkdir(exist_ok=True)
    df.to_csv(out / "prices.csv", index=False)
    df.groupby(df.Date.dt.to_period("M")).agg(
        close=("AAPL.Adjusted", "last"),
        volatility=("daily_return", "std")
    ).to_csv(out / "monthly.csv")
    summary = {
        "observations": len(df),
        "start_date": str(df.Date.min().date()),
        "end_date": str(df.Date.max().date()),
        "total_return": float(df["AAPL.Adjusted"].iloc[-1]/df["AAPL.Adjusted"].iloc[0]-1),
        "annualized_volatility": float(df.daily_return.std() * np.sqrt(252)),
        "maximum_drawdown": float(df.drawdown.min()),
        "monthly_rows": int(df.Date.dt.to_period("M").nunique()),
        "source": URL
    }
    (out / "pipeline_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
