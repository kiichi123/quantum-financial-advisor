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

    // Risk Metrics (CVaR)
    const risk = data.risk || {};

    // VaR (Value at Risk)
    const varValue = (risk.var_classical || 0) * 100;
    document.getElementById('varValue').textContent = varValue.toFixed(1) + '%';

    // CVaR (Conditional VaR / Expected Shortfall)
    const cvarValue = (risk.cvar || 0) * 100;
    document.getElementById('cvarValue').textContent = cvarValue.toFixed(1) + '%';

    // Volatility
    const volatility = (risk.volatility || 0) * 100;
    document.getElementById('volatilityValue').textContent = volatility.toFixed(1) + '%';

    // Max Drawdown
    const maxDrawdown = (risk.max_drawdown || 0) * 100;
    document.getElementById('maxDrawdownValue').textContent = maxDrawdown.toFixed(1) + '%';

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

    // Sentiment Display
    const sentiment = data.analysis.sentiment || {};
    const sentimentBar = document.getElementById('sentimentBar');
    const sentimentLabel = document.getElementById('sentimentLabel');
    const sentimentSection = document.getElementById('sentimentSection');

    if (sentiment.overall !== undefined) {
        const overallPercent = (sentiment.overall * 100).toFixed(0);
        sentimentBar.style.width = overallPercent + '%';

        // Color based on sentiment
        if (sentiment.overall > 0.6) {
            sentimentBar.style.background = 'linear-gradient(90deg, #4ade80, #22d3ee)';
            sentimentLabel.textContent = `📈 Bullish (${overallPercent}%)`;
            sentimentLabel.style.color = '#4ade80';
        } else if (sentiment.overall < 0.4) {
            sentimentBar.style.background = 'linear-gradient(90deg, #f87171, #fbbf24)';
            sentimentLabel.textContent = `📉 Bearish (${overallPercent}%)`;
            sentimentLabel.style.color = '#f87171';
        } else {
            sentimentBar.style.background = 'linear-gradient(90deg, #fbbf24, #818cf8)';
            sentimentLabel.textContent = `⚖️ Neutral (${overallPercent}%)`;
            sentimentLabel.style.color = '#fbbf24';
        }
        sentimentSection.classList.remove('hidden');
    } else {
        sentimentSection.classList.add('hidden');
    }

    // News Headlines
    const newsHeadlines = document.getElementById('newsHeadlines');
    newsHeadlines.innerHTML = '';
    (data.analysis.news_headlines || []).forEach(headline => {
        if (headline) {
            const item = document.createElement('div');
            item.className = 'news-item';
            item.textContent = '• ' + headline.substring(0, 80) + (headline.length > 80 ? '...' : '');
            newsHeadlines.appendChild(item);
        }
    });

    // Economic Indicators
    const economic = data.economic || {};

    // CPI
    const cpi = economic.cpi || {};
    const cpiChange = cpi.yoy_change || 0;
    document.getElementById('cpiValue').textContent = cpiChange.toFixed(1) + '%';
    document.getElementById('cpiValue').style.color = cpiChange > 3 ? '#f87171' : '#4ade80';

    // Federal Funds Rate
    const fedRate = economic.fed_rate || {};
    document.getElementById('fedRateValue').textContent = (fedRate.value || 0).toFixed(2) + '%';

    // GDP
    const gdp = economic.gdp || {};
    const gdpGrowth = gdp.growth || 0;
    document.getElementById('gdpValue').textContent = (gdpGrowth >= 0 ? '+' : '') + gdpGrowth.toFixed(1) + '%';
    document.getElementById('gdpValue').style.color = gdpGrowth >= 0 ? '#4ade80' : '#f87171';

    // Economic Regime
    const ecoRegime = economic.regime || {};
    document.getElementById('ecoRegimeValue').textContent = ecoRegime.label || '-';
    document.getElementById('ecoDescription').textContent = ecoRegime.description || '-';

    // Render Charts
    renderAllocationChart(data);
    renderRiskReturnChart(data);

    results.classList.remove('hidden');
}

function renderAllocationChart(data) {
    const tickers = data.result.selected_tickers || [];
    const weights = data.result.weights || [];

    if (tickers.length === 0) return;

    const chartData = [{
        values: weights.map(w => w * 100),
        labels: tickers,
        type: 'pie',
        hole: 0.4,
        marker: {
            colors: ['#38bdf8', '#818cf8', '#22d3ee', '#4ade80']
        },
        textinfo: 'label+percent',
        textposition: 'outside'
    }];

    const layout = {
        title: {
            text: 'ポートフォリオ配分',
            font: { color: '#f8fafc', size: 14 }
        },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#94a3b8' },
        margin: { t: 40, b: 30, l: 30, r: 30 },
        showlegend: false
    };

    Plotly.newPlot('allocationChart', chartData, layout, { responsive: true, displayModeBar: false });
}

function renderRiskReturnChart(data) {
    const candidates = data.candidates || {};
    const tickers = candidates.tickers || [];
    const returns = candidates.returns_1y || [];
    const selectedTickers = data.result.selected_tickers || [];

    if (tickers.length === 0) return;

    // Simulated volatility (would need real data)
    const volatilities = returns.map(r => Math.abs(r) * 0.5 + 0.1);

    const colors = tickers.map(t =>
        selectedTickers.includes(t) ? '#4ade80' : '#64748b'
    );

    const sizes = tickers.map(t =>
        selectedTickers.includes(t) ? 20 : 12
    );

    const chartData = [{
        x: volatilities.map(v => v * 100),
        y: returns.map(r => r * 100),
        mode: 'markers+text',
        type: 'scatter',
        text: tickers,
        textposition: 'top center',
        marker: {
            size: sizes,
            color: colors
        },
        textfont: { color: '#f8fafc', size: 10 }
    }];

    const layout = {
        title: {
            text: 'リスク・リターン分析',
            font: { color: '#f8fafc', size: 14 }
        },
        xaxis: {
            title: 'ボラティリティ (%)',
            color: '#94a3b8',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            title: 'リターン (%)',
            color: '#94a3b8',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#94a3b8' },
        margin: { t: 40, b: 50, l: 50, r: 30 }
    };

    Plotly.newPlot('riskReturnChart', chartData, layout, { responsive: true, displayModeBar: false });
}
