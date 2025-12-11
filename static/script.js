async function analyzeMarket() {
    const userInput = document.getElementById('userInput').value;
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const btnText = document.getElementById('btnText');
    const analyzeBtn = document.getElementById('analyzeBtn');

    if (!userInput.trim()) {
        alert("社会情勢を入力してください。");
        return;
    }

    // UI Updates
    loading.classList.remove('hidden');
    results.classList.add('hidden');
    analyzeBtn.disabled = true;
    btnText.textContent = "分析中...";

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: userInput }),
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayResults(data);
        } else {
            alert('エラーが発生しました: ' + data.message);
        }

    } catch (error) {
        console.error('Error:', error);
        alert('通信エラーが発生しました。');
    } finally {
        loading.classList.add('hidden');
        analyzeBtn.disabled = false;
        btnText.textContent = "量子分析を開始";
    }
}

function displayResults(data) {
    const results = document.getElementById('results');
    const tickerList = document.getElementById('tickerList');
    const riskValue = document.getElementById('riskValue');
    const regimeValue = document.getElementById('regimeValue');

    // Update Ticker List
    tickerList.innerHTML = '';
    data.result.selected_tickers.forEach(ticker => {
        const li = document.createElement('li');
        li.textContent = ticker;
        li.style.animation = 'fadeIn 0.5s ease-out';
        tickerList.appendChild(li);
    });

    // Update Values
    const riskPercentage = (data.result.risk_probability * 100).toFixed(1);
    riskValue.textContent = `${riskPercentage}%`;
    
    // Determine Regime (Just a heuristic based on available tickers or randomness for now in display)
    // In real app, backend sends the regime name.
    // Let's deduce from Logic in backend: 
    // tickers: Gold/Utility -> Defensive
    // tickers: Tech/Crypto -> Aggressive
    
    let regime = "Balanced (中立)";
    const tickers = data.regime_data.tickers;
    if (tickers.includes("Gold")) regime = "Defensive (守り)";
    if (tickers.includes("Crypto")) regime = "Aggressive (攻め)";
    
    regimeValue.textContent = regime;

    // Show Results
    results.classList.remove('hidden');
}
