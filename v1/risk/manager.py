"""Risk manager - position limits, exposure tracking, kill switch."""
from dataclasses import dataclass, field
from typing import Dict
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAX_POSITION_PCT, BANKROLL
from strategy.engine import TradeDecision


@dataclass
class RiskManager:
    max_position_pct: float = MAX_POSITION_PCT
    max_total_exposure_pct: float = 0.50  # max 50% of bankroll deployed
    max_per_market_usd: float = 10000
    max_daily_loss_pct: float = 0.10      # 10% daily stop loss
    kill_switch: bool = False
    
    # Tracking
    total_exposure: float = 0.0
    daily_pnl: float = 0.0
    positions_by_market: Dict[str, float] = field(default_factory=dict)
    
    def check_trade(self, decision: TradeDecision, bankroll: float) -> tuple:
        """
        Check if a trade passes risk limits.
        Returns (approved: bool, reason: str)
        """
        if self.kill_switch:
            return False, "KILL SWITCH ACTIVE"
        
        # Daily loss limit
        if self.daily_pnl < -bankroll * self.max_daily_loss_pct:
            return False, f"Daily loss limit hit: ${self.daily_pnl:,.0f}"
        
        # Total exposure limit
        new_exposure = self.total_exposure + decision.size_usd
        if new_exposure > bankroll * self.max_total_exposure_pct:
            return False, f"Total exposure limit: ${new_exposure:,.0f} > ${bankroll * self.max_total_exposure_pct:,.0f}"
        
        # Per-market limit
        market_key = decision.market_question[:50]
        current_in_market = self.positions_by_market.get(market_key, 0)
        if current_in_market + decision.size_usd > self.max_per_market_usd:
            return False, f"Per-market limit: ${current_in_market + decision.size_usd:,.0f} > ${self.max_per_market_usd:,.0f}"
        
        # Single position size
        if decision.size_usd > bankroll * self.max_position_pct:
            return False, f"Position too large: ${decision.size_usd:,.0f} > ${bankroll * self.max_position_pct:,.0f}"
        
        return True, "approved"
    
    def record_trade(self, decision: TradeDecision):
        self.total_exposure += decision.size_usd
        market_key = decision.market_question[:50]
        self.positions_by_market[market_key] = self.positions_by_market.get(market_key, 0) + decision.size_usd
    
    def record_pnl(self, pnl: float):
        self.daily_pnl += pnl
    
    def close_position(self, market_question: str, size_usd: float):
        self.total_exposure = max(0, self.total_exposure - size_usd)
        market_key = market_question[:50]
        if market_key in self.positions_by_market:
            self.positions_by_market[market_key] = max(0, self.positions_by_market[market_key] - size_usd)
    
    def reset_daily(self):
        self.daily_pnl = 0.0
    
    def activate_kill_switch(self):
        self.kill_switch = True
        print("🚨 KILL SWITCH ACTIVATED - All trading halted")
    
    def deactivate_kill_switch(self):
        self.kill_switch = False
        print("✅ Kill switch deactivated")
    
    def status(self) -> dict:
        return {
            "kill_switch": self.kill_switch,
            "total_exposure": round(self.total_exposure, 2),
            "daily_pnl": round(self.daily_pnl, 2),
            "markets_active": len([v for v in self.positions_by_market.values() if v > 0]),
        }
