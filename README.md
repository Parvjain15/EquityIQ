<h1 align="center">EquityIQ</h1>

<p align="center">
  <b>Grow your wealth with AI-powered insights.</b><br/>
  An equity research platform built for retail investors — screen, analyse, and value stocks with AI in one place.
</p>

<p align="center">
  <a href="https://equityiq-a5aoq8iq3aclmvs2nlmd9g.streamlit.app/"><b>🚀 Live Demo</b></a> ·
  <a href="#features">Features</a> ·
  <a href="#tech-stack">Tech Stack</a> ·
  <a href="#getting-started">Getting Started</a>
</p>

---

## Overview

Professional equity research tools cost thousands per year and are locked behind institutional paywalls. EquityIQ brings that workflow — screening, fundamental analysis, valuation, and news sentiment — into a single open platform for retail investors. Upload an annual report and get an instant AI-generated breakdown. Filter 550+ stocks across the S&P 500 and Nifty 50 using 30+ criteria. Run a DCF valuation. Track live market sentiment. All from one dashboard.

## Features

- **🔍 Stock Screener** — Filter 550+ stocks across the S&P 500 and Nifty 50 with 30+ configurable filters (market cap, P/E, growth, sector, etc.)
- **📄 Annual Report Analysis** — Upload a 10-K or annual report and get an instant AI breakdown of strategy, risks, and financials
- **💰 DCF Valuation** — Run discounted cash flow models with adjustable assumptions and visualise intrinsic value vs. market price
- **📰 Live News Sentiment** — Real-time news ingestion with LLM-based sentiment scoring per ticker
- **⚖️ Stock Comparison** — Side-by-side comparison of fundamentals, valuation multiples, and performance
- **📊 Quarterly Insights** — Earnings highlights and trend visualisations across reporting periods
- **📡 Market Pulse** — Live indices dashboard tracking S&P 500, Nifty 50, NASDAQ, and more
- **🎯 Watchlist** — Track stocks of interest with personalised alerts

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend & App** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Visualisation** | Plotly |
| **AI / LLM** | Google Gemini, Groq (Llama 3.3) |
| **Market Data** | yfinance, Finnhub API |
| **Deployment** | Streamlit Community Cloud |

## Getting Started

```bash
# Clone the repository
git clone https://github.com/Parvjain15/EquityIQ.git
cd EquityIQ

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see below)
cp .env.example .env

# Run the app
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) to view the app.

## Environment Variables

```
GEMINI_API_KEY=
GROQ_API_KEY=
FINNHUB_API_KEY=
```

> `yfinance` doesn't require an API key.

## How It Works

1. **Pick a stock or upload a report** — Search across 550+ tickers or drop in a PDF annual report
2. **Screen and filter** — Narrow your universe with 30+ filters built for fundamental investors
3. **Analyse with AI** — Gemini and Groq/Llama process reports and news in real time
4. **Value and compare** — Run DCF models, compare peers, and track sentiment side-by-side

## Project Structure

- `app.py` — Main Streamlit entry point
- `pages/` — Multi-page Streamlit modules (screener, analysis, compare, watchlist)
- `utils/` — Data fetchers (yfinance, Finnhub), AI wrappers (Gemini, Groq), valuation models
- `requirements.txt` — Python dependencies

## Disclaimer

EquityIQ is built for educational and research purposes only. It is **not** financial advice. Always do your own research and consult a qualified financial advisor before making investment decisions.

## Author

**Parv Jain** — [Portfolio](https://parv.is-a.dev) · [LinkedIn](https://www.linkedin.com/in/parv-jain-424a60383) · [GitHub](https://github.com/Parvjain15)

---

<p align="center"><i>If you found this project interesting, consider giving it a ⭐</i></p>
