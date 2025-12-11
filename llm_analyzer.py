"""
LLM Analyzer Module - Gemini API Integration
Analyzes market conditions using Google's Gemini AI
"""
import os
import json
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def analyze_with_llm(user_input: str) -> dict:
    """
    Use Gemini to analyze market conditions and extract structured insights.
    
    Returns:
        dict with keys: regime, sectors, reasoning, tickers
    """
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not set. Using fallback analysis.")
        return fallback_analysis(user_input)
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        prompt = f"""あなたは金融市場のエキスパートアナリストです。
以下のユーザー入力を分析し、投資戦略を提案してください。

ユーザー入力: {user_input}

以下のJSON形式で回答してください（他の説明は不要）:
{{
    "regime": "aggressive" または "defensive" または "neutral",
    "sectors": ["推奨セクター1", "推奨セクター2", "推奨セクター3"],
    "reasoning": "判断理由を1-2文で",
    "tickers": ["AAPL", "GOOGL", "MSFT", "AMZN"]  // 推奨する具体的な米国株ティッカー4つ
}}

注意:
- aggressive: 成長株・テック株・暗号資産関連を推奨
- defensive: 金・公益・債券・生活必需品を推奨  
- neutral: バランス型・インデックス連動を推奨
- tickersは必ず実在する米国株のティッカーシンボルを4つ選んでください
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        # Validate required fields
        if not all(k in result for k in ["regime", "sectors", "tickers"]):
            raise ValueError("Missing required fields in LLM response")
            
        return result
        
    except Exception as e:
        print(f"LLM analysis failed: {e}")
        return fallback_analysis(user_input)

def fallback_analysis(user_input: str) -> dict:
    """
    Fallback keyword-based analysis when LLM is unavailable.
    """
    input_lower = user_input.lower()
    
    if any(word in input_lower for word in ["inflation", "インフレ", "war", "戦争", "recession", "不況", "守り"]):
        return {
            "regime": "defensive",
            "sectors": ["Gold", "Utilities", "Consumer Staples"],
            "reasoning": "防衛的な市場環境のため、安全資産を推奨",
            "tickers": ["GLD", "XLU", "KO", "JNJ"]
        }
    elif any(word in input_lower for word in ["growth", "成長", "tech", "テック", "boom", "攻め", "AI", "半導体"]):
        return {
            "regime": "aggressive",
            "sectors": ["Technology", "Semiconductors", "AI"],
            "reasoning": "成長期待が高い環境のため、テック株を推奨",
            "tickers": ["NVDA", "GOOGL", "MSFT", "AMD"]
        }
    else:
        return {
            "regime": "neutral",
            "sectors": ["S&P500", "Diversified"],
            "reasoning": "不確実な環境のため、分散投資を推奨",
            "tickers": ["SPY", "AAPL", "MSFT", "AMZN"]
        }
