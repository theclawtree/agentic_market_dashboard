"""Paper trading engine - simulates execution with realistic fees/slippage."""
import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FEE_RATE, BANKROLL
from strategy.engine import TradeDecision


@dataclass
class PaperPosition:
    trade_id: int
    market_question: str
    platform: str
    token_id: str
    direction: str
    size_usd: float
    entry_price: float
    estimated_prob: float
    market_price_at_entry: float
    edge: float
    timestamp: float
    signal_text: str
    resolved: bool = False
    resolution_price: float = 0.0
    pnl: float = 0.0


@dataclass
class PaperTrader:
    bankroll: float = BANKROLL
    positions: List[PaperPosition] = field(default_factory=list)
    trade_count: int = 0
    total_pnl: float = 0.0
    total_fees: float = 0.0
    log_path: str = ""

    def __post_init__(self):
        if not self.log_path:
            self.log_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "paper_trades.jsonl"
            )

    def execute(self, decision: TradeDecision) -> PaperPosition:
        """Execute a paper trade."""
        self.trade_count += 1
        
        pos = PaperPosition(
            trade_id=self.trade_count,
            market_question=decision.market_question,
            platform=decision.platform,
            token_id=decision.token_id,
            direction=decision.direction,
            size_usd=decision.size_usd,
            entry_price=decision.entry_price,
            estimated_prob=decision.estimated_prob,
            market_price_at_entry=decision.market_price,
            edge=decision.edge,
            timestamp=time.time(),
            signal_text=decision.signal.text[:200],
        )
        
        self.positions.append(pos)
        self._log_trade(pos, "OPEN")
        return pos

    def mark_to_market(self, token_id: str, current_price: float):
        """Update unrealized P&L for open positions."""
        for pos in self.positions:
            if pos.token_id == token_id and not pos.resolved:
                if pos.direction == "buy_yes":
                    shares = pos.size_usd / pos.entry_price
                    pos.pnl = shares * (current_price - pos.entry_price)
                else:
                    shares = pos.size_usd / (1 - pos.entry_price)
                    pos.pnl = shares * ((1 - current_price) - (1 - pos.entry_price))

    def resolve(self, token_id: str, outcome: bool):
        """Resolve a position (YES=True, NO=False)."""
        for pos in self.positions:
            if pos.token_id == token_id and not pos.resolved:
                pos.resolved = True
                pos.resolution_price = 1.0 if outcome else 0.0
                
                if pos.direction == "buy_yes":
                    shares = pos.size_usd / pos.entry_price
                    gross = shares * (pos.resolution_price - pos.entry_price)
                else:
                    shares = pos.size_usd / (1 - pos.entry_price)
                    gross = shares * ((1 - pos.resolution_price) - (1 - pos.entry_price))
                
                fee = max(0, gross) * FEE_RATE
                pos.pnl = gross - fee
                self.total_pnl += pos.pnl
                self.total_fees += fee
                self.bankroll += pos.pnl
                self._log_trade(pos, "RESOLVED")

    def summary(self) -> dict:
        open_positions = [p for p in self.positions if not p.resolved]
        resolved = [p for p in self.positions if p.resolved]
        unrealized = sum(p.pnl for p in open_positions)
        realized = sum(p.pnl for p in resolved)
        
        return {
            "bankroll": round(self.bankroll, 2),
            "total_trades": self.trade_count,
            "open_positions": len(open_positions),
            "resolved_positions": len(resolved),
            "unrealized_pnl": round(unrealized, 2),
            "realized_pnl": round(realized, 2),
            "total_fees": round(self.total_fees, 2),
            "win_rate": (
                sum(1 for p in resolved if p.pnl > 0) / len(resolved)
                if resolved else 0
            ),
        }

    def _log_trade(self, pos: PaperPosition, action: str):
        try:
            with open(self.log_path, "a") as f:
                entry = {
                    "action": action,
                    "trade_id": pos.trade_id,
                    "question": pos.market_question[:100],
                    "direction": pos.direction,
                    "size": pos.size_usd,
                    "entry": pos.entry_price,
                    "pnl": pos.pnl,
                    "ts": pos.timestamp,
                }
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def print_summary(self):
        s = self.summary()
        print(f"\n{'='*60}")
        print(f"  PAPER TRADING SUMMARY")
        print(f"{'='*60}")
        print(f"  Bankroll:     ${s['bankroll']:>12,.2f}")
        print(f"  Total Trades: {s['total_trades']:>12}")
        print(f"  Open:         {s['open_positions']:>12}")
        print(f"  Resolved:     {s['resolved_positions']:>12}")
        print(f"  Unrealized:   ${s['unrealized_pnl']:>12,.2f}")
        print(f"  Realized:     ${s['realized_pnl']:>12,.2f}")
        print(f"  Fees Paid:    ${s['total_fees']:>12,.2f}")
        print(f"  Win Rate:     {s['win_rate']:>11.1%}")
        print(f"{'='*60}\n")
