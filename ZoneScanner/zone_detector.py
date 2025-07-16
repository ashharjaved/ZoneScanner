import pandas as pd
from datetime import datetime
import os
import plotly.graph_objects as go

def to_float(x):
    try:
        if hasattr(x, "item"):
            return float(x.item())
        elif isinstance(x, pd.Series):
            return float(x.iloc[0] if x.notna().any() else 0.0)
        return float(x)
    except Exception:
        return 0.0

def to_scalar(val):
    return val.iloc[0] if isinstance(val, pd.Series) else val

def is_strong_bullish(candle) -> bool:
    return (
        to_float(candle['Close']) > to_float(candle['Open']) and
        abs(to_float(candle['Close']) - to_float(candle['Open'])) >= 0.5 * (to_float(candle['High']) - to_float(candle['Low']))
    )

def is_base_candle(candle) -> bool:
    return (
        abs(to_scalar(candle['Close']) - to_scalar(candle['Open'])) < 0.5 * (to_scalar(candle['High']) - to_scalar(candle['Low'])) and
        (to_scalar(candle['High']) - to_scalar(candle['Low'])) > 0
    )

def detect_zones(df: pd.DataFrame, tf: str, symbol: str, fresh_only: bool = True, min_base: int = 1, max_base: int = 3, distance_range=(1.0, 5.0)) -> list[dict]:
    zones = []
    df = df.copy()
    df.index = pd.to_datetime(df.index)

    if "Date" not in df.columns:
        df["Date"] = df.index

    tf_label_map = {"1mo": "Month", "1wk": "Week", "1d": "Day"}
    label = tf_label_map.get(tf, "Month")
    time_fmt = {"Month": "%Y-%m", "Week": "%m-%d", "Day": "%Y-%m-%d"}[label]

    for i in range(3, len(df) - 4):
        leg_in = df.iloc[i - 1]

        for base_len in range(max_base, min_base - 1, -1):
            if i + base_len + 1 >= len(df):
                continue

            base = df.iloc[i:i + base_len]
            if not all(is_base_candle(row) for _, row in base.iterrows()):
                continue

            leg_out_candle = df.iloc[i + base_len]
            if not is_strong_bullish(leg_in) or not is_strong_bullish(leg_out_candle):
                continue

            future = df.iloc[i + base_len + 1:]
            fresh = True
            if not future.empty and "Low" in future.columns:
                fresh_vals = (future["Low"] <= to_float(base["Close"].max()))
                fresh = not bool(fresh_vals.any().item())
            if fresh_only and not fresh:
                continue

            base_vol = to_float(base["Volume"].mean())
            leg_out_vol = to_float(leg_out_candle["Volume"])
            vol_spike = leg_out_vol > 1.5 * base_vol if base_vol > 0 else False

            leg_in_strength = abs(to_float(leg_in["Close"]) - to_float(leg_in["Open"]))
            leg_out_strength = to_float(leg_out_candle["Close"]) - to_float(leg_out_candle["Open"])
            score = (2 if fresh else 1) + (2 if leg_out_strength > 2 * leg_in_strength else 1) + (1 if vol_spike else 0)
            if score < 3:
                continue

            start_date = to_scalar(base["Date"].iloc[0])
            cmp = to_float(df["Close"].iloc[-1])
            proximal = to_float(base["Close"].max())
            distal = to_float(base["Low"].min())
            distance_pct = round(((cmp - proximal) / cmp) * 100, 2)

            if distance_pct < distance_range[0] or distance_pct > distance_range[1]:
                continue

            zones.append({
                "Symbol": symbol,
                "Timeframe": tf,
                "Start": start_date.strftime("%Y-%m-%d"),
                "Proximal": round(proximal, 2),
                "Distal": round(distal, 2),
                "Score": score,
                "Fresh": fresh,
                "Legout Strength": round(leg_out_strength, 2),
                "Base Count": base_len,
                f"Base {label}": ", ".join(to_scalar(row["Date"]).strftime(time_fmt) for _, row in base.iterrows()),
                f"Leg-in {label}": to_scalar(leg_in["Date"]).strftime(time_fmt),
                f"Leg-out {label}": to_scalar(leg_out_candle["Date"]).strftime(time_fmt),
                "Zone Type": "MIT" if tf == "1mo" else "WIT",
                "Distance": distance_pct
            })

    return zones

class DemandZoneScanner:
    def __init__(self, symbols, timeframes, fresh_only=True, plot=False, local_csv_dir="csv_data"):
        self.symbols = symbols
        self.timeframes = timeframes
        self.fresh_only = fresh_only
        self.plot = plot
        self.local_csv_dir = local_csv_dir

    def run(self):
        all_zones = []
        for tf, period in self.timeframes.items():
            for symbol in self.symbols:
                try:
                    filepath = os.path.join(self.local_csv_dir, f"{symbol}_{tf}.csv")
                    if not os.path.exists(filepath):
                        print(f"⚠️ Cached file not found: {filepath}")
                        continue

                    df = pd.read_csv(filepath, index_col="Date", parse_dates=True)
                    df = df.loc[:, ~df.columns.duplicated()]

                    suffix = f"_{symbol}"
                    rename_map = {
                        f"Open{suffix}": "Open",
                        f"High{suffix}": "High",
                        f"Low{suffix}": "Low",
                        f"Close{suffix}": "Close",
                        f"Volume{suffix}": "Volume"
                    }
                    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

                    for col in df.columns:
                        if any(x in col for x in ["Open", "High", "Low", "Close", "Volume"]):
                            df[col] = pd.to_numeric(df[col], errors="coerce")

                    df.dropna(subset=[col for col in ["Open", "High", "Low", "Close"] if col in df.columns], inplace=True)
                    df.index.name = "Date"
                    df["Date"] = df.index

                    zones = detect_zones(df, tf, symbol, self.fresh_only)
                    all_zones.extend(zones)

                except Exception as e:
                    print(f"❌ Error with {symbol} [{tf}] – {type(e).__name__}: {e}")

        return pd.DataFrame(all_zones)
        
    def plot_zone(self, df, zone, output_folder="plots", buffer=1.0):
        symbol = zone["Symbol"].replace(".NS", "")
        start_date = pd.to_datetime(zone["Start"])
        tf = zone["Timeframe"]

        window = df.loc[start_date - pd.DateOffset(months=5): start_date + pd.DateOffset(months=10)].copy()
        if window.empty:
            print(f"⚠️ No window data for {symbol} @ {start_date}")
            return

        entry = zone["Proximal"]
        stop = zone["Distal"] - buffer
        zone_color = "rgba(0,200,100,0.2)" if tf == "1mo" else "rgba(0,100,255,0.2)"

        fig = go.Figure(data=[
            go.Candlestick(
                x=window.index,
                open=window["Open"],
                high=window["High"],
                low=window["Low"],
                close=window["Close"],
                name="Price"
            ),
            go.Scatter(
                x=[window.index[0], window.index[-1]],
                y=[entry, entry],
                mode="lines",
                name="Entry",
                line=dict(color="blue", dash="dot")
            ),
            go.Scatter(
                x=[window.index[0], window.index[-1]],
                y=[stop, stop],
                mode="lines",
                name="Stop-Loss",
                line=dict(color="red", dash="dash")
            )
        ])

        fig.add_shape(
            type="rect",
            x0=window.index[0],
            x1=window.index[-1],
            y0=zone["Distal"],
            y1=zone["Proximal"],
            fillcolor=zone_color,
            line=dict(color="green", width=1),
            layer="below"
        )

        fig.update_layout(
            title=f"{symbol} | Demand Zone from {zone['Start']} ({tf})",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            height=600
        )

        os.makedirs(output_folder, exist_ok=True)
        filename = f"{symbol}_{tf}_{zone['Start']}_Score{zone['Score']}.html".replace(" ", "_")
        fig.write_html(os.path.join(output_folder, filename))
        print(f"📈 Saved Plot: {filename}")