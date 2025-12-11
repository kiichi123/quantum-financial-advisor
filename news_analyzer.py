"""
News Analyzer Module - Finnhub API Integration
Fetches news and sentiment data for market analysis
"""
import os
import finnhub
from datetime import datetime, timedelta
from functools import lru_cache

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")

def get_finnhub_client():
    """Get Finnhub client if API key is available."""
    if not FINNHUB_API_KEY:
        return None
    return finnhub.Client(api_key=FINNHUB_API_KEY)

@lru_cache(maxsize=50)
def get_stock_sentiment(ticker: str) -> dict:
    """
    Get sentiment data for a specific stock.
    
    Returns:
        dict with bullish/bearish scores and news buzz
    """
    client = get_finnhub_client()
    if not client:
        return get_fallback_sentiment(ticker)
    
    try:
        sentiment = client.news_sentiment(ticker)
        
        if not sentiment or 'sentiment' not in sentiment:
            return get_fallback_sentiment(ticker)
        
        return {
            "ticker": ticker,
            "bullish": sentiment.get("sentiment", {}).get("bullishPercent", 0.5),
            "bearish": sentiment.get("sentiment", {}).get("bearishPercent", 0.5),
            "buzz": sentiment.get("buzz", {}).get("buzz", 0),
            "articles_in_last_week": sentiment.get("buzz", {}).get("articlesInLastWeek", 0),
            "company_news_score": sentiment.get("companyNewsScore", 0.5),
            "sector_average_score": sentiment.get("sectorAverageNewsScore", 0.5),
        }
    except Exception as e:
        print(f"Finnhub sentiment error for {ticker}: {e}")
        return get_fallback_sentiment(ticker)

def get_market_news(category: str = "general", limit: int = 5) -> list:
    """
    Get general market news.
    
    Args:
        category: 'general', 'forex', 'crypto', 'merger'
    """
    client = get_finnhub_client()
    if not client:
        return []
    
    try:
        news = client.general_news(category, min_id=0)
        return news[:limit] if news else []
    except Exception as e:
        print(f"Finnhub news error: {e}")
        return []

def get_company_news(ticker: str, days: int = 7, limit: int = 5) -> list:
    """Get news for a specific company."""
    client = get_finnhub_client()
    if not client:
        return []
    
    try:
        today = datetime.now()
        from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        
        news = client.company_news(ticker, _from=from_date, to=to_date)
        return news[:limit] if news else []
    except Exception as e:
        print(f"Finnhub company news error for {ticker}: {e}")
        return []

def aggregate_sentiment(tickers: list) -> dict:
    """
    Aggregate sentiment across multiple tickers.
    
    Returns:
        dict with overall sentiment score and breakdown
    """
    if not tickers:
        return {"overall": 0.5, "breakdown": []}
    
    sentiments = []
    for ticker in tickers:
        s = get_stock_sentiment(ticker)
        sentiments.append(s)
    
    # Calculate weighted average (by company news score)
    total_score = 0
    total_weight = 0
    
    for s in sentiments:
        weight = s.get("company_news_score", 0.5)
        bullish = s.get("bullish", 0.5)
        total_score += bullish * weight
        total_weight += weight
    
    overall = total_score / total_weight if total_weight > 0 else 0.5
    
    return {
        "overall": overall,
        "overall_label": "Bullish" if overall > 0.6 else ("Bearish" if overall < 0.4 else "Neutral"),
        "breakdown": sentiments
    }

def get_fallback_sentiment(ticker: str) -> dict:
    """Fallback sentiment when API is unavailable."""
    return {
        "ticker": ticker,
        "bullish": 0.5,
        "bearish": 0.5,
        "buzz": 0,
        "articles_in_last_week": 0,
        "company_news_score": 0.5,
        "sector_average_score": 0.5,
        "fallback": True
    }

def clear_cache():
    """Clear the sentiment cache."""
    get_stock_sentiment.cache_clear()
