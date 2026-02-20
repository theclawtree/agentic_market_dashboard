"""LLM-based sentiment analysis — pluggable backend (API or local)."""
import json
import requests
import pandas as pd
import os


SYSTEM_PROMPT = """You are a prediction market analyst. For each news article, assess:
1. sentiment: "bullish" (supports YES), "bearish" (supports NO), or "neutral"
2. sentiment_score: float from -1.0 (strong NO) to +1.0 (strong YES)
3. relevance: float 0.0-1.0, how relevant this article is to the market question

Respond ONLY with a JSON object: {"sentiment": "...", "sentiment_score": 0.0, "relevance": 0.0}"""


def analyze_with_api(headline: str, description: str, market_question: str,
                     api_base: str, api_key: str, model: str, temperature: float = 0.1) -> dict:
    """Call OpenAI-compatible API for sentiment analysis."""
    if not api_key:
        return _keyword_fallback(headline, description, market_question)
    
    user_msg = f"""Market question: {market_question}
    
Article headline: {headline}
Article description: {description[:300]}

Analyze this article's impact on the market question."""

    try:
        r = requests.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": temperature,
                "max_tokens": 150,
            },
            timeout=15,
        )
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            # Parse JSON from response
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1].strip()
                if content.startswith("json"):
                    content = content[4:].strip()
            return json.loads(content)
    except Exception:
        pass
    
    return _keyword_fallback(headline, description, market_question)


def analyze_with_ollama(headline: str, description: str, market_question: str,
                        ollama_url: str, model: str) -> dict:
    """Call local Ollama for sentiment analysis."""
    user_msg = f"Market: {market_question}\nHeadline: {headline}\nDescription: {description[:200]}"
    
    try:
        r = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "stream": False,
            },
            timeout=30,
        )
        if r.status_code == 200:
            content = r.json()["message"]["content"]
            return json.loads(content)
    except Exception:
        pass
    
    return _keyword_fallback(headline, description, market_question)


def _keyword_fallback(headline: str, description: str, market_question: str) -> dict:
    """Simple keyword-based sentiment when no LLM available."""
    text = (headline + " " + description).lower()
    
    pos_words = ["approve", "pass", "win", "gain", "rise", "surge", "support",
                 "agree", "success", "positive", "bullish", "increase", "grow"]
    neg_words = ["reject", "fail", "lose", "drop", "fall", "crash", "oppose",
                 "deny", "block", "negative", "bearish", "decrease", "decline"]
    
    pos = sum(1 for w in pos_words if w in text)
    neg = sum(1 for w in neg_words if w in text)
    total = pos + neg
    
    if total == 0:
        return {"sentiment": "neutral", "sentiment_score": 0.0, "relevance": 0.3}
    
    score = (pos - neg) / total
    sentiment = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral"
    
    # Rough relevance: do market question words appear in article?
    q_words = set(market_question.lower().split()) - {"will", "the", "a", "be", "by", "in", "of", "?"}
    t_words = set(text.split())
    overlap = len(q_words & t_words) / max(len(q_words), 1)
    
    return {"sentiment": sentiment, "sentiment_score": round(score, 2), "relevance": round(min(overlap, 1.0), 2)}


def analyze_news_df(news_df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Run sentiment analysis on all articles in the DataFrame."""
    if news_df.empty:
        return news_df
    
    llm_cfg = cfg["llm"]
    backend = llm_cfg["backend"]
    api_key = llm_cfg.get("api_key", "") or os.environ.get("LLM_API_KEY", "")
    
    results = []
    for _, row in news_df.iterrows():
        headline = row.get("headline", "")
        desc = row.get("description", "")
        question = row.get("market_question", "")
        
        if backend == "openai_compatible" and api_key:
            result = analyze_with_api(
                headline, desc, question,
                llm_cfg["api_base"], api_key, llm_cfg["model"], llm_cfg.get("temperature", 0.1),
            )
        elif backend == "ollama":
            result = analyze_with_ollama(
                headline, desc, question,
                llm_cfg["ollama_url"], llm_cfg["ollama_model"],
            )
        else:
            result = _keyword_fallback(headline, desc, question)
        
        results.append(result)
    
    news_df = news_df.copy()
    news_df["sentiment"] = [r.get("sentiment", "neutral") for r in results]
    news_df["sentiment_score"] = [r.get("sentiment_score", 0.0) for r in results]
    news_df["relevance"] = [r.get("relevance", 0.0) for r in results]
    
    return news_df
