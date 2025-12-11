"""
Stock Data Module - Real-time stock data using yfinance
Fetches actual market data and calculates statistics for optimization
"""
import yfinance as yf
import numpy as np
import pandas as pd
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_stock_data(tickers_tuple: tuple, period: str = "1y") -> dict:
    """
    Fetch stock data for given tickers.
    Uses caching to avoid hitting rate limits.
    
    Args:
        tickers_tuple: Tuple of ticker symbols (tuple for caching)
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        dict with mu (expected returns), sigma (covariance matrix), names
    """
    tickers = list(tickers_tuple)
    
    try:
        # Download data
        data = yf.download(tickers, period=period, progress=False, auto_adjust=True)
        
        if data.empty:
            raise ValueError("No data returned from yfinance")
        
        # Handle single ticker case
        if len(tickers) == 1:
            prices = data["Close"].to_frame()
            prices.columns = tickers
        else:
            prices = data["Close"]
        
        # Calculate daily returns
        returns = prices.pct_change().dropna()
        
        if len(returns) < 20:
            raise ValueError("Insufficient data points")
        
        # Annualized expected returns (252 trading days)
        mu = returns.mean().values * 252
        
        # Annualized covariance matrix
        sigma = returns.cov().values * 252
        
        # Get company names
        names = []
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).info
                names.append(info.get("shortName", ticker))
            except:
                names.append(ticker)
        
        return {
            "tickers": tickers,
            "names": names,
            "mu": mu,
            "sigma": sigma,
            "last_prices": prices.iloc[-1].values.tolist(),
            "returns_1y": ((prices.iloc[-1] / prices.iloc[0]) - 1).values.tolist()
        }
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return generate_synthetic_data(tickers)

def generate_synthetic_data(tickers: list) -> dict:
    """
    Generate synthetic data when real data is unavailable.
    """
    n = len(tickers)
    np.random.seed(42)
    
    # Random expected returns (5-15% annually)
    mu = np.random.uniform(0.05, 0.15, n)
    
    # Random covariance matrix (positive semi-definite)
    A = np.random.uniform(-0.1, 0.1, (n, n))
    sigma = np.dot(A, A.T) + np.eye(n) * 0.04
    
    return {
        "tickers": tickers,
        "names": tickers,
        "mu": mu,
        "sigma": sigma,
        "last_prices": [100.0] * n,
        "returns_1y": mu.tolist(),
        "synthetic": True
    }

def get_sector_tickers(sector: str) -> list:
    """
    Get representative tickers for a given sector.
    """
    sector_map = {
        "technology": ["AAPL", "MSFT", "GOOGL", "META"],
        "semiconductors": ["NVDA", "AMD", "INTC", "TSM"],
        "ai": ["NVDA", "GOOGL", "MSFT", "PLTR"],
        "energy": ["XOM", "CVX", "COP", "SLB"],
        "utilities": ["NEE", "DUK", "SO", "D"],
        "healthcare": ["JNJ", "UNH", "PFE", "MRK"],
        "financials": ["JPM", "BAC", "GS", "MS"],
        "consumer": ["AMZN", "WMT", "COST", "TGT"],
        "gold": ["GLD", "GDX", "NEM", "GOLD"],
        "defensive": ["JNJ", "PG", "KO", "PEP"],
        "growth": ["TSLA", "NVDA", "AMZN", "GOOGL"],
    }
    
    return sector_map.get(sector.lower(), ["SPY", "QQQ", "DIA", "IWM"])

def clear_cache():
    """Clear the stock data cache."""
    get_stock_data.cache_clear()
