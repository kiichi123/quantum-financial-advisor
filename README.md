# Quantum Financial Advisor

量子コンピューティングを活用した金融ポートフォリオ最適化ツール。

## 機能
- 社会情勢テキストまたはニュースURLから市場レジームを分析
- 量子アルゴリズム (QAOA/VQE) によるポートフォリオ最適化
- 量子振幅推定 (QAE) によるリスク分析

## デプロイ
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## ローカル実行
```bash
pip install -r requirements.txt
python server.py
# http://127.0.0.1:5000 にアクセス
```

## 技術スタック
- Flask (Python Web Framework)
- Qiskit (Quantum Computing SDK)
- Gunicorn (Production Server)
