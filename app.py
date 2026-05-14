import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from financial_analyzer import FinancialAnalyzer
from news_radar import NewsRadarAnalyzer, SECTOR_TICKERS, IMPACT_CATEGORIES
from screener import (
    fetch_sp500_tickers, get_all_tickers, fetch_screener_data,
    compute_health_score as screener_health_score,
    get_upcoming_dividends,
)
from utils import (
    setup_page, format_number,
    create_metric_card, create_valuation_card, create_info_card
)

load_dotenv()

# On Streamlit Cloud, secrets live in st.secrets — inject them into os.environ
# so every os.getenv() call works without any other code changes.
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass


# ── Shared helpers ─────────────────────────────────────────────────────────────

def safe_num(val, default=0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _render_news_card(article, highlight=False):
    import html as _html

    sentiment = (article.get("sentiment") or "neutral").lower()
    urgency   = (article.get("urgency") or "low").lower()

    sentiment_styles = {
        "positive": ("#16a34a", "#f0fdf4", "#bbf7d0"),
        "negative": ("#dc2626", "#fef2f2", "#fecaca"),
        "neutral":  ("#64748b", "#f8fafc", "#e2e8f0"),
        "mixed":    ("#d97706", "#fffbeb", "#fde68a"),
    }
    urgency_styles = {
        "high":   ("#dc2626", "#fef2f2"),
        "medium": ("#d97706", "#fffbeb"),
        "low":    ("#16a34a", "#f0fdf4"),
    }
    s_txt, s_bg, s_bdr = sentiment_styles.get(sentiment, ("#64748b", "#f8fafc", "#e2e8f0"))
    u_txt, u_bg        = urgency_styles.get(urgency, ("#64748b", "#f8fafc"))

    tickers     = article.get("affected_tickers") or []
    ticker_html = "".join(f'<span class="nr-ticker-tag">{_html.escape(str(t))}</span>' for t in tickers[:6])

    # Escape text content so article data never breaks HTML structure
    title_e      = _html.escape(str(article.get("title", "")))
    source_e     = _html.escape(str(article.get("source", "")))
    pub_date_e   = _html.escape(str(article.get("publishedAt", "")))
    url          = str(article.get("url") or "#")
    summary_e    = _html.escape(str(article.get("summary") or article.get("description") or ""))
    reason_e     = _html.escape(str(article.get("reason") or ""))
    impact_e     = _html.escape(str(article.get("possible_impact") or ""))
    sector_e     = _html.escape(str(article.get("sector") or ""))
    region_e     = _html.escape(str(article.get("region") or ""))
    impact_cat_e = _html.escape(str(article.get("impact_category") or "Other"))
    ai_generated = article.get("_ai_generated", False)

    border_style = "border-left:4px solid #00d09c;background:#fafffe;" if highlight else ""

    # Build HTML with concatenation to avoid multi-line f-string markdown parsing quirks
    h = f'<div class="nr-card" style="{border_style}">'
    h += '<div class="nr-card-top"><div class="nr-badges">'
    h += f'<span class="nr-sentiment-badge" style="color:{s_txt};background:{s_bg};border:1px solid {s_bdr};">{sentiment.upper()}</span>'
    h += f'<span class="nr-urgency-badge" style="color:{u_txt};background:{u_bg};">{urgency.upper()} URGENCY</span>'
    h += f'<span class="nr-category-tag">{impact_cat_e}</span>'
    if region_e:
        h += f'<span class="nr-meta-tag">🌍 {region_e}</span>'
    if sector_e:
        h += f'<span class="nr-meta-tag">🏭 {sector_e}</span>'
    if ai_generated:
        h += '<span class="nr-meta-tag" style="color:#d97706;background:#fffbeb;border-color:#fde68a;">🤖 AI Knowledge</span>'
    h += '</div>'
    src_text = f'{source_e} · {pub_date_e}' if pub_date_e else source_e
    h += f'<div class="nr-source">{src_text}</div>'
    h += '</div>'
    h += f'<div class="nr-headline"><a href="{url}" target="_blank">{title_e}</a></div>'
    if summary_e:
        h += f'<div class="nr-summary">{summary_e}</div>'
    if reason_e:
        h += f'<div class="nr-reason"><b>Sentiment Reason:</b> {reason_e}</div>'
    if impact_e:
        h += f'<div class="nr-impact"><b>Market Impact:</b> {impact_e}</div>'
    if tickers:
        h += f'<div class="nr-tickers">{ticker_html}</div>'
    h += f'<div class="nr-read-more"><a href="{url}" target="_blank">Read full article →</a></div>'
    h += '</div>'

    st.markdown(h, unsafe_allow_html=True)


def display_results(metrics, valuation, analyzer, api_key=""):
    st.markdown("---")
    company  = metrics.get("Company Name", "Unknown")
    fy       = metrics.get("Fiscal Year", "N/A")
    currency = metrics.get("Currency", "USD")
    ticker   = metrics.get("Ticker", "")

    st.markdown(f"""
    <div class="company-header">
        <span class="company-name">{company}</span>
        <span class="fy-badge">FY {fy} · {currency}</span>
    </div>
    """, unsafe_allow_html=True)

    # Key Financials
    st.markdown('<div class="section-head">Key Financials</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        create_metric_card("Revenue", format_number(metrics.get("Revenue")))
    with c2:
        create_metric_card("Net Income", format_number(metrics.get("Net Income")))
    with c3:
        eps_val = metrics.get("EPS")
        create_metric_card("EPS", f"${eps_val}" if eps_val is not None else "N/A")
    with c4:
        create_metric_card("Free Cash Flow", format_number(metrics.get("Free Cash Flow")))

    # Financial Ratio Dashboard
    ratio_defs = [
        ("P/E Ratio",     metrics.get("PE Ratio"),       lambda v: f"{v:.1f}x"),
        ("P/B Ratio",     metrics.get("PB Ratio"),       lambda v: f"{v:.2f}x"),
        ("ROE",           metrics.get("ROE"),             lambda v: f"{v:.1%}"),
        ("ROA",           metrics.get("ROA"),             lambda v: f"{v:.1%}"),
        ("Debt / Equity", metrics.get("Debt to Equity"), lambda v: f"{(v/100 if v > 10 else v):.2f}x"),
        ("Current Ratio", metrics.get("Current Ratio"),  lambda v: f"{v:.2f}x"),
    ]
    if any(v is not None for _, v, _ in ratio_defs):
        st.markdown('<div class="section-head">Financial Ratios</div>', unsafe_allow_html=True)
        ratio_cols = st.columns(6)
        for col, (label, value, fmt) in zip(ratio_cols, ratio_defs):
            with col:
                display_val = fmt(value) if value is not None else "N/A"
                create_metric_card(label, display_val)

    # Stock Health Score
    st.markdown('<div class="section-head">Stock Health Score</div>', unsafe_allow_html=True)
    health    = analyzer.calculate_health_score(metrics)
    score     = health["score"]
    grade     = health["grade"]
    color     = health["color"]
    breakdown = health["breakdown"]

    score_col, breakdown_col = st.columns([1, 3])
    with score_col:
        st.markdown(f"""
        <div class="health-score-widget">
            <div class="health-score-number" style="color:{color};">{score}</div>
            <div class="health-score-grade" style="background:{color};">{grade}</div>
            <div class="health-score-label">Health Score / 100</div>
        </div>
        """, unsafe_allow_html=True)
    with breakdown_col:
        status_styles = {
            "excellent": ("#16a34a", "#f0fdf4"),
            "good":      ("#00b386", "#f0fdf8"),
            "fair":      ("#d97706", "#fffbeb"),
            "weak":      ("#ea580c", "#fff7ed"),
            "poor":      ("#dc2626", "#fef2f2"),
            "neutral":   ("#94a3b8", "#f5f5f6"),
        }
        pills_html = ""
        for name, data in breakdown.items():
            txt_color, bg_color = status_styles.get(data["status"], ("#94a3b8", "#f5f5f6"))
            pills_html += f"""
            <div class="health-pill" style="border-color:{txt_color};background:{bg_color};">
                <span class="hp-name">{name}</span>
                <span class="hp-value" style="color:{txt_color};">{data['label']}</span>
                <span class="hp-pts" style="color:{txt_color};">{data['pts']}/{data['max']} pts</span>
            </div>"""
        st.markdown(f'<div class="health-breakdown">{pills_html}</div>', unsafe_allow_html=True)

    # Intrinsic Valuation
    st.markdown('<div class="section-head">Intrinsic Valuation</div>', unsafe_allow_html=True)
    v1, v2 = st.columns(2)
    with v1:
        dcf    = valuation.get("DCF Value", 0)
        growth = valuation.get("Assumptions", {}).get("Growth Rate", "5.0%")
        create_valuation_card(
            "DCF Model", f"${dcf:,.2f}",
            f"5-year projection · {growth} growth · 10% discount",
            tooltip="Discounted Cash Flow (DCF) estimates a company's value by projecting its future cash flows and discounting them back to today's value using a required rate of return."
        )
    with v2:
        graham = valuation.get("Graham Number", 0)
        bvps   = valuation.get("Book Value Per Share", 0)
        create_valuation_card(
            "Graham Number", f"${graham:,.2f}",
            f"BVPS: ${bvps:,.2f} · Conservative estimate",
            tooltip="The Graham Number, developed by Benjamin Graham, calculates the maximum fair price for a stock using its EPS and book value per share. Formula: √(22.5 × EPS × BVPS)"
        )

    # Financial Snapshot Chart
    st.markdown('<div class="section-head">Financial Snapshot</div>', unsafe_allow_html=True)
    chart_keys = ["Revenue", "Net Income", "Free Cash Flow", "Total Assets", "Total Liabilities"]
    labels     = ["Revenue", "Net Income", "FCF", "Assets", "Liabilities"]
    values     = [safe_num(metrics.get(k)) for k in chart_keys]
    colors     = ['#818cf8', '#06b6d4', '#a78bfa', '#34d399', '#f87171']

    fig = go.Figure(data=[go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, line=dict(color='rgba(255,255,255,0.05)', width=1)),
        hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'
    )])
    fig.update_layout(
        template="plotly_white", paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        font=dict(family="Inter", size=13, color="#44475b"),
        xaxis=dict(gridcolor='#f0f0f2'), yaxis=dict(gridcolor='#f0f0f2'),
        margin=dict(l=20, r=20, t=20, b=40), height=350, hovermode="x unified"
    )
    st.plotly_chart(fig, width="stretch")

    # Analysis Details
    st.markdown('<div class="section-head">Analysis Details</div>', unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    with r1:
        risks     = metrics.get("Risk Factors", [])
        risk_html = "<br>".join([f"• {r}" for r in risks]) if risks else "No risks identified"
        create_info_card("Risk Factors", risk_html)
    with r2:
        notes = metrics.get("Notes", "No additional notes.")
        create_info_card("AI Analyst Notes", notes)

    # Investment Memo
    if api_key and len(api_key) > 10:
        st.markdown('<div class="section-head">Investment Memo</div>', unsafe_allow_html=True)
        memo_key = f"memo_{company}_{ticker}"

        if memo_key not in st.session_state:
            if st.button("📝 Generate Investment Memo", key=f"memo_btn_{ticker}_{company}"):
                with st.spinner("Generating investment memo..."):
                    current_price_for_memo = analyzer.get_current_price(ticker) if ticker else None
                    memo_text = analyzer.generate_investment_memo(metrics, valuation, current_price_for_memo)
                    st.session_state[memo_key] = memo_text
                    st.rerun()

        if memo_key in st.session_state:
            memo_text  = st.session_state[memo_key]
            memo_lines = memo_text.split("\n")
            formatted_memo = ""
            for line in memo_lines:
                stripped = line.strip()
                if not stripped:
                    formatted_memo += '<div style="height:6px"></div>'
                elif stripped[:2] in ("1.", "2.", "3.", "4.", "5.", "6.", "7.") or stripped.isupper():
                    formatted_memo += f'<div class="memo-section-title">{stripped}</div>'
                else:
                    formatted_memo += f'<div class="memo-line">{stripped}</div>'

            st.markdown(f"""
            <div class="memo-card">
                <div class="memo-header">
                    <span class="memo-title">Investment Memo — {company}</span>
                    <span class="memo-badge">AI Generated</span>
                </div>
                <div class="memo-body">{formatted_memo}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔄 Regenerate Memo", key=f"memo_regen_{ticker}_{company}"):
                del st.session_state[memo_key]
                st.rerun()

    # Latest News
    if ticker:
        news_articles = analyzer.get_recent_news(ticker, max_items=3)
        if news_articles:
            st.markdown('<div class="section-head">Latest News</div>', unsafe_allow_html=True)
            for article in news_articles:
                pub     = article.get("published", "")
                pub_str = f'<span>🕒 {pub}</span>' if pub else ""
                st.markdown(f"""
                <div class="news-card">
                    <div class="news-title"><a href="{article['link']}" target="_blank">{article['title']}</a></div>
                    <div class="news-meta">
                        <span>📰 {article['publisher']}</span>{pub_str}
                        <span><a href="{article['link']}" target="_blank" style="color:#a5b4fc;font-size:0.73rem;">Read more →</a></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Investment Verdict
    if ticker:
        st.markdown('<div class="section-head">Investment Verdict</div>', unsafe_allow_html=True)
        current_price = analyzer.get_current_price(ticker)
        if current_price is not None:
            dcf_val    = safe_num(valuation.get("DCF Value"))
            graham_val = safe_num(valuation.get("Graham Number"))
            avg_intrinsic = 0
            count = 0
            if dcf_val > 0:
                avg_intrinsic += dcf_val
                count += 1
            if graham_val > 0:
                avg_intrinsic += graham_val
                count += 1
            avg_intrinsic = avg_intrinsic / count if count > 0 else 0

            if avg_intrinsic > 0:
                margin = ((avg_intrinsic - current_price) / current_price) * 100
                if margin > 15:
                    signal, signal_class, card_class, emoji = "BUY", "buy", "verdict-buy", "🟢"
                    explanation = f"The stock appears <b>undervalued</b>. Fair value (${avg_intrinsic:,.2f}) is <b>{margin:.1f}% above</b> market price."
                elif margin < -15:
                    signal, signal_class, card_class, emoji = "SELL / AVOID", "sell", "verdict-sell", "🔴"
                    explanation = f"The stock appears <b>overvalued</b>. Price is <b>{abs(margin):.1f}% above</b> fair value (${avg_intrinsic:,.2f})."
                else:
                    signal, signal_class, card_class, emoji = "HOLD", "hold", "verdict-hold", "🟡"
                    explanation = f"Trading <b>near fair value</b> (${avg_intrinsic:,.2f}). No strong signal."

                st.markdown(f"""
                <div class="verdict-card {card_class}">
                    <div style="font-size:0.8rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">{ticker} · Current Market Price</div>
                    <div class="verdict-price">${current_price:,.2f}</div>
                    <div class="verdict-signal {signal_class}">{emoji} {signal}</div>
                    <div class="verdict-explain">{explanation}</div>
                    <div style="margin-top:14px;font-size:0.75rem;color:#94a3b8;">⚠️ Not financial advice. Always do your own research.</div>
                </div>
                """, unsafe_allow_html=True)

    _render_trust_footer()


def _render_trust_footer():
    st.markdown("""
    <div class="trust-footer">
        <div class="trust-badges">
            <div class="trust-badge"><span class="badge-icon">🔒</span> Data never stored</div>
            <div class="trust-badge"><span class="badge-icon">📊</span> DCF &amp; Graham Models</div>
            <div class="trust-badge"><span class="badge-icon">🌐</span> Real-time pricing</div>
            <div class="trust-badge"><span class="badge-icon">🛡️</span> For educational use only</div>
        </div>
        <div class="trust-legal">
            EquityIQ is for educational and informational purposes only. Not financial advice.<br>
            Always consult a qualified financial advisor before making investment decisions.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Topbar ─────────────────────────────────────────────────────────────────────

def _render_topbar(current_page: str):
    nav_items = [
        ("ticker",       "Stocks"),
        ("screener",     "Screener"),
        ("pdf",          "Analysis"),
        ("compare",      "Compare"),
        ("quarterly",    "Quarterly"),
        ("market-pulse", "Market Pulse"),
        ("news-radar",   "News Radar"),
        ("watchlist",    "Watchlist"),
    ]
    nav_html = ""
    for key, label in nav_items:
        active = ' class="nav-active"' if current_page == key else ""
        nav_html += f'<a href="?nav={key}"{active} target="_self">{label}</a>'

    st.markdown(f"""
    <div class="topbar">
        <div class="topbar-left">
            <a href="?nav=home" style="text-decoration:none;" target="_self">
                <div class="topbar-logo">
                    <span class="logo-dot"></span>
                    Equity<span>IQ</span>
                </div>
            </a>
            <div class="topbar-nav">
                {nav_html}
            </div>
        </div>
        <div class="topbar-right">
            <a class="topbar-cta" href="?nav=ticker" target="_self">Get Started</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Live market ticker strip ───────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _get_market_data():
    import yfinance as yf
    indices_map = {
        "SENSEX":  "^BSESN",
        "NIFTY 50": "^NSEI",
        "S&P 500": "^GSPC",
        "NASDAQ":  "^IXIC",
    }
    results = []
    for name, symbol in indices_map.items():
        try:
            hist = yf.Ticker(symbol).history(period="2d")
            if hist.empty:
                continue
            current     = float(hist['Close'].iloc[-1])
            prev        = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current
            change      = current - prev
            change_pct  = (change / prev) * 100 if prev else 0
            results.append({"name": name, "price": round(current, 2),
                            "change": round(change, 2), "change_pct": round(change_pct, 2)})
        except Exception:
            continue
    return results


def _render_ticker_strip():
    try:
        indices = _get_market_data()
    except Exception:
        indices = []
    if not indices:
        return
    ticker_html = ""
    for idx in indices:
        change_class = "t-up" if idx["change"] >= 0 else "t-down"
        arrow        = "▲" if idx["change"] >= 0 else "▼"
        ticker_html += f"""
        <div class="ticker-item">
            <span class="t-name">{idx["name"]}</span>
            <span class="t-price">{idx["price"]:,.2f}</span>
            <span class="{change_class}">{arrow} {abs(idx["change_pct"]):.2f}%</span>
        </div>"""
    st.markdown(f'<div class="ticker-strip">{ticker_html}</div>', unsafe_allow_html=True)


# ── Page: Home ─────────────────────────────────────────────────────────────────

def render_home_page(api_key):
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">Grow your wealth with<br><span class="accent">AI-powered</span> insights</div>
        <div class="hero-sub">Upload reports, analyze stocks, compare tickers, and track market sentiment — all in one platform.</div>
        <a class="hero-cta" href="?nav=ticker" target="_self">Get started</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="features-row">
        <div class="feature-card">
            <span class="feature-dot green"></span>
            <div class="feature-name">AI Report Analyzer</div>
            <div class="feature-desc">Upload 10-K / 10-Q reports and get AI-extracted financials, ratios &amp; health score instantly</div>
        </div>
        <div class="feature-card">
            <span class="feature-dot blue"></span>
            <div class="feature-name">Stock Health Score</div>
            <div class="feature-desc">Composite A–F grade across profitability, valuation, debt, growth &amp; cash flow</div>
        </div>
        <div class="feature-card">
            <span class="feature-dot purple"></span>
            <div class="feature-name">Investment Memo</div>
            <div class="feature-desc">AI-generated professional investment memo with thesis, risks &amp; recommendation</div>
        </div>
        <div class="feature-card">
            <span class="feature-dot orange"></span>
            <div class="feature-name">News Radar</div>
            <div class="feature-desc">Global news classified by sentiment, urgency &amp; impact with affected-stock detection</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Page: PDF Analysis ─────────────────────────────────────────────────────────

def render_pdf_page(api_key):
    st.markdown('<div class="page-title">AI Report Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Upload a 10-K, 10-Q, or annual report PDF and get AI-extracted financials instantly.</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Financial Report (PDF)", type="pdf")
    st.markdown("""
    <div class="supported-docs">
        Supported: <span>10-K Annual Reports</span> <span>10-Q Quarterly</span>
        <span>Annual Reports</span> <span>Investor Presentations</span>
    </div>
    """, unsafe_allow_html=True)

    if uploaded_file and api_key:
        analyzer = FinancialAnalyzer(api_key)
        if st.button("🚀 Analyze Report", key="pdf_btn"):
            progress = st.progress(0)
            status   = st.empty()

            status.info("📄 Extracting text from PDF...")
            progress.progress(15)
            text, error = analyzer.extract_text_from_pdf(uploaded_file)
            if error:
                st.error(error)
                progress.empty()
                status.empty()
                return

            progress.progress(35)
            status.info("🧠 AI is analyzing financials...")
            metrics = analyzer.analyze_financials(text)
            progress.progress(75)
            if "error" in metrics:
                st.error(f"Analysis Error: {metrics['error']}")
                progress.empty()
                status.empty()
                return

            status.info("💎 Computing intrinsic value...")
            valuation = analyzer.calculate_intrinsic_value(metrics)
            progress.progress(100)
            status.empty()
            progress.empty()
            display_results(metrics, valuation, analyzer, api_key=api_key)

    elif not api_key:
        st.info("Set your Gemini API Key in the .env file to get started.")


# ── Page: Ticker Lookup ────────────────────────────────────────────────────────

def render_ticker_page(api_key):
    st.markdown('<div class="page-title">Stock Lookup</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter any stock ticker to pull live financial data, health score &amp; valuation.</div>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        ticker_input = st.text_input(
            "Stock Ticker",
            placeholder="e.g.  AAPL,  TSLA,  RELIANCE.NS",
            label_visibility="collapsed",
        )
    with col_btn:
        ticker_go = st.button("🔍 Analyze", key="ticker_btn")

    st.markdown("""
    <div class="supported-docs">
        Examples: <span>AAPL</span> <span>TSLA</span> <span>GOOGL</span>
        <span>MSFT</span> <span>RELIANCE.NS</span> <span>TCS.NS</span> <span>INFY.NS</span>
    </div>
    """, unsafe_allow_html=True)

    if ticker_go and ticker_input:
        ticker_clean = ticker_input.strip().upper()
        dummy_key    = api_key if api_key else "ticker-mode"
        try:
            analyzer = FinancialAnalyzer(dummy_key)
        except ValueError:
            analyzer = None

        progress = st.progress(0)
        status   = st.empty()
        status.info(f"🌐 Fetching live data for **{ticker_clean}**...")
        progress.progress(30)

        metrics, error = analyzer.fetch_stock_data(ticker_clean) if analyzer else (None, "Internal error")
        if error:
            st.error(f"❌ {error}")
            progress.empty()
            status.empty()
        else:
            progress.progress(70)
            status.info("💎 Computing valuation...")
            valuation = analyzer.calculate_intrinsic_value(metrics)
            progress.progress(100)
            status.empty()
            progress.empty()
            display_results(metrics, valuation, analyzer, api_key=api_key)

    elif ticker_go and not ticker_input:
        st.warning("Please enter a stock ticker symbol.")


# ── Page: Compare Stocks ───────────────────────────────────────────────────────

def render_compare_page(api_key):
    st.markdown('<div class="page-title">Compare Stocks</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Add two or more tickers to compare them side-by-side on key metrics.</div>', unsafe_allow_html=True)

    if "compare_count" not in st.session_state:
        st.session_state.compare_count = 2

    input_cols   = st.columns(list([3] * st.session_state.compare_count) + [1])
    ticker_values = []
    for i in range(st.session_state.compare_count):
        with input_cols[i]:
            val = st.text_input(
                f"Stock {i+1}",
                placeholder=f"e.g. {'AAPL' if i == 0 else 'MSFT' if i == 1 else 'GOOGL'}",
                key=f"cmp_{i}",
            )
            ticker_values.append(val)
    with input_cols[-1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕", key="add_ticker", help="Add another stock"):
            st.session_state.compare_count += 1
            st.rerun()

    btn_cols = st.columns([2, 1])
    with btn_cols[0]:
        compare_go = st.button("⚖️ Compare", key="compare_btn")
    with btn_cols[1]:
        if st.session_state.compare_count > 2:
            if st.button("➖ Remove last", key="remove_ticker"):
                st.session_state.compare_count -= 1
                st.rerun()

    st.markdown("""
    <div class="supported-docs">
        US: <span>AAPL</span> <span>MSFT</span> <span>TSLA</span>
        India: <span>RELIANCE.NS</span> <span>TCS.NS</span> <span>INFY.NS</span>
    </div>
    """, unsafe_allow_html=True)

    if compare_go:
        tickers = [t.strip().upper() for t in ticker_values if t and t.strip()]
        if len(tickers) < 2:
            st.warning("Please enter at least 2 tickers to compare.")
        else:
            dummy_key = api_key if api_key else "ticker-mode"
            try:
                analyzer = FinancialAnalyzer(dummy_key)
            except ValueError:
                st.error("Could not initialize analyzer.")
                analyzer = None

            if analyzer:
                progress = st.progress(0)
                status   = st.empty()
                all_data = []

                for i, tk in enumerate(tickers):
                    status.info(f"🌐 Fetching data for **{tk}**... ({i+1}/{len(tickers)})")
                    progress.progress(int((i + 1) / (len(tickers) + 1) * 80))
                    m, err = analyzer.fetch_stock_data(tk)
                    if err:
                        st.warning(f"⚠️ Could not fetch {tk}: {err}")
                    else:
                        val   = analyzer.calculate_intrinsic_value(m)
                        price = analyzer.get_current_price(tk)
                        all_data.append({"ticker": tk, "metrics": m, "valuation": val, "price": price})

                progress.progress(100)
                status.empty()
                progress.empty()

                if len(all_data) < 2:
                    st.error("Need data for at least 2 stocks to compare.")
                else:
                    st.markdown("---")
                    st.markdown('<div class="section-head">Comparison Table</div>', unsafe_allow_html=True)

                    rows = []
                    for d in all_data:
                        m, v, p = d["metrics"], d["valuation"], d["price"]
                        dcf_v    = safe_num(v.get("DCF Value"))
                        graham_v = safe_num(v.get("Graham Number"))
                        avg_fair = 0
                        cnt      = 0
                        if dcf_v > 0:
                            avg_fair += dcf_v
                            cnt += 1
                        if graham_v > 0:
                            avg_fair += graham_v
                            cnt += 1
                        avg_fair = avg_fair / cnt if cnt > 0 else 0

                        if p and avg_fair > 0:
                            upside  = ((avg_fair - p) / p) * 100
                            verdict = "🟢 BUY" if upside > 15 else ("🔴 SELL" if upside < -15 else "🟡 HOLD")
                        else:
                            upside, verdict = 0, "⚪ N/A"

                        rows.append({
                            "Ticker":     d["ticker"],
                            "Company":    m.get("Company Name", "—"),
                            "Price":      f"${p:,.2f}" if p else "N/A",
                            "Revenue":    format_number(m.get("Revenue")),
                            "Net Income": format_number(m.get("Net Income")),
                            "EPS":        f"${safe_num(m.get('EPS')):.2f}",
                            "DCF Value":  f"${dcf_v:,.2f}",
                            "Graham #":   f"${graham_v:,.2f}",
                            "Upside":     f"{upside:+.1f}%",
                            "Verdict":    verdict,
                        })

                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Grouped bar chart
                    st.markdown('<div class="section-head">Visual Comparison</div>', unsafe_allow_html=True)
                    compare_keys = ["Revenue", "Net Income", "Free Cash Flow", "Total Assets"]
                    bar_colors   = ['#818cf8', '#06b6d4', '#a78bfa', '#34d399']

                    fig = go.Figure()
                    for i, d in enumerate(all_data):
                        m    = d["metrics"]
                        vals = [safe_num(m.get(k)) for k in compare_keys]
                        fig.add_trace(go.Bar(
                            name=d["ticker"],
                            x=["Revenue", "Net Income", "FCF", "Assets"],
                            y=vals,
                            marker_color=bar_colors[i % len(bar_colors)],
                            hovertemplate='%{x}<br>$%{y:,.0f}<extra>' + d["ticker"] + '</extra>'
                        ))

                    fig.update_layout(
                        barmode='group', template="plotly_white",
                        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
                        font=dict(family="Inter", size=13, color="#44475b"),
                        xaxis=dict(gridcolor='#f0f0f2'), yaxis=dict(gridcolor='#f0f0f2'),
                        margin=dict(l=20, r=20, t=20, b=40), height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#44475b')),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, width="stretch")

                    # Verdict cards
                    st.markdown('<div class="section-head">Verdict</div>', unsafe_allow_html=True)
                    verdict_cols = st.columns(len(all_data))
                    for i, d in enumerate(all_data):
                        with verdict_cols[i]:
                            v, p     = d["valuation"], d["price"]
                            dcf_v    = safe_num(v.get("DCF Value"))
                            graham_v = safe_num(v.get("Graham Number"))
                            avg_fair = 0
                            cnt      = 0
                            if dcf_v > 0:
                                avg_fair += dcf_v
                                cnt += 1
                            if graham_v > 0:
                                avg_fair += graham_v
                                cnt += 1
                            avg_fair = avg_fair / cnt if cnt > 0 else 0

                            if p and avg_fair > 0:
                                margin = ((avg_fair - p) / p) * 100
                                if margin > 15:
                                    card_cls, sig = "verdict-buy", "🟢 BUY"
                                elif margin < -15:
                                    card_cls, sig = "verdict-sell", "🔴 SELL"
                                else:
                                    card_cls, sig = "verdict-hold", "🟡 HOLD"
                                price_str = f"${p:,.2f}"
                                fair_str  = f"Fair Value: ${avg_fair:,.2f}"
                            else:
                                card_cls, sig = "verdict-hold", "⚪ N/A"
                                price_str, fair_str = "N/A", "Insufficient data"

                            st.markdown(f"""
                            <div class="verdict-card {card_cls}" style="padding:20px;">
                                <div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;">{d['ticker']}</div>
                                <div class="verdict-price">{price_str}</div>
                                <div class="verdict-signal" style="font-size:1.5rem;">{sig}</div>
                                <div style="font-size:0.82rem;color:#64748b;">{fair_str}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    _render_trust_footer()


# ── Page: Quarterly Analysis ───────────────────────────────────────────────────

def render_quarterly_page(api_key):
    st.markdown('<div class="page-title">Quarterly Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Upload 2–8 quarterly reports (PDFs) to track growth trends and get AI pros &amp; cons.</div>', unsafe_allow_html=True)

    q_files = st.file_uploader(
        "Upload Quarterly Reports (PDF)", type="pdf",
        accept_multiple_files=True, key="quarterly_uploader"
    )
    st.markdown("""
    <div class="supported-docs">
        Upload in order: <span>Q1</span> <span>Q2</span> <span>Q3</span> <span>Q4</span>
        &nbsp;·&nbsp; Supported: <span>10-Q</span> <span>Quarterly Reports</span> <span>Investor Updates</span>
    </div>
    """, unsafe_allow_html=True)

    if q_files and api_key:
        badge_html = "".join([f'<span class="quarter-badge">📄 {f.name}</span>' for f in q_files])
        st.markdown(f'<div style="margin:10px 0;">{badge_html}</div>', unsafe_allow_html=True)

        if st.button("🚀 Analyze Quarters", key="quarterly_btn"):
            if len(q_files) < 2:
                st.warning("⚠️ Please upload at least 2 quarterly reports to compare.")
            else:
                analyzer = FinancialAnalyzer(api_key)
                progress = st.progress(0)
                status   = st.empty()

                pdf_pairs = []
                for i, f in enumerate(q_files):
                    label = f"Q{i+1}"
                    fname = f.name.upper()
                    for q_tag in ["Q1", "Q2", "Q3", "Q4"]:
                        if q_tag in fname:
                            label = q_tag
                            break
                    pdf_pairs.append((f, label))

                status.info(f"📄 Analyzing {len(q_files)} quarterly reports...")
                progress.progress(10)

                result = analyzer.analyze_quarterly_comparison(pdf_pairs)
                progress.progress(90)

                if "error" in result:
                    st.error(f"❌ {result['error']}")
                    progress.empty()
                    status.empty()
                else:
                    progress.progress(100)
                    status.empty()
                    progress.empty()

                    quarters_data = result["quarters"]
                    growth_data   = result["growth"]
                    pros_cons     = result["pros_cons"]
                    company_name  = result["company_name"]

                    if result.get("errors"):
                        for e in result["errors"]:
                            st.warning(f"⚠️ {e}")

                    st.markdown("---")
                    quarter_labels = " · ".join([q.get("Quarter Label", "?") for q in quarters_data])
                    st.markdown(f"""
                    <div class="company-header">
                        <span class="company-name">{company_name}</span>
                        <span class="fy-badge">{quarter_labels}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="section-head">Quarterly Metrics</div>', unsafe_allow_html=True)
                    table_rows = []
                    for q in quarters_data:
                        table_rows.append({
                            "Quarter":          q.get("Quarter Label", "—"),
                            "Revenue":          format_number(q.get("Revenue")),
                            "Net Income":       format_number(q.get("Net Income")),
                            "EPS":              f"${safe_num(q.get('EPS')):.2f}",
                            "Free Cash Flow":   format_number(q.get("Free Cash Flow")),
                            "Total Assets":     format_number(q.get("Total Assets")),
                            "Total Liabilities": format_number(q.get("Total Liabilities")),
                        })
                    df_q = pd.DataFrame(table_rows)
                    st.dataframe(df_q, use_container_width=True, hide_index=True)

                    st.markdown('<div class="section-head">Quarterly Growth Trends</div>', unsafe_allow_html=True)
                    q_labels    = [q.get("Quarter Label", f"Q{i+1}") for i, q in enumerate(quarters_data)]
                    trend_keys  = ["Revenue", "Net Income", "EPS", "Free Cash Flow"]
                    trend_colors = ['#818cf8', '#06b6d4', '#a78bfa', '#34d399']

                    fig_trend = go.Figure()
                    for idx, key in enumerate(trend_keys):
                        values        = [safe_num(q.get(key)) for q in quarters_data]
                        display_label = "FCF" if key == "Free Cash Flow" else key
                        fig_trend.add_trace(go.Scatter(
                            x=q_labels, y=values,
                            mode='lines+markers',
                            name=display_label,
                            line=dict(color=trend_colors[idx], width=3),
                            marker=dict(size=8),
                            hovertemplate=f'{display_label}<br>%{{x}}: $%{{y:,.0f}}<extra></extra>'
                        ))
                    fig_trend.update_layout(
                        template="plotly_white", paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
                        font=dict(family="Inter", size=13, color="#44475b"),
                        xaxis=dict(gridcolor='#f0f0f2', title="Quarter"),
                        yaxis=dict(gridcolor='#f0f0f2', title="Value ($)"),
                        margin=dict(l=20, r=20, t=20, b=40), height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#44475b')),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

                    if growth_data:
                        st.markdown('<div class="section-head">Quarter-over-Quarter Growth (%)</div>', unsafe_allow_html=True)
                        growth_labels  = [g["Quarter"] for g in growth_data]
                        growth_keys    = ["Revenue", "Net Income", "EPS", "Free Cash Flow"]
                        growth_colors  = ['#818cf8', '#06b6d4', '#a78bfa', '#34d399']

                        fig_growth = go.Figure()
                        for idx, key in enumerate(growth_keys):
                            values        = [g.get(key, 0) for g in growth_data]
                            display_label = "FCF" if key == "Free Cash Flow" else key
                            fig_growth.add_trace(go.Bar(
                                name=display_label,
                                x=growth_labels, y=values,
                                marker_color=growth_colors[idx],
                                hovertemplate=f'{display_label}<br>%{{x}}: %{{y:+.1f}}%<extra></extra>'
                            ))
                        fig_growth.update_layout(
                            barmode='group', template="plotly_white",
                            paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
                            font=dict(family="Inter", size=13, color="#44475b"),
                            xaxis=dict(gridcolor='#f0f0f2', title="Quarter"),
                            yaxis=dict(gridcolor='#f0f0f2', title="Growth %", zeroline=True, zerolinecolor='#e8e8eb'),
                            margin=dict(l=20, r=20, t=20, b=40), height=380,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#44475b')),
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig_growth, use_container_width=True)

                    st.markdown('<div class="section-head">Strengths & Risks</div>', unsafe_allow_html=True)
                    pc1, pc2 = st.columns(2)
                    with pc1:
                        pros_list = pros_cons.get("pros", [])
                        pros_html = "<br>".join([f"✅ {p}" for p in pros_list])
                        st.markdown(f"""
                        <div class="pros-card">
                            <div class="pc-card-title pros">💪 Strengths & Positives</div>
                            <div class="pc-bullet">{pros_html}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with pc2:
                        cons_list = pros_cons.get("cons", [])
                        cons_html = "<br>".join([f"⚠️ {c}" for c in cons_list])
                        st.markdown(f"""
                        <div class="cons-card">
                            <div class="pc-card-title cons">⚠️ Weaknesses & Risks</div>
                            <div class="pc-bullet">{cons_html}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    trajectory = pros_cons.get("trajectory", "No trajectory analysis available.")
                    st.markdown(f"""
                    <div class="trajectory-card" style="margin-top:20px;">
                        <div class="pc-card-title trajectory">🧭 Overall Trajectory</div>
                        <div class="pc-bullet">{trajectory}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    _render_trust_footer()

    elif q_files and not api_key:
        st.info("Add your Gemini API Key in the .env file to analyze quarterly reports.")
    elif not q_files:
        st.markdown("""
        <div style="text-align:center; padding:50px 0; color:#7c7e8c;">
            <div style="font-size:1rem; font-weight:500; color:#44475b;">Upload quarterly report PDFs above to get started</div>
            <div style="font-size:0.85rem; margin-top:8px; color:#7c7e8c;">Drag & drop or click to browse · Min 2, Max 8 reports</div>
        </div>
        """, unsafe_allow_html=True)


# ── Page: Market Pulse ─────────────────────────────────────────────────────────

def render_market_pulse_page(api_key):
    st.markdown('<div class="page-title">Market Pulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">AI-powered sentiment analysis of the latest financial news with stock impact predictions.</div>', unsafe_allow_html=True)

    if not api_key:
        st.info("Add your Gemini API Key in the .env file to use Market Pulse.")
        return

    if st.button("⚡ Scan Latest News", key="sentiment_btn"):
        analyzer = FinancialAnalyzer(api_key)
        progress = st.progress(0)
        status   = st.empty()

        status.info("📡 Fetching latest market news from multiple sources...")
        progress.progress(20)

        sentiment_results = analyzer.fetch_market_news_with_sentiment()
        progress.progress(80)
        status.info("🧠 Classifying sentiment and stock impact...")
        progress.progress(100)
        status.empty()
        progress.empty()

        if not sentiment_results:
            st.warning("Could not fetch news at this time. Please try again in a moment.")
        else:
            st.markdown('<div class="section-head">Market Sentiment Feed</div>', unsafe_allow_html=True)

            for item in sentiment_results:
                sentiment    = item.get("sentiment", "mixed")
                badge_class  = "positive" if sentiment == "positive" else ("negative" if sentiment == "negative" else "mixed")
                badge_label  = sentiment.upper()

                bullish_tags = "".join(
                    f'<span class="stock-tag bullish">▲ {s}</span>'
                    for s in item.get("bullish_stocks", [])
                )
                bearish_tags = "".join(
                    f'<span class="stock-tag bearish">▼ {s}</span>'
                    for s in item.get("bearish_stocks", [])
                )

                link_html   = (
                    f' · <a href="{item["link"]}" target="_blank" style="color:#00b386;font-size:0.72rem;text-decoration:none;">Read article →</a>'
                    if item.get("link") and item["link"] != "#" else ""
                )
                source_html = f'{item["publisher"]}{link_html}' if item.get("publisher") else ""

                st.markdown(f"""
                <div class="sentiment-card">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                        <span class="sentiment-badge {badge_class}">{badge_label}</span>
                        <span class="sentiment-source">{item.get("published", "")}</span>
                    </div>
                    <div class="sentiment-headline">{item["headline"]}</div>
                    <div class="sentiment-source">{source_html}</div>
                    <div class="sentiment-stocks">{bullish_tags}{bearish_tags}</div>
                    <div class="sentiment-reason">{item.get("reason", "")}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div class="trust-footer">
                <div class="trust-badges">
                    <div class="trust-badge"><span class="badge-icon">🌐</span> Real-time news</div>
                    <div class="trust-badge"><span class="badge-icon">📊</span> Sentiment Analysis</div>
                </div>
                <div class="trust-legal">
                    Sentiment predictions are AI-generated and for informational purposes only. Not financial advice.
                </div>
            </div>
            """, unsafe_allow_html=True)


# ── Page: Watchlist ────────────────────────────────────────────────────────────

def render_watchlist_page(api_key):
    st.markdown('<div class="page-title">Watchlist & Alerts</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Track stocks and get price alerts when they hit your target.</div>', unsafe_allow_html=True)

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    st.markdown('<div class="section-head">Add to Watchlist</div>', unsafe_allow_html=True)
    wl_c1, wl_c2, wl_c3, wl_c4 = st.columns([3, 2, 3, 1])
    with wl_c1:
        wl_ticker_in  = st.text_input("Ticker", placeholder="e.g. AAPL, TCS.NS", key="wl_ticker_input", label_visibility="collapsed")
    with wl_c2:
        wl_alert_price = st.number_input("Alert below ($)", min_value=0.0, value=0.0, step=0.5, key="wl_alert_input", label_visibility="collapsed")
    with wl_c3:
        wl_note = st.text_input("Note (optional)", placeholder="Why watching this stock?", key="wl_note_input", label_visibility="collapsed")
    with wl_c4:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("➕ Add", key="wl_add_btn"):
            if wl_ticker_in.strip():
                ticker_up = wl_ticker_in.strip().upper()
                existing  = [w["ticker"] for w in st.session_state.watchlist]
                if ticker_up in existing:
                    st.warning(f"{ticker_up} is already in your watchlist.")
                else:
                    st.session_state.watchlist.append({
                        "ticker":        ticker_up,
                        "alert_price":   wl_alert_price,
                        "note":          wl_note,
                        "current_price": None,
                        "company":       "",
                    })
                    st.rerun()
            else:
                st.warning("Enter a ticker symbol.")

    st.markdown("""
    <div class="supported-docs">
        Examples: <span>AAPL</span> <span>TSLA</span> <span>NVDA</span> <span>MSFT</span>
        <span>RELIANCE.NS</span> <span>TCS.NS</span> <span>INFY.NS</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.watchlist:
        btn_c1, btn_c2, _ = st.columns([1.5, 1.5, 7])
        with btn_c1:
            if st.button("🔄 Refresh Prices", key="wl_refresh"):
                try:
                    import yfinance as yf
                    wl_analyzer = FinancialAnalyzer(api_key if api_key else "ticker-mode")
                except Exception:
                    wl_analyzer = None
                if wl_analyzer:
                    with st.spinner("Fetching live prices..."):
                        for item in st.session_state.watchlist:
                            item["current_price"] = wl_analyzer.get_current_price(item["ticker"])
                            if not item.get("company"):
                                try:
                                    import yfinance as yf
                                    info = yf.Ticker(item["ticker"]).info
                                    item["company"] = (
                                        info.get("longName") or info.get("shortName") or item["ticker"]
                                    )
                                except Exception:
                                    item["company"] = item["ticker"]
                    st.rerun()
        with btn_c2:
            if st.button("🗑️ Clear All", key="wl_clear"):
                st.session_state.watchlist = []
                st.rerun()

        alerts = [
            w for w in st.session_state.watchlist
            if w.get("current_price") and w.get("alert_price", 0) > 0
            and w["current_price"] <= w["alert_price"]
        ]
        if alerts:
            alert_names = " · ".join(w["ticker"] for w in alerts)
            st.markdown(f"""
            <div class="alert-banner">
                🔔 <b>{len(alerts)} stock(s) hit your alert price!</b> &nbsp;{alert_names}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-head">Your Watchlist</div>', unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.watchlist):
            ticker      = item["ticker"]
            cur_price   = item.get("current_price")
            alert_price = item.get("alert_price", 0)
            company     = item.get("company") or ticker
            note        = item.get("note", "")

            if cur_price and alert_price > 0:
                if cur_price <= alert_price:
                    card_cls     = "wl-alert"
                    status_icon  = "🔔"
                    status_text  = f"ALERT — at/below ${alert_price:,.2f} target"
                    status_color = "#16a34a"
                else:
                    pct          = ((cur_price - alert_price) / alert_price) * 100
                    card_cls     = "wl-normal"
                    status_icon  = "⚪"
                    status_text  = f"{pct:.1f}% above alert target"
                    status_color = "#94a3b8"
            else:
                card_cls     = "wl-normal"
                status_icon  = "⚪"
                status_text  = "Click 'Refresh Prices' to load" if not cur_price else "No alert set"
                status_color = "#94a3b8"

            price_display = f"${cur_price:,.2f}" if cur_price else "—"
            alert_display = f"${alert_price:,.2f}" if alert_price > 0 else "—"
            note_html     = f'<span class="wl-note">"{note}"</span>' if note else ""

            card_col, rm_col = st.columns([11, 1])
            with card_col:
                st.markdown(f"""
                <div class="watchlist-card {card_cls}">
                    <div class="wl-row">
                        <div class="wl-left">
                            <span class="wl-ticker">{ticker}</span>
                            <div>
                                <span class="wl-company">{company}</span>
                                {note_html}
                            </div>
                        </div>
                        <div class="wl-right">
                            <div class="wl-price">{price_display}</div>
                            <div class="wl-alert-price">Alert: {alert_display}</div>
                            <div class="wl-status" style="color:{status_color};">{status_icon} {status_text}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with rm_col:
                if st.button("✕", key=f"wl_remove_{i}", help=f"Remove {ticker}"):
                    st.session_state.watchlist.pop(i)
                    st.rerun()

    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#7c7e8c;">
            <div style="font-size:2.5rem;margin-bottom:12px;">📋</div>
            <div style="font-size:1rem;font-weight:600;color:#44475b;">Your watchlist is empty</div>
            <div style="font-size:0.84rem;margin-top:6px;">Add tickers above and set price alerts to get notified</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="trust-footer">
        <div class="trust-badges">
            <div class="trust-badge"><span class="badge-icon">🔒</span> Stored in session only</div>
            <div class="trust-badge"><span class="badge-icon">🌐</span> Real-time price checks</div>
            <div class="trust-badge"><span class="badge-icon">🔔</span> Price alert detection</div>
        </div>
        <div class="trust-legal">EquityIQ is for educational and informational purposes only. Not financial advice.</div>
    </div>
    """, unsafe_allow_html=True)


# ── Page: News Radar ───────────────────────────────────────────────────────────

def render_news_radar_page(api_key):
    st.markdown('<div class="page-title">News Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">AI-powered global news intelligence — sentiment, impact analysis &amp; affected-stock detection.</div>', unsafe_allow_html=True)

    nr_c1, nr_c2, nr_c3 = st.columns([4, 2, 1])
    with nr_c1:
        nr_query = st.text_input(
            "Search", placeholder="e.g. NVDA · TSLA · Semiconductors · Banking · EV & Clean Energy",
            key="nr_query", label_visibility="collapsed",
        )
    with nr_c2:
        nr_type = st.selectbox("Type", ["Ticker", "Sector"], key="nr_type", label_visibility="collapsed")
    with nr_c3:
        nr_search_btn = st.button("🔍 Search", key="nr_search_btn")

    f1, f2, f3 = st.columns(3)
    with f1:
        nr_sentiment_filter = st.selectbox(
            "Sentiment", ["All", "Positive", "Negative", "Neutral", "Mixed"],
            key="nr_sent_filter",
        )
    with f2:
        nr_category_filter = st.selectbox(
            "Impact Category", ["All"] + IMPACT_CATEGORIES,
            key="nr_cat_filter",
        )
    with f3:
        nr_urgency_filter = st.selectbox(
            "Urgency", ["All", "High", "Medium", "Low"],
            key="nr_urg_filter",
        )

    st.markdown("""
    <div class="supported-docs">
        Tickers: <span>NVDA</span> <span>TSLA</span> <span>AAPL</span> <span>MSFT</span> <span>TCS.NS</span>
        &nbsp;·&nbsp; Sectors: <span>Semiconductors</span> <span>Banking</span>
        <span>EV &amp; Clean Energy</span> <span>Healthcare</span> <span>Indian Markets</span>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.info("Add your Gemini API Key in the .env file to use News Radar.")
        return

    if nr_search_btn and nr_query.strip():
        query_clean     = nr_query.strip().upper() if nr_type == "Ticker" else nr_query.strip()
        query_type_clean = "ticker" if nr_type == "Ticker" else "sector"

        nr_analyzer = NewsRadarAnalyzer(api_key)
        progress    = st.progress(0)
        status      = st.empty()

        status.info(f"📡 Fetching latest news for **{query_clean}**...")
        progress.progress(20)
        raw_articles = nr_analyzer.fetch_news(query_clean, query_type_clean)

        if not raw_articles:
            st.warning(f"No news found for **{query_clean}**. Try a different ticker or sector.")
            progress.empty()
            status.empty()
        else:
            progress.progress(45)
            status.info(f"🧠 Classifying {len(raw_articles)} articles with AI...")
            classified = nr_analyzer.classify_with_ai(raw_articles, query_clean, query_type_clean)

            progress.progress(75)
            status.info("📊 Generating market summary...")
            summary_data = nr_analyzer.generate_summary(classified, query_clean)

            progress.progress(100)
            status.empty()
            progress.empty()

            overall       = summary_data["overall"]
            counts        = summary_data.get("counts", {})
            overall_color = {
                "Positive": "#16a34a", "Negative": "#dc2626",
                "Neutral":  "#64748b", "Mixed":    "#d97706",
            }.get(overall, "#94a3b8")

            st.markdown('<div class="section-head">Market Sentiment Summary</div>', unsafe_allow_html=True)
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            with sc1:
                st.markdown(f"""
                <div class="nr-summary-card" style="border-color:{overall_color};">
                    <div class="nr-summary-label">Overall</div>
                    <div class="nr-summary-value" style="color:{overall_color};">{overall}</div>
                </div>
                """, unsafe_allow_html=True)
            with sc2:
                create_metric_card("Positive", str(counts.get("positive", 0)))
            with sc3:
                create_metric_card("Negative", str(counts.get("negative", 0)))
            with sc4:
                create_metric_card("Neutral", str(counts.get("neutral", 0)))
            with sc5:
                create_metric_card("Mixed", str(counts.get("mixed", 0)))

            st.markdown(f"""
            <div class="nr-ai-summary">
                <div class="nr-ai-summary-label">🧠 What changed today?</div>
                <div class="nr-ai-summary-text">{summary_data['summary']}</div>
            </div>
            """, unsafe_allow_html=True)

            top3 = summary_data.get("top3", [])
            if top3:
                st.markdown('<div class="section-head">Top Priority News</div>', unsafe_allow_html=True)
                for art in top3:
                    _render_news_card(art, highlight=True)

            filtered = classified
            if nr_sentiment_filter != "All":
                filtered = [a for a in filtered if (a.get("sentiment") or "").lower() == nr_sentiment_filter.lower()]
            if nr_category_filter != "All":
                filtered = [a for a in filtered if a.get("impact_category") == nr_category_filter]
            if nr_urgency_filter != "All":
                filtered = [a for a in filtered if (a.get("urgency") or "").lower() == nr_urgency_filter.lower()]

            st.markdown(f'<div class="section-head">All Articles ({len(filtered)} of {len(classified)})</div>', unsafe_allow_html=True)

            if not filtered:
                st.info("No articles match the selected filters. Try clearing some filters.")
            else:
                for art in filtered:
                    _render_news_card(art)

            st.markdown("""
            <div class="trust-footer">
                <div class="trust-badges">
                    <div class="trust-badge"><span class="badge-icon">🌐</span> Multi-source news</div>
                    <div class="trust-badge"><span class="badge-icon">📊</span> AI sentiment classification</div>
                    <div class="trust-badge"><span class="badge-icon">🔍</span> Affected-stock detection</div>
                </div>
                <div class="trust-legal">
                    ⚠️ This is AI-generated market research, not financial advice.
                    Always verify with official sources before making investment decisions.
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif nr_search_btn:
        st.warning("Please enter a ticker symbol or sector name.")


# ── Page: Stock Screener ──────────────────────────────────────────────────────

def _fmt(val, fmt=".2f", suffix="", scale=1, na="N/A"):
    if val is None:
        return na
    try:
        return f"{float(val) * scale:{fmt}}{suffix}"
    except (TypeError, ValueError):
        return na


def _mcap_label(val):
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.1f}B"
    if val >= 1e6:
        return f"${val/1e6:.0f}M"
    return f"${val:,.0f}"


def render_screener_page(_api_key):
    st.markdown('<div class="page-title">Stock Screener</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Screen the full S&amp;P 500 (US) and Nifty 50 + Next 50 (India) — 550+ stocks with live fundamental data.</div>', unsafe_allow_html=True)

    mk1, mk2, _ = st.columns([2, 2, 6])
    with mk1:
        include_us = st.checkbox("S&P 500 · US", value=True, key="sc_us")
    with mk2:
        include_india = st.checkbox("Nifty 100 · India", value=True, key="sc_india")

    all_tickers = get_all_tickers(include_us, include_india)
    st.markdown(
        f'<div style="color:#64748b;font-size:0.82rem;margin:4px 0 12px;">'
        f'<b>{len(all_tickers)} tickers</b> selected — '
        f'S&amp;P 500 list refreshes daily from Wikipedia · '
        f'Indian list: Nifty 50 + Nifty Next 50'
        f'</div>',
        unsafe_allow_html=True,
    )

    btn_col, refresh_col, _ = st.columns([2, 2, 6])
    with btn_col:
        scan_btn = st.button("🔍 Screen Stocks", key="sc_scan")
    with refresh_col:
        if st.session_state.get("screener_results"):
            if st.button("🔄 Refresh Data", key="sc_refresh", help="Clear cache and re-fetch fresh data"):
                fetch_screener_data.clear()
                st.session_state.pop("screener_results", None)
                st.rerun()

    if scan_btn:
        with st.spinner(f"Fetching live data for {len(all_tickers)} stocks — first run takes ~60–90 s, then cached 15 min…"):
            raw = fetch_screener_data(tuple(sorted(all_tickers)))
        for d in raw:
            sc, gr, cl = screener_health_score(d)
            d["health_score"] = sc
            d["health_grade"] = gr
            d["health_color"] = cl
        st.session_state["screener_results"] = raw

    stocks = st.session_state.get("screener_results", [])
    if not stocks:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#7c7e8c;">
            <div style="font-size:2.5rem;margin-bottom:12px;">🔍</div>
            <div style="font-size:1rem;font-weight:600;color:#44475b;">Click Screen Stocks to load live data</div>
            <div style="font-size:0.84rem;margin-top:6px;">First scan: ~60–90 s &nbsp;·&nbsp; Results cached 15 minutes</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Filter panels ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-head">Filters</div>', unsafe_allow_html=True)

    # helper: read float from slider key
    def sf(key, default=(0.0, 999999.0)):
        return st.session_state.get(key, default)

    f1, f2 = st.columns(2)

    with f1:
        with st.expander("🌍 Market Filters", expanded=False):
            mc_range = st.slider("Market Cap ($B)", 0.0, 3000.0, (0.0, 3000.0), 10.0, key="f_mc")
            all_sectors = sorted({d.get("sector","") for d in stocks if d.get("sector")})
            all_countries = sorted({d.get("country","") for d in stocks if d.get("country")})
            sel_sectors  = st.multiselect("Sector", all_sectors, key="f_sec")
            sel_countries = st.multiselect("Country", all_countries, key="f_cty")

        with st.expander("📊 Valuation Filters", expanded=False):
            pe_range  = st.slider("P/E Ratio",      0.0,  100.0, (0.0, 100.0),  1.0, key="f_pe")
            pb_range  = st.slider("P/B Ratio",      0.0,   25.0, (0.0,  25.0),  0.5, key="f_pb")
            ps_range  = st.slider("P/S Ratio",      0.0,   25.0, (0.0,  25.0),  0.5, key="f_ps")
            div_range = st.slider("Dividend Yield (%)", 0.0, 15.0, (0.0, 15.0), 0.25, key="f_div")

        with st.expander("💎 Quality Filters", expanded=False):
            roe_range = st.slider("ROE (%)",           -30.0, 100.0, (-30.0, 100.0), 1.0, key="f_roe")
            roa_range = st.slider("ROA (%)",           -20.0,  50.0, (-20.0,  50.0), 1.0, key="f_roa")
            pm_range  = st.slider("Profit Margin (%)", -50.0,  80.0, (-50.0,  80.0), 1.0, key="f_pm")
            pos_fcf   = st.checkbox("Positive Free Cash Flow only", key="f_fcf")

        with st.expander("📈 Growth Filters", expanded=False):
            rg_range  = st.slider("Revenue Growth (%)",  -50.0, 100.0, (-50.0, 100.0), 1.0, key="f_rg")
            eg_range  = st.slider("Earnings Growth (%)", -50.0, 100.0, (-50.0, 100.0), 1.0, key="f_eg")

    with f2:
        with st.expander("⚠️ Risk Filters", expanded=False):
            de_range  = st.slider("Debt / Equity",  0.0, 5.0, (0.0, 5.0), 0.1, key="f_de")
            cr_range  = st.slider("Current Ratio",  0.0, 5.0, (0.0, 5.0), 0.1, key="f_cr")
            beta_range = st.slider("Beta",          -1.0, 4.0, (-1.0, 4.0), 0.1, key="f_beta")

        with st.expander("💰 Dividend Filters", expanded=False):
            only_divid = st.checkbox("Dividend payers only", key="f_only_div")
            upcoming_div = st.checkbox("Upcoming ex-dividend (next 60 days)", key="f_upcoming_div")
            min_yield  = st.slider("Min Dividend Yield (%)", 0.0, 10.0, 0.0, 0.25, key="f_min_yield")
            max_payout = st.slider("Max Payout Ratio (%)", 0.0, 200.0, 200.0, 5.0, key="f_payout")

        with st.expander("📰 Analyst Filters", expanded=False):
            sel_analyst  = st.multiselect(
                "Analyst Rating",
                ["strong_buy", "buy", "hold", "underperform", "sell"],
                key="f_analyst",
            )
            has_target   = st.checkbox("Has analyst target price", key="f_has_target")
            min_analysts = st.slider("Min analyst opinions", 0, 50, 0, 1, key="f_min_analysts")

    # ── Apply filters ──────────────────────────────────────────────────────────
    import datetime as _dt

    today = _dt.date.today()
    cutoff_div = today + _dt.timedelta(days=60)

    filtered = []
    for d in stocks:
        mc_b = (d.get("market_cap") or 0) / 1e9
        if not (mc_range[0] <= mc_b <= mc_range[1]):
            continue

        if sel_sectors and d.get("sector") not in sel_sectors:
            continue
        if sel_countries and d.get("country") not in sel_countries:
            continue

        pe = d.get("pe_ratio")
        if pe is not None and pe > 0 and not (pe_range[0] <= pe <= pe_range[1]):
            continue

        pb = d.get("pb_ratio")
        if pb is not None and pb > 0 and not (pb_range[0] <= pb <= pb_range[1]):
            continue

        ps = d.get("ps_ratio")
        if ps is not None and ps > 0 and not (ps_range[0] <= ps <= ps_range[1]):
            continue

        dy = (d.get("dividend_yield") or 0) * 100
        if not (div_range[0] <= dy <= div_range[1]):
            continue

        roe = d.get("roe")
        if roe is not None and not (roe_range[0] <= roe * 100 <= roe_range[1]):
            continue

        roa = d.get("roa")
        if roa is not None and not (roa_range[0] <= roa * 100 <= roa_range[1]):
            continue

        pm = d.get("profit_margin")
        if pm is not None and not (pm_range[0] <= pm * 100 <= pm_range[1]):
            continue

        if pos_fcf and not (d.get("free_cash_flow") or 0) > 0:
            continue

        rg = d.get("revenue_growth")
        if rg is not None and not (rg_range[0] <= rg * 100 <= rg_range[1]):
            continue

        eg = d.get("earnings_growth")
        if eg is not None and not (eg_range[0] <= eg * 100 <= eg_range[1]):
            continue

        de = d.get("debt_to_equity")
        if de is not None and not (de_range[0] <= de <= de_range[1]):
            continue

        cr = d.get("current_ratio")
        if cr is not None and not (cr_range[0] <= cr <= cr_range[1]):
            continue

        beta = d.get("beta")
        if beta is not None and not (beta_range[0] <= beta <= beta_range[1]):
            continue

        if only_divid and not (d.get("dividend_yield") or 0) > 0:
            continue

        if min_yield > 0 and (d.get("dividend_yield") or 0) * 100 < min_yield:
            continue

        pr = (d.get("payout_ratio") or 0) * 100
        if pr > max_payout:
            continue

        if upcoming_div:
            ex_s = d.get("ex_div_date", "")
            try:
                ex_d = _dt.date.fromisoformat(ex_s) if ex_s else None
            except ValueError:
                ex_d = None
            if not ex_d or not (today <= ex_d <= cutoff_div):
                continue

        if sel_analyst and d.get("analyst_rating") not in sel_analyst:
            continue

        if has_target and not d.get("target_price"):
            continue

        if d.get("analyst_count", 0) < min_analysts:
            continue

        filtered.append(d)

    # ── Summary bar ───────────────────────────────────────────────────────────
    div_payers = sum(1 for d in filtered if (d.get("dividend_yield") or 0) > 0)
    avg_hs     = round(sum(d.get("health_score", 0) for d in filtered) / len(filtered)) if filtered else 0

    sm1, sm2, sm3, sm4 = st.columns(4)
    with sm1:
        create_metric_card("Matching Stocks", str(len(filtered)))
    with sm2:
        create_metric_card("Dividend Payers", str(div_payers))
    with sm3:
        create_metric_card("Avg Health Score", str(avg_hs))
    with sm4:
        a_grades = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for d in filtered:
            g = d.get("health_grade", "")
            if g in a_grades:
                a_grades[g] += 1
        top_grade = max(a_grades, key=a_grades.get) if filtered else "—"
        create_metric_card("Most Common Grade", top_grade)

    # ── Results table ─────────────────────────────────────────────────────────
    st.markdown(f'<div class="section-head">Results ({len(filtered)} stocks)</div>', unsafe_allow_html=True)

    if not filtered:
        st.info("No stocks match the current filters. Try relaxing the filter ranges.")
    else:
        import pandas as pd

        rows = []
        for d in filtered:
            rows.append({
                "Ticker":       d["ticker"],
                "Company":      (d["company"] or d["ticker"])[:28],
                "Sector":       d.get("sector", ""),
                "Price":        f"${d['price']:,.2f}" if d.get("price") else "N/A",
                "Mkt Cap":      _mcap_label(d.get("market_cap")),
                "P/E":          _fmt(d.get("pe_ratio"), ".1f"),
                "P/B":          _fmt(d.get("pb_ratio"), ".2f"),
                "P/S":          _fmt(d.get("ps_ratio"), ".2f"),
                "Div Yield":    _fmt(d.get("dividend_yield"), ".2f", "%", 100) if d.get("dividend_yield") else "—",
                "ROE":          _fmt(d.get("roe"), ".1f", "%", 100),
                "ROA":          _fmt(d.get("roa"), ".1f", "%", 100),
                "Rev Growth":   _fmt(d.get("revenue_growth"), ".1f", "%", 100),
                "D/E":          _fmt(d.get("debt_to_equity"), ".2f"),
                "Cur Ratio":    _fmt(d.get("current_ratio"), ".2f"),
                "Health":       f'{d.get("health_score","?")} ({d.get("health_grade","?")})',
                "Analyst":      (d.get("analyst_rating") or "—").replace("_", " ").title(),
                "Target":       f"${d['target_price']:,.2f}" if d.get("target_price") else "—",
                "Ex-Div Date":  d.get("ex_div_date") or "—",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=420)

        # Download button
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV", csv, "screener_results.csv", "text/csv", key="sc_csv")

    # ── Dividend Calendar (yfinance data for screened stocks) ─────────────────
    upcoming = get_upcoming_dividends(filtered, days=90)

    # Optionally enrich US stocks with Finnhub and pull NSE calendar
    finnhub_key = os.getenv("FINNHUB_API_KEY", "")
    from screener import enrich_dividends_finnhub, fetch_nse_dividend_calendar

    finnhub_enriched = {}
    if finnhub_key:
        us_tickers = tuple(
            d["ticker"] for d in filtered
            if not d["ticker"].endswith(".NS") and not d["ticker"].endswith(".BO")
        )
        if us_tickers:
            with st.spinner("Enriching US dividend dates via Finnhub…"):
                finnhub_enriched = enrich_dividends_finnhub(finnhub_key, us_tickers)
            # Merge Finnhub dates into upcoming list items where available
            for item in upcoming:
                tk = item["ticker"]
                if tk in finnhub_enriched:
                    fh = finnhub_enriched[tk]
                    if fh.get("ex_div_date"):
                        item["ex_div_date"]   = fh["ex_div_date"]
                        item["pay_date"]      = fh.get("pay_date", item.get("pay_date", ""))
                        item["dividend_rate"] = fh.get("dividend_rate") or item.get("dividend_rate")
                        item["_source"]       = "Finnhub"

    # NSE India calendar for Indian stocks
    nse_divs = []
    has_indian = any(
        d["ticker"].endswith(".NS") or d["ticker"].endswith(".BO")
        for d in filtered
    )
    if has_indian:
        with st.spinner("Fetching NSE dividend calendar…"):
            nse_divs = fetch_nse_dividend_calendar(days_ahead=90)

    if upcoming or nse_divs:
        st.markdown('<div class="section-head">Upcoming Dividend Calendar (next 90 days)</div>', unsafe_allow_html=True)

        # Show yfinance/Finnhub upcoming (US + global)
        if upcoming:
            st.markdown('<div style="font-size:0.85rem;color:#64748b;margin-bottom:8px;">US &amp; Global Stocks</div>', unsafe_allow_html=True)
            for d in upcoming:
                days_left     = d["_days_until"]
                urgency_color = "#dc2626" if days_left <= 7 else ("#d97706" if days_left <= 21 else "#16a34a")
                dy_pct = _fmt(d.get("dividend_yield"), ".2f", "%", 100) if d.get("dividend_yield") else "—"
                dr     = f"${d['dividend_rate']:.2f}/yr" if d.get("dividend_rate") else "—"
                pay_d  = d.get("pay_date") or "—"
                src    = d.get("_source", "yfinance")

                h  = '<div class="watchlist-card wl-normal" style="margin-bottom:10px;">'
                h += '<div class="wl-row">'
                h += '<div class="wl-left">'
                h += f'<span class="wl-ticker">{d["ticker"]}</span>'
                h += f'<div><span class="wl-company">{d["company"][:30]}</span>'
                h += f' <span style="font-size:0.72rem;color:#94a3b8;">via {src}</span></div>'
                h += '</div>'
                h += '<div class="wl-right" style="text-align:right;">'
                h += f'<div class="wl-price">{dy_pct} yield · {dr}</div>'
                h += f'<div class="wl-alert-price">Ex-Div: <b>{d["ex_div_date"]}</b> · Pay: {pay_d}</div>'
                h += f'<div class="wl-status" style="color:{urgency_color};font-weight:600;">⏰ {days_left} days until ex-dividend</div>'
                h += '</div></div></div>'
                st.markdown(h, unsafe_allow_html=True)

        # Show NSE India calendar
        if nse_divs:
            st.markdown('<div style="font-size:0.85rem;color:#64748b;margin:16px 0 8px;">NSE India (via NSE Official API)</div>', unsafe_allow_html=True)
            import datetime as _dt2
            today2 = _dt2.date.today()
            for item in nse_divs[:20]:
                ex_s = item.get("ex_div_date", "")
                try:
                    ex_d   = _dt2.date.fromisoformat(ex_s)
                    days_l = (ex_d - today2).days
                except (ValueError, TypeError):
                    days_l = 0
                urg_c = "#dc2626" if days_l <= 7 else ("#d97706" if days_l <= 21 else "#16a34a")

                h  = '<div class="watchlist-card wl-normal" style="margin-bottom:10px;">'
                h += '<div class="wl-row">'
                h += '<div class="wl-left">'
                h += f'<span class="wl-ticker">{item["symbol"]}</span>'
                h += f'<div><span class="wl-company">{item["company"][:30]}</span>'
                h += ' <span style="font-size:0.72rem;color:#94a3b8;">NSE India</span></div>'
                h += '</div>'
                h += '<div class="wl-right" style="text-align:right;">'
                h += f'<div class="wl-price">{item.get("dividend_amount", "—")}</div>'
                h += f'<div class="wl-alert-price">Ex-Div: <b>{ex_s}</b></div>'
                h += f'<div class="wl-status" style="color:{urg_c};font-weight:600;">⏰ {days_l} days until ex-dividend</div>'
                h += '</div></div></div>'
                st.markdown(h, unsafe_allow_html=True)

    _render_trust_footer()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    setup_page()

    env_key = os.getenv("GEMINI_API_KEY")
    api_key = env_key if (env_key and len(env_key) > 10) else ""

    page = st.query_params.get("nav", "home")

    _render_topbar(page)
    _render_ticker_strip()

    if page == "home":
        render_home_page(api_key)
    elif page == "pdf":
        render_pdf_page(api_key)
    elif page == "ticker":
        render_ticker_page(api_key)
    elif page == "screener":
        render_screener_page(api_key)
    elif page == "compare":
        render_compare_page(api_key)
    elif page == "quarterly":
        render_quarterly_page(api_key)
    elif page == "market-pulse":
        render_market_pulse_page(api_key)
    elif page == "watchlist":
        render_watchlist_page(api_key)
    elif page == "news-radar":
        render_news_radar_page(api_key)
    else:
        render_home_page(api_key)


if __name__ == "__main__":
    main()
