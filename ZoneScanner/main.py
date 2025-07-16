import argparse
import os
import sys
import logging
from datetime import datetime
from ZoneScanner.stock_scanner import StockScanner
from ZoneScanner.fetch import get_symbol_list

# Example
# demandzone --tf 1wk --symbol NH.NS --limit 5 --fresh --distance-range 1 5 --min-base 1 --max-base 3
# demandzone --tf 1wk --limit 5 --fresh --distance-range 1 5 --min-base 1 --max-base 3

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
    if args.symbol:
        symbols = [args.symbol]
    else:
        symbols = get_symbol_list(csv_path="StockList.csv", sectors=args.sector)
        if args.limit:
            symbols = symbols[:args.limit]

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
        
    
if __name__ == "__main__":
    main()