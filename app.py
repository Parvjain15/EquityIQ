import streamlit as st
import streamlit.components.v1 as components
import os
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from financial_analyzer import FinancialAnalyzer
from news_radar import NewsRadarAnalyzer, SECTOR_TICKERS, IMPACT_CATEGORIES
from screener import (
    fetch_sp500_tickers, get_all_tickers, fetch_screener_data,
    compute_health_score as screener_health_score,
    get_upcoming_dividends, get_company_directory,
    get_usd_inr_rate, convert_market_cap,
    enrich_dividends_finnhub, fetch_nse_dividend_calendar,
)
from utils import (
    setup_page, format_number, currency_symbol,
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


def _chart_theme():
    """Plotly layout colors matching the current light/dark theme, so charts
    don't stay hardcoded white when the rest of the app switches to dark."""
    if st.session_state.get("dark_mode", False):
        return dict(
            template="plotly_dark",
            paper_bgcolor="#171B22", plot_bgcolor="#171B22",
            font_color="#F2F4F7", grid_color="#262B34",
        )
    return dict(
        template="plotly_white",
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font_color="#44475b", grid_color="#f0f0f2",
    )


_TICKER_SEP = " — "


def _company_search_options():
    """'Company Name — TICKER' options for the searchable ticker widgets, so
    typing a company name (e.g. "apple") surfaces its ticker without the user
    needing to already know the symbol."""
    return [f"{row['name']}{_TICKER_SEP}{row['ticker']}" for row in get_company_directory()]


def _resolve_ticker_input(raw):
    """Extracts a ticker from either a 'Company Name — TICKER' selection or a
    raw ticker typed directly (accept_new_options lets users bypass the list
    entirely for symbols outside the curated S&P 500 / Nifty 100 directory)."""
    raw = (raw or "").strip()
    if _TICKER_SEP in raw:
        candidate = raw.rsplit(_TICKER_SEP, 1)[-1].strip()
        if candidate:
            return candidate.upper()
    return raw.upper()


def _render_news_card(article, highlight=False):
    import html as _html

    sentiment = (article.get("sentiment") or "neutral").lower()
    urgency   = (article.get("urgency") or "low").lower()

    sentiment_styles = {
        "positive": ("#16A36A", "rgba(22,163,106,0.08)", "rgba(22,163,106,0.30)"),
        "negative": ("#E5484D", "rgba(229,72,77,0.08)", "rgba(229,72,77,0.30)"),
        "neutral":  ("#6F7580", "#F7F9FB", "#E5E8EC"),
        "mixed":    ("#B9791F", "rgba(242,169,59,0.12)", "rgba(242,169,59,0.35)"),
    }
    urgency_styles = {
        "high":   ("#E5484D", "rgba(229,72,77,0.08)"),
        "medium": ("#B9791F", "rgba(242,169,59,0.12)"),
        "low":    ("#16A36A", "rgba(22,163,106,0.08)"),
    }
    s_txt, s_bg, s_bdr = sentiment_styles.get(sentiment, ("#6F7580", "#F7F9FB", "#E5E8EC"))
    u_txt, u_bg        = urgency_styles.get(urgency, ("#6F7580", "#F7F9FB"))

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

    border_style = "border-left:4px solid #08A6DC;background:#F7FDFF;" if highlight else ""

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
        h += '<span class="nr-meta-tag" style="color:#B9791F;background:rgba(242,169,59,0.12);border-color:rgba(242,169,59,0.35);">🤖 AI Knowledge</span>'
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
    sym      = currency_symbol(currency)
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
        create_metric_card("Revenue", format_number(metrics.get("Revenue"), sym))
    with c2:
        create_metric_card("Net Income", format_number(metrics.get("Net Income"), sym))
    with c3:
        eps_val = metrics.get("EPS")
        create_metric_card("EPS", f"{sym}{eps_val}" if eps_val is not None else "N/A")
    with c4:
        create_metric_card("Free Cash Flow", format_number(metrics.get("Free Cash Flow"), sym))

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
            "excellent": ("#16A36A", "rgba(22,163,106,0.08)"),
            "good":      ("#16A36A", "rgba(22,163,106,0.08)"),
            "fair":      ("#B9791F", "rgba(242,169,59,0.12)"),
            "weak":      ("#B9791F", "rgba(242,169,59,0.12)"),
            "poor":      ("#E5484D", "rgba(229,72,77,0.08)"),
            "neutral":   ("#6F7580", "#F7F9FB"),
        }
        pills_html = ""
        for name, data in breakdown.items():
            txt_color, bg_color = status_styles.get(data["status"], ("#6F7580", "#F7F9FB"))
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
            "DCF Model", f"{sym}{dcf:,.2f}",
            f"5-year projection · {growth} growth · 10% discount",
            tooltip="Discounted Cash Flow (DCF) estimates a company's value by projecting its future cash flows and discounting them back to today's value using a required rate of return."
        )
    with v2:
        graham = valuation.get("Graham Number", 0)
        bvps   = valuation.get("Book Value Per Share", 0)
        create_valuation_card(
            "Graham Number", f"{sym}{graham:,.2f}",
            f"BVPS: {sym}{bvps:,.2f} · Conservative estimate",
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
        hovertemplate='%{x}<br>' + sym + '%{y:,.0f}<extra></extra>'
    )])
    ct = _chart_theme()
    fig.update_layout(
        template=ct["template"], paper_bgcolor=ct["paper_bgcolor"], plot_bgcolor=ct["plot_bgcolor"],
        font=dict(family="Inter", size=13, color=ct["font_color"]),
        xaxis=dict(gridcolor=ct["grid_color"]), yaxis=dict(gridcolor=ct["grid_color"]),
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
                    explanation = f"The stock appears <b>undervalued</b>. Fair value ({sym}{avg_intrinsic:,.2f}) is <b>{margin:.1f}% above</b> market price."
                elif margin < -15:
                    signal, signal_class, card_class, emoji = "SELL / AVOID", "sell", "verdict-sell", "🔴"
                    explanation = f"The stock appears <b>overvalued</b>. Price is <b>{abs(margin):.1f}% above</b> fair value ({sym}{avg_intrinsic:,.2f})."
                else:
                    signal, signal_class, card_class, emoji = "HOLD", "hold", "verdict-hold", "🟡"
                    explanation = f"Trading <b>near fair value</b> ({sym}{avg_intrinsic:,.2f}). No strong signal."

                st.markdown(f"""
                <div class="verdict-card {card_class}">
                    <div style="font-size:0.8rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">{ticker} · Current Market Price</div>
                    <div class="verdict-price">{sym}{current_price:,.2f}</div>
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

def _navigate(page_key: str):
    """Switch pages via st.query_params + st.rerun() instead of an <a href> link.

    A raw <a href="?nav=..."> forces the browser to do a full page navigation —
    reloading the whole Streamlit JS bundle and reconnecting the WebSocket —
    which is what caused the blank-page flash when switching tabs. Setting
    query params and rerunning keeps the existing session alive, so only the
    page content changes.
    """
    st.query_params["nav"] = page_key
    st.rerun()


def _toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()


def _render_topbar(current_page: str):
    nav_items = [
        ("ticker",       "Stocks"),
        ("screener",     "Screener"),
        ("pdf",          "Analysis"),
        ("compare",      "Compare"),
        ("quarterly",    "Quarterly"),
        ("news-radar",   "News Radar"),
    ]

    with st.container(key="topbar"):
        logo_col, nav_col, login_col, theme_col, cta_col, burger_col = st.columns(
            [2.2, 5.0, 0.9, 0.6, 1.5, 0.5], vertical_alignment="center"
        )

        with logo_col:
            with st.container(key="topbar_logo"):
                if st.button("🔵 EquityIQ", key="nav_home", type="tertiary"):
                    _navigate("home")

        with nav_col:
            with st.container(key="topbar_nav"):
                nav_cols = st.columns(len(nav_items))
                for col, (nav_key, nav_label) in zip(nav_cols, nav_items):
                    with col:
                        btn_type = "primary" if current_page == nav_key else "tertiary"
                        if st.button(nav_label, key=f"nav_{nav_key}", type=btn_type, use_container_width=True):
                            _navigate(nav_key)

        with login_col:
            with st.container(key="topbar_login"):
                if st.button("Log in", key="nav_login", type="tertiary"):
                    st.toast("Login is coming soon — EquityIQ is currently open access.", icon="🔒")

        with theme_col:
            with st.container(key="topbar_theme"):
                icon = "☀️" if st.session_state.dark_mode else "🌙"
                if st.button(icon, key="nav_theme", type="tertiary", help="Switch to light theme" if st.session_state.dark_mode else "Switch to dark theme"):
                    _toggle_theme()

        with cta_col:
            with st.container(key="topbar_cta"):
                if st.button("Get Started", key="nav_cta", type="primary", use_container_width=True):
                    _navigate("ticker")

        with burger_col:
            with st.container(key="topbar_hamburger"):
                with st.popover("☰"):
                    with st.container(key="topbar_mobilemenu"):
                        for nav_key, nav_label in nav_items:
                            btn_type = "primary" if current_page == nav_key else "tertiary"
                            if st.button(nav_label, key=f"mnav_{nav_key}", type=btn_type):
                                _navigate(nav_key)
                        st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)
                        if st.button("Log in", key="mnav_login", type="tertiary"):
                            st.toast("Login is coming soon — EquityIQ is currently open access.", icon="🔒")
                        if st.button("Get Started", key="mnav_cta", type="primary"):
                            _navigate("ticker")


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

_HERO_DEMO_HTML = """
<div id="eiqDemo" class="eiq-demo-root">
  <div class="eiq-steps">
    <div class="step" data-i="0"><span class="dot"></span><span class="cap">Search a company</span></div>
    <div class="step" data-i="1"><span class="dot"></span><span class="cap">Health Score</span></div>
    <div class="step" data-i="2"><span class="dot"></span><span class="cap">Upload 10-K</span></div>
    <div class="step" data-i="3"><span class="dot"></span><span class="cap">Investment Memo</span></div>
  </div>
  <div class="frame-wrap">
    <div class="device-frame">
      <div class="bar"><span class="d"></span><span class="d"></span><span class="d"></span><span class="url">equityiq.app</span></div>
      <div class="screen">
        <div class="slide" data-slide="0">
          <div class="s-label">Search any stock</div>
          <div class="search-box"><span class="mag">&#128269;</span><span class="q">NVIDIA</span><span class="caret"></span></div>
          <div class="result-row"><span class="res-tkr">NVDA</span><span class="res-name">NVIDIA Corporation</span><span class="res-px">$187.62</span></div>
        </div>
        <div class="slide" data-slide="1">
          <div class="s-label">Stock Health Score</div>
          <div class="ring-row">
            <div class="mp-ring2"><div class="ring-inner"><span class="ring-label">0</span></div></div>
            <div class="hbars">
              <div class="hbar-row"><span>Profitability</span><div class="htrack"><div class="hbar" data-pct="88"></div></div></div>
              <div class="hbar-row"><span>Valuation</span><div class="htrack"><div class="hbar warn" data-pct="70"></div></div></div>
              <div class="hbar-row"><span>Debt</span><div class="htrack"><div class="hbar" data-pct="90"></div></div></div>
              <div class="hbar-row"><span>Growth</span><div class="htrack"><div class="hbar" data-pct="82"></div></div></div>
            </div>
          </div>
        </div>
        <div class="slide" data-slide="2">
          <div class="s-label">Upload a 10-K report</div>
          <div class="file-chip">&#128196; NVDA_10-K_2025.pdf</div>
          <div class="up-track"><div class="up-fill"></div></div>
          <div class="fig-row"><span>Revenue</span><b>$130.5B</b></div>
          <div class="fig-row"><span>Net Income</span><b>$72.9B</b></div>
          <div class="fig-row"><span>EPS</span><b>$2.94</b></div>
        </div>
        <div class="slide" data-slide="3">
          <div class="s-label">Investment Memo</div>
          <div class="memo-block"><b>Thesis</b><span>Dominant AI-compute franchise with durable pricing power.</span></div>
          <div class="memo-block"><b>Risks</b><span>Customer concentration and export-control exposure.</span></div>
          <div class="memo-block"><b>Recommendation</b><span class="rec-buy">BUY &mdash; below intrinsic value estimate</span></div>
        </div>
      </div>
    </div>
    <div class="fc fc1"><span class="fc-dot" style="background:var(--pos)"></span>Health Score&nbsp;<b>A</b></div>
    <div class="fc fc2"><span class="fc-dot" style="background:var(--pos)"></span>Revenue Growth&nbsp;<b class="pos">+18.4%</b></div>
    <div class="fc fc3"><span class="fc-dot" style="background:var(--pos)"></span>Debt Risk&nbsp;<b class="pos">Low</b></div>
    <div class="fc fc4"><span class="fc-dot" style="background:var(--pos)"></span>Sentiment&nbsp;<b class="pos">Positive</b></div>
  </div>
</div>
<style>
  :root {
    --blue:#08A6DC; --blue-hover:#008CC0; --pale:#E6F7FC;
    --text:#111318; --sec:#6F7580; --border:#E5E8EC; --bg-alt:#F7F9FB;
    --pos:#16A36A; --neg:#E5484D; --warn:#F2A93B;
  }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; background:transparent; font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; }
  .eiq-demo-root { display:flex; align-items:center; gap:10px; padding: 30px 6px; }
  .eiq-steps { display:flex; flex-direction:column; gap:22px; flex-shrink:0; padding-top:4px; }
  .step { display:flex; align-items:flex-start; gap:8px; }
  .step .dot { width:9px; height:9px; border-radius:50%; background:var(--border); margin-top:3px; flex-shrink:0; transition:background .4s, box-shadow .4s; }
  .step .cap { font-size:11px; color:var(--sec); max-width:70px; line-height:1.35; transition:color .4s, font-weight .4s; }
  .step.active .dot { background:var(--blue); box-shadow:0 0 0 4px var(--pale); }
  .step.active .cap { color:var(--blue-hover); font-weight:700; }
  .frame-wrap { position:relative; flex:1; padding:22px; min-width:0; }
  .device-frame { background:#fff; border:1px solid var(--border); border-radius:18px; box-shadow:0 1px 2px rgba(17,19,24,.04), 0 8px 24px rgba(17,19,24,.07); overflow:hidden; }
  .bar { display:flex; align-items:center; gap:6px; padding:10px 14px; border-bottom:1px solid var(--border); background:var(--bg-alt); }
  .d { width:7px; height:7px; border-radius:50%; background:var(--border); }
  .url { margin-left:8px; font-size:11px; color:var(--sec); background:#fff; border:1px solid var(--border); border-radius:6px; padding:2px 10px; flex:1; }
  .screen { position:relative; height:250px; }
  .slide { position:absolute; inset:0; padding:20px 22px; opacity:0; transform:translateY(6px); transition:opacity .5s ease, transform .5s ease; pointer-events:none; }
  .slide.active { opacity:1; transform:translateY(0); pointer-events:auto; }
  .s-label { font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:var(--sec); margin-bottom:16px; }
  .search-box { display:flex; align-items:center; gap:8px; border:1px solid var(--border); border-radius:10px; padding:10px 14px; font-size:14px; color:var(--text); background:var(--bg-alt); }
  .search-box .mag { font-size:13px; }
  .caret { width:1px; height:14px; background:var(--blue); animation: blink 1s step-end infinite; }
  @keyframes blink { 50% { opacity:0; } }
  .result-row { display:flex; align-items:center; gap:10px; margin-top:12px; padding:10px 12px; border:1px solid var(--border); border-radius:10px; }
  .res-tkr { font-weight:800; font-size:12px; color:var(--blue-hover); font-family: monospace; }
  .res-name { flex:1; font-size:12px; color:var(--text); }
  .res-px { font-size:12px; font-weight:700; color:var(--text); font-variant-numeric: tabular-nums; }
  .ring-row { display:flex; align-items:center; gap:20px; }
  .mp-ring2 { --p:0; width:82px; height:82px; border-radius:50%; flex-shrink:0; background:conic-gradient(var(--pos) calc(var(--p) * 1%), var(--border) 0); transition: --p .9s cubic-bezier(.16,1,.3,1); }
  @property --p { syntax:'<number>'; inherits:true; initial-value:0; }
  .ring-inner { width:62px; height:62px; margin:10px; border-radius:50%; background:#fff; display:flex; align-items:center; justify-content:center; font-size:19px; font-weight:800; color:var(--pos); }
  .hbars { flex:1; }
  .hbar-row { font-size:10.5px; color:var(--sec); margin-bottom:8px; }
  .hbar-row span { display:block; margin-bottom:3px; }
  .htrack { height:6px; border-radius:6px; background:var(--border); overflow:hidden; }
  .hbar { height:100%; width:0%; border-radius:6px; background:var(--pos); transition:width .8s cubic-bezier(.16,1,.3,1); }
  .hbar.warn { background:var(--warn); }
  .file-chip { display:inline-flex; align-items:center; gap:8px; background:var(--bg-alt); border:1px solid var(--border); border-radius:10px; padding:8px 14px; font-size:12px; font-weight:600; color:var(--text); margin-bottom:14px; }
  .up-track { height:7px; border-radius:7px; background:var(--border); overflow:hidden; margin-bottom:16px; }
  .up-fill { height:100%; width:0%; border-radius:7px; background:var(--blue); transition:width 1.1s cubic-bezier(.16,1,.3,1); }
  .fig-row { display:flex; justify-content:space-between; font-size:12.5px; padding:6px 0; border-bottom:1px solid var(--border); opacity:0; transform:translateY(6px); transition:opacity .4s ease, transform .4s ease; }
  .fig-row span { color:var(--sec); }
  .fig-row b { color:var(--text); font-family:monospace; }
  .memo-block { margin-bottom:12px; opacity:0; transform:translateY(6px); transition:opacity .4s ease, transform .4s ease; }
  .memo-block b { display:block; font-size:10px; text-transform:uppercase; letter-spacing:.5px; color:var(--blue-hover); margin-bottom:3px; }
  .memo-block span { font-size:12px; color:var(--sec); line-height:1.5; }
  .rec-buy { color:var(--pos) !important; font-weight:700; }
  .fc { position:absolute; background:#fff; border:1px solid var(--border); border-radius:12px; box-shadow:0 1px 2px rgba(17,19,24,.04), 0 8px 20px rgba(17,19,24,.08); padding:8px 12px; font-size:11px; color:var(--sec); display:flex; align-items:center; gap:6px; opacity:0; animation: fcIn .5s ease forwards; white-space:nowrap; }
  .fc b { color:var(--text); }
  .fc b.pos { color:var(--pos); }
  .fc-dot { width:7px; height:7px; border-radius:50%; }
  .fc1 { top:2px; left:14px; animation-delay:.3s; }
  .fc2 { top:2px; right:14px; animation-delay:.6s; }
  .fc3 { bottom:2px; left:38px; animation-delay:.9s; }
  .fc4 { bottom:2px; right:38px; animation-delay:1.2s; }
  @keyframes fcIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
  @media (prefers-reduced-motion: reduce) {
    .slide { transition:none; }
    .caret { animation:none; opacity:1; }
    .fc { animation:none; opacity:1; }
    .mp-ring2, .hbar, .up-fill { transition:none; }
  }
</style>
<script>
(function () {
  var root = document.getElementById('eiqDemo');
  var slides = root.querySelectorAll('.slide');
  var steps = root.querySelectorAll('.eiq-steps .step');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var idx = 0;
  var timer = null;

  function countUp(el, target, dur) {
    var start = performance.now();
    function tick(now) {
      var p = Math.min(1, (now - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased);
      if (p < 1) { requestAnimationFrame(tick); }
      else { el.textContent = 'A'; }
    }
    requestAnimationFrame(tick);
  }

  function activate(i) {
    for (var s = 0; s < slides.length; s++) {
      slides[s].classList.toggle('active', s === i);
    }
    for (var s2 = 0; s2 < steps.length; s2++) {
      steps[s2].classList.toggle('active', s2 === i);
    }
    if (i === 1) {
      var ring = root.querySelector('.mp-ring2');
      var label = root.querySelector('.ring-label');
      if (ring) { ring.style.setProperty('--p', 0); requestAnimationFrame(function () { ring.style.setProperty('--p', 84); }); }
      if (label) { countUp(label, 84, 900); }
      var bars = root.querySelectorAll('.hbar');
      bars.forEach(function (b, bi) {
        b.style.width = '0%';
        setTimeout(function () { b.style.width = b.dataset.pct + '%'; }, 150 + bi * 100);
      });
    }
    if (i === 2) {
      var fill = root.querySelector('.up-fill');
      if (fill) { fill.style.width = '0%'; setTimeout(function () { fill.style.width = '100%'; }, 100); }
      var figs = root.querySelectorAll('.fig-row');
      figs.forEach(function (r, ri) {
        r.style.opacity = 0; r.style.transform = 'translateY(6px)';
        setTimeout(function () { r.style.opacity = 1; r.style.transform = 'translateY(0)'; }, 750 + ri * 220);
      });
    }
    if (i === 3) {
      var blocks = root.querySelectorAll('.memo-block');
      blocks.forEach(function (r, ri) {
        r.style.opacity = 0; r.style.transform = 'translateY(6px)';
        setTimeout(function () { r.style.opacity = 1; r.style.transform = 'translateY(0)'; }, 150 + ri * 300);
      });
    }
  }

  function next() { idx = (idx + 1) % slides.length; activate(idx); }
  function start() { if (!timer) { timer = setInterval(next, 2400); } }
  function stop() { clearInterval(timer); timer = null; }

  activate(0);

  if (!reduce) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) { start(); } else { stop(); } });
      }, { threshold: 0.3 });
      io.observe(root);
    } else {
      start();
    }
  } else {
    activate(1);
  }
})();
</script>
"""


def _render_story_section(eyebrow, title, desc, preview_html, reverse=False, anchor_id=None, shaded=False):
    alt_class = " alt" if reverse else ""
    shaded_class = " story-shaded" if shaded else ""
    id_attr = f' id="{anchor_id}"' if anchor_id else ""
    # Flatten preview_html to a single line first — Streamlit's markdown renderer treats
    # 4+ space-indented lines as a fenced code block, which was escaping our injected HTML
    # whenever a multi-line, indented preview string landed inside this f-string.
    preview_flat = " ".join(line.strip() for line in preview_html.strip().splitlines())
    html = (
        f'<div class="story-section-outer{shaded_class}"{id_attr}>'
        f'<div class="story-section{alt_class}">'
        f'<div>'
        f'<div class="story-eyebrow">{eyebrow}</div>'
        f'<div class="story-title">{title}</div>'
        f'<div class="story-desc">{desc}</div>'
        f'</div>'
        f'<div class="story-preview">{preview_flat}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_home_page(api_key):
    with st.container(key="hero_wrap"):
        left_col, right_col = st.columns([1.05, 0.95], gap="large", vertical_alignment="center")

        with left_col:
            st.markdown("""
            <div class="hero-label">✨ AI-powered equity research</div>
            <div class="hero-title-v2">Research any stock.<br>Understand it <span class="accent">instantly</span>.</div>
            <div class="hero-sub-v2">Upload financial reports, evaluate company health, compare stocks and monitor market-moving news — all from one intelligent research platform.</div>
            """, unsafe_allow_html=True)

            cta_a, cta_b = st.columns([1, 1.2])
            with cta_a:
                with st.container(key="hero_cta_primary"):
                    if st.button("Analyze a stock", key="hero_primary_btn", use_container_width=True):
                        _navigate("ticker")
            with cta_b:
                st.markdown(
                    '<a class="btn-secondary" href="#eiq-story-1">Explore the platform</a>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<div class="hero-trust">Built for investors, analysts and research teams.</div>',
                unsafe_allow_html=True,
            )

        with right_col:
            components.html(_HERO_DEMO_HTML, height=430, scrolling=False)

    _render_story_section(
        "10-K / 10-Q Analyzer",
        "Turn filings into answers",
        "Upload an annual or quarterly report and EquityIQ extracts revenue, margins, cash flow and risk factors in seconds — no manual line-item hunting.",
        """
        <div class="mp-file-chip">📄 NVDA_10-K_2025.pdf</div>
        <div class="mp-progress-track"><div class="mp-progress-fill"></div></div>
        <div class="mp-figure-row" style="animation-delay:.1s"><span class="mp-fig-label">Revenue</span><span class="mp-fig-value">$130.5B</span></div>
        <div class="mp-figure-row" style="animation-delay:.3s"><span class="mp-fig-label">Net Income</span><span class="mp-fig-value">$72.9B</span></div>
        <div class="mp-figure-row" style="animation-delay:.5s"><span class="mp-fig-label">Free Cash Flow</span><span class="mp-fig-value">$60.7B</span></div>
        <div class="mp-figure-row" style="animation-delay:.7s"><span class="mp-fig-label">EPS</span><span class="mp-fig-value">$2.94</span></div>
        """,
        reverse=False,
        anchor_id="eiq-story-1",
    )

    _render_story_section(
        "Stock Health Score",
        "Understand company health at a glance",
        "A composite A–F grade built from profitability, valuation, debt, growth and cash-flow signals — so you can size up a business before reading a single filing.",
        """
        <div class="mp-ring-wrap">
            <div class="mp-ring"><div class="mp-ring-inner">A</div></div>
            <div style="flex:1;">
                <div class="mp-bar-row"><div class="mp-bar-label"><span>Profitability</span><span>88</span></div><div class="mp-bar-track"><div class="mp-bar-fill" style="width:88%"></div></div></div>
                <div class="mp-bar-row"><div class="mp-bar-label"><span>Valuation</span><span>70</span></div><div class="mp-bar-track"><div class="mp-bar-fill" style="width:70%;background:var(--eiq-warning)"></div></div></div>
                <div class="mp-bar-row"><div class="mp-bar-label"><span>Debt</span><span>90</span></div><div class="mp-bar-track"><div class="mp-bar-fill" style="width:90%"></div></div></div>
                <div class="mp-bar-row"><div class="mp-bar-label"><span>Growth</span><span>82</span></div><div class="mp-bar-track"><div class="mp-bar-fill" style="width:82%"></div></div></div>
                <div class="mp-bar-row"><div class="mp-bar-label"><span>Cash Flow</span><span>76</span></div><div class="mp-bar-track"><div class="mp-bar-fill" style="width:76%"></div></div></div>
            </div>
        </div>
        """,
        reverse=True,
        shaded=True,
    )

    _render_story_section(
        "Investment Memo",
        "Build an investment case in minutes",
        "EquityIQ assembles a professional memo — thesis, opportunities, risks and a clear recommendation — grounded in the numbers it just extracted.",
        """
        <div class="mp-memo-line" style="animation-delay:.1s">Thesis</div>
        <div class="mp-memo-text" style="animation-delay:.2s">Dominant AI-compute franchise with durable pricing power.</div>
        <div class="mp-memo-line" style="animation-delay:.5s">Opportunities</div>
        <div class="mp-memo-text" style="animation-delay:.6s">Data-center demand and expanding software-attach margins.</div>
        <div class="mp-memo-line" style="animation-delay:.9s">Risks</div>
        <div class="mp-memo-text" style="animation-delay:1.0s">Customer concentration and export-control exposure.</div>
        <div class="mp-memo-line" style="animation-delay:1.3s">Recommendation</div>
        <div class="mp-memo-text" style="animation-delay:1.4s"><b style="color:var(--eiq-positive);">BUY</b> — trading below intrinsic value estimate.</div>
        """,
        reverse=False,
    )

    _render_story_section(
        "News Radar",
        "Know what is moving the market",
        "Every headline is classified by sentiment, urgency and the tickers it affects — so you spend time on the news that actually matters to your positions.",
        """
        <div class="mp-news-row" style="animation-delay:.1s"><span class="mp-news-pill pos">Positive</span><span class="mp-news-headline">NVIDIA beats on data-center revenue, raises guidance</span></div>
        <div class="mp-news-row" style="animation-delay:.3s"><span class="mp-news-pill warn">Medium</span><span class="mp-news-headline">New export restrictions could affect China shipments</span></div>
        <div class="mp-news-row" style="animation-delay:.5s"><span class="mp-news-pill neg">High</span><span class="mp-news-headline">Supplier delay raises short-term supply-chain risk</span></div>
        """,
        reverse=True,
        shaded=True,
    )


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
    st.markdown('<div class="page-sub">Search by company name or ticker to pull live financial data, health score &amp; valuation.</div>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        ticker_input = st.selectbox(
            "Stock Ticker",
            options=_company_search_options(),
            index=None,
            accept_new_options=True,
            placeholder="Type a company name (e.g. Apple, Reliance) or a ticker",
            label_visibility="collapsed",
            key="ticker_search",
        )
    with col_btn:
        ticker_go = st.button("🔍 Analyze", key="ticker_btn")

    st.markdown("""
    <div class="supported-docs">
        Examples: <span>Apple</span> <span>Tesla</span> <span>Google</span>
        <span>Microsoft</span> <span>Reliance</span> <span>TCS</span> <span>Infosys</span>
    </div>
    """, unsafe_allow_html=True)

    if ticker_go and ticker_input:
        ticker_clean = _resolve_ticker_input(ticker_input)
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

    compare_options = _company_search_options()
    input_cols   = st.columns(list([3] * st.session_state.compare_count) + [1])
    ticker_values = []
    for i in range(st.session_state.compare_count):
        with input_cols[i]:
            val = st.selectbox(
                f"Stock {i+1}",
                options=compare_options,
                index=None,
                accept_new_options=True,
                placeholder=f"e.g. {'Apple' if i == 0 else 'Microsoft' if i == 1 else 'Google'}",
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
        US: <span>Apple</span> <span>Microsoft</span> <span>Tesla</span>
        India: <span>Reliance</span> <span>TCS</span> <span>Infosys</span>
    </div>
    """, unsafe_allow_html=True)

    if compare_go:
        tickers = [_resolve_ticker_input(t) for t in ticker_values if t and str(t).strip()]
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
                        sym      = currency_symbol(m.get("Currency", "USD"))
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
                            "Price":      f"{sym}{p:,.2f}" if p else "N/A",
                            "Revenue":    format_number(m.get("Revenue"), sym),
                            "Net Income": format_number(m.get("Net Income"), sym),
                            "EPS":        f"{sym}{safe_num(m.get('EPS')):.2f}",
                            "DCF Value":  f"{sym}{dcf_v:,.2f}",
                            "Graham #":   f"{sym}{graham_v:,.2f}",
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
                        m         = d["metrics"]
                        trace_sym = currency_symbol(m.get("Currency", "USD"))
                        vals = [safe_num(m.get(k)) for k in compare_keys]
                        fig.add_trace(go.Bar(
                            name=d["ticker"],
                            x=["Revenue", "Net Income", "FCF", "Assets"],
                            y=vals,
                            marker_color=bar_colors[i % len(bar_colors)],
                            hovertemplate='%{x}<br>' + trace_sym + '%{y:,.0f}<extra>' + d["ticker"] + '</extra>'
                        ))

                    ct = _chart_theme()
                    fig.update_layout(
                        barmode='group', template=ct["template"],
                        paper_bgcolor=ct["paper_bgcolor"], plot_bgcolor=ct["plot_bgcolor"],
                        font=dict(family="Inter", size=13, color=ct["font_color"]),
                        xaxis=dict(gridcolor=ct["grid_color"]), yaxis=dict(gridcolor=ct["grid_color"]),
                        margin=dict(l=20, r=20, t=20, b=40), height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=ct["font_color"])),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, width="stretch")

                    # Verdict cards
                    st.markdown('<div class="section-head">Verdict</div>', unsafe_allow_html=True)
                    verdict_cols = st.columns(len(all_data))
                    for i, d in enumerate(all_data):
                        with verdict_cols[i]:
                            v, p     = d["valuation"], d["price"]
                            card_sym = currency_symbol(d["metrics"].get("Currency", "USD"))
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
                                price_str = f"{card_sym}{p:,.2f}"
                                fair_str  = f"Fair Value: {card_sym}{avg_fair:,.2f}"
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
                    q_sym         = currency_symbol(quarters_data[0].get("Currency", "USD")) if quarters_data else "$"

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
                            "Revenue":          format_number(q.get("Revenue"), q_sym),
                            "Net Income":       format_number(q.get("Net Income"), q_sym),
                            "EPS":              f"{q_sym}{safe_num(q.get('EPS')):.2f}",
                            "Free Cash Flow":   format_number(q.get("Free Cash Flow"), q_sym),
                            "Total Assets":     format_number(q.get("Total Assets"), q_sym),
                            "Total Liabilities": format_number(q.get("Total Liabilities"), q_sym),
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
                            hovertemplate=f'{display_label}<br>%{{x}}: {q_sym}%{{y:,.0f}}<extra></extra>'
                        ))
                    ct = _chart_theme()
                    fig_trend.update_layout(
                        template=ct["template"], paper_bgcolor=ct["paper_bgcolor"], plot_bgcolor=ct["plot_bgcolor"],
                        font=dict(family="Inter", size=13, color=ct["font_color"]),
                        xaxis=dict(gridcolor=ct["grid_color"], title="Quarter"),
                        yaxis=dict(gridcolor=ct["grid_color"], title=f"Value ({q_sym})"),
                        margin=dict(l=20, r=20, t=20, b=40), height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=ct["font_color"])),
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
                        ct = _chart_theme()
                        fig_growth.update_layout(
                            barmode='group', template=ct["template"],
                            paper_bgcolor=ct["paper_bgcolor"], plot_bgcolor=ct["plot_bgcolor"],
                            font=dict(family="Inter", size=13, color=ct["font_color"]),
                            xaxis=dict(gridcolor=ct["grid_color"], title="Quarter"),
                            yaxis=dict(gridcolor=ct["grid_color"], title="Growth %", zeroline=True, zerolinecolor=ct["grid_color"]),
                            margin=dict(l=20, r=20, t=20, b=40), height=380,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=ct["font_color"])),
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


def _render_general_market_scan(api_key):
    """General, query-less market sentiment scan (formerly the standalone Market Pulse page)."""
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
        return

    st.markdown('<div class="section-head">General Market Sentiment Feed</div>', unsafe_allow_html=True)

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


# ── Page: News Radar (also covers general market sentiment, formerly "Market Pulse") ──

def render_news_radar_page(api_key):
    st.markdown('<div class="page-title">News Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">AI-powered news intelligence — scan the general market or search a specific ticker/sector for sentiment, impact analysis &amp; affected-stock detection.</div>', unsafe_allow_html=True)

    if not api_key:
        st.info("Add your Gemini API Key in the .env file to use News Radar.")
        return

    scan_btn = st.button("⚡ Scan General Market News", key="sentiment_btn")

    st.markdown('<div class="section-head" style="margin-top:20px;">Or Search a Ticker / Sector</div>', unsafe_allow_html=True)

    nr_c1, nr_c2, nr_c3 = st.columns([4, 2, 1])
    with nr_c2:
        nr_type = st.selectbox("Type", ["Ticker", "Sector"], key="nr_type", label_visibility="collapsed")
    with nr_c1:
        if nr_type == "Ticker":
            nr_query_sel = st.selectbox(
                "Search", options=_company_search_options(), index=None,
                accept_new_options=True,
                placeholder="e.g. NVDA, Apple, Tesla, TCS...",
                key="nr_query_ticker", label_visibility="collapsed",
            )
            nr_query = _resolve_ticker_input(nr_query_sel) if nr_query_sel else ""
        else:
            nr_query = st.text_input(
                "Search", placeholder="e.g. Semiconductors · Banking · EV & Clean Energy",
                key="nr_query_sector", label_visibility="collapsed",
            )
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
        Tickers: <span>NVIDIA</span> <span>Tesla</span> <span>Apple</span> <span>Microsoft</span> <span>TCS</span>
        &nbsp;·&nbsp; Sectors: <span>Semiconductors</span> <span>Banking</span>
        <span>EV &amp; Clean Energy</span> <span>Healthcare</span> <span>Indian Markets</span>
    </div>
    """, unsafe_allow_html=True)

    if scan_btn:
        _render_general_market_scan(api_key)

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
                "Positive": "#16A36A", "Negative": "#E5484D",
                "Neutral":  "#6F7580", "Mixed":    "#B9791F",
            }.get(overall, "#6F7580")

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


def _mcap_label(val, sym="$"):
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"{sym}{val/1e12:.2f}T"
    if val >= 1e9:
        return f"{sym}{val/1e9:.1f}B"
    if val >= 1e6:
        return f"{sym}{val/1e6:.0f}M"
    return f"{sym}{val:,.0f}"


# ── Screener filter metadata — single source of truth for every filter's
#    session-state key, widget kind, default value and category. Drives Reset,
#    active-filter counts, the accordion summaries and the removable chip row.
#    Every key/default matches the original implementation exactly — nothing
#    renamed, removed or duplicated across categories. ──────────────────────
_SC_FILTER_META = {
    "f_mc":           {"kind": "range",    "label": "Market Cap",           "default": (0.0, 3000.0),  "unit": "Bn", "category": "market"},
    "f_sec":          {"kind": "multi",    "label": "Sector",               "default": [],              "category": "market"},
    "f_cty":          {"kind": "multi",    "label": "Country",              "default": [],              "category": "market"},
    "f_pe":           {"kind": "range",    "label": "P/E",                  "default": (0.0, 100.0),   "unit": "x", "category": "valuation"},
    "f_pb":           {"kind": "range",    "label": "P/B",                  "default": (0.0, 25.0),    "unit": "x", "category": "valuation"},
    "f_ps":           {"kind": "range",    "label": "P/S",                  "default": (0.0, 25.0),    "unit": "x", "category": "valuation"},
    "f_div":          {"kind": "range",    "label": "Dividend Yield",       "default": (0.0, 15.0),    "unit": "%", "category": "valuation"},
    "f_roe":          {"kind": "range",    "label": "ROE",                  "default": (-30.0, 100.0), "unit": "%", "category": "quality"},
    "f_roa":          {"kind": "range",    "label": "ROA",                  "default": (-20.0, 50.0),  "unit": "%", "category": "quality"},
    "f_pm":           {"kind": "range",    "label": "Profit Margin",        "default": (-50.0, 80.0),  "unit": "%", "category": "quality"},
    "f_fcf":          {"kind": "bool",     "label": "Positive FCF only",    "default": False,           "category": "quality"},
    "f_rg":           {"kind": "range",    "label": "Revenue Growth",       "default": (-50.0, 100.0), "unit": "%", "category": "growth"},
    "f_eg":           {"kind": "range",    "label": "Earnings Growth",      "default": (-50.0, 100.0), "unit": "%", "category": "growth"},
    "f_de":           {"kind": "range",    "label": "Debt/Equity",          "default": (0.0, 5.0),     "unit": "x", "category": "risk"},
    "f_cr":           {"kind": "range",    "label": "Current Ratio",        "default": (0.0, 5.0),     "unit": "x", "category": "risk"},
    "f_beta":         {"kind": "range",    "label": "Beta",                 "default": (-1.0, 4.0),    "unit": "",  "category": "risk"},
    "f_only_div":     {"kind": "bool",     "label": "Dividend payers only", "default": False,           "category": "dividend"},
    "f_upcoming_div": {"kind": "bool",     "label": "Upcoming ex-dividend", "default": False,           "category": "dividend"},
    "f_min_yield":    {"kind": "min_only", "label": "Min Dividend Yield",   "default": 0.0,    "unit": "%", "category": "dividend"},
    "f_payout":       {"kind": "max_only", "label": "Max Payout Ratio",     "default": 200.0,  "unit": "%", "category": "dividend"},
    "f_analyst":      {"kind": "multi",    "label": "Analyst Rating",       "default": [],               "category": "analyst"},
    "f_has_target":   {"kind": "bool",     "label": "Has target price",     "default": False,            "category": "analyst"},
    "f_min_analysts": {"kind": "min_only", "label": "Min analyst opinions", "default": 0,       "unit": "", "category": "analyst"},
}

_SC_CATEGORIES = [
    ("market",    "Market",    "public"),
    ("valuation", "Valuation", "monitoring"),
    ("quality",   "Quality",   "verified"),
    ("growth",    "Growth",    "trending_up"),
    ("risk",      "Risk",      "warning"),
    ("dividend",  "Dividend",  "payments"),
    ("analyst",   "Analyst",   "groups"),
]

_SC_KEYWORDS = {
    "market":    ["market cap", "sector", "country", "market", "currency"],
    "valuation": ["p/e", "pe ratio", "p/b", "pb ratio", "p/s", "ps ratio", "valuation", "dividend yield"],
    "quality":   ["roe", "roa", "profit margin", "quality", "free cash flow", "fcf", "health"],
    "growth":    ["revenue growth", "earnings growth", "growth"],
    "risk":      ["debt", "equity", "current ratio", "beta", "risk"],
    "dividend":  ["dividend", "yield", "payout", "ex-dividend"],
    "analyst":   ["analyst", "rating", "target price", "buy", "sell", "hold"],
}


def _sc_is_active(key):
    m = _SC_FILTER_META[key]
    return st.session_state.get(key, m["default"]) != m["default"]


def _sc_phrase(key):
    m = _SC_FILTER_META[key]
    if not _sc_is_active(key):
        return ""
    cur = st.session_state.get(key, m["default"])
    kind, label, unit = m["kind"], m["label"], m.get("unit", "")
    if kind == "range":
        lo_d, hi_d = m["default"]
        lo, hi = cur
        if lo != lo_d and hi != hi_d:
            return f"{label} {lo:g}–{hi:g}{unit}"
        if hi != hi_d:
            return f"{label} below {hi:g}{unit}"
        return f"{label} above {lo:g}{unit}"
    if kind == "min_only":
        return f"{label} above {cur:g}{unit}"
    if kind == "max_only":
        return f"{label} below {cur:g}{unit}"
    if kind == "bool":
        return label
    if kind == "multi":
        vals = [str(c).replace("_", " ").title() for c in cur]
        if len(vals) <= 2:
            return f"{label}: {', '.join(vals)}"
        return f"{label}: {len(vals)} selected"
    return label


def _sc_category_active_count(cat):
    return sum(1 for k, m in _SC_FILTER_META.items() if m["category"] == cat and _sc_is_active(k))


def _sc_category_summary(cat):
    phrases = [_sc_phrase(k) for k, m in _SC_FILTER_META.items() if m["category"] == cat]
    return " · ".join(p for p in phrases if p)


def _sc_reset_all():
    """Reset-to-defaults, used exclusively as an on_click callback (never called
    inline). Callbacks run *before* the script body re-executes and re-creates
    the filter widgets, so writing to their session-state keys here is safe —
    doing the same thing inline, after those widgets have already rendered
    this run, raises StreamlitAPIException. Streamlit reruns automatically
    after an on_click callback, so no explicit st.rerun() is needed or wanted."""
    for k, m in _SC_FILTER_META.items():
        st.session_state[k] = m["default"]
    for k in ("f_mc_min_input", "f_mc_max_input", "sc_search", "sc_filter_search", "f_currency", "f_currency_prev"):
        st.session_state.pop(k, None)


def _sc_clear_one(key):
    """Clears a single filter — on_click callback only (see _sc_reset_all)."""
    st.session_state[key] = _SC_FILTER_META[key]["default"]
    if key == "f_mc":
        st.session_state.pop("f_mc_min_input", None)
        st.session_state.pop("f_mc_max_input", None)


def _sc_select_all_sectors(all_sectors):
    st.session_state["f_sec"] = all_sectors


def _sc_clear_sectors():
    st.session_state["f_sec"] = []


def _render_sc_filters(stocks, search_text=""):
    """Renders the 7 filter accordions. Called from either the sidebar column
    or the collapsed-sidebar popover — same widgets, same session-state keys,
    either way, so filtering logic downstream never needs to know which."""
    fx_rate = get_usd_inr_rate()
    prev_currency = st.session_state.get("f_currency_prev", "USD")
    cur_currency  = st.session_state.get("f_currency", "USD")
    if cur_currency != prev_currency:
        factor = fx_rate if cur_currency == "INR" else (1.0 / fx_rate)
        old_lo, old_hi = st.session_state.get("f_mc", (0.0, 3000.0))
        st.session_state["f_mc"] = (old_lo * factor, old_hi * factor)
        st.session_state.pop("f_mc_min_input", None)
        st.session_state.pop("f_mc_max_input", None)
        st.session_state["f_currency_prev"] = cur_currency

    mc_bound = round(3000.0 * (fx_rate if cur_currency == "INR" else 1.0), -1)
    mc_step  = round(10.0 * (fx_rate if cur_currency == "INR" else 1.0), 1) or 1.0
    mc_sym   = "₹" if cur_currency == "INR" else "$"

    q = (search_text or "").strip().lower()

    for cat_key, cat_label, icon in _SC_CATEGORIES:
        if q and q not in cat_label.lower() and not any(q in kw for kw in _SC_KEYWORDS.get(cat_key, [])):
            continue

        n_active = _sc_category_active_count(cat_key)
        summary  = _sc_category_summary(cat_key)
        label = cat_label
        if n_active:
            label += f" · {n_active} active"
        if summary:
            label += f"  —  {summary}"

        with st.expander(label, icon=f":material/{icon}:", expanded=bool(q)):
            if cat_key == "market":
                st.selectbox(
                    "Market Cap currency", ["USD", "INR"], key="f_currency",
                    help="Converts every stock's market cap into this currency so the filter below "
                         "compares US and Indian companies on one consistent scale.",
                )
                cur_mc = st.session_state.get("f_mc", (0.0, mc_bound))
                st.session_state.setdefault("f_mc_min_input", float(min(max(cur_mc[0], 0.0), mc_bound)))
                st.session_state.setdefault("f_mc_max_input", float(min(max(cur_mc[1], 0.0), mc_bound)))

                def _sc_mc_from_inputs():
                    lo = st.session_state.get("f_mc_min_input", 0.0)
                    hi = st.session_state.get("f_mc_max_input", 0.0)
                    st.session_state["f_mc"] = (min(lo, hi), max(lo, hi))

                def _sc_mc_from_slider():
                    lo, hi = st.session_state.get("f_mc", (0.0, mc_bound))
                    st.session_state["f_mc_min_input"] = lo
                    st.session_state["f_mc_max_input"] = hi

                nc1, nc2 = st.columns(2)
                with nc1:
                    st.number_input(
                        f"Min ({mc_sym}Bn)", min_value=0.0, max_value=mc_bound,
                        step=mc_step, key="f_mc_min_input", on_change=_sc_mc_from_inputs,
                    )
                with nc2:
                    st.number_input(
                        f"Max ({mc_sym}Bn)", min_value=0.0, max_value=mc_bound,
                        step=mc_step, key="f_mc_max_input", on_change=_sc_mc_from_inputs,
                    )
                # Widgets sync each other via on_change callbacks (which run *before* the
                # script re-executes) rather than writing to session_state after the fact —
                # Streamlit forbids modifying a widget's state once it's been instantiated
                # in the same run, so post-hoc syncing here would raise StreamlitAPIException.
                mc_range = st.slider(
                    f"Market Cap ({mc_sym}Bn)", 0.0, mc_bound,
                    value=st.session_state.get("f_mc", (0.0, mc_bound)), step=mc_step,
                    key="f_mc", on_change=_sc_mc_from_slider,
                )

                all_sectors   = sorted({d.get("sector", "") for d in stocks if d.get("sector")})
                all_countries = sorted({d.get("country", "") for d in stocks if d.get("country")})
                st.multiselect("Sector", all_sectors, key="f_sec")
                bsel, bclr = st.columns(2)
                with bsel:
                    st.button(
                        "Select all sectors", key="f_sec_all", width="stretch",
                        on_click=_sc_select_all_sectors, args=(all_sectors,),
                    )
                with bclr:
                    st.button("Clear sectors", key="f_sec_clr", width="stretch", on_click=_sc_clear_sectors)
                st.multiselect("Country", all_countries, key="f_cty")

            elif cat_key == "valuation":
                st.slider("P/E Ratio", 0.0, 100.0, (0.0, 100.0), 1.0, key="f_pe",
                          help="Price-to-Earnings — years of current earnings to pay back the share price.")
                st.slider("P/B Ratio", 0.0, 25.0, (0.0, 25.0), 0.5, key="f_pb",
                          help="Price-to-Book — share price relative to book value per share.")
                st.slider("P/S Ratio", 0.0, 25.0, (0.0, 25.0), 0.5, key="f_ps",
                          help="Price-to-Sales — market cap relative to annual revenue.")
                st.slider("Dividend Yield (%)", 0.0, 15.0, (0.0, 15.0), 0.25, key="f_div",
                          help="Annual dividend as a percentage of share price.")

            elif cat_key == "quality":
                st.slider("ROE (%)", -30.0, 100.0, (-30.0, 100.0), 1.0, key="f_roe",
                          help="Return on Equity — net income as a percentage of shareholder equity.")
                st.slider("ROA (%)", -20.0, 50.0, (-20.0, 50.0), 1.0, key="f_roa",
                          help="Return on Assets — net income as a percentage of total assets.")
                st.slider("Profit Margin (%)", -50.0, 80.0, (-50.0, 80.0), 1.0, key="f_pm")
                st.checkbox("Positive Free Cash Flow only", key="f_fcf")
                st.caption("EquityIQ Health Score (0–100, A–F) is a sortable column in the results table below.")

            elif cat_key == "growth":
                st.slider("Revenue Growth (%)", -50.0, 100.0, (-50.0, 100.0), 1.0, key="f_rg")
                st.slider("Earnings Growth (%)", -50.0, 100.0, (-50.0, 100.0), 1.0, key="f_eg")

            elif cat_key == "risk":
                st.slider("Debt / Equity", 0.0, 5.0, (0.0, 5.0), 0.1, key="f_de")
                st.slider("Current Ratio", 0.0, 5.0, (0.0, 5.0), 0.1, key="f_cr")
                st.slider("Beta", -1.0, 4.0, (-1.0, 4.0), 0.1, key="f_beta")

            elif cat_key == "dividend":
                st.checkbox("Dividend payers only", key="f_only_div")
                st.checkbox("Upcoming ex-dividend (next 60 days)", key="f_upcoming_div")
                st.slider("Min Dividend Yield (%)", 0.0, 10.0, 0.0, 0.25, key="f_min_yield")
                st.slider("Max Payout Ratio (%)", 0.0, 200.0, 200.0, 5.0, key="f_payout")

            elif cat_key == "analyst":
                st.multiselect(
                    "Analyst Rating", ["strong_buy", "buy", "hold", "underperform", "sell"],
                    key="f_analyst", format_func=lambda v: v.replace("_", " ").title(),
                )
                st.checkbox("Has analyst target price", key="f_has_target")
                st.slider("Min analyst opinions", 0, 50, 0, 1, key="f_min_analysts")


def render_screener_page(_api_key):
    import datetime as _dt
    import pandas as pd

    st.session_state.setdefault("sc_sidebar_open", True)

    header_l, header_r = st.columns([1.6, 2], vertical_alignment="bottom")
    with header_l:
        st.markdown('<div class="page-title">Stock Screener</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Discover companies matching your investment criteria across US and Indian markets.</div>', unsafe_allow_html=True)
    with header_r:
        with st.container(key="sc_header_actions"):
            hb1, hb2, hb3, hb4 = st.columns(4)
            with hb1:
                with st.container(key="sc_reset"):
                    if st.button("Reset", key="sc_reset_btn", icon=":material/restart_alt:", width="stretch"):
                        _sc_reset_all()
            with hb2:
                sidebar_label = "Hide filters" if st.session_state.sc_sidebar_open else "Show filters"
                with st.container(key="sc_sidebar_toggle_wrap"):
                    if st.button(sidebar_label, key="sc_sidebar_toggle", icon=":material/tune:", width="stretch"):
                        # No st.rerun() here on purpose: this button sits *before* the
                        # sc_us/sc_india checkboxes in the script. Calling st.rerun() here
                        # interrupts the run before those widgets are instantiated this
                        # pass, which made Streamlit treat them as orphaned and reset them
                        # to their value= default on the next run. Letting the script
                        # continue naturally (it already reruns because the button was
                        # clicked) avoids that entirely.
                        st.session_state.sc_sidebar_open = not st.session_state.sc_sidebar_open
            with hb3:
                refresh_clicked = False
                with st.container(key="sc_refresh"):
                    if st.session_state.get("screener_results"):
                        refresh_clicked = st.button(
                            "Refresh", key="sc_refresh_btn", icon=":material/refresh:", width="stretch",
                            help="Clear cache and re-fetch fresh data",
                        )
            with hb4:
                with st.container(key="sc_run"):
                    scan_btn = st.button("Run Screen", key="sc_scan", type="primary", icon=":material/search:", width="stretch")
            if st.session_state.get("screener_fetched_at"):
                st.markdown(f'<div class="sc-refresh-meta">Last refreshed {st.session_state["screener_fetched_at"]}</div>', unsafe_allow_html=True)

    # ── Market universe ──────────────────────────────────────────────────────
    with st.container(key="sc_market_row"):
        st.markdown('<div class="sc-universe-card"><div class="sc-universe-label">Market Universe</div>', unsafe_allow_html=True)
        um1, um2 = st.columns([1, 1])
        with um1:
            include_us = st.checkbox("S&P 500 · US", value=True, key="sc_us")
        with um2:
            include_india = st.checkbox("Nifty 100 · India", value=True, key="sc_india")
        all_tickers = get_all_tickers(include_us, include_india)
        st.markdown(
            f'<div class="sc-universe-count"><b>{len(all_tickers)} companies</b> selected '
            f'<span class="info-tooltip">ⓘ<span class="info-tooltip-text">'
            f'S&amp;P 500 list refreshes daily from Wikipedia. Indian list covers Nifty 50 + Nifty Next 50 (Nifty 100).'
            f'</span></span></div></div>',
            unsafe_allow_html=True,
        )

    if refresh_clicked:
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
        st.session_state["screener_fetched_at"] = _dt.datetime.now().strftime("%I:%M %p").lstrip("0")

    stocks = st.session_state.get("screener_results", [])
    if not stocks:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:var(--eiq-text-secondary);">
            <div style="font-size:1rem;font-weight:600;color:var(--eiq-text);">Run a screen to load live data</div>
            <div style="font-size:0.84rem;margin-top:6px;">First scan: ~60–90 s &nbsp;·&nbsp; Results cached 15 minutes</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Filter sidebar (or popover when collapsed) + results workspace ────────
    total_active = sum(1 for k in _SC_FILTER_META if _sc_is_active(k))

    def _sidebar_header_and_filters():
        badge = f'<span class="sc-active-badge">{total_active}</span>' if total_active else ""
        st.markdown(f'<div class="sc-sidebar-header"><div class="sc-sidebar-title">Filters{badge}</div></div>', unsafe_allow_html=True)
        hc1, hc2 = st.columns([3, 1.4])
        with hc1:
            filter_search = st.text_input(
                "Search filters", placeholder="Search filters (P/E, ROE, dividend…)",
                key="sc_filter_search", label_visibility="collapsed",
            )
        with hc2:
            with st.container(key="sc_clear_all"):
                if total_active and st.button("Clear all", key="sc_clear_all_btn"):
                    _sc_reset_all()
        _render_sc_filters(stocks, filter_search)

    if st.session_state.sc_sidebar_open:
        sidebar_col, results_col = st.columns([1, 2.7], gap="large")
        with sidebar_col:
            with st.container(key="sc_sidebar"):
                _sidebar_header_and_filters()
    else:
        results_col = st.container()
        with results_col:
            with st.popover("Filters", icon=":material/tune:"):
                _sidebar_header_and_filters()

    with results_col:
        # ── Read current filter values from session state ──────────────────
        mc_range      = st.session_state.get("f_mc", (0.0, 3000.0))
        sel_sectors   = st.session_state.get("f_sec", [])
        sel_countries = st.session_state.get("f_cty", [])
        pe_range      = st.session_state.get("f_pe", (0.0, 100.0))
        pb_range      = st.session_state.get("f_pb", (0.0, 25.0))
        ps_range      = st.session_state.get("f_ps", (0.0, 25.0))
        div_range     = st.session_state.get("f_div", (0.0, 15.0))
        roe_range     = st.session_state.get("f_roe", (-30.0, 100.0))
        roa_range     = st.session_state.get("f_roa", (-20.0, 50.0))
        pm_range      = st.session_state.get("f_pm", (-50.0, 80.0))
        pos_fcf       = st.session_state.get("f_fcf", False)
        rg_range      = st.session_state.get("f_rg", (-50.0, 100.0))
        eg_range      = st.session_state.get("f_eg", (-50.0, 100.0))
        de_range      = st.session_state.get("f_de", (0.0, 5.0))
        cr_range      = st.session_state.get("f_cr", (0.0, 5.0))
        beta_range    = st.session_state.get("f_beta", (-1.0, 4.0))
        only_divid    = st.session_state.get("f_only_div", False)
        upcoming_div  = st.session_state.get("f_upcoming_div", False)
        min_yield     = st.session_state.get("f_min_yield", 0.0)
        max_payout    = st.session_state.get("f_payout", 200.0)
        sel_analyst   = st.session_state.get("f_analyst", [])
        has_target    = st.session_state.get("f_has_target", False)
        min_analysts  = st.session_state.get("f_min_analysts", 0)
        cur_currency  = st.session_state.get("f_currency", "USD")
        mc_sym        = "₹" if cur_currency == "INR" else "$"
        fx_rate       = get_usd_inr_rate()

        today      = _dt.date.today()
        cutoff_div = today + _dt.timedelta(days=60)

        filtered = []
        for d in stocks:
            conv_cap = convert_market_cap(d.get("market_cap"), d.get("currency", "USD"), cur_currency, fx_rate)
            mc_b = (conv_cap or 0) / 1e9
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

        # ── Active-filter chips ──────────────────────────────────────────────
        active_keys = [k for k in _SC_FILTER_META if _sc_is_active(k)]
        if active_keys:
            st.markdown('<div style="font-size:0.78rem;font-weight:600;color:var(--eiq-text-secondary);margin:2px 0 6px;">Active filters</div>', unsafe_allow_html=True)
            with st.container(key="sc_active_chips"):
                for k in active_keys:
                    st.button(_sc_phrase(k), key=f"chip_{k}", icon=":material/close:", on_click=_sc_clear_one, args=(k,))
                if len(active_keys) > 1:
                    st.button("Clear all", key="sc_clear_all_chip", icon=":material/clear_all:", on_click=_sc_reset_all)

        # ── Summary cards ─────────────────────────────────────────────────────
        div_payers = sum(1 for d in filtered if (d.get("dividend_yield") or 0) > 0)
        avg_hs     = round(sum(d.get("health_score", 0) for d in filtered) / len(filtered)) if filtered else 0
        a_grades   = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for d in filtered:
            g = d.get("health_grade", "")
            if g in a_grades:
                a_grades[g] += 1
        top_grade = max(a_grades, key=a_grades.get) if filtered and any(a_grades.values()) else "—"

        st.markdown(f"""
        <div class="sc-summary-row">
            <div class="sc-summary-card"><div>
                <div class="sc-summary-label">Matching Stocks</div>
                <div class="sc-summary-value">{len(filtered)}</div>
            </div></div>
            <div class="sc-summary-card"><div>
                <div class="sc-summary-label">Dividend Payers</div>
                <div class="sc-summary-value">{div_payers}</div>
            </div></div>
            <div class="sc-summary-card"><div>
                <div class="sc-summary-label">Avg Health Score</div>
                <div class="sc-summary-value">{avg_hs}<span class="sc-summary-help"> /100</span></div>
            </div></div>
            <div class="sc-summary-card"><div>
                <div class="sc-summary-label">Most Common Grade</div>
                <div class="sc-summary-value">{top_grade}</div>
            </div></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Results table ────────────────────────────────────────────────────
        st.markdown(f'<div class="section-head">Results ({len(filtered)} stocks)</div>', unsafe_allow_html=True)

        if not filtered:
            st.markdown("""
            <div style="text-align:center;padding:50px 0;color:var(--eiq-text-secondary);">
                <div style="font-size:1rem;font-weight:600;color:var(--eiq-text);">No companies match your filters.</div>
                <div style="font-size:0.84rem;margin-top:6px;">Try relaxing the filter ranges or clearing some filters.</div>
            </div>
            """, unsafe_allow_html=True)
            if active_keys:
                st.button("Clear filters", key="sc_clear_empty", icon=":material/clear_all:", on_click=_sc_reset_all)
        else:
            mc_col_name = f"Mkt Cap ({mc_sym}Bn)"
            with st.container(key="sc_toolbar"):
                tb1, tb2, tb3 = st.columns([3, 2.4, 1.4])
                with tb1:
                    search_q = st.text_input(
                        "Search results", placeholder="Search by ticker or company…",
                        key="sc_search", label_visibility="collapsed",
                    )
                with tb2:
                    optional_cols = ["Sector", "P/S", "ROA", "Current Ratio", "Ex-Div Date"]
                    shown_optional = st.multiselect(
                        "Columns", optional_cols, default=optional_cols, key="sc_columns",
                        label_visibility="collapsed", placeholder="Customize columns",
                    )
                with tb3:
                    density = st.selectbox("Density", ["Comfortable", "Compact"], key="sc_density", label_visibility="collapsed")

            table_data = filtered
            if search_q and search_q.strip():
                sq = search_q.strip().lower()
                table_data = [d for d in table_data if sq in d["ticker"].lower() or sq in (d.get("company") or "").lower()]

            rows = []
            for d in table_data:
                row_sym  = currency_symbol(d.get("currency", "USD"))
                conv_cap = convert_market_cap(d.get("market_cap"), d.get("currency", "USD"), cur_currency, fx_rate)
                exch = "NSE" if d["ticker"].endswith(".NS") else ("BSE" if d["ticker"].endswith(".BO") else "US")
                rows.append({
                    "Ticker":      d["ticker"],
                    "Company":     d["company"] or d["ticker"],
                    "Exchange":    exch,
                    "Sector":      d.get("sector", ""),
                    mc_col_name:   round(conv_cap / 1e9, 2) if conv_cap else None,
                    "Price":       f"{row_sym}{d['price']:,.2f}" if d.get("price") else None,
                    "P/E":         d.get("pe_ratio"),
                    "P/B":         d.get("pb_ratio"),
                    "P/S":         d.get("ps_ratio"),
                    "Div Yield":   round(d["dividend_yield"] * 100, 2) if d.get("dividend_yield") else None,
                    "ROE":         round(d["roe"] * 100, 1) if d.get("roe") is not None else None,
                    "ROA":         round(d["roa"] * 100, 1) if d.get("roa") is not None else None,
                    "Rev Growth":  round(d["revenue_growth"] * 100, 1) if d.get("revenue_growth") is not None else None,
                    "D/E":         d.get("debt_to_equity"),
                    "Current Ratio": d.get("current_ratio"),
                    "Health":      f'{d.get("health_score", "?")} · {d.get("health_grade", "?")}',
                    "Analyst":     (d.get("analyst_rating") or "").replace("_", " ").title() or "—",
                    "Target":      f"{row_sym}{d['target_price']:,.2f}" if d.get("target_price") else None,
                    "Ex-Div Date": d.get("ex_div_date") or "—",
                })

            df = pd.DataFrame(rows)

            canonical = ["Ticker", "Company", "Exchange", "Sector", mc_col_name, "Price", "P/E", "P/B", "P/S",
                         "Div Yield", "ROE", "ROA", "Rev Growth", "D/E", "Current Ratio", "Health", "Analyst",
                         "Target", "Ex-Div Date"]
            visible = {"Ticker", "Company", "Exchange", mc_col_name, "Price", "P/E", "P/B", "Div Yield",
                       "ROE", "Rev Growth", "D/E", "Health", "Analyst", "Target"} | set(shown_optional)
            visible_cols = [c for c in canonical if c in visible]

            col_cfg = {
                "Ticker":        st.column_config.TextColumn("Ticker", pinned=True, width="small"),
                "Company":       st.column_config.TextColumn("Company", pinned=True, width="medium"),
                "Exchange":      st.column_config.TextColumn("Exch", width="small"),
                "Sector":        st.column_config.TextColumn("Sector"),
                mc_col_name:     st.column_config.NumberColumn(mc_col_name, format="%.2f", alignment="right"),
                "Price":         st.column_config.TextColumn("Price", alignment="right"),
                "P/E":           st.column_config.NumberColumn("P/E", format="%.1f", alignment="right"),
                "P/B":           st.column_config.NumberColumn("P/B", format="%.2f", alignment="right"),
                "P/S":           st.column_config.NumberColumn("P/S", format="%.2f", alignment="right"),
                "Div Yield":     st.column_config.NumberColumn("Div Yield %", format="%.2f", alignment="right"),
                "ROE":           st.column_config.NumberColumn("ROE %", format="%.1f", alignment="right"),
                "ROA":           st.column_config.NumberColumn("ROA %", format="%.1f", alignment="right"),
                "Rev Growth":    st.column_config.NumberColumn("Rev Growth %", format="%.1f", alignment="right"),
                "D/E":           st.column_config.NumberColumn("D/E", format="%.2f", alignment="right"),
                "Current Ratio": st.column_config.NumberColumn("Cur Ratio", format="%.2f", alignment="right"),
                "Health":        st.column_config.TextColumn("Health (score · grade)"),
                "Analyst":       st.column_config.TextColumn("Analyst"),
                "Target":        st.column_config.TextColumn("Target", alignment="right"),
                "Ex-Div Date":   st.column_config.TextColumn("Ex-Div"),
            }

            row_h = 34 if density == "Compact" else 46
            selection = st.dataframe(
                df[visible_cols], hide_index=True, width="stretch",
                height=420, column_config=col_cfg, row_height=row_h,
                on_select="rerun", selection_mode="single-row", key="sc_table",
            )

            try:
                sel_rows = selection.selection["rows"] if hasattr(selection, "selection") else []
            except Exception:
                sel_rows = []
            if sel_rows:
                sel_idx = sel_rows[0]
                if st.session_state.get("sc_last_nav_idx") != (sel_idx, len(table_data)):
                    st.session_state["sc_last_nav_idx"] = (sel_idx, len(table_data))
                    sel_ticker = df.iloc[sel_idx]["Ticker"]
                    match = next(
                        (f"{row['name']}{_TICKER_SEP}{row['ticker']}" for row in get_company_directory() if row["ticker"] == sel_ticker),
                        sel_ticker,
                    )
                    st.session_state["ticker_search"] = match
                    _navigate("ticker")

            exp_col, _sp = st.columns([1.6, 8.4])
            with exp_col:
                csv = df[visible_cols].to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Export CSV", csv, "screener_results.csv", "text/csv",
                    key="sc_csv", icon=":material/download:",
                )

        # ── Dividend Calendar (yfinance data for screened stocks) ────────────
        upcoming = get_upcoming_dividends(filtered, days=90)

        finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        finnhub_enriched = {}
        if finnhub_key:
            us_tickers = tuple(
                d["ticker"] for d in filtered
                if not d["ticker"].endswith(".NS") and not d["ticker"].endswith(".BO")
            )
            if us_tickers:
                with st.spinner("Enriching US dividend dates via Finnhub…"):
                    finnhub_enriched = enrich_dividends_finnhub(finnhub_key, us_tickers)
                for item in upcoming:
                    tk = item["ticker"]
                    if tk in finnhub_enriched:
                        fh = finnhub_enriched[tk]
                        if fh.get("ex_div_date"):
                            item["ex_div_date"]   = fh["ex_div_date"]
                            item["pay_date"]      = fh.get("pay_date", item.get("pay_date", ""))
                            item["dividend_rate"] = fh.get("dividend_rate") or item.get("dividend_rate")
                            item["_source"]       = "Finnhub"

        nse_divs = []
        has_indian = any(d["ticker"].endswith(".NS") or d["ticker"].endswith(".BO") for d in filtered)
        if has_indian:
            with st.spinner("Fetching NSE dividend calendar…"):
                nse_divs = fetch_nse_dividend_calendar(days_ahead=90)

        if upcoming or nse_divs:
            st.markdown('<div class="section-head">Upcoming Dividend Calendar (next 90 days)</div>', unsafe_allow_html=True)

            if upcoming:
                st.markdown('<div style="font-size:0.85rem;color:var(--eiq-text-secondary);margin-bottom:8px;">US &amp; Global Stocks</div>', unsafe_allow_html=True)
                for d in upcoming:
                    days_left     = d["_days_until"]
                    urgency_color = "#E5484D" if days_left <= 7 else ("#B9791F" if days_left <= 21 else "#16A36A")
                    div_sym = currency_symbol(d.get("currency", "USD"))
                    dy_pct  = _fmt(d.get("dividend_yield"), ".2f", "%", 100) if d.get("dividend_yield") else "—"
                    dr      = f"{div_sym}{d['dividend_rate']:.2f}/yr" if d.get("dividend_rate") else "—"
                    pay_d   = d.get("pay_date") or "—"
                    src     = d.get("_source", "yfinance")

                    h  = '<div class="watchlist-card wl-normal" style="margin-bottom:10px;">'
                    h += '<div class="wl-row">'
                    h += '<div class="wl-left">'
                    h += f'<span class="wl-ticker">{d["ticker"]}</span>'
                    h += f'<div><span class="wl-company">{d["company"][:30]}</span>'
                    h += f' <span class="sc-exch-badge">via {src}</span></div>'
                    h += '</div>'
                    h += '<div class="wl-right" style="text-align:right;">'
                    h += f'<div class="wl-price">{dy_pct} yield · {dr}</div>'
                    h += f'<div class="wl-alert-price">Ex-Div: <b>{d["ex_div_date"]}</b> · Pay: {pay_d}</div>'
                    h += f'<div class="wl-status" style="color:{urgency_color};font-weight:600;">{days_left} days until ex-dividend</div>'
                    h += '</div></div></div>'
                    st.markdown(h, unsafe_allow_html=True)

            if nse_divs:
                st.markdown('<div style="font-size:0.85rem;color:var(--eiq-text-secondary);margin:16px 0 8px;">NSE India (via NSE Official API)</div>', unsafe_allow_html=True)
                today2 = _dt.date.today()
                for item in nse_divs[:20]:
                    ex_s = item.get("ex_div_date", "")
                    try:
                        ex_d   = _dt.date.fromisoformat(ex_s)
                        days_l = (ex_d - today2).days
                    except (ValueError, TypeError):
                        days_l = 0
                    urg_c = "#E5484D" if days_l <= 7 else ("#B9791F" if days_l <= 21 else "#16A36A")

                    h  = '<div class="watchlist-card wl-normal" style="margin-bottom:10px;">'
                    h += '<div class="wl-row">'
                    h += '<div class="wl-left">'
                    h += f'<span class="wl-ticker">{item["symbol"]}</span>'
                    h += f'<div><span class="wl-company">{item["company"][:30]}</span>'
                    h += ' <span class="sc-exch-badge">NSE India</span></div>'
                    h += '</div>'
                    h += '<div class="wl-right" style="text-align:right;">'
                    h += f'<div class="wl-price">{item.get("dividend_amount", "—")}</div>'
                    h += f'<div class="wl-alert-price">Ex-Div: <b>{ex_s}</b></div>'
                    h += f'<div class="wl-status" style="color:{urg_c};font-weight:600;">{days_l} days until ex-dividend</div>'
                    h += '</div></div></div>'
                    st.markdown(h, unsafe_allow_html=True)

        _render_trust_footer()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    st.session_state.setdefault("dark_mode", False)
    setup_page(dark_mode=st.session_state.dark_mode)

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
    elif page in ("news-radar", "market-pulse"):
        render_news_radar_page(api_key)
    else:
        render_home_page(api_key)


if __name__ == "__main__":
    main()
