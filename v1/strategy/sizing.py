"""Position sizing - Kelly criterion and risk management."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import KELLY_FRACTION, MAX_POSITION_PCT, MIN_EDGE, BASE_SLIPPAGE


def kelly_size(
    estimated_prob: float,
    market_price: float,
    bankroll: float,
    kelly_fraction: float = KELLY_FRACTION,
    max_position_pct: float = MAX_POSITION_PCT,
    min_edge: float = MIN_EDGE,
) -> dict:
    """
    Calculate optimal position size using fractional Kelly criterion.
    
    Returns dict with:
        - size_usd: dollar amount to trade
        - direction: 'buy_yes' or 'buy_no'
        - edge: estimated edge
        - kelly_raw: raw Kelly fraction
        - kelly_adj: adjusted Kelly fraction
    """
    edge = estimated_prob - market_price
    abs_edge = abs(edge)
    
    if abs_edge < min_edge:
        return {"size_usd": 0, "direction": None, "edge": edge, "kelly_raw": 0, "kelly_adj": 0, "reason": "edge below threshold"}
    
    if edge > 0:
        # Buy YES: we think true prob > market price
        direction = "buy_yes"
        p_win = estimated_prob
        cost = market_price
        profit_if_win = 1.0 - cost
        loss_if_lose = cost
    else:
        # Buy NO: we think true prob < market price
        direction = "buy_no"
        p_win = 1.0 - estimated_prob
        cost = 1.0 - market_price
        profit_if_win = 1.0 - cost
        loss_if_lose = cost
    
    if loss_if_lose <= 0 or profit_if_win <= 0:
        return {"size_usd": 0, "direction": direction, "edge": edge, "kelly_raw": 0, "kelly_adj": 0, "reason": "degenerate odds"}
    
    b = profit_if_win / loss_if_lose
    q = 1.0 - p_win
    kelly_raw = (p_win * b - q) / b
    kelly_adj = max(0, kelly_raw) * kelly_fraction
    
    position_pct = min(kelly_adj, max_position_pct)
    size_usd = bankroll * position_pct
    
    return {
        "size_usd": round(size_usd, 2),
        "direction": direction,
        "edge": round(edge, 4),
        "kelly_raw": round(kelly_raw, 4),
        "kelly_adj": round(kelly_adj, 4),
        "reason": "trade" if size_usd > 0 else "kelly_negative",
    }


def compute_slippage(trade_size_usd: float, book_depth_usd: float) -> float:
    """Slippage model: base + impact proportional to size/depth."""
    if book_depth_usd <= 0:
        return 0.05  # 5% slippage if no book data
    ratio = trade_size_usd / book_depth_usd
    return BASE_SLIPPAGE + 0.02 * (ratio ** 1.5)


if __name__ == "__main__":
    print("=== Kelly Sizing Examples ===\n")
    
    examples = [
        (0.65, 0.50, 50000, "Strong edge: 65% true vs 50¢ market"),
        (0.55, 0.50, 50000, "Moderate edge: 55% true vs 50¢ market"),
        (0.52, 0.50, 50000, "Small edge: 52% true vs 50¢ market (below threshold)"),
        (0.30, 0.50, 50000, "Short: 30% true vs 50¢ market"),
        (0.90, 0.80, 50000, "High prob: 90% true vs 80¢ market"),
    ]
    
    for est, mkt, bank, desc in examples:
        result = kelly_size(est, mkt, bank)
        print(f"{desc}")
        print(f"  → {result['direction'] or 'NO TRADE'}: ${result['size_usd']:,.0f} | edge={result['edge']:+.2%} | kelly={result['kelly_adj']:.4f} | {result['reason']}")
        print()
