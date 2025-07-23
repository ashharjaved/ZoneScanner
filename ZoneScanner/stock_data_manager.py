# stock_data_manager.py

import os
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from ZoneScanner.yahooquery_fetcher import YahooQueryFetcher

class StockDataManager:
    def __init__(self, base_cache_dir="parquet_data", interval="1d", fresh_only=False, max_workers=5):
        self.base_cache_dir = base_cache_dir
        self.interval = interval
        self.fresh_only = fresh_only
        self.max_workers = max_workers
        self.fetcher = YahooQueryFetcher(interval=interval)

    def _get_cache_path(self, symbol: str) -> str:
        folder = os.path.join(self.base_cache_dir, self.interval)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{symbol}.parquet")

    def _load_parquet_cache(self, filepath: str) -> pd.DataFrame:
        try:
            if os.path.exists(filepath):
                df = pd.read_parquet(filepath)
                return df
        except Exception as e:
            logging.warning(f"❌ Failed to read cache: {filepath} — {e}")
        return pd.DataFrame()

    def _save_parquet_cache(self, df: pd.DataFrame, filepath: str):
        try:
            df.to_parquet(filepath)
        except Exception as e:
            logging.error(f"❌ Failed to write cache: {filepath} — {e}")

    def _fetch_symbol(self, symbol: str) -> pd.DataFrame:
        try:            
            filepath = self._get_cache_path(symbol)
            df_old = self._load_parquet_cache(filepath) if not self.fresh_only else pd.DataFrame()
            start_date = df_old.index.max().strftime('%Y-%m-%d') if not df_old.empty else None
    
            print(f"🌐 Fetching {symbol} from {start_date or 'start'}...")
            df_new = self.fetcher.fetch(symbol, start_date=start_date)
    
            if df_new.empty and df_old.empty:
                print(f"⚠️ No data for {symbol}")
                return pd.DataFrame()
    
            df_new.index.name = "Date"
            df_new["Date"] = df_new.index
    
            df_combined = pd.concat([df_old, df_new])
            df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
            df_combined.sort_index(inplace=True)
    
            self._save_parquet_cache(df_combined, filepath)
            print(f"✅ Cached: {filepath} — Last: {df_combined.index.max().date()}")
        except Exception as e:
            logging.error(e)
        return df_combined

    def fetch_batch(self, symbols: list[str]) -> dict[str, pd.DataFrame]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._fetch_symbol, symbol): symbol for symbol in symbols}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    df = future.result()
                    if not df.empty:
                        results[symbol] = df
                except Exception as e:
                    logging.error(f"❌ Error fetching {symbol}: {e}")
        return results

    def clear_cache(self, symbol: str = None):
        folder = os.path.join(self.base_cache_dir, self.interval)
        if symbol:
            file_path = os.path.join(folder, f"{symbol}.parquet")
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Deleted cache for {symbol}")
        else:
            for fname in os.listdir(folder):
                if fname.endswith(".parquet"):
                    os.remove(os.path.join(folder, fname))
            print(f"🗑️ Cleared all cache in {folder}")

    def list_cached_symbols(self) -> list[str]:
        folder = os.path.join(self.base_cache_dir, self.interval)
        if not os.path.exists(folder):
            return []
        return [f[:-8] for f in os.listdir(folder) if f.endswith(".parquet")]