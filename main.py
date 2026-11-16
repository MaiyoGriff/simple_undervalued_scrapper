"""
Simple undervalued / up-and-coming stock scanner (Planet Labs-style growth names).

Setup:   pip install yfinance pandas
Run:     python undervalued_scanner.py
         python undervalued_scanner.py PL RKLB ASTS IONQ   (custom tickers)

Output: ranked table in the terminal + scan_results.csv

NOT financial advice. Data comes from Yahoo Finance and can be missing or wrong.
"""
import sys
import pandas as pd
import yfinance as yf

# Starter watchlist: small/mid-cap growth names (space, AI, quantum, fintech, energy)
DEFAULT_TICKERS = [
    "PL", "RKLB", "ASTS", "LUNR", "RDW", "BKSY", "SPIR",
    "IONQ", "RGTI", "SOUN", "PATH", "AI", "S", "DOCN",
    "SOFI", "HOOD", "AFRM", "UPST", "OKLO", "SMR",
    "JOBY", "ACHR", "TEM", "RXRX", "BBAI",
]

FIELDS = {
    "shortName": "name",
    "currentPrice": "price",
    "marketCap": "mkt_cap",
    "priceToSalesTrailing12Months": "ps",
    "enterpriseToRevenue": "ev_rev",
    "forwardPE": "fwd_pe",
    "revenueGrowth": "rev_growth",
    "grossMargins": "gross_margin",
    "fiftyTwoWeekHigh": "high_52w",
    "targetMeanPrice": "target",
    "totalCash": "cash",
    "totalDebt": "debt",
}


def fetch(ticker):
    try:
        info = yf.Ticker(ticker).info
    except Exception as e:
        print(f"  ! {ticker}: {e}")
        return None
    row = {"ticker": ticker}
    for src, dst in FIELDS.items():
        row[dst] = info.get(src)
    return row


def score(df):
    df = df.copy()
    df["drawdown"] = 1 - df["price"] / df["high_52w"]          # % below 52w high
    df["upside"] = df["target"] / df["price"] - 1               # analyst target upside
    df["net_cash"] = df["cash"].fillna(0) - df["debt"].fillna(0)

    # Rank each metric 0-1 (higher = better), then average what's available.
    parts = pd.DataFrame(index=df.index)
    parts["growth"] = df["rev_growth"].rank(pct=True)
    parts["cheap_ev_rev"] = 1 - df["ev_rev"].rank(pct=True)
    parts["cheap_ps"] = 1 - df["ps"].rank(pct=True)
    parts["drawdown"] = df["drawdown"].rank(pct=True)
    parts["upside"] = df["upside"].rank(pct=True)
    parts["margin"] = df["gross_margin"].rank(pct=True)
    df["score"] = parts.mean(axis=1, skipna=True).round(3)
    return df.sort_values("score", ascending=False)


def main():
    tickers = [t.upper() for t in sys.argv[1:]] or DEFAULT_TICKERS
    print(f"Scanning {len(tickers)} tickers...")
    rows = [r for t in tickers if (r := fetch(t))]
    if not rows:
        print("No data returned. Check your internet connection.")
        return

    df = score(pd.DataFrame(rows))

    out = df[["ticker", "name", "price", "mkt_cap", "ev_rev", "ps", "rev_growth",
              "gross_margin", "drawdown", "upside", "score"]].copy()
    out["mkt_cap"] = (out["mkt_cap"] / 1e9).round(2)  # in $B
    for c in ["rev_growth", "gross_margin", "drawdown", "upside"]:
        out[c] = (out[c] * 100).round(1)
    out = out.round(2).rename(columns={
        "mkt_cap": "mcap_$B", "rev_growth": "rev_gr_%", "gross_margin": "gm_%",
        "drawdown": "off_high_%", "upside": "target_up_%",
    })

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(out.to_string(index=False))
    out.to_csv("scan_results.csv", index=False)
    print("\nSaved scan_results.csv")


if __name__ == "__main__":
    main()
