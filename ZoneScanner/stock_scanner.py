import os
import pandas as pd
import yfinance as yf
import logging
from typing import List, Optional
from datetime import datetime
from ZoneScanner.zone_detector import DemandZoneScanner
from ZoneScanner.fetch import get_symbol_list

class StockScanner:
    def __init__(self, 
                 cache_dir: str = "csv_data",
                 tf: str = "1d",
                 fresh_only: bool = True,
                 plot: bool = False):
        self.cache_dir = cache_dir
        self.fresh_only = fresh_only
        self.plot = plot
        self.tf = tf
        self.period = self._get_max_period(tf)
        self.zones = []
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_max_period(self, tf: str) -> str:
        tf_period_map = {
            "1d": "1825d",
            "1wk": "5y",
            "1mo": "15y"
        }
        return tf_period_map.get(tf, "365d")

    def _load_or_download_data(self, symbol: str, tf: str, period: str) -> pd.DataFrame:
        filename = f"{symbol}_{tf}.csv"
        filepath = os.path.join(self.cache_dir, filename)

        if not self.fresh_only and os.path.exists(filepath):
            print(f"💾 Cached CSV → {filepath}")
            df = pd.read_csv(filepath, index_col="Date", parse_dates=True)
        else:
            print(f"🌐 Downloading {symbol} ({tf}, {period}) from yfinance …")
            df = yf.download(
                symbol, period=period, interval=tf, auto_adjust=False, progress=False
            )
            if df.empty:
                print(f"⚠️ No data for {symbol}")
                logging.warning(f"No data for {symbol}")
                return pd.DataFrame()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join([str(c) for c in tup if c]) for tup in df.columns]

            df.index.name = "Date"
            df["Date"] = df.index
            df.to_csv(filepath, index_label="Date")

        df = df.loc[:, ~df.columns.duplicated()]
        suffix = f"_{symbol}"
        rename_map = {
            f"Open{suffix}": "Open", f"High{suffix}": "High",
            f"Low{suffix}": "Low", f"Close{suffix}": "Close",
            f"Volume{suffix}": "Volume"
        }
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        df["Date"] = df.index
        return df

    def run(self, source_csv: str = "StockList.csv", sectors: Optional[List[str]] = None, symbols: List[str] = None):
        if symbols is None:
            symbols = get_symbol_list(csv_path=source_csv, sectors=sectors)
        print("🚀 Starting demand‑zone scan …")
        logging.info("Starting demand‑zone scan …")

        all_zones = []
        for symbol in symbols:
            try:
                df = self._load_or_download_data(symbol, self.tf, self.period)
                if df.empty:
                    continue

                scanner = DemandZoneScanner(
                    symbols=[symbol],
                    timeframes={self.tf: self.period},
                    fresh_only=self.fresh_only,
                    plot=self.plot,
                    local_csv_dir=self.cache_dir
                )
                zones_df = scanner.run()
                zones = zones_df.to_dict(orient="records") if not zones_df.empty else []

                all_zones.extend(zones)

            except Exception as e:
                print(f"❌ Error with {symbol} [{self.tf}] – {type(e).__name__}: {e}")
                logging.warning(f"Error with {symbol} [{self.tf}] – {type(e).__name__}: {e}")

        if all_zones:
            result_df = pd.DataFrame(all_zones)
            if not result_df.empty and "Score" in result_df.columns:
                result_df = result_df.sort_values(by="Score", ascending=False)
            output_file = f"demand_zones_{self.tf}.csv"
            result_df.to_csv(output_file, index=False)
            self.zones = result_df.to_dict(orient="records")
            print(f"\n📁 Saved to: {output_file}")
            logging.info(f"Saved demand zones to: {output_file}")
        else:
            print("🚫 No valid demand zones detected.")
            logging.info("No valid demand zones detected.")