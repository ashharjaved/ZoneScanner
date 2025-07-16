import argparse
import os
import sys
import logging
import io
from datetime import datetime
from ZoneScanner.stock_scanner import StockScanner
from ZoneScanner.fetch import get_symbol_list

# Example
# demandzone --tf 1wk --symbol NH.NS --limit 5 --fresh --distance-range 1 5 --min-base 1 --max-base 3
# demandzone --tf 1wk --limit 5 --fresh --distance-range 1 5 --min-base 1 --max-base 3

LOG_DIR = "logs"
LOG_RETENTION_DAYS = 7

def setup_logging():
    # 💡 Force stdout/stderr to use UTF-8 and avoid UnicodeEncodeError
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now()

    # Delete old log files
    for f in os.listdir(LOG_DIR):
        path = os.path.join(LOG_DIR, f)
        if os.path.isfile(path):
            mod_time = datetime.fromtimestamp(os.path.getmtime(path))
            if (now - mod_time).days > LOG_RETENTION_DAYS:
                os.remove(path)

    log_path = os.path.join(LOG_DIR, f"scanner_{now.strftime('%Y%m%d_%H%M%S')}.log")

    # Reset logging (important if previous logging was already configured)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # File handler (UTF-8 safe)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    # Console handler (safe with replacement)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

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
    
    all_zones = []
    for tf in args.tf:
        scanner = StockScanner(
            tf=tf,
            fresh_only=args.no_cache,
            plot=args.plot,
        )
        scanner.run(
            source_csv="StockList.csv" if not args.symbol else None,
            sectors=args.sector,
            symbols=symbols
        )
        if scanner.zones:
            logging.info(f"Zones found in tf={tf}: {len(scanner.zones)}")
            all_zones.extend(scanner.zones)
        else:
            logging.info(f"⚠️ No zones found in tf={tf}")

    # Final summary log
    logging.info("\n================ SUMMARY ================")
    total_zones = 0
    for zone in all_zones:
        logging.info(f"{zone['Symbol']} | {zone['Timeframe']} | Score: {zone['Score']} | Zone: {zone['Entry']} - {zone['Stop Loss']} | Start: {zone['Start']}")
        total_zones += 1
    if total_zones == 0:
        logging.info("⚠️ No valid zones detected.")
    else:
        logging.info(f"🎯 Total zones detected: {total_zones}")
    logging.info("========================================")      
    
if __name__ == "__main__":
    main()