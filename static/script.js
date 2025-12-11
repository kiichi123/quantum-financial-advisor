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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: userInput }),
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayResults(data);
        } else {
            alert('エラー: ' + data.message);
        }

    } catch (error) {
        console.error('Error:', error);
        alert('通信エラーが発生しました。');
    } finally {
        loading.classList.add('hidden');
        analyzeBtn.disabled = false;
        btnText.textContent = "🚀 量子分析を開始";
    }
}

function displayResults(data) {
    const results = document.getElementById('results');

    // Regime Badge
    const regimeBadge = document.getElementById('regimeBadge');
    const regime = data.analysis.regime;
    const regimeLabels = {
        'aggressive': '🚀 攻撃的 (Aggressive)',
        'defensive': '🛡️ 防御的 (Defensive)',
        'neutral': '⚖️ 中立 (Neutral)'
    };
    regimeBadge.textContent = regimeLabels[regime] || regime;
    regimeBadge.className = 'regime-badge ' + regime;

    // Reasoning
    document.getElementById('reasoning').textContent = data.analysis.reasoning || '-';

    // Sectors
    const sectorsDiv = document.getElementById('sectors');
    sectorsDiv.innerHTML = '';
    (data.analysis.sectors || []).forEach(sector => {
        const tag = document.createElement('span');
        tag.className = 'sector-tag';
        tag.textContent = sector;
        sectorsDiv.appendChild(tag);
    });

    // Selected Stocks
    const selectedStocks = document.getElementById('selectedStocks');
    selectedStocks.innerHTML = '';
    data.result.selected_tickers.forEach((ticker, i) => {
        const name = data.result.selected_names?.[i] || ticker;
        const weight = data.result.weights?.[i] || 0;

        const item = document.createElement('div');
        item.className = 'stock-item';
        item.innerHTML = `
            <div>
                <span class="ticker">${ticker}</span>
                <span class="name">${name}</span>
            </div>
            <span class="weight">${(weight * 100).toFixed(0)}%</span>
        `;
        selectedStocks.appendChild(item);
    });

    // Expected Return
    const expectedReturn = data.result.expected_return || 0;
    document.getElementById('expectedReturn').textContent =
        (expectedReturn >= 0 ? '+' : '') + (expectedReturn * 100).toFixed(1) + '%';

    // Risk
    const riskPercentage = (data.result.risk_probability * 100).toFixed(1);
    document.getElementById('riskValue').textContent = `${riskPercentage}%`;

    // Candidate Stocks
    const candidateStocks = document.getElementById('candidateStocks');
    candidateStocks.innerHTML = '';
    data.candidates.tickers.forEach((ticker, i) => {
        const name = data.candidates.names?.[i] || ticker;
        const returnVal = data.candidates.returns_1y?.[i] || 0;
        const returnClass = returnVal >= 0 ? 'positive' : 'negative';

        const item = document.createElement('div');
        item.className = 'candidate-item';
        item.innerHTML = `
            <div class="ticker">${ticker}</div>
            <div class="name" style="font-size:0.75rem;color:#64748b;">${name}</div>
            <div class="return ${returnClass}">
                ${returnVal >= 0 ? '+' : ''}${(returnVal * 100).toFixed(1)}% (1Y)
            </div>
        `;
        candidateStocks.appendChild(item);
    });

    // Data source
    const dataSource = document.getElementById('dataSource');
    if (data.analysis.synthetic) {
        dataSource.textContent = '⚠️ シミュレーションデータを使用中（実データ取得に失敗）';
        dataSource.style.color = '#fbbf24';
    } else {
        dataSource.textContent = '✓ Yahoo Finance からリアルタイムデータを取得';
        dataSource.style.color = '#4ade80';
    }

    results.classList.remove('hidden');
}
