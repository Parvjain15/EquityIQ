import streamlit as st


def setup_page():
    """Sets up the Streamlit page configuration and Groww-inspired light theme CSS."""
    st.set_page_config(
        page_title="EquityIQ — Smart Financial Intelligence",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        /* === HIDE SIDEBAR & DEFAULTS === */
        section[data-testid="stSidebar"] { display: none !important; }
        button[data-testid="stSidebarCollapsedControl"] { display: none !important; }
        #MainMenu { display: none !important; }
        footer { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        /* Remove default top padding that creates the blank gap */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }
        .stMainBlockContainer { padding-top: 0 !important; }
        .stApp > div:first-child { padding-top: 0 !important; }

        /* === GLOBAL === */
        .stApp {
            background: #ffffff;
            color: #44475b;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        h1, h2, h3, h4 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            color: #44475b !important;
        }

        /* === TOPBAR === */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 0;
            border-bottom: 1px solid #e8e8eb;
            margin-bottom: 0;
        }
        .topbar-left {
            display: flex;
            align-items: center;
            gap: 36px;
        }
        .topbar-logo {
            font-size: 1.45rem;
            font-weight: 800;
            color: #44475b;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .topbar-logo .logo-dot {
            width: 28px; height: 28px;
            background: #00d09c;
            border-radius: 50%;
            display: inline-block;
        }
        .topbar-logo span { color: #00d09c; }
        .topbar-nav {
            display: flex;
            gap: 28px;
            align-items: center;
        }
        .topbar-nav a {
            color: #44475b;
            text-decoration: none;
            font-size: 0.87rem;
            font-weight: 500;
            transition: color 0.18s;
        }
        .topbar-nav a:hover { color: #00d09c; }
        .topbar-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .topbar-search {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #f5f5f6;
            border: 1px solid #e8e8eb;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 0.82rem;
            color: #a0a2ab;
            min-width: 200px;
        }
        .topbar-search kbd {
            background: #e8e8eb;
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 0.7rem;
            color: #7c7e8c;
            margin-left: auto;
        }
        .topbar-cta {
            background: #00d09c;
            color: #fff !important;
            border-radius: 8px;
            padding: 9px 22px;
            font-size: 0.85rem;
            font-weight: 600;
            text-decoration: none;
            transition: background 0.2s;
            white-space: nowrap;
        }
        .topbar-cta:hover { background: #00b386; }
        .topbar-nav a.nav-active {
            color: #00d09c !important;
            border-bottom: 2px solid #00d09c;
            padding-bottom: 2px;
        }

        /* === PAGE HEADERS === */
        .page-title {
            font-size: 1.6rem;
            font-weight: 800;
            color: #1e293b;
            margin: 24px 0 4px 0;
            letter-spacing: -0.3px;
        }
        .page-sub {
            font-size: 0.9rem;
            color: #64748b;
            margin-bottom: 20px;
        }

        /* === TICKER STRIP === */
        .ticker-strip {
            display: flex;
            align-items: center;
            gap: 32px;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f2;
            font-size: 0.8rem;
            overflow-x: auto;
            white-space: nowrap;
            background: #fafbfc;
        }
        .ticker-strip::-webkit-scrollbar { display: none; }
        .ticker-item {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #44475b;
            font-weight: 500;
        }
        .ticker-item .t-name { color: #7c7e8c; font-weight: 400; }
        .ticker-item .t-price { font-family: 'JetBrains Mono', monospace; font-weight: 600; }
        .ticker-item .t-up { color: #00d09c; font-weight: 600; }
        .ticker-item .t-down { color: #eb5b3c; font-weight: 600; }

        /* === HERO === */
        .hero-section {
            text-align: center;
            padding: 56px 20px 36px;
        }
        .hero-title {
            font-size: 2.9rem;
            font-weight: 800;
            color: #44475b;
            letter-spacing: -1.2px;
            line-height: 1.15;
            margin-bottom: 14px;
        }
        .hero-title .accent { color: #00d09c; }
        .hero-sub {
            text-align: center;
            color: #7c7e8c;
            font-size: 1rem;
            font-weight: 400;
            margin-bottom: 28px;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
            line-height: 1.6;
        }
        .hero-cta {
            display: inline-block;
            background: #00d09c;
            color: #fff;
            border-radius: 8px;
            padding: 12px 32px;
            font-size: 0.92rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s;
        }
        .hero-cta:hover { background: #00b386; box-shadow: 0 4px 14px rgba(0,208,156,0.25); }

        /* === FEATURE CARDS === */
        .features-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            max-width: 900px;
            margin: 0 auto 44px;
            padding: 0 20px;
        }
        .feature-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            padding: 24px 20px;
            text-align: left;
            transition: all 0.2s ease;
            cursor: default;
        }
        .feature-card:hover {
            border-color: #c8c9cd;
            box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        }
        .feature-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-bottom: 12px;
        }
        .feature-dot.green { background: #00d09c; }
        .feature-dot.blue { background: #5367ff; }
        .feature-dot.purple { background: #9b59b6; }
        .feature-dot.orange { background: #f39c12; }
        .feature-name {
            font-size: 0.9rem;
            font-weight: 600;
            color: #44475b;
            margin-bottom: 6px;
        }
        .feature-desc {
            font-size: 0.77rem;
            color: #7c7e8c;
            line-height: 1.5;
        }

        /* === DIVIDER === */
        .section-divider {
            width: 48px; height: 3px;
            background: #00d09c;
            border-radius: 2px;
            margin: 0 auto 36px;
        }

        /* === TABS — Clean underline style === */
        .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            border-radius: 0;
            padding: 0;
            gap: 0;
            border: none;
            border-bottom: 1px solid #e8e8eb;
            justify-content: flex-start;
        }
        .stTabs [data-baseweb="tab"] {
            color: #7c7e8c;
            border-radius: 0;
            font-weight: 500;
            font-size: 0.88rem;
            padding: 12px 24px;
            transition: color 0.2s;
            border-bottom: 2px solid transparent;
            background: transparent !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #44475b;
            background: transparent !important;
        }
        .stTabs [aria-selected="true"] {
            background: transparent !important;
            color: #44475b !important;
            font-weight: 600;
            border-bottom: 2px solid #00d09c !important;
            box-shadow: none !important;
        }
        .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
        .stTabs [data-baseweb="tab-border"] { display: none; }

        /* === METRIC CARDS === */
        .metric-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            padding: 20px;
            transition: border-color 0.2s;
        }
        .metric-card:hover { border-color: #c8c9cd; }
        .metric-label {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #7c7e8c;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #44475b;
            font-family: 'JetBrains Mono', monospace;
        }
        .metric-delta { font-size: 0.78rem; color: #7c7e8c; margin-top: 4px; }

        /* === VALUATION CARDS === */
        .val-card {
            background: #f0fdf8;
            border: 1px solid #d1f5e8;
            border-radius: 12px;
            padding: 28px 24px;
            text-align: center;
            transition: border-color 0.2s;
        }
        .val-card:hover { border-color: #00d09c; }
        .val-label {
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #00b386;
        }
        .val-amount {
            font-size: 2rem;
            font-weight: 700;
            color: #44475b;
            font-family: 'JetBrains Mono', monospace;
            margin: 8px 0 6px;
        }
        .val-desc { font-size: 0.78rem; color: #7c7e8c; line-height: 1.4; }

        /* === INFO CARDS === */
        .info-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            padding: 22px;
            min-height: 160px;
        }
        .info-card-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #44475b;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #f0f0f2;
        }
        .info-card-body { color: #7c7e8c; font-size: 0.85rem; line-height: 1.7; }

        /* === COMPANY HEADER === */
        .company-header {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 0;
            flex-wrap: wrap;
        }
        .company-name { font-size: 1.6rem; font-weight: 700; color: #44475b; }
        .fy-badge {
            background: #00d09c;
            color: #ffffff;
            padding: 4px 14px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        /* === SECTION HEADERS === */
        .section-head {
            font-size: 1rem;
            font-weight: 600;
            color: #44475b;
            margin: 32px 0 16px;
            padding-bottom: 10px;
            border-bottom: 1px solid #f0f0f2;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-head::before {
            content: '';
            width: 3px; height: 18px;
            background: #00d09c;
            border-radius: 2px;
            display: inline-block;
        }

        /* === SUPPORTED DOCS === */
        .supported-docs {
            text-align: center;
            padding: 8px 0 4px;
            color: #7c7e8c;
            font-size: 0.78rem;
        }
        .supported-docs span {
            display: inline-block;
            background: #f5f5f6;
            border: 1px solid #e8e8eb;
            border-radius: 6px;
            padding: 3px 10px;
            margin: 2px 2px;
            font-size: 0.72rem;
            font-weight: 500;
            color: #44475b;
        }

        /* === TRUST FOOTER === */
        .trust-footer {
            text-align: center;
            padding: 36px 0 16px;
            margin-top: 40px;
            border-top: 1px solid #f0f0f2;
        }
        .trust-badges {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 14px;
            flex-wrap: wrap;
        }
        .trust-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #7c7e8c;
            font-size: 0.78rem;
            font-weight: 500;
        }
        .trust-badge .badge-icon { font-size: 0.9rem; }
        .trust-legal {
            color: #a0a2ab;
            font-size: 0.68rem;
            margin-top: 10px;
            line-height: 1.5;
        }

        /* === BUTTONS === */
        .stButton > button {
            background: #00d09c !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px;
            padding: 0.55rem 1.4rem;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.88rem;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background: #00b386 !important;
            box-shadow: 0 2px 10px rgba(0,208,156,0.2) !important;
        }

        /* === INPUTS === */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px;
            color: #44475b !important;
            font-family: 'Inter', sans-serif;
            font-size: 0.88rem;
        }
        .stTextInput > div > div > input:focus {
            border-color: #00d09c !important;
            box-shadow: 0 0 0 1px rgba(0,208,156,0.2) !important;
        }
        .stTextInput > div > div > input::placeholder { color: #a0a2ab !important; }

        /* === FILE UPLOADER === */
        .stFileUploader {
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px;
            padding: 20px;
            background: #fafbfc !important;
            transition: border-color 0.2s;
        }
        .stFileUploader:hover { border-color: #00d09c !important; }

        /* === DIVIDERS === */
        hr { border-color: #f0f0f2 !important; }

        /* === VERDICT CARD === */
        .verdict-card {
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            margin-top: 14px;
            transition: border-color 0.2s;
        }
        .verdict-buy { background: #f0fdf4; border: 1.5px solid #22c55e; }
        .verdict-sell { background: #fef2f2; border: 1.5px solid #ef4444; }
        .verdict-hold { background: #fffbeb; border: 1.5px solid #f59e0b; }
        .verdict-signal { font-size: 1.8rem; font-weight: 800; margin: 8px 0; }
        .verdict-signal.buy { color: #16a34a; }
        .verdict-signal.sell { color: #dc2626; }
        .verdict-signal.hold { color: #d97706; }
        .verdict-price {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.2rem; font-weight: 600; color: #44475b; margin: 6px 0;
        }
        .verdict-explain { font-size: 0.85rem; color: #7c7e8c; line-height: 1.6; margin-top: 8px; }

        /* === NEWS CARDS === */
        .news-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-left: 3px solid #00d09c;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 10px;
            transition: border-color 0.2s;
        }
        .news-card:hover { border-left-color: #00b386; }
        .news-title a {
            font-size: 0.9rem; font-weight: 600; color: #44475b; text-decoration: none;
        }
        .news-title a:hover { color: #00b386; }
        .news-meta { font-size: 0.73rem; color: #a0a2ab; margin-top: 5px; }
        .news-meta span { margin-right: 10px; }

        /* === SENTIMENT NEWS CARDS === */
        .sentiment-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 14px;
            transition: border-color 0.2s;
        }
        .sentiment-card:hover { border-color: #c8c9cd; }
        .sentiment-headline {
            font-size: 0.92rem; font-weight: 600; color: #44475b;
            margin-bottom: 8px; line-height: 1.4;
        }
        .sentiment-source { font-size: 0.72rem; color: #a0a2ab; margin-bottom: 12px; }
        .sentiment-stocks {
            display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;
        }
        .stock-tag {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 4px 12px; border-radius: 6px;
            font-size: 0.75rem; font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        .stock-tag.bullish { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
        .stock-tag.bearish { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
        .stock-tag.neutral { background: #f5f5f6; color: #7c7e8c; border: 1px solid #e8e8eb; }
        .sentiment-reason {
            font-size: 0.8rem; color: #7c7e8c; margin-top: 10px;
            line-height: 1.5; padding-top: 10px; border-top: 1px solid #f0f0f2;
        }
        .sentiment-badge {
            display: inline-block; padding: 3px 10px; border-radius: 4px;
            font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .sentiment-badge.positive { background: #f0fdf4; color: #16a34a; }
        .sentiment-badge.negative { background: #fef2f2; color: #dc2626; }
        .sentiment-badge.mixed { background: #fffbeb; color: #d97706; }

        /* === QUARTERLY CARDS === */
        .pros-card {
            background: #f0fdf4; border: 1px solid #bbf7d0;
            border-radius: 12px; padding: 24px 20px;
        }
        .cons-card {
            background: #fef2f2; border: 1px solid #fecaca;
            border-radius: 12px; padding: 24px 20px;
        }
        .trajectory-card {
            background: #f0fdf8; border: 1px solid #d1f5e8;
            border-radius: 12px; padding: 24px 20px;
        }
        .pc-card-title {
            font-size: 0.95rem; font-weight: 700;
            margin-bottom: 12px; padding-bottom: 8px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .pc-card-title.pros { color: #16a34a; }
        .pc-card-title.cons { color: #dc2626; }
        .pc-card-title.trajectory { color: #00b386; }
        .pc-bullet { font-size: 0.85rem; color: #5c5e6e; line-height: 1.8; }
        .quarter-badge {
            display: inline-block; background: #00d09c; color: #fff;
            padding: 3px 12px; border-radius: 6px;
            font-size: 0.73rem; font-weight: 600; margin: 0 3px 5px 0;
        }

        /* === TOOLTIP === */
        .info-tooltip {
            display: inline-block; position: relative; cursor: pointer;
            color: #00b386; font-size: 0.82rem; margin-left: 4px; vertical-align: middle;
        }
        .info-tooltip .info-tooltip-text {
            visibility: hidden; opacity: 0; position: absolute; bottom: 130%; left: 50%;
            transform: translateX(-50%); background-color: #44475b; color: #f5f7fa;
            padding: 10px 14px; border-radius: 8px; font-size: 0.75rem; font-weight: 400;
            line-height: 1.5; width: 240px; text-align: left; text-transform: none;
            letter-spacing: normal; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            transition: opacity 0.2s ease; z-index: 100;
        }
        .info-tooltip .info-tooltip-text::after {
            content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px;
            border-width: 5px; border-style: solid;
            border-color: #44475b transparent transparent transparent;
        }
        .info-tooltip:hover .info-tooltip-text { visibility: visible; opacity: 1; }

        /* === PROGRESS BAR === */
        .stProgress > div > div > div > div { background: #00d09c !important; }

        /* === DATAFRAME === */
        .stDataFrame { border-radius: 10px; overflow: hidden; }

        /* === HEALTH SCORE WIDGET === */
        .health-score-widget {
            text-align: center;
            padding: 24px 16px;
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            height: 100%;
        }
        .health-score-number {
            font-size: 3.8rem;
            font-weight: 800;
            line-height: 1;
            font-family: 'JetBrains Mono', monospace;
        }
        .health-score-grade {
            display: inline-block;
            color: #fff;
            font-size: 1.3rem;
            font-weight: 800;
            padding: 4px 20px;
            border-radius: 8px;
            margin: 10px 0 8px;
        }
        .health-score-label {
            font-size: 0.72rem;
            color: #7c7e8c;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .health-breakdown {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-content: flex-start;
            padding: 8px 0;
        }
        .health-pill {
            border: 1px solid;
            border-radius: 8px;
            padding: 8px 14px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 110px;
        }
        .hp-name { font-size: 0.66rem; font-weight: 600; color: #7c7e8c; text-transform: uppercase; letter-spacing: 0.5px; }
        .hp-value { font-size: 0.88rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .hp-pts { font-size: 0.63rem; color: #94a3b8; }

        /* === INVESTMENT MEMO === */
        .memo-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            padding: 28px;
            margin-top: 8px;
        }
        .memo-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f0f0f2;
        }
        .memo-title { font-size: 1rem; font-weight: 700; color: #44475b; }
        .memo-badge {
            background: #f0fdf8;
            color: #00b386;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 4px;
            border: 1px solid #d1f5e8;
        }
        .memo-body { font-size: 0.85rem; color: #5c5e6e; line-height: 1.75; }
        .memo-section-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: #44475b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 14px;
            margin-bottom: 4px;
        }
        .memo-line { margin-bottom: 2px; }

        /* === WATCHLIST === */
        .watchlist-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            padding: 16px 22px;
            margin-bottom: 10px;
            transition: border-color 0.2s;
        }
        .watchlist-card.wl-alert {
            border-color: #22c55e;
            background: #f0fdf4;
        }
        .watchlist-card.wl-normal:hover { border-color: #c8c9cd; }
        .wl-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }
        .wl-left { display: flex; align-items: center; gap: 14px; }
        .wl-ticker {
            font-size: 1.15rem;
            font-weight: 700;
            color: #44475b;
            font-family: 'JetBrains Mono', monospace;
        }
        .wl-company { font-size: 0.8rem; color: #7c7e8c; }
        .wl-note { font-size: 0.75rem; color: #a0a2ab; font-style: italic; margin-left: 6px; }
        .wl-right { text-align: right; }
        .wl-price {
            font-size: 1.25rem;
            font-weight: 700;
            color: #44475b;
            font-family: 'JetBrains Mono', monospace;
        }
        .wl-alert-price { font-size: 0.73rem; color: #7c7e8c; margin-top: 2px; }
        .wl-status { font-size: 0.73rem; margin-top: 4px; font-weight: 500; }
        .alert-banner {
            background: #f0fdf4;
            border: 1px solid #22c55e;
            border-radius: 10px;
            padding: 14px 20px;
            font-size: 0.88rem;
            color: #16a34a;
            margin: 12px 0 16px;
        }

        /* === NEWS RADAR CARDS === */
        .nr-card {
            background: #ffffff;
            border: 1px solid #e8e8eb;
            border-radius: 12px;
            padding: 20px 22px;
            margin-bottom: 14px;
            transition: border-color 0.2s;
        }
        .nr-card:hover { border-color: #c8c9cd; }
        .nr-card-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 8px;
        }
        .nr-badges { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
        .nr-sentiment-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .nr-urgency-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.65rem;
            font-weight: 600;
        }
        .nr-category-tag {
            display: inline-block;
            background: #f0f4ff;
            color: #5367ff;
            border: 1px solid #dbe4ff;
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.65rem;
            font-weight: 600;
        }
        .nr-meta-tag {
            display: inline-block;
            background: #f5f5f6;
            color: #7c7e8c;
            border: 1px solid #e8e8eb;
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.65rem;
            font-weight: 500;
        }
        .nr-source { font-size: 0.72rem; color: #a0a2ab; white-space: nowrap; }
        .nr-headline { font-size: 0.92rem; font-weight: 700; color: #44475b; margin: 8px 0 6px; line-height: 1.4; }
        .nr-headline a { color: #44475b; text-decoration: none; }
        .nr-headline a:hover { color: #00b386; }
        .nr-summary { font-size: 0.82rem; color: #5c5e6e; line-height: 1.6; margin-bottom: 8px; }
        .nr-reason {
            font-size: 0.8rem;
            color: #64748b;
            line-height: 1.5;
            padding: 10px 14px;
            background: #fafbfc;
            border-left: 3px solid #e8e8eb;
            border-radius: 0 6px 6px 0;
            margin: 8px 0;
        }
        .nr-impact {
            font-size: 0.8rem;
            color: #64748b;
            line-height: 1.5;
            padding: 10px 14px;
            background: #fff8f0;
            border-left: 3px solid #fed7aa;
            border-radius: 0 6px 6px 0;
            margin: 8px 0;
        }
        .nr-tickers { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
        .nr-ticker-tag {
            display: inline-block;
            background: #f0f4ff;
            color: #5367ff;
            border: 1px solid #dbe4ff;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.73rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        .nr-read-more {
            margin-top: 12px;
            font-size: 0.75rem;
        }
        .nr-read-more a { color: #00b386; text-decoration: none; font-weight: 600; }
        .nr-read-more a:hover { color: #00d09c; }

        /* === NEWS RADAR SUMMARY PANEL === */
        .nr-summary-card {
            background: #ffffff;
            border: 2px solid;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .nr-summary-label {
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #7c7e8c;
            margin-bottom: 8px;
        }
        .nr-summary-value {
            font-size: 1.8rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }
        .nr-ai-summary {
            background: #f0fdf8;
            border: 1px solid #d1f5e8;
            border-radius: 12px;
            padding: 20px 24px;
            margin: 16px 0 8px;
        }
        .nr-ai-summary-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: #00b386;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .nr-ai-summary-text {
            font-size: 0.88rem;
            color: #44475b;
            line-height: 1.7;
        }

        @media (max-width: 768px) {
            .features-row { grid-template-columns: repeat(2, 1fr); }
            .hero-title { font-size: 2rem; }
            .topbar-search { display: none; }
            .topbar-nav { gap: 16px; }
            .ticker-strip { gap: 20px; }
            .health-breakdown { gap: 6px; }
            .health-pill { min-width: 90px; }
        }
        </style>
    """, unsafe_allow_html=True)


def format_number(num):
    """Formats large numbers into readable strings."""
    if num is None:
        return "N/A"
    try:
        num = float(num)
    except (ValueError, TypeError):
        return str(num)
    if abs(num) >= 1e12:
        return f"${num / 1e12:.2f}T"
    if abs(num) >= 1e9:
        return f"${num / 1e9:.2f}B"
    if abs(num) >= 1e6:
        return f"${num / 1e6:.2f}M"
    if abs(num) >= 1e3:
        return f"${num / 1e3:.1f}K"
    return f"${num:.2f}"


def create_metric_card(label, value, delta=None):
    """Creates a metric card."""
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def create_valuation_card(label, amount, description, tooltip=None):
    """Creates a valuation card with optional info tooltip."""
    tooltip_html = ""
    if tooltip:
        tooltip_html = f'''
        <span class="info-tooltip">ⓘ
            <span class="info-tooltip-text">{tooltip}</span>
        </span>'''
    st.markdown(f"""
    <div class="val-card">
        <div class="val-label">{label} {tooltip_html}</div>
        <div class="val-amount">{amount}</div>
        <div class="val-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def create_info_card(title, content, icon=""):
    """Creates an info card for risks/notes."""
    st.markdown(f"""
    <div class="info-card">
        <div class="info-card-title">{icon} {title}</div>
        <div class="info-card-body">{content}</div>
    </div>
    """, unsafe_allow_html=True)
