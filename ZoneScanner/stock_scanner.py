import os
import pandas as pd
import logging
from typing import List, Optional
from ZoneScanner.zone_detector import DemandZoneScanner
from ZoneScanner.fetch import get_symbol_list
from ZoneScanner.stock_data_manager import StockDataManager

class StockScanner:
    def __init__(self, 
                 cache_dir: str = "parquet_data",
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
        self.data_manager = StockDataManager(base_cache_dir=cache_dir, interval=tf, fresh_only=fresh_only)

    def _get_max_period(self, tf: str) -> str:
        tf_period_map = {
            "1d": "1825d",
            "1wk": "5y",
            "1mo": "15y"
        }
        return tf_period_map.get(tf, "365d")

    def run(self, source_csv: str = "StockList.csv", sectors: Optional[List[str]] = None, symbols: List[str] = None):
        if symbols is None:
            symbols = get_symbol_list(csv_path=source_csv, sectors=sectors)
        print("🚀 Starting demand‑zone scan …")
        logging.info("🚀 Starting demand‑zone scan …")
        
        all_zones = []
        for symbol in symbols:
            try:
                df = self.data_manager._fetch_symbol(symbol)
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
                logging.warning(f"❌ Error with {symbol} [{self.tf}] – {type(e).__name__}: {e}")

        if all_zones:
            result_df = pd.DataFrame(all_zones)
            if not result_df.empty and "Score" in result_df.columns:
                result_df = result_df.sort_values(by="Score", ascending=False)
            output_file = f"demand_zones_{self.tf}.csv"
            result_df.to_csv(output_file, index=False)
            self.zones = result_df.to_dict(orient="records")
            print(f"\n📁 Saved to: {output_file}")
            logging.info(f"📁 Saved demand zones to: {output_file}")
        else:
            print("🚫 No valid demand zones detected.")
            logging.info("🚫 No valid demand zones detected.")
