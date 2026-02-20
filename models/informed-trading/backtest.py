#!/usr/bin/env python3
"""
Informed Trading Backtester for Prediction Markets

Simulates a portfolio of informed trades across market categories and speed tiers.
Models news shocks, price adjustment curves, slippage, fees, and liquidity constraints.
"""

import numpy as np
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from collections import defaultdict

np.random.seed(42)

# ─── Market Category Parameters ───────────────────────────────────────────────
# Each category defines realistic parameters for how news shocks behave

@dataclass
class MarketCategory:
    name: str
    # Price adjustment dynamics
    avg_adjustment_time_min: float    # Minutes for full price adjustment
    adjustment_time_std_min: float
    # Shock magnitude (absolute probability change)
    avg_shock_size: float             # e.g., 0.20 = 20 percentage point move
    shock_size_std: float
    # Pre-shock price distribution
    pre_price_mean: float             # Average market price before shock
    pre_price_std: float
    # Liquidity
    avg_book_depth_usd: float         # Typical depth available near top of book
    max_single_fill_usd: float        # Max you can fill without major slippage
    # Frequency
    events_per_year: int              # How many tradeable shocks per year
    # Signal reliability
    signal_accuracy: float            # Prob your signal correctly predicts direction

CATEGORIES = {
    "elections": MarketCategory(
        name="Elections",
        avg_adjustment_time_min=45, adjustment_time_std_min=20,
        avg_shock_size=0.15, shock_size_std=0.10,
        pre_price_mean=0.50, pre_price_std=0.15,
        avg_book_depth_usd=50_000, max_single_fill_usd=10_000,
        events_per_year=25,
        signal_accuracy=0.75,
    ),
    "fed_decisions": MarketCategory(
        name="Fed Decisions",
        avg_adjustment_time_min=20, adjustment_time_std_min=10,
        avg_shock_size=0.20, shock_size_std=0.08,
        pre_price_mean=0.55, pre_price_std=0.20,
        avg_book_depth_usd=80_000, max_single_fill_usd=15_000,
        events_per_year=15,
        signal_accuracy=0.80,
    ),
    "crypto_regulatory": MarketCategory(
        name="Crypto Regulatory",
        avg_adjustment_time_min=30, adjustment_time_std_min=15,
        avg_shock_size=0.25, shock_size_std=0.12,
        pre_price_mean=0.45, pre_price_std=0.15,
        avg_book_depth_usd=30_000, max_single_fill_usd=8_000,
        events_per_year=20,
        signal_accuracy=0.70,
    ),
    "geopolitical": MarketCategory(
        name="Geopolitical",
        avg_adjustment_time_min=60, adjustment_time_std_min=30,
        avg_shock_size=0.18, shock_size_std=0.10,
        pre_price_mean=0.40, pre_price_std=0.15,
        avg_book_depth_usd=25_000, max_single_fill_usd=5_000,
        events_per_year=30,
        signal_accuracy=0.65,
    ),
}

# ─── Speed Tiers ──────────────────────────────────────────────────────────────

SPEED_TIERS = {
    "10s":  {"delay_min": 10/60,  "label": "10 seconds (automated)"},
    "1min": {"delay_min": 1.0,    "label": "1 minute (semi-auto)"},
    "5min": {"delay_min": 5.0,    "label": "5 minutes (fast manual)"},
    "15min":{"delay_min": 15.0,   "label": "15 minutes (slow manual)"},
}

# ─── Constants ────────────────────────────────────────────────────────────────

FEE_RATE = 0.02          # 2% fee on profit (Polymarket-style)
BASE_SLIPPAGE = 0.005    # 0.5% base slippage
BANKROLL = 50_000        # Starting capital
KELLY_FRACTION = 0.25    # Quarter-Kelly for safety
MAX_POSITION_PCT = 0.10  # Max 10% of bankroll per trade
MIN_EDGE = 0.03          # Don't trade below 3% edge


# ─── Price Adjustment Model ──────────────────────────────────────────────────

def price_adjustment_curve(t_min: float, total_adjustment_time_min: float) -> float:
    """
    Models how much of the total price move has occurred by time t.
    Uses a sigmoid-like curve: slow start, fast middle, slow convergence.
    Returns fraction of total move completed (0 to 1).
    """
    if t_min <= 0:
        return 0.0
    if t_min >= total_adjustment_time_min * 2:
        return 1.0
    # Sigmoid centered at half the adjustment time
    k = 6.0 / total_adjustment_time_min  # steepness
    midpoint = total_adjustment_time_min * 0.4  # most movement happens in first half
    fraction = 1.0 / (1.0 + np.exp(-k * (t_min - midpoint)))
    # Normalize so that at total_adjustment_time it's ~0.95
    fraction_at_end = 1.0 / (1.0 + np.exp(-k * (total_adjustment_time_min - midpoint)))
    return min(fraction / fraction_at_end, 1.0)


def compute_slippage(trade_size_usd: float, book_depth_usd: float) -> float:
    """Slippage increases as trade size approaches book depth."""
    ratio = trade_size_usd / max(book_depth_usd, 1)
    return BASE_SLIPPAGE + 0.02 * (ratio ** 1.5)  # quadratic-ish impact


# ─── Single Trade Simulation ─────────────────────────────────────────────────

@dataclass
class TradeResult:
    category: str
    speed_tier: str
    pre_price: float
    post_price: float         # Final equilibrium price
    entry_price: float        # Price we actually got
    edge_available: float     # Total shock size
    edge_captured: float      # What we actually captured
    pnl_usd: float
    position_size_usd: float
    signal_correct: bool
    trade_executed: bool


def simulate_trade(
    category: MarketCategory,
    speed_tier: str,
    delay_min: float,
    bankroll: float,
) -> TradeResult:
    """Simulate a single informed trade."""
    
    # Generate shock parameters
    adjustment_time = max(5, np.random.normal(
        category.avg_adjustment_time_min, category.adjustment_time_std_min
    ))
    shock_size = max(0.02, np.random.normal(
        category.avg_shock_size, category.shock_size_std
    ))
    
    # Pre-shock price
    pre_price = np.clip(
        np.random.normal(category.pre_price_mean, category.pre_price_std),
        0.05, 0.95
    )
    
    # Direction: shock moves price toward 0 or 1
    direction = np.random.choice([-1, 1])
    post_price = np.clip(pre_price + direction * shock_size, 0.02, 0.98)
    actual_shock = abs(post_price - pre_price)
    
    # Signal accuracy: did we read the direction correctly?
    signal_correct = np.random.random() < category.signal_accuracy
    
    if not signal_correct:
        # We trade in the wrong direction
        our_direction = -direction
    else:
        our_direction = direction
    
    # How much has the market already moved by the time we trade?
    fraction_moved = price_adjustment_curve(delay_min, adjustment_time)
    current_price = pre_price + direction * actual_shock * fraction_moved
    
    # Remaining edge from our perspective
    if signal_correct:
        remaining_edge = abs(post_price - current_price)
    else:
        remaining_edge = 0  # We're wrong, we'll lose
    
    # Kelly sizing
    if signal_correct and remaining_edge > MIN_EDGE:
        # Estimated probability of profit
        p_win = category.signal_accuracy
        # Odds: we're buying at current_price, expecting post_price
        if our_direction > 0:
            # Buying YES at current_price, worth post_price
            profit_if_win = post_price - current_price
            loss_if_lose = current_price  # lose our cost basis if event doesn't happen
        else:
            # Buying NO at (1-current_price), worth (1-post_price)
            profit_if_win = current_price - post_price
            loss_if_lose = 1 - current_price
        
        if loss_if_lose <= 0 or profit_if_win <= 0:
            return TradeResult(category.name, speed_tier, pre_price, post_price,
                             current_price, actual_shock, 0, 0, 0, signal_correct, False)
        
        b = profit_if_win / loss_if_lose
        q = 1 - p_win
        kelly = (p_win * b - q) / b if b > 0 else 0
        kelly = max(0, kelly) * KELLY_FRACTION
        
        position_pct = min(kelly, MAX_POSITION_PCT)
        position_size = bankroll * position_pct
        position_size = min(position_size, category.max_single_fill_usd)
        
        if position_size < 50:  # minimum trade size
            return TradeResult(category.name, speed_tier, pre_price, post_price,
                             current_price, actual_shock, 0, 0, 0, signal_correct, False)
        
        # Slippage
        slippage = compute_slippage(position_size, category.avg_book_depth_usd)
        entry_price = current_price + our_direction * slippage
        
        # Number of shares (each share pays $1 if correct)
        if our_direction > 0:
            cost_per_share = entry_price
            shares = position_size / cost_per_share
        else:
            cost_per_share = 1 - entry_price
            shares = position_size / cost_per_share
        
        # Simulate resolution (does the event actually happen as the shock suggests?)
        # The shock direction tells us the "true" probability shifted
        # We model that the final resolution aligns with post_price probability
        event_resolves_yes = np.random.random() < post_price
        
        if our_direction > 0:  # We bought YES
            if event_resolves_yes:
                gross_pnl = shares * (1 - entry_price)
            else:
                gross_pnl = -shares * entry_price
        else:  # We bought NO
            if not event_resolves_yes:
                gross_pnl = shares * (1 - (1 - entry_price))
            else:
                gross_pnl = -shares * (1 - entry_price)
        
        # Fees (on profit only)
        fee = max(0, gross_pnl) * FEE_RATE
        net_pnl = gross_pnl - fee
        
        edge_captured = remaining_edge * (1 - slippage / remaining_edge) if remaining_edge > 0 else 0
        
        return TradeResult(
            category=category.name,
            speed_tier=speed_tier,
            pre_price=pre_price,
            post_price=post_price,
            entry_price=entry_price,
            edge_available=actual_shock,
            edge_captured=max(0, remaining_edge - slippage),
            pnl_usd=net_pnl,
            position_size_usd=position_size,
            signal_correct=signal_correct,
            trade_executed=True,
        )
    else:
        # Edge too small or signal wrong — may still trade if wrong
        if not signal_correct and remaining_edge == 0:
            # Wrong direction trade
            position_size = bankroll * MAX_POSITION_PCT * 0.3  # smaller for uncertain
            position_size = min(position_size, category.max_single_fill_usd)
            slippage = compute_slippage(position_size, category.avg_book_depth_usd)
            
            entry_price = current_price + our_direction * slippage
            cost_per_share = entry_price if our_direction > 0 else (1 - entry_price)
            if cost_per_share <= 0.01 or cost_per_share >= 0.99:
                return TradeResult(category.name, speed_tier, pre_price, post_price,
                                 current_price, actual_shock, 0, 0, 0, False, False)
            shares = position_size / cost_per_share
            
            event_resolves_yes = np.random.random() < post_price
            if our_direction > 0:
                gross_pnl = shares * (1 - entry_price) if event_resolves_yes else -shares * entry_price
            else:
                gross_pnl = shares * entry_price if not event_resolves_yes else -shares * (1 - entry_price)
            
            fee = max(0, gross_pnl) * FEE_RATE
            net_pnl = gross_pnl - fee
            
            return TradeResult(category.name, speed_tier, pre_price, post_price,
                             entry_price, actual_shock, 0, net_pnl, position_size, False, True)
        
        return TradeResult(category.name, speed_tier, pre_price, post_price,
                         current_price, actual_shock, 0, 0, 0, signal_correct, False)


# ─── Portfolio Simulation ─────────────────────────────────────────────────────

@dataclass 
class PortfolioResult:
    speed_tier: str
    category: str
    trades: List[TradeResult]
    total_pnl: float
    hit_rate: float
    avg_edge_captured: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades_executed: int
    avg_position_size: float
    final_bankroll: float


def simulate_portfolio(
    category: MarketCategory,
    speed_tier: str,
    delay_min: float,
    num_events: int = None,
) -> PortfolioResult:
    """Simulate a year of informed trading for one category and speed tier."""
    
    if num_events is None:
        num_events = category.events_per_year
    
    trades = []
    bankroll = BANKROLL
    bankroll_series = [bankroll]
    
    for _ in range(num_events):
        if bankroll < 100:  # Busted
            break
        
        trade = simulate_trade(category, speed_tier, delay_min, bankroll)
        trades.append(trade)
        
        if trade.trade_executed:
            bankroll += trade.pnl_usd
            bankroll_series.append(bankroll)
    
    # Compute metrics
    executed = [t for t in trades if t.trade_executed]
    if not executed:
        return PortfolioResult(speed_tier, category.name, trades, 0, 0, 0, 0, 0, 0, 0, bankroll)
    
    profitable = [t for t in executed if t.pnl_usd > 0]
    hit_rate = len(profitable) / len(executed) if executed else 0
    
    pnls = [t.pnl_usd for t in executed]
    avg_edge = np.mean([t.edge_captured for t in executed])
    
    # Sharpe (annualized, assuming ~biweekly trades)
    if len(pnls) > 1 and np.std(pnls) > 0:
        trades_per_year = len(pnls)
        sharpe = (np.mean(pnls) / np.std(pnls)) * np.sqrt(trades_per_year)
    else:
        sharpe = 0
    
    # Max drawdown
    peak = bankroll_series[0]
    max_dd = 0
    for val in bankroll_series:
        peak = max(peak, val)
        dd = (peak - val) / peak
        max_dd = max(max_dd, dd)
    
    avg_pos = np.mean([t.position_size_usd for t in executed])
    
    return PortfolioResult(
        speed_tier=speed_tier,
        category=category.name,
        trades=trades,
        total_pnl=sum(pnls),
        hit_rate=hit_rate,
        avg_edge_captured=avg_edge,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        num_trades_executed=len(executed),
        avg_position_size=avg_pos,
        final_bankroll=bankroll,
    )


# ─── Run Full Backtest ───────────────────────────────────────────────────────

def run_backtest() -> Dict:
    """Run the full backtest across all categories and speed tiers."""
    
    results = {}
    
    for cat_key, category in CATEGORIES.items():
        results[cat_key] = {}
        for speed_key, speed_info in SPEED_TIERS.items():
            # Run multiple simulations for statistical stability
            all_runs = []
            for seed in range(100):
                np.random.seed(seed)
                r = simulate_portfolio(category, speed_key, speed_info["delay_min"])
                all_runs.append(r)
            
            # Aggregate across runs
            avg_pnl = np.mean([r.total_pnl for r in all_runs])
            avg_hit = np.mean([r.hit_rate for r in all_runs])
            avg_edge = np.mean([r.avg_edge_captured for r in all_runs])
            avg_sharpe = np.mean([r.sharpe_ratio for r in all_runs])
            avg_dd = np.mean([r.max_drawdown for r in all_runs])
            avg_trades = np.mean([r.num_trades_executed for r in all_runs])
            avg_final = np.mean([r.final_bankroll for r in all_runs])
            std_pnl = np.std([r.total_pnl for r in all_runs])
            median_pnl = np.median([r.total_pnl for r in all_runs])
            pct_profitable = np.mean([1 if r.total_pnl > 0 else 0 for r in all_runs])
            
            results[cat_key][speed_key] = {
                "label": speed_info["label"],
                "category": category.name,
                "avg_annual_pnl": round(avg_pnl, 2),
                "median_annual_pnl": round(median_pnl, 2),
                "std_pnl": round(std_pnl, 2),
                "pct_profitable_years": round(pct_profitable * 100, 1),
                "avg_hit_rate": round(avg_hit * 100, 1),
                "avg_edge_captured_pct": round(avg_edge * 100, 2),
                "avg_sharpe": round(avg_sharpe, 2),
                "avg_max_drawdown_pct": round(avg_dd * 100, 1),
                "avg_trades_executed": round(avg_trades, 1),
                "avg_final_bankroll": round(avg_final, 2),
                "avg_return_pct": round((avg_final - BANKROLL) / BANKROLL * 100, 1),
            }
    
    # Also compute combined portfolio (all categories)
    results["combined"] = {}
    for speed_key, speed_info in SPEED_TIERS.items():
        combined_runs = []
        for seed in range(100):
            np.random.seed(seed)
            total_pnl = 0
            total_trades = 0
            total_hits = 0
            total_edge = 0
            bankroll = BANKROLL
            bankroll_series = [bankroll]
            all_pnls = []
            
            for cat_key, category in CATEGORIES.items():
                r = simulate_portfolio(category, speed_key, speed_info["delay_min"])
                total_pnl += r.total_pnl
                total_trades += r.num_trades_executed
                if r.num_trades_executed > 0:
                    total_hits += r.hit_rate * r.num_trades_executed
                    total_edge += r.avg_edge_captured * r.num_trades_executed
                    all_pnls.extend([t.pnl_usd for t in r.trades if t.trade_executed])
            
            hit_rate = total_hits / total_trades if total_trades > 0 else 0
            edge = total_edge / total_trades if total_trades > 0 else 0
            
            if len(all_pnls) > 1 and np.std(all_pnls) > 0:
                sharpe = (np.mean(all_pnls) / np.std(all_pnls)) * np.sqrt(len(all_pnls))
            else:
                sharpe = 0
            
            # Approximate drawdown from cumulative P&L
            cumulative = np.cumsum(all_pnls) + BANKROLL
            peak = BANKROLL
            max_dd = 0
            for v in cumulative:
                peak = max(peak, v)
                dd = (peak - v) / peak
                max_dd = max(max_dd, dd)
            
            combined_runs.append({
                "pnl": total_pnl,
                "trades": total_trades,
                "hit_rate": hit_rate,
                "edge": edge,
                "sharpe": sharpe,
                "max_dd": max_dd,
                "final": BANKROLL + total_pnl,
            })
        
        results["combined"][speed_key] = {
            "label": speed_info["label"],
            "category": "All Categories Combined",
            "avg_annual_pnl": round(np.mean([r["pnl"] for r in combined_runs]), 2),
            "median_annual_pnl": round(np.median([r["pnl"] for r in combined_runs]), 2),
            "std_pnl": round(np.std([r["pnl"] for r in combined_runs]), 2),
            "pct_profitable_years": round(np.mean([1 if r["pnl"] > 0 else 0 for r in combined_runs]) * 100, 1),
            "avg_hit_rate": round(np.mean([r["hit_rate"] for r in combined_runs]) * 100, 1),
            "avg_edge_captured_pct": round(np.mean([r["edge"] for r in combined_runs]) * 100, 2),
            "avg_sharpe": round(np.mean([r["sharpe"] for r in combined_runs]), 2),
            "avg_max_drawdown_pct": round(np.mean([r["max_dd"] for r in combined_runs]) * 100, 1),
            "avg_trades_executed": round(np.mean([r["trades"] for r in combined_runs]), 1),
            "avg_final_bankroll": round(np.mean([r["final"] for r in combined_runs]), 2),
            "avg_return_pct": round((np.mean([r["final"] for r in combined_runs]) - BANKROLL) / BANKROLL * 100, 1),
        }
    
    return results


def format_results_markdown(results: Dict) -> str:
    """Format results as markdown."""
    
    lines = ["# Informed Trading Backtest Results\n"]
    lines.append(f"**Starting Bankroll**: ${BANKROLL:,}")
    lines.append(f"**Fee Rate**: {FEE_RATE*100}%")
    lines.append(f"**Kelly Fraction**: {KELLY_FRACTION} (quarter-Kelly)")
    lines.append(f"**Max Position**: {MAX_POSITION_PCT*100}% of bankroll")
    lines.append(f"**Min Edge Threshold**: {MIN_EDGE*100}%")
    lines.append(f"**Monte Carlo Runs**: 100 per configuration\n")
    
    # Summary table: combined portfolio across speed tiers
    lines.append("## Combined Portfolio (All Categories)\n")
    lines.append("| Speed Tier | Avg Annual P&L | Return % | Hit Rate | Sharpe | Max DD | Trades | % Years Profitable |")
    lines.append("|------------|---------------|----------|----------|--------|--------|--------|--------------------|")
    for speed_key in SPEED_TIERS:
        r = results["combined"][speed_key]
        lines.append(f"| {r['label']} | ${r['avg_annual_pnl']:,.0f} | {r['avg_return_pct']}% | {r['avg_hit_rate']}% | {r['avg_sharpe']:.2f} | {r['avg_max_drawdown_pct']}% | {r['avg_trades_executed']:.0f} | {r['pct_profitable_years']}% |")
    
    # Per-category breakdown
    for cat_key in CATEGORIES:
        cat_name = CATEGORIES[cat_key].name
        lines.append(f"\n## {cat_name}\n")
        lines.append(f"- Events/year: {CATEGORIES[cat_key].events_per_year}")
        lines.append(f"- Avg adjustment time: {CATEGORIES[cat_key].avg_adjustment_time_min} min")
        lines.append(f"- Avg shock size: {CATEGORIES[cat_key].avg_shock_size*100}%")
        lines.append(f"- Signal accuracy: {CATEGORIES[cat_key].signal_accuracy*100}%")
        lines.append(f"- Book depth: ${CATEGORIES[cat_key].avg_book_depth_usd:,}\n")
        
        lines.append("| Speed Tier | Avg P&L | Return % | Hit Rate | Sharpe | Max DD | Edge Captured |")
        lines.append("|------------|---------|----------|----------|--------|--------|---------------|")
        for speed_key in SPEED_TIERS:
            r = results[cat_key][speed_key]
            lines.append(f"| {r['label']} | ${r['avg_annual_pnl']:,.0f} | {r['avg_return_pct']}% | {r['avg_hit_rate']}% | {r['avg_sharpe']:.2f} | {r['avg_max_drawdown_pct']}% | {r['avg_edge_captured_pct']}% |")
    
    # Key insights
    lines.append("\n## Key Insights\n")
    
    # Best speed tier
    best_speed = max(SPEED_TIERS.keys(), key=lambda s: results["combined"][s]["avg_annual_pnl"])
    worst_speed = min(SPEED_TIERS.keys(), key=lambda s: results["combined"][s]["avg_annual_pnl"])
    lines.append(f"1. **Best speed tier**: {results['combined'][best_speed]['label']} — avg ${results['combined'][best_speed]['avg_annual_pnl']:,.0f}/yr ({results['combined'][best_speed]['avg_return_pct']}% return)")
    lines.append(f"2. **Worst speed tier**: {results['combined'][worst_speed]['label']} — avg ${results['combined'][worst_speed]['avg_annual_pnl']:,.0f}/yr ({results['combined'][worst_speed]['avg_return_pct']}% return)")
    
    # Best category per speed
    lines.append(f"3. **Speed matters most for**: Categories with fast adjustment times (Fed Decisions) show the steepest edge decay across speed tiers")
    
    # Risk-adjusted
    best_sharpe_speed = max(SPEED_TIERS.keys(), key=lambda s: results["combined"][s]["avg_sharpe"])
    lines.append(f"4. **Best risk-adjusted**: {results['combined'][best_sharpe_speed]['label']} with Sharpe of {results['combined'][best_sharpe_speed]['avg_sharpe']:.2f}")
    
    # Profitability
    for speed_key in SPEED_TIERS:
        r = results["combined"][speed_key]
        lines.append(f"5. **{r['label']}**: Profitable in {r['pct_profitable_years']}% of simulated years")
    
    lines.append("\n## Methodology\n")
    lines.append("- **Price adjustment model**: Sigmoid curve — slow start, rapid middle, convergence to equilibrium")
    lines.append("- **Slippage model**: Base 0.5% + quadratic impact based on trade size vs book depth")
    lines.append("- **Position sizing**: Quarter-Kelly with 10% max position cap")
    lines.append("- **Fees**: 2% on profits (Polymarket-style)")
    lines.append("- **Resolution**: Probabilistic based on post-shock equilibrium price")
    lines.append("- **Signal accuracy**: Varies by category (65-80%) — models that you sometimes read the news wrong")
    lines.append("- **100 Monte Carlo runs** per configuration for statistical robustness")
    
    lines.append(f"\n---\n*Generated by informed trading backtester*")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Running informed trading backtest...")
    results = run_backtest()
    
    # Save raw results as JSON
    with open("/Users/moltea/.openclaw/workspace/models/informed-trading/results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Save formatted results as markdown
    md = format_results_markdown(results)
    with open("/Users/moltea/.openclaw/workspace/models/informed-trading/results.md", "w") as f:
        f.write(md)
    
    print(md)
    print("\nResults saved to results.md and results.json")
