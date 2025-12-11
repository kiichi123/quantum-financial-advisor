from flask import Flask, render_template, request, jsonify
import quantum_lib
import numpy as np
import traceback
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def get_text_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        # Extract title and paragraphs
        text = soup.title.string if soup.title else ""
        for p in soup.find_all('p'):
            text += " " + p.get_text()
        return text[:5000] # Limit length
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
        
        # Check if input is a URL
        if user_input.startswith('http://') or user_input.startswith('https://'):
            print(f"URL detected: {user_input}")
            scraped_text = get_text_from_url(user_input)
            if scraped_text:
                print("Successfully scraped text.")
                user_input = scraped_text
            else:
                return jsonify({'status': 'error', 'message': 'URLからテキストを取得できませんでした。'}), 400
        
        # 1. Market Analysis (Regime Detection)
        tickers, mu, sigma = quantum_lib.analyze_market(user_input)
        
        # 2. Quantum Optimization (VQE/QAOA)
        budget = 2
        selection_binary, optimal_value = quantum_lib.run_quantum_portfolio_optimization(mu, sigma, budget=budget)
        
        selected_tickers = []
        indices = [i for i, x in enumerate(selection_binary) if x > 0.5]
        for i in indices:
            selected_tickers.append(tickers[i])
            
        # 3. Calculate Risk (Quantum VaR)
        risk_prob = quantum_lib.calculate_risk_qae(selection_binary, mu, sigma)
        
        return jsonify({
            'status': 'success',
            'regime_data': {
                'tickers': tickers,
                'mu': mu.tolist(),
                'sigma': sigma.tolist()
            },
            'result': {
                'selected_tickers': selected_tickers,
                'optimal_value': float(optimal_value),
                'risk_probability': float(risk_prob)
            }
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

import os

if __name__ == '__main__':
    # Use environment variable for production vs development
    is_production = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    
    if is_production:
        # Production: Gunicorn will handle this, but fallback
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development
        app.run(debug=True, port=port)
