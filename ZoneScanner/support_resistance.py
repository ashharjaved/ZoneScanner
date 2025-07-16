# support_resistance.py

def detect_support_resistance(df, swing=2, tolerance=0.015, min_touches=2):
    """
    Detects support and resistance levels using swing high/low logic.
    Returns a dictionary with 'Support' and 'Resistance' levels.
    """
    support = []
    resistance = []

    for i in range(swing, len(df) - swing):
        high = df['High'].iloc[i]
        low = df['Low'].iloc[i]

        # Detect resistance (local maximum)
        is_res = all(high > df['High'].iloc[i - j] and high > df['High'].iloc[i + j] for j in range(1, swing + 1))
        if is_res and not any(abs(high - r) / r < tolerance for r in resistance):
            resistance.append(high)

        # Detect support (local minimum)
        is_sup = all(low < df['Low'].iloc[i - j] and low < df['Low'].iloc[i + j] for j in range(1, swing + 1))
        if is_sup and not any(abs(low - s) / s < tolerance for s in support):
            support.append(low)

    return {
        "Support": sorted(set(round(s, 2) for s in support)),
        "Resistance": sorted(set(round(r, 2) for r in resistance))
    }