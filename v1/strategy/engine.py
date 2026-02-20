"""Strategy engine - matches signals to markets and generates trade decisions."""
from dataclasses import dataclass
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORIES, MIN_EDGE
from signals.classifier import Signal, SignalClassifier
from strategy.sizing import kelly_size, compute_slippage
from data.polymarket import PolyMarket


@dataclass
class TradeDecision:
    market_question: str
    platform: str
    token_id: str
    direction: str          # buy_yes or buy_no
    size_usd: float
    entry_price: float      # expected fill price after slippage
    estimated_prob: float   # our estimate
    market_price: float
    edge: float
    signal: Signal
    slippage: float
    confidence: float

    @property
    def expected_pnl(self) -> float:
        if self.direction == "buy_yes":
            return self.size_usd * (self.estimated_prob * (1.0 / self.entry_price - 1) - (1 - self.estimated_prob))
        else:
            return self.size_usd * ((1 - self.estimated_prob) * (1.0 / (1 - self.entry_price) - 1) - self.estimated_prob)


class StrategyEngine:
    def __init__(self, bankroll: float):
        self.bankroll = bankroll
        self.classifier = SignalClassifier()
        self.positions = {}  # token_id -> position info

    def match_signal_to_markets(self, signal: Signal, markets: List[PolyMarket]) -> List[PolyMarket]:
        """Find markets that a signal is relevant to."""
        matches = []
        for mkt in markets:
            score = self.classifier.score_for_market(signal, mkt.question)
            if score > 0.1:
                mkt.category = signal.category
                matches.append((mkt, score))
        matches.sort(key=lambda x: x[1], reverse=True)
        return [m for m, s in matches[:5]]  # Top 5 matches

    def estimate_probability(self, signal: Signal, market: PolyMarket) -> float:
        """
        Estimate true probability based on signal + current market price.
        
        Simple model: shift market price by signal direction * confidence * category accuracy.
        In production, this would use LLM analysis or domain-specific models.
        """
        cat_accuracy = CATEGORIES.get(signal.category, {}).get("signal_accuracy", 0.5)
        
        # How much to shift from current market price
        shift = signal.direction * signal.confidence * cat_accuracy * 0.15  # max ~12% shift
        estimated = market.yes_price + shift
        return max(0.02, min(0.98, estimated))

    def generate_decisions(self, signals: List[Signal], markets: List[PolyMarket]) -> List[TradeDecision]:
        """Generate trade decisions from signals and available markets."""
        decisions = []
        
        for signal in signals:
            if signal.confidence < 0.3:
                continue
            
            matched_markets = self.match_signal_to_markets(signal, markets)
            
            for market in matched_markets:
                estimated_prob = self.estimate_probability(signal, market)
                
                sizing = kelly_size(estimated_prob, market.yes_price, self.bankroll)
                
                if sizing["size_usd"] <= 0:
                    continue
                
                slippage = compute_slippage(sizing["size_usd"], market.book_depth_usd)
                
                if sizing["direction"] == "buy_yes":
                    entry_price = market.yes_price + slippage
                else:
                    entry_price = market.yes_price - slippage
                entry_price = max(0.01, min(0.99, entry_price))
                
                decisions.append(TradeDecision(
                    market_question=market.question,
                    platform=market.platform,
                    token_id=market.yes_token if sizing["direction"] == "buy_yes" else market.no_token,
                    direction=sizing["direction"],
                    size_usd=sizing["size_usd"],
                    entry_price=entry_price,
                    estimated_prob=estimated_prob,
                    market_price=market.yes_price,
                    edge=sizing["edge"],
                    signal=signal,
                    slippage=slippage,
                    confidence=signal.confidence,
                ))
        
        # Sort by edge * confidence (best opportunities first)
        decisions.sort(key=lambda d: abs(d.edge) * d.confidence, reverse=True)
        return decisions
