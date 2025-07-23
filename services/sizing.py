# services/sizing.py

def calculate_position_size(entry_price, stop_price, resistance_price, capital=100000, risk_pct=0.01):
    """
    Calculate stop loss ₹, quantity, position size, and RR ratio.
    Args:
        entry_price (float): Entry/proximal price
        stop_price (float): Distal stop loss price
        resistance_price (float or None): Nearest resistance price
        capital (float): Total capital available
        risk_pct (float): Percentage of capital to risk (e.g., 0.01 for 1%)

    Returns:
        dict: {
            'stop_loss_value': float,
            'quantity': int,
            'position_size': float,
            'rr_ratio': float or None
        }
    """
    if entry_price <= 0 or stop_price <= 0:
        return {
            'stop_loss_value': 0,
            'quantity': 0,
            'position_size': 0,
            'rr_ratio': None
        }

    stop_loss_value = round(entry_price - stop_price, 2)
    capital_to_risk = capital * risk_pct

    if stop_loss_value <= 0:
        return {
            'stop_loss_value': 0,
            'quantity': 0,
            'position_size': 0,
            'rr_ratio': None
        }

    quantity = int(capital_to_risk // stop_loss_value) if stop_loss_value > 0 else 0
    position_size = round(quantity * entry_price, 2)

    rr_ratio = None
    if resistance_price is not None and resistance_price > 0:
        rr_ratio = round((resistance_price - entry_price) / stop_loss_value, 2)

    return {
        'stop_loss_value': stop_loss_value,
        'quantity': quantity,
        'position_size': position_size,
        'rr_ratio': rr_ratio
    }