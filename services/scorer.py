# services/scorer.py

def score_zone(fresh: bool, leg_in_strength: float, leg_out_strength: float, vol_spike: bool) -> int:
    """
    Score a demand zone based on freshness, leg-out power, and volume spike.
    Returns a score (int). Minimum recommended threshold: 3.
    """
    score = 0

    # Fresh zone adds higher score
    score += 2 if fresh else 1

    # Leg-out stronger than leg-in
    if leg_out_strength > 2 * leg_in_strength:
        score += 2
    else:
        score += 1

    # Volume spike bonus
    if vol_spike:
        score += 1

    return score
