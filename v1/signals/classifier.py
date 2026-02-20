"""Signal classifier - matches news text to market categories and scores relevance."""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORIES


@dataclass
class Signal:
    text: str
    source: str
    category: str
    category_name: str
    relevance_score: float   # 0-1, how relevant to category
    direction: float         # -1 to 1, negative=bearish positive=bullish for YES
    confidence: float        # 0-1
    timestamp: float = 0.0
    matched_keywords: List[str] = None

    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = []


# Direction keywords: words that suggest a YES or NO outcome
BULLISH_WORDS = {
    "fed_decisions": ["cut", "lower", "dovish", "ease", "reduce", "pause", "hold steady", "supportive"],
    "elections": ["leads", "ahead", "surge", "winning", "endorse", "momentum", "landslide"],
    "crypto_regulatory": ["approve", "approved", "favorable", "green light", "legalize", "adopt", "embrace"],
    "geopolitical": ["ceasefire", "peace", "agreement", "withdraw", "de-escalat", "diplomacy", "treaty"],
}

BEARISH_WORDS = {
    "fed_decisions": ["hike", "raise", "hawkish", "tighten", "increase", "restrictive", "aggressive"],
    "elections": ["trails", "behind", "drops out", "scandal", "losing", "collapse", "withdraw"],
    "crypto_regulatory": ["ban", "reject", "crack down", "enforce", "restrict", "prohibit", "sue"],
    "geopolitical": ["escalat", "attack", "strike", "invade", "missile", "bomb", "deploy", "mobilize"],
}

# High-credibility sources get boosted
HIGH_CRED_SOURCES = {
    "reuters", "ap", "bloomberg", "wsj", "nytimes", "federal_reserve",
    "bls.gov", "sec.gov", "whitehouse", "official",
}


class SignalClassifier:
    def __init__(self):
        self.categories = CATEGORIES

    def classify(self, text: str, source: str = "unknown") -> List[Signal]:
        """Classify a piece of text into zero or more category signals."""
        text_lower = text.lower()
        signals = []

        for cat_key, cat_info in self.categories.items():
            matched = []
            for kw in cat_info["keywords"]:
                if kw.lower() in text_lower:
                    matched.append(kw)

            if not matched:
                continue

            # Relevance: more keywords matched = more relevant
            relevance = min(1.0, len(matched) / 3.0)

            # Direction scoring
            bull_count = sum(1 for w in BULLISH_WORDS.get(cat_key, []) if w.lower() in text_lower)
            bear_count = sum(1 for w in BEARISH_WORDS.get(cat_key, []) if w.lower() in text_lower)
            total = bull_count + bear_count
            direction = (bull_count - bear_count) / total if total > 0 else 0.0

            # Confidence based on keyword density + source credibility
            source_boost = 1.3 if any(s in source.lower() for s in HIGH_CRED_SOURCES) else 1.0
            confidence = min(1.0, relevance * source_boost * (0.5 + 0.5 * abs(direction)))

            signals.append(Signal(
                text=text[:500],
                source=source,
                category=cat_key,
                category_name=cat_info["name"],
                relevance_score=relevance,
                direction=direction,
                confidence=confidence,
                matched_keywords=matched,
            ))

        return signals

    def score_for_market(self, signal: Signal, market_question: str) -> float:
        """Score how relevant a signal is to a specific market question."""
        q_lower = market_question.lower()
        # Check if signal keywords appear in market question
        overlap = sum(1 for kw in signal.matched_keywords if kw.lower() in q_lower)
        if overlap == 0:
            # Fuzzy: check if any significant words from signal appear in question
            sig_words = set(signal.text.lower().split()) - {"the", "a", "an", "is", "are", "was", "were", "will", "be"}
            q_words = set(q_lower.split())
            overlap = len(sig_words & q_words) / max(len(q_words), 1)
            return min(1.0, overlap * signal.relevance_score)
        return min(1.0, overlap / 2.0 * signal.relevance_score)


if __name__ == "__main__":
    classifier = SignalClassifier()

    test_texts = [
        ("Federal Reserve signals potential rate cut at next FOMC meeting, Powell adopts dovish tone", "reuters"),
        ("Bitcoin ETF approved by SEC in landmark decision for crypto industry", "bloomberg"),
        ("Ukraine and Russia agree to ceasefire after marathon peace talks", "ap"),
        ("Trump surges ahead in latest swing state polls, leads by 5 points", "nytimes"),
        ("New study shows cats prefer boxes over expensive beds", "buzzfeed"),
    ]

    for text, source in test_texts:
        signals = classifier.classify(text, source)
        print(f"\n📰 [{source}] {text[:80]}...")
        if signals:
            for s in signals:
                arrow = "↑" if s.direction > 0 else "↓" if s.direction < 0 else "→"
                print(f"   {arrow} {s.category_name}: rel={s.relevance_score:.2f} dir={s.direction:+.2f} conf={s.confidence:.2f} kw={s.matched_keywords}")
        else:
            print("   (no market signals)")
