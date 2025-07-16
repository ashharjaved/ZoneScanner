import pandas as pd
import argparse
from typing import List, Optional
from stockfetcher.fetcher import StockFetcher
import os
import logging

def fetch_stocks(limit: int = 5, sectors: Optional[List[str]] = None) -> pd.DataFrame:
    csv_file = 'StockList.csv'

    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        fetcher = StockFetcher(sectors=sectors, exchange='nse')
        df = fetcher.collect_data(nse_limit=None, mode='shariah')
        required_columns = [
            'SYMBOL', 'SERIES', 'DATE OF LISTING', 'ISIN NUMBER', 'FACE VALUE',
            'YahooSymbol', 'Symbol', 'Company', 'Sector', 'Industry'
        ]
        for col in required_columns:
            if col not in df.columns:
                df[col] = 'N/A'
        df = df[required_columns]
        df.to_csv(csv_file, index=False)
        print(f"Saved stock list to {csv_file}")
        logging.info(f"✅ Saved stock list to {csv_file}")

    if sectors is not None:
        df = df[df['Sector'].isin(sectors)]

    return df.head(limit)[['YahooSymbol']]

def get_symbol_list(csv_path: str = "StockList.csv", sectors: Optional[List[str]] = None) -> List[str]:
    try:
        df = fetch_stocks(limit=None, sectors=sectors)
        return df['YahooSymbol'].dropna().astype(str).tolist()
    except Exception as e:
        logging.warning(f"Failed to fetch symbols: {e}. Using hardcoded symbols.")
        return ["RELIANCE.NS", "ITC.NS"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch stock symbols")
    parser.add_argument("--limit", type=int, default=5, help="Limit the number of symbols")
    parser.add_argument("--sector", type=str, action="append", help="Filter by sector(s)")
    args = parser.parse_args()
    result = fetch_stocks(args.limit, args.sector)
    print(result)
