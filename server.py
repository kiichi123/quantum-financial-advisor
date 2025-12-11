"""
Quantum Financial Advisor - Flask Server
Production-ready web server with LLM and real stock data integration
"""
from flask import Flask, render_template, request, jsonify
import numpy as np
import traceback
import requests
from bs4 import BeautifulSoup
import os

# Import our modules
import quantum_lib

app = Flask(__name__)

def get_text_from_url(url):
    """Scrape text content from a URL."""
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Extract title and paragraphs
        text = soup.title.string if soup.title else ""
        for p in soup.find_all('p'):
            text += " " + p.get_text()
        return text[:5000]
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return ""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        user_input = data.get('text', '').strip()
        
        if not user_input:
            return jsonify({'status': 'error', 'message': '入力が空です'}), 400
        
        # Check if input is a URL
        if user_input.startswith('http://') or user_input.startswith('https://'):
            print(f"URL detected: {user_input}")
            scraped_text = get_text_from_url(user_input)
            if scraped_text:
                user_input = scraped_text
            else:
                return jsonify({'status': 'error', 'message': 'URLからテキストを取得できませんでした'}), 400
        
        # 1. Market Analysis (LLM + Real Data)
        analysis = quantum_lib.analyze_market(user_input)
        
        tickers = analysis["tickers"]
        mu = analysis["mu"]
        sigma = analysis["sigma"]
        
        # 2. Quantum Optimization
        budget = min(2, len(tickers))  # Select 2 stocks
        selection_binary, optimal_value = quantum_lib.run_quantum_portfolio_optimization(
            mu, sigma, budget=budget
        )
        
        # Get selected tickers
        selected_tickers = []
        selected_names = []
        weights = []
        indices = [i for i, x in enumerate(selection_binary) if x > 0.5]
        
        for i in indices:
            selected_tickers.append(tickers[i])
            selected_names.append(analysis["names"][i] if i < len(analysis["names"]) else tickers[i])
            weights.append(1.0 / len(indices) if indices else 0)
            
        # 3. Calculate Risk (Quantum VaR)
        risk_prob = quantum_lib.calculate_risk_qae(selection_binary, mu, sigma)
        
        # Calculate expected return for selected portfolio
        if indices:
            expected_return = sum(mu[i] * (1.0/len(indices)) for i in indices)
        else:
            expected_return = 0
        
        return jsonify({
            'status': 'success',
            'analysis': {
                'regime': analysis.get('regime', 'neutral'),
                'sectors': analysis.get('sectors', []),
                'reasoning': analysis.get('reasoning', ''),
                'synthetic': analysis.get('synthetic', False)
            },
            'candidates': {
                'tickers': tickers,
                'names': analysis.get('names', tickers),
                'returns_1y': analysis.get('returns_1y', [])
            },
            'result': {
                'selected_tickers': selected_tickers,
                'selected_names': selected_names,
                'weights': weights,
                'expected_return': float(expected_return),
                'risk_probability': float(risk_prob),
                'optimal_value': float(optimal_value)
            }
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'gemini_configured': bool(os.environ.get('GEMINI_API_KEY')),
        'finnhub_configured': bool(os.environ.get('FINNHUB_API_KEY'))
    })

if __name__ == '__main__':
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    
    if is_production:
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        app.run(debug=True, port=port)
