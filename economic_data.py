"""
Economic Data Module - Alpha Vantage API Integration
Fetches macroeconomic indicators for market analysis
"""
import os
import requests
from functools import lru_cache
from datetime import datetime

ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

@lru_cache(maxsize=20)
def get_cpi() -> dict:
    """
    Get Consumer Price Index (CPI) - Inflation indicator.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return get_fallback_cpi()
    
    try:
        params = {
            "function": "CPI",
            "interval": "monthly",
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if "data" not in data or not data["data"]:
            return get_fallback_cpi()
        
        latest = data["data"][0]
        previous = data["data"][1] if len(data["data"]) > 1 else latest
        
        current_cpi = float(latest["value"])
        previous_cpi = float(previous["value"])
        yoy_change = ((current_cpi - previous_cpi) / previous_cpi) * 100
        
        return {
            "name": "CPI (消費者物価指数)",
            "value": current_cpi,
            "date": latest["date"],
            "yoy_change": yoy_change,
            "interpretation": "High" if yoy_change > 3 else ("Low" if yoy_change < 1 else "Moderate")
        }
    except Exception as e:
        print(f"Error fetching CPI: {e}")
        return get_fallback_cpi()

@lru_cache(maxsize=20)
def get_federal_funds_rate() -> dict:
    """
    Get Federal Funds Rate - Interest rate set by the Fed.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return get_fallback_fed_rate()
    
    try:
        params = {
            "function": "FEDERAL_FUNDS_RATE",
            "interval": "monthly",
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if "data" not in data or not data["data"]:
            return get_fallback_fed_rate()
        
        latest = data["data"][0]
        
        rate = float(latest["value"])
        
        return {
            "name": "Federal Funds Rate (政策金利)",
            "value": rate,
            "date": latest["date"],
            "interpretation": "Tight" if rate > 4 else ("Loose" if rate < 2 else "Neutral")
        }
    except Exception as e:
        print(f"Error fetching Fed Rate: {e}")
        return get_fallback_fed_rate()

@lru_cache(maxsize=20)
def get_gdp() -> dict:
    """
    Get Real GDP - Economic growth indicator.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return get_fallback_gdp()
    
    try:
        params = {
            "function": "REAL_GDP",
            "interval": "quarterly",
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if "data" not in data or not data["data"]:
            return get_fallback_gdp()
        
        latest = data["data"][0]
        previous = data["data"][1] if len(data["data"]) > 1 else latest
        
        current_gdp = float(latest["value"])
        previous_gdp = float(previous["value"])
        growth = ((current_gdp - previous_gdp) / previous_gdp) * 100
        
        return {
            "name": "Real GDP (実質GDP)",
            "value": current_gdp,
            "date": latest["date"],
            "growth": growth,
            "interpretation": "Growing" if growth > 0 else "Contracting"
        }
    except Exception as e:
        print(f"Error fetching GDP: {e}")
        return get_fallback_gdp()

def get_all_economic_indicators() -> dict:
    """
    Get all economic indicators in one call.
    """
    cpi = get_cpi()
    fed_rate = get_federal_funds_rate()
    gdp = get_gdp()
    
    # Determine overall economic regime
    regime = determine_economic_regime(cpi, fed_rate, gdp)
    
    return {
        "cpi": cpi,
        "fed_rate": fed_rate,
        "gdp": gdp,
        "regime": regime,
        "api_configured": bool(ALPHA_VANTAGE_API_KEY)
    }

def determine_economic_regime(cpi: dict, fed_rate: dict, gdp: dict) -> dict:
    """
    Determine overall economic regime based on indicators.
    """
    cpi_interpretation = cpi.get("interpretation", "Moderate")
    fed_interpretation = fed_rate.get("interpretation", "Neutral")
    gdp_interpretation = gdp.get("interpretation", "Growing")
    
    # Logic for regime determination
    if cpi_interpretation == "High" and fed_interpretation == "Tight":
        regime = "Stagflation Risk"
        recommendation = "defensive"
        description = "高インフレ・高金利環境。守備的な資産配分を推奨。"
    elif gdp_interpretation == "Contracting":
        regime = "Recession Risk"
        recommendation = "defensive"
        description = "景気後退リスク。債券・金などの安全資産を推奨。"
    elif cpi_interpretation == "Low" and fed_interpretation == "Loose":
        regime = "Growth Favorable"
        recommendation = "aggressive"
        description = "低インフレ・低金利環境。成長株への投資を推奨。"
    else:
        regime = "Balanced"
        recommendation = "neutral"
        description = "バランスの取れた経済環境。分散投資を推奨。"
    
    return {
        "label": regime,
        "recommendation": recommendation,
        "description": description
    }

# Fallback functions when API is not available
def get_fallback_cpi() -> dict:
    return {
        "name": "CPI (消費者物価指数)",
        "value": 3.2,
        "date": "2024-11",
        "yoy_change": 3.2,
        "interpretation": "Moderate",
        "fallback": True
    }

def get_fallback_fed_rate() -> dict:
    return {
        "name": "Federal Funds Rate (政策金利)",
        "value": 5.25,
        "date": "2024-11",
        "interpretation": "Tight",
        "fallback": True
    }

def get_fallback_gdp() -> dict:
    return {
        "name": "Real GDP (実質GDP)",
        "value": 22000,
        "date": "2024-Q3",
        "growth": 2.8,
        "interpretation": "Growing",
        "fallback": True
    }

def clear_cache():
    """Clear all cached economic data."""
    get_cpi.cache_clear()
    get_federal_funds_rate.cache_clear()
    get_gdp.cache_clear()
