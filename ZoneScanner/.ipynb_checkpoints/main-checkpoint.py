import argparse
import os
import sys
import logging
from datetime import datetime
from ZoneScanner.stock_scanner import StockScanner
from ZoneScanner.fetch import get_symbol_list

LOG_DIR = "logs"
LOG_RETENTION_DAYS = 7

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now()
    for f in os.listdir(LOG_DIR):
        path = os.path.join(LOG_DIR, f)
        if os.path.isfile(path):
            mod_time = datetime.fromtimestamp(os.path.getmtime(path))
            if (now - mod_time).days > LOG_RETENTION_DAYS:
                os.remove(path)
    log_path = os.path.join(LOG_DIR, f"scanner_{now.strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"📋 Logging to: {log_path}")
    return log_path

def main():
    parser = argparse.ArgumentParser(description="Demand Zone Screener")
    parser.add_argument("--tf", nargs="+", default=["1mo", "1wk", "1d"], help="Timeframes to scan")
    parser.add_argument("--plot", action="store_true", help="Enable chart plotting")
    parser.add_argument("--fresh", action="store_true", help="Only include fresh zones")
    parser.add_argument("--symbol", type=str, help="Run for a single symbol only (e.g., TCS.NS)")
    parser.add_argument("--distance-range", nargs=2, type=float, default=[1.0, 5.0], help="Valid zone distance percentage (e.g., 1 5)")
    parser.add_argument("--min-base", type=int, default=1, help="Minimum base candle count")
    parser.add_argument("--max-base", type=int, default=3, help="Maximum base candle count")
    parser.add_argument("--sector", nargs="+", help="Filter by one or more sectors in StockList.csv (e.g., IT Energy)")
    parser.add_argument("--limit", type=int, help="Max number of symbols to scan")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh OHLC data download, ignore CSV cache")

    args = parser.parse_args()
    setup_logging()

    if args.symbol:
        symbols = [args.symbol]
    else:
        symbols = get_symbol_list(csv_path="StockList.csv", sectors=args.sector)
        if args.limit:
            symbols = symbols[:args.limit]

    for tf in args.tf:
        scanner = StockScanner(
            tf=tf,
            fresh_only=args.fresh,
            plot=args.plot,
            force_refresh=args.no_cache
        )
        scanner.run(
            source_csv="StockList.csv" if not args.symbol else None,
            sectors=args.sector,
            symbols=symbols
        )
        
    # Final summary log
    logging.info("\n================ SUMMARY ================")
    total_zones = 0
    for df in all_zones:
        for _, row in df.iterrows():
            logging.info(f"✅ {row['Symbol']} | {row['Timeframe']} | Score: {row['Score']} | Zone: {row['Proximal']} - {row['Distal']} | Start: {row['Start']}")
            total_zones += 1
    if total_zones == 0:
        logging.info("⚠️ No valid zones detected.")
    else:
        logging.info(f"🎯 Total zones detected: {total_zones}")
    logging.info("========================================")
    
if __name__ == "__main__":
    main()
