# yahooquery_fetcher.py

import pandas as pd
from yahooquery import Ticker
import logging

class YahooQueryFetcher:
    def __init__(self, interval="1d"):
        self.interval = interval

    def fetch(self, symbol: str, start_date=None, end_date=None) -> pd.DataFrame:
        try:
            t = Ticker(symbol)
            df = t.history(start=start_date, end=end_date, interval=self.interval)

            if isinstance(df, pd.DataFrame) and not df.empty:
                if isinstance(df.index, pd.MultiIndex):
                    df = df.reset_index()
                elif 'date' in df.columns:
                    df = df.rename(columns={"date": "Date"})
            
                if 'Date' not in df.columns and df.index.name == "Date":
                    df.reset_index(inplace=True)
            
                if 'Date' not in df.columns:
                    df['Date'] = df.index  # fallback if date is still the index
            
                df['Date'] = pd.to_datetime(df['Date'])  # ensure datetime format
                df.set_index("Date", inplace=True)

                # Normalize OHLC column names
                df.columns = [col.capitalize() if col.lower() in {"open", "high", "low", "close", "volume"} else col for col in df.columns]
                # Final OHLC check
                required_cols = {"Open", "High", "Low", "Close", "Volume"}
                if not required_cols.issubset(df.columns):
                    logging.error(f"❌ Fetched data for {symbol} missing required OHLC columns: {set(df.columns)}")
                    return pd.DataFrame()

                return df
            else:
                logging.warning(f"No data fetched for {symbol}")
                return pd.DataFrame()

        except Exception as e:
            logging.error(f"YahooQuery fetch error for {symbol}: {e}")
            return pd.DataFrame()
