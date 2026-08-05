import streamlit as st


# ── Design tokens: one CSS custom-property set per theme. setup_page() picks
#    the active set with a plain Python conditional and concatenates it into
#    the (much larger, non-f-string) stylesheet below — every component that
#    already reads var(--eiq-*) repaints automatically, no per-component
#    dark-mode CSS needed. ─────────────────────────────────────────────────
_LIGHT_TOKENS = """
        :root {
            --eiq-bg: #FFFFFF;
            --eiq-bg-alt: #F7F9FB;
            --eiq-surface: #FFFFFF;
            --eiq-text: #111318;
            --eiq-text-secondary: #6F7580;
            --eiq-border: #E5E8EC;
            --eiq-blue: #08A6DC;
            --eiq-blue-hover: #008CC0;
            --eiq-blue-pale: #E6F7FC;
            --eiq-blue-pale-border: #CDEFFA;
            --eiq-positive: #16A36A;
            --eiq-negative: #E5484D;
            --eiq-warning: #F2A93B;
            --eiq-warning-text: #B9791F;
            --eiq-positive-bg: rgba(22,163,106,0.08);
            --eiq-positive-border: rgba(22,163,106,0.30);
            --eiq-negative-bg: rgba(229,72,77,0.08);
            --eiq-negative-border: rgba(229,72,77,0.30);
            --eiq-warning-bg: rgba(242,169,59,0.12);
            --eiq-warning-border: rgba(242,169,59,0.35);
            --eiq-radius: 16px;
            --eiq-shadow: 0 1px 2px rgba(17,19,24,0.04), 0 8px 24px rgba(17,19,24,0.05);
            --eiq-bg-translucent: rgba(255,255,255,0.92);
        }
"""

_DARK_TOKENS = """
        :root {
            --eiq-bg: #0A0C10;
            --eiq-bg-alt: #12151B;
            --eiq-surface: #171B22;
            --eiq-text: #F2F4F7;
            --eiq-text-secondary: #9BA3AF;
            --eiq-border: #262B34;
            --eiq-blue: #1CB6E8;
            --eiq-blue-hover: #4FC9F0;
            --eiq-blue-pale: rgba(28,182,232,0.14);
            --eiq-blue-pale-border: rgba(28,182,232,0.30);
            --eiq-positive: #22C58A;
            --eiq-negative: #F2666B;
            --eiq-warning: #F5BB55;
            --eiq-warning-text: #F5BB55;
            --eiq-positive-bg: rgba(34,197,138,0.14);
            --eiq-positive-border: rgba(34,197,138,0.35);
            --eiq-negative-bg: rgba(242,102,107,0.14);
            --eiq-negative-border: rgba(242,102,107,0.35);
            --eiq-warning-bg: rgba(245,187,85,0.14);
            --eiq-warning-border: rgba(245,187,85,0.35);
            --eiq-radius: 16px;
            --eiq-shadow: 0 1px 2px rgba(0,0,0,0.35), 0 8px 24px rgba(0,0,0,0.45);
            --eiq-bg-translucent: rgba(10,12,16,0.92);
        }
"""


def setup_page(dark_mode: bool = False):
    """Sets up the Streamlit page configuration and the EquityIQ theme CSS."""
    st.set_page_config(
        page_title="EquityIQ — Smart Financial Intelligence",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    tokens = _DARK_TOKENS if dark_mode else _LIGHT_TOKENS

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
        """ + tokens + """

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
            background: var(--eiq-bg);
            color: var(--eiq-text);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        h1, h2, h3, h4 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            color: var(--eiq-text) !important;
        }
        .eiq-tabular { font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
        :focus-visible {
            outline: 2px solid var(--eiq-blue) !important;
            outline-offset: 2px !important;
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.001ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.001ms !important;
                scroll-behavior: auto !important;
            }
        }

        @keyframes eiqFadeUp {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes eiqFadeIn {
            from { opacity: 0; }
            to   { opacity: 1; }
        }
        .eiq-animate-in {
            animation: eiqFadeUp 0.6s cubic-bezier(0.16,1,0.3,1) both;
        }

        /* === TOPBAR (built from st.button widgets — real Streamlit reruns instead
               of full-page <a href> navigation, so switching tabs no longer causes
               a full browser reload / blank-page flash) === */
        .st-key-topbar {
            position: sticky;
            top: 0;
            z-index: 999;
            background: var(--eiq-bg-translucent);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--eiq-border);
            padding: 10px 0;
            margin-bottom: 0;
            min-height: 72px;
            display: flex;
            align-items: center;
        }
        .st-key-topbar > div { width: 100%; }
        .st-key-topbar div[data-testid="stVerticalBlock"] { gap: 0 !important; }
        .st-key-topbar div[data-testid="stHorizontalBlock"] { align-items: center; gap: 8px; }
        .st-key-topbar div[data-testid="stElementContainer"] { margin: 0 !important; }
        /* Selectors use ".stButton > button" (not just "button") so specificity beats
           the global ".stButton > button" pill-button rule below, regardless of source order. */
        .st-key-topbar .stButton > button {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 8px 4px !important;
            white-space: nowrap;
            min-height: auto !important;
        }

        /* Brand / logo button */
        .st-key-topbar_logo .stButton > button {
            font-size: 1.2rem !important;
            font-weight: 800 !important;
            color: var(--eiq-text) !important;
            letter-spacing: -0.5px;
            justify-content: flex-start !important;
        }

        /* Nav item buttons (desktop) */
        .st-key-topbar_nav { display: block; }
        .st-key-topbar_nav .stButton > button {
            color: var(--eiq-text) !important;
            font-size: 0.87rem !important;
            font-weight: 500 !important;
            transition: color 0.18s;
            justify-content: center !important;
        }
        .st-key-topbar_nav .stButton > button:hover { color: var(--eiq-blue) !important; }
        .st-key-topbar_nav .stButton > button[kind="primary"] {
            color: var(--eiq-blue) !important;
            border-bottom: 2px solid var(--eiq-blue) !important;
            border-radius: 0 !important;
        }

        /* "Log in" secondary text button (top-right) */
        .st-key-topbar_login .stButton > button {
            color: var(--eiq-text) !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
        }
        .st-key-topbar_login .stButton > button:hover { color: var(--eiq-blue) !important; }

        /* "Get Started" CTA pill (top-right) */
        .st-key-topbar_cta .stButton > button {
            background: var(--eiq-blue) !important;
            color: #fff !important;
            border-radius: 12px !important;
            padding: 12px 26px !important;
            height: 46px !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            transition: background 0.2s;
        }
        .st-key-topbar_cta .stButton > button:hover { background: var(--eiq-blue-hover) !important; color: #fff !important; }

        /* Light/dark theme toggle */
        .st-key-topbar_theme .stButton > button {
            border: 1px solid var(--eiq-border) !important;
            background: var(--eiq-surface) !important;
            border-radius: 10px !important;
            padding: 8px 10px !important;
            font-size: 1rem !important;
            line-height: 1 !important;
        }
        .st-key-topbar_theme .stButton > button:hover { border-color: var(--eiq-blue) !important; }

        /* Mobile hamburger (st.popover) — hidden on desktop, shown under 900px */
        .st-key-topbar_hamburger { display: none; }
        .st-key-topbar_hamburger button[data-testid="stPopoverButton"] {
            border: 1px solid var(--eiq-border) !important;
            background: var(--eiq-surface) !important;
            border-radius: 10px !important;
            padding: 8px 12px !important;
            font-size: 1.1rem !important;
            color: var(--eiq-text) !important;
        }
        .st-key-topbar_mobilemenu .stButton > button {
            width: 100%;
            justify-content: flex-start !important;
            background: transparent !important;
            border: none !important;
            color: var(--eiq-text) !important;
            font-weight: 500 !important;
            padding: 10px 6px !important;
        }
        .st-key-topbar_mobilemenu .stButton > button[kind="primary"] { color: var(--eiq-blue) !important; }

        /* === PAGE HEADERS === */
        .page-title {
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--eiq-text);
            margin: 24px 0 4px 0;
            letter-spacing: -0.3px;
        }
        .page-sub {
            font-size: 0.9rem;
            color: var(--eiq-text-secondary);
            margin-bottom: 20px;
        }

        /* === TICKER STRIP === */
        .ticker-strip {
            display: flex;
            align-items: center;
            gap: 28px;
            padding: 7px 4px;
            border-bottom: 1px solid var(--eiq-border);
            font-size: 0.76rem;
            overflow-x: auto;
            white-space: nowrap;
            background: var(--eiq-bg-alt);
        }
        .ticker-strip::-webkit-scrollbar { display: none; }
        .ticker-item {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: var(--eiq-text);
            font-weight: 500;
            animation: eiqFadeIn 0.5s ease both;
        }
        .ticker-item .t-name { color: var(--eiq-text-secondary); font-weight: 400; }
        .ticker-item .t-price { font-family: 'JetBrains Mono', monospace; font-weight: 600; font-variant-numeric: tabular-nums; }
        .ticker-item .t-up { color: var(--eiq-positive); font-weight: 600; }
        .ticker-item .t-down { color: var(--eiq-negative); font-weight: 600; }

        /* === HERO (two-column, built with st.columns so the primary CTA can be a
               real st.button — see the "switching tabs" fix note on the topbar) === */
        .st-key-hero_wrap {
            padding: 48px 20px 40px;
            max-width: 1280px;
            margin: 0 auto;
        }
        .st-key-hero_wrap div[data-testid="stHorizontalBlock"] { align-items: center; }
        .btn-secondary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            height: 48px;
            padding: 0 28px;
            border-radius: 12px;
            background: var(--eiq-surface);
            color: var(--eiq-text);
            border: 1px solid var(--eiq-border);
            font-weight: 600;
            font-size: 0.94rem;
            text-decoration: none;
            transition: all 0.2s;
            white-space: nowrap;
        }
        .btn-secondary:hover {
            background: var(--eiq-blue-pale);
            border-color: var(--eiq-blue);
            color: var(--eiq-blue-hover);
        }
        .hero-label {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--eiq-blue-pale);
            color: var(--eiq-blue-hover);
            font-size: 0.76rem;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 20px;
            margin-bottom: 18px;
            animation: eiqFadeUp 0.5s ease both;
        }
        .hero-title-v2 {
            font-size: clamp(2rem, 3.4vw, 3.1rem);
            font-weight: 800;
            color: var(--eiq-text);
            letter-spacing: -1.2px;
            line-height: 1.12;
            margin-bottom: 18px;
            animation: eiqFadeUp 0.6s 0.05s ease both;
        }
        .hero-title-v2 .accent { color: var(--eiq-blue); }
        .hero-sub-v2 {
            color: var(--eiq-text-secondary);
            font-size: 1.05rem;
            font-weight: 400;
            margin-bottom: 30px;
            max-width: 480px;
            line-height: 1.65;
            animation: eiqFadeUp 0.6s 0.1s ease both;
        }
        .hero-cta-row { display: flex; gap: 12px; flex-wrap: wrap; animation: eiqFadeUp 0.6s 0.15s ease both; }
        .st-key-hero_cta_primary .stButton > button {
            background: var(--eiq-blue) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            height: 48px !important;
            padding: 0 28px !important;
            font-size: 0.94rem !important;
            font-weight: 600 !important;
            transition: all 0.2s;
        }
        .st-key-hero_cta_primary .stButton > button:hover {
            background: var(--eiq-blue-hover) !important;
            color: #fff !important;
            box-shadow: 0 4px 14px rgba(8,166,220,0.25);
        }
        .st-key-hero_cta_secondary .stButton > button {
            background: var(--eiq-surface) !important;
            color: var(--eiq-text) !important;
            border: 1px solid var(--eiq-border) !important;
            border-radius: 12px !important;
            height: 48px !important;
            padding: 0 28px !important;
            font-size: 0.94rem !important;
            font-weight: 600 !important;
            transition: all 0.2s;
        }
        .st-key-hero_cta_secondary .stButton > button:hover {
            background: var(--eiq-blue-pale) !important;
            border-color: var(--eiq-blue) !important;
            color: var(--eiq-blue-hover) !important;
        }
        .hero-trust {
            margin-top: 18px;
            font-size: 0.8rem;
            color: var(--eiq-text-secondary);
            animation: eiqFadeUp 0.6s 0.2s ease both;
        }

        /* === PRODUCT DEMO MOCKUP (right column of hero) === */
        .hero-visual {
            position: relative;
            display: flex;
            align-items: center;
            gap: 14px;
            animation: eiqFadeIn 0.7s 0.1s ease both;
        }
        .eiq-steps {
            display: flex;
            flex-direction: column;
            gap: 22px;
            flex-shrink: 0;
        }
        .eiq-step-dot {
            width: 10px; height: 10px;
            border-radius: 50%;
            background: var(--eiq-border);
            transition: background 0.4s;
        }
        .eiq-step-dot.active { background: var(--eiq-blue); box-shadow: 0 0 0 4px var(--eiq-blue-pale); }
        .eiq-step-caption {
            font-size: 0.68rem;
            color: var(--eiq-text-secondary);
            max-width: 68px;
            line-height: 1.3;
            transition: color 0.4s, font-weight 0.4s;
        }
        .eiq-step-caption.active { color: var(--eiq-blue-hover); font-weight: 700; }
        .device-frame {
            flex: 1;
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 18px;
            box-shadow: var(--eiq-shadow);
            overflow: hidden;
            position: relative;
        }
        .device-frame-bar {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 12px 16px;
            border-bottom: 1px solid var(--eiq-border);
            background: var(--eiq-bg-alt);
        }
        .device-frame-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--eiq-border); }
        .device-frame-url {
            margin-left: 10px;
            font-size: 0.7rem;
            color: var(--eiq-text-secondary);
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 6px;
            padding: 3px 10px;
            flex: 1;
        }

        /* === FLOATING CARDS === */
        .eiq-float-card {
            position: absolute;
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            box-shadow: var(--eiq-shadow);
            padding: 10px 14px;
            font-size: 0.76rem;
            display: flex;
            align-items: center;
            gap: 8px;
            opacity: 0;
            animation: eiqFadeUp 0.6s ease forwards;
        }
        .eiq-float-card .fc-dot { width: 8px; height: 8px; border-radius: 50%; }
        .eiq-float-card .fc-label { color: var(--eiq-text-secondary); }
        .eiq-float-card .fc-value { font-weight: 700; color: var(--eiq-text); font-variant-numeric: tabular-nums; }

        /* === FEATURE STORY SECTIONS (alternating 50/50) ===
           Background lives on the full-width outer wrapper, not .story-section itself,
           so shaded sections span edge-to-edge instead of just the 1200px content column. */
        .story-section-outer.story-shaded { background: var(--eiq-bg-alt); }
        .story-section {
            max-width: 1200px;
            margin: 0 auto;
            padding: 64px 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 64px;
            align-items: center;
        }
        .story-section.alt { direction: rtl; }
        .story-section.alt > * { direction: ltr; }
        .story-eyebrow {
            display: inline-block;
            color: var(--eiq-blue-hover);
            background: var(--eiq-blue-pale);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.4px;
            padding: 5px 12px;
            border-radius: 16px;
            margin-bottom: 14px;
        }
        .story-title {
            font-size: 1.9rem;
            font-weight: 800;
            color: var(--eiq-text);
            letter-spacing: -0.6px;
            line-height: 1.2;
            margin-bottom: 12px;
        }
        .story-desc {
            font-size: 0.98rem;
            color: var(--eiq-text-secondary);
            line-height: 1.7;
            max-width: 440px;
        }
        .story-preview {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: var(--eiq-radius);
            box-shadow: var(--eiq-shadow);
            padding: 24px;
        }

        /* --- mini preview: upload/extraction --- */
        .mp-file-chip {
            display: inline-flex; align-items: center; gap: 8px;
            background: var(--eiq-bg-alt); border: 1px solid var(--eiq-border);
            border-radius: 10px; padding: 8px 14px; font-size: 0.8rem;
            font-weight: 600; color: var(--eiq-text); margin-bottom: 16px;
        }
        .mp-progress-track {
            width: 100%; height: 8px; border-radius: 8px;
            background: var(--eiq-border); overflow: hidden; margin-bottom: 18px;
        }
        .mp-progress-fill {
            height: 100%; border-radius: 8px; background: var(--eiq-blue);
            width: 78%; animation: mpProgress 3.2s ease-in-out infinite;
        }
        @keyframes mpProgress { 0% { width: 6%; } 55% { width: 92%; } 100% { width: 92%; } }
        .mp-figure-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 9px 0; border-bottom: 1px solid var(--eiq-border);
            font-size: 0.83rem; opacity: 0; animation: eiqFadeUp 0.5s ease forwards;
        }
        .mp-figure-row:last-child { border-bottom: none; }
        .mp-figure-row .mp-fig-label { color: var(--eiq-text-secondary); }
        .mp-figure-row .mp-fig-value { font-weight: 700; color: var(--eiq-text); font-family: 'JetBrains Mono', monospace; }

        /* --- mini preview: health score ring --- */
        @property --eiq-ring-pct { syntax: '<number>'; inherits: true; initial-value: 0; }
        .mp-ring-wrap { display: flex; align-items: center; gap: 24px; margin-bottom: 18px; }
        .mp-ring {
            --eiq-ring-pct: 84;
            width: 108px; height: 108px; border-radius: 50%; flex-shrink: 0;
            background: conic-gradient(var(--eiq-positive) calc(var(--eiq-ring-pct) * 1%), var(--eiq-border) 0);
            display: flex; align-items: center; justify-content: center;
            animation: mpRingSweep 3.4s ease-in-out infinite;
        }
        @keyframes mpRingSweep { 0% { --eiq-ring-pct: 0; } 50% { --eiq-ring-pct: 84; } 100% { --eiq-ring-pct: 84; } }
        .mp-ring-inner {
            width: 82px; height: 82px; border-radius: 50%; background: var(--eiq-surface);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.7rem; font-weight: 800; color: var(--eiq-positive);
        }
        .mp-bar-row { margin-bottom: 10px; }
        .mp-bar-label {
            display: flex; justify-content: space-between; font-size: 0.74rem;
            color: var(--eiq-text-secondary); margin-bottom: 4px;
        }
        .mp-bar-track { height: 6px; border-radius: 6px; background: var(--eiq-border); overflow: hidden; }
        .mp-bar-fill { height: 100%; border-radius: 6px; background: var(--eiq-positive); }

        /* --- mini preview: memo assembly --- */
        .mp-memo-line {
            font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.5px; color: var(--eiq-blue-hover); margin: 14px 0 4px;
            opacity: 0; animation: eiqFadeUp 0.5s ease forwards;
        }
        .mp-memo-line:first-child { margin-top: 0; }
        .mp-memo-text {
            font-size: 0.85rem; color: var(--eiq-text-secondary); line-height: 1.6;
            opacity: 0; animation: eiqFadeUp 0.5s ease forwards;
        }

        /* --- mini preview: news radar feed --- */
        .mp-news-row {
            display: flex; align-items: center; gap: 10px; padding: 10px 0;
            border-bottom: 1px solid var(--eiq-border);
            opacity: 0; animation: eiqFadeUp 0.5s ease forwards;
        }
        .mp-news-row:last-child { border-bottom: none; }
        .mp-news-pill {
            font-size: 0.65rem; font-weight: 700; padding: 3px 9px; border-radius: 12px;
            white-space: nowrap; text-transform: uppercase; letter-spacing: 0.3px;
        }
        .mp-news-pill.pos { background: var(--eiq-positive-bg); color: var(--eiq-positive); }
        .mp-news-pill.neg { background: var(--eiq-negative-bg); color: var(--eiq-negative); }
        .mp-news-pill.warn { background: var(--eiq-warning-bg); color: var(--eiq-warning-text); }
        .mp-news-headline { font-size: 0.82rem; color: var(--eiq-text); flex: 1; }

        @media (prefers-reduced-motion: reduce) {
            .mp-progress-fill { animation: none; width: 92%; }
            .mp-ring { animation: none; --eiq-ring-pct: 84; }
            .mp-figure-row, .mp-memo-line, .mp-memo-text, .mp-news-row { animation: none; opacity: 1; }
        }

        /* === TABS — Clean underline style === */
        .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            border-radius: 0;
            padding: 0;
            gap: 0;
            border: none;
            border-bottom: 1px solid var(--eiq-border);
            justify-content: flex-start;
        }
        .stTabs [data-baseweb="tab"] {
            color: var(--eiq-text-secondary);
            border-radius: 0;
            font-weight: 500;
            font-size: 0.88rem;
            padding: 12px 24px;
            transition: color 0.2s;
            border-bottom: 2px solid transparent;
            background: transparent !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: var(--eiq-text);
            background: transparent !important;
        }
        .stTabs [aria-selected="true"] {
            background: transparent !important;
            color: var(--eiq-text) !important;
            font-weight: 600;
            border-bottom: 2px solid var(--eiq-blue) !important;
            box-shadow: none !important;
        }
        .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
        .stTabs [data-baseweb="tab-border"] { display: none; }

        /* === METRIC CARDS === */
        .metric-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            padding: 20px;
            transition: border-color 0.2s, transform 0.2s;
        }
        .metric-card:hover { border-color: var(--eiq-blue); transform: translateY(-2px); }
        .metric-label {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--eiq-text-secondary);
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--eiq-text);
            font-family: 'JetBrains Mono', monospace;
        }
        .metric-delta { font-size: 0.78rem; color: var(--eiq-text-secondary); margin-top: 4px; }

        /* === VALUATION CARDS === */
        .val-card {
            background: var(--eiq-blue-pale);
            border: 1px solid var(--eiq-blue-pale-border);
            border-radius: 14px;
            padding: 28px 24px;
            text-align: center;
            transition: border-color 0.2s;
        }
        .val-card:hover { border-color: var(--eiq-blue); }
        .val-label {
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--eiq-blue-hover);
        }
        .val-amount {
            font-size: 2rem;
            font-weight: 700;
            color: var(--eiq-text);
            font-family: 'JetBrains Mono', monospace;
            margin: 8px 0 6px;
        }
        .val-desc { font-size: 0.78rem; color: var(--eiq-text-secondary); line-height: 1.4; }

        /* === INFO CARDS === */
        .info-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            padding: 22px;
            min-height: 160px;
        }
        .info-card-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--eiq-text);
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--eiq-border);
        }
        .info-card-body { color: var(--eiq-text-secondary); font-size: 0.85rem; line-height: 1.7; }

        /* === COMPANY HEADER === */
        .company-header {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 0;
            flex-wrap: wrap;
        }
        .company-name { font-size: 1.6rem; font-weight: 700; color: var(--eiq-text); }
        .fy-badge {
            background: var(--eiq-blue);
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
            color: var(--eiq-text);
            margin: 32px 0 16px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--eiq-border);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-head::before {
            content: '';
            width: 3px; height: 18px;
            background: var(--eiq-blue);
            border-radius: 2px;
            display: inline-block;
        }

        /* === SUPPORTED DOCS === */
        .supported-docs {
            text-align: center;
            padding: 8px 0 4px;
            color: var(--eiq-text-secondary);
            font-size: 0.78rem;
        }
        .supported-docs span {
            display: inline-block;
            background: var(--eiq-bg-alt);
            border: 1px solid var(--eiq-border);
            border-radius: 6px;
            padding: 3px 10px;
            margin: 2px 2px;
            font-size: 0.72rem;
            font-weight: 500;
            color: var(--eiq-text);
        }

        /* === TRUST FOOTER === */
        .trust-footer {
            text-align: center;
            padding: 36px 0 16px;
            margin-top: 40px;
            border-top: 1px solid var(--eiq-border);
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
            color: var(--eiq-text-secondary);
            font-size: 0.78rem;
            font-weight: 500;
        }
        .trust-badge .badge-icon { font-size: 0.9rem; }
        .trust-legal {
            color: var(--eiq-text-secondary);
            font-size: 0.68rem;
            margin-top: 10px;
            line-height: 1.5;
        }

        /* === BUTTONS (base) === */
        .stButton > button {
            background: var(--eiq-blue) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px;
            height: 46px;
            padding: 0 26px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.88rem;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background: var(--eiq-blue-hover) !important;
            box-shadow: 0 2px 10px rgba(8,166,220,0.2) !important;
        }
        .stButton > button:active { transform: translateY(1px); }

        /* === INPUTS === */
        .stTextInput > div > div > input {
            background-color: var(--eiq-surface) !important;
            border: 1px solid var(--eiq-border) !important;
            border-radius: 10px;
            color: var(--eiq-text) !important;
            font-family: 'Inter', sans-serif;
            font-size: 0.88rem;
        }
        .stTextInput > div > div > input:focus {
            border-color: var(--eiq-blue) !important;
            box-shadow: 0 0 0 1px rgba(8,166,220,0.25) !important;
        }
        .stTextInput > div > div > input::placeholder { color: var(--eiq-text-secondary) !important; }

        /* === FILE UPLOADER === */
        .stFileUploader {
            border: 1px solid var(--eiq-border) !important;
            border-radius: 14px;
            padding: 20px;
            background: var(--eiq-bg-alt) !important;
            transition: border-color 0.2s;
        }
        .stFileUploader:hover { border-color: var(--eiq-blue) !important; }

        /* === DIVIDERS === */
        hr { border-color: var(--eiq-border) !important; }

        /* === VERDICT CARD === */
        .verdict-card {
            border-radius: 14px;
            padding: 24px;
            text-align: center;
            margin-top: 14px;
            transition: border-color 0.2s;
        }
        .verdict-buy { background: var(--eiq-positive-bg); border: 1.5px solid var(--eiq-positive-border); }
        .verdict-sell { background: var(--eiq-negative-bg); border: 1.5px solid var(--eiq-negative-border); }
        .verdict-hold { background: var(--eiq-warning-bg); border: 1.5px solid var(--eiq-warning-border); }
        .verdict-signal { font-size: 1.8rem; font-weight: 800; margin: 8px 0; }
        .verdict-signal.buy { color: var(--eiq-positive); }
        .verdict-signal.sell { color: var(--eiq-negative); }
        .verdict-signal.hold { color: var(--eiq-warning-text); }
        .verdict-price {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.2rem; font-weight: 600; color: var(--eiq-text); margin: 6px 0;
            font-variant-numeric: tabular-nums;
        }
        .verdict-explain { font-size: 0.85rem; color: var(--eiq-text-secondary); line-height: 1.6; margin-top: 8px; }

        /* === NEWS CARDS === */
        .news-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-left: 3px solid var(--eiq-blue);
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 10px;
            transition: border-color 0.2s;
        }
        .news-card:hover { border-left-color: var(--eiq-blue-hover); }
        .news-title a {
            font-size: 0.9rem; font-weight: 600; color: var(--eiq-text); text-decoration: none;
        }
        .news-title a:hover { color: var(--eiq-blue-hover); }
        .news-meta { font-size: 0.73rem; color: var(--eiq-text-secondary); margin-top: 5px; }
        .news-meta span { margin-right: 10px; }

        /* === SENTIMENT NEWS CARDS === */
        .sentiment-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 14px;
            transition: border-color 0.2s;
        }
        .sentiment-card:hover { border-color: var(--eiq-blue); }
        .sentiment-headline {
            font-size: 0.92rem; font-weight: 600; color: var(--eiq-text);
            margin-bottom: 8px; line-height: 1.4;
        }
        .sentiment-source { font-size: 0.72rem; color: var(--eiq-text-secondary); margin-bottom: 12px; }
        .sentiment-stocks {
            display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;
        }
        .stock-tag {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 4px 12px; border-radius: 6px;
            font-size: 0.75rem; font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        .stock-tag.bullish { background: var(--eiq-positive-bg); color: var(--eiq-positive); border: 1px solid var(--eiq-positive-border); }
        .stock-tag.bearish { background: var(--eiq-negative-bg); color: var(--eiq-negative); border: 1px solid var(--eiq-negative-border); }
        .stock-tag.neutral { background: var(--eiq-bg-alt); color: var(--eiq-text-secondary); border: 1px solid var(--eiq-border); }
        .sentiment-reason {
            font-size: 0.8rem; color: var(--eiq-text-secondary); margin-top: 10px;
            line-height: 1.5; padding-top: 10px; border-top: 1px solid var(--eiq-border);
        }
        .sentiment-badge {
            display: inline-block; padding: 3px 10px; border-radius: 4px;
            font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .sentiment-badge.positive { background: var(--eiq-positive-bg); color: var(--eiq-positive); }
        .sentiment-badge.negative { background: var(--eiq-negative-bg); color: var(--eiq-negative); }
        .sentiment-badge.mixed { background: var(--eiq-warning-bg); color: var(--eiq-warning-text); }

        /* === QUARTERLY CARDS === */
        .pros-card {
            background: var(--eiq-positive-bg); border: 1px solid var(--eiq-positive-border);
            border-radius: 14px; padding: 24px 20px;
        }
        .cons-card {
            background: var(--eiq-negative-bg); border: 1px solid var(--eiq-negative-border);
            border-radius: 14px; padding: 24px 20px;
        }
        .trajectory-card {
            background: var(--eiq-blue-pale); border: 1px solid var(--eiq-blue-pale-border);
            border-radius: 14px; padding: 24px 20px;
        }
        .pc-card-title {
            font-size: 0.95rem; font-weight: 700;
            margin-bottom: 12px; padding-bottom: 8px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .pc-card-title.pros { color: var(--eiq-positive); }
        .pc-card-title.cons { color: var(--eiq-negative); }
        .pc-card-title.trajectory { color: var(--eiq-blue-hover); }
        .pc-bullet { font-size: 0.85rem; color: var(--eiq-text-secondary); line-height: 1.8; }
        .quarter-badge {
            display: inline-block; background: var(--eiq-blue); color: #fff;
            padding: 3px 12px; border-radius: 6px;
            font-size: 0.73rem; font-weight: 600; margin: 0 3px 5px 0;
        }

        /* === TOOLTIP === */
        .info-tooltip {
            display: inline-block; position: relative; cursor: pointer;
            color: var(--eiq-blue-hover); font-size: 0.82rem; margin-left: 4px; vertical-align: middle;
        }
        .info-tooltip .info-tooltip-text {
            visibility: hidden; opacity: 0; position: absolute; bottom: 130%; left: 50%;
            transform: translateX(-50%); background-color: var(--eiq-text); color: #F5F7FA;
            padding: 10px 14px; border-radius: 8px; font-size: 0.75rem; font-weight: 400;
            line-height: 1.5; width: 240px; text-align: left; text-transform: none;
            letter-spacing: normal; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            transition: opacity 0.2s ease; z-index: 100;
        }
        .info-tooltip .info-tooltip-text::after {
            content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px;
            border-width: 5px; border-style: solid;
            border-color: var(--eiq-text) transparent transparent transparent;
        }
        .info-tooltip:hover .info-tooltip-text { visibility: visible; opacity: 1; }

        /* === PROGRESS BAR === */
        .stProgress > div > div > div > div { background: var(--eiq-blue) !important; }

        /* === FORM ACCENTS (checkbox / slider) — Streamlit defaults these to red;
               switch to brand blue for a consistent accent colour. Targeted via
               data-testid/attribute selectors (not emotion-hashed classnames, which
               are unstable across Streamlit versions). === */
        div[data-testid="stCheckbox"] label[data-selected="true"] > div:first-of-type {
            background-color: var(--eiq-blue) !important;
            border-color: var(--eiq-blue) !important;
        }
        .stSlider [role="slider"] { background-color: var(--eiq-blue) !important; border-color: var(--eiq-blue) !important; }
        .stSlider > div > div > div > div { background: var(--eiq-blue) !important; }

        /* === DATAFRAME === */
        .stDataFrame { border-radius: 10px; overflow: hidden; }

        /* === HEALTH SCORE WIDGET === */
        .health-score-widget {
            text-align: center;
            padding: 24px 16px;
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
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
            color: var(--eiq-text-secondary);
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
        .hp-name { font-size: 0.66rem; font-weight: 600; color: var(--eiq-text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
        .hp-value { font-size: 0.88rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .hp-pts { font-size: 0.63rem; color: var(--eiq-text-secondary); }

        /* === INVESTMENT MEMO === */
        .memo-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            padding: 28px;
            margin-top: 8px;
        }
        .memo-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--eiq-border);
        }
        .memo-title { font-size: 1rem; font-weight: 700; color: var(--eiq-text); }
        .memo-badge {
            background: var(--eiq-blue-pale);
            color: var(--eiq-blue-hover);
            font-size: 0.7rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 4px;
            border: 1px solid var(--eiq-blue-pale-border);
        }
        .memo-body { font-size: 0.85rem; color: var(--eiq-text-secondary); line-height: 1.75; }
        .memo-section-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--eiq-text);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 14px;
            margin-bottom: 4px;
        }
        .memo-line { margin-bottom: 2px; }

        /* === WATCHLIST-STYLE ROW CARDS (also reused by Screener's dividend calendar) === */
        .watchlist-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            padding: 16px 22px;
            margin-bottom: 10px;
            transition: border-color 0.2s;
        }
        .watchlist-card.wl-alert {
            border-color: var(--eiq-positive-border);
            background: var(--eiq-positive-bg);
        }
        .watchlist-card.wl-normal:hover { border-color: var(--eiq-blue); }
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
            color: var(--eiq-text);
            font-family: 'JetBrains Mono', monospace;
        }
        .wl-company { font-size: 0.8rem; color: var(--eiq-text-secondary); }
        .wl-note { font-size: 0.75rem; color: var(--eiq-text-secondary); font-style: italic; margin-left: 6px; }
        .wl-right { text-align: right; }
        .wl-price {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--eiq-text);
            font-family: 'JetBrains Mono', monospace;
        }
        .wl-alert-price { font-size: 0.73rem; color: var(--eiq-text-secondary); margin-top: 2px; }
        .wl-status { font-size: 0.73rem; margin-top: 4px; font-weight: 500; }
        .alert-banner {
            background: var(--eiq-positive-bg);
            border: 1px solid var(--eiq-positive-border);
            border-radius: 10px;
            padding: 14px 20px;
            font-size: 0.88rem;
            color: var(--eiq-positive);
            margin: 12px 0 16px;
        }

        /* === NEWS RADAR CARDS === */
        .nr-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            padding: 20px 22px;
            margin-bottom: 14px;
            transition: border-color 0.2s;
        }
        .nr-card:hover { border-color: var(--eiq-blue); }
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
            background: var(--eiq-blue-pale);
            color: var(--eiq-blue-hover);
            border: 1px solid var(--eiq-blue-pale-border);
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.65rem;
            font-weight: 600;
        }
        .nr-meta-tag {
            display: inline-block;
            background: var(--eiq-bg-alt);
            color: var(--eiq-text-secondary);
            border: 1px solid var(--eiq-border);
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 0.65rem;
            font-weight: 500;
        }
        .nr-source { font-size: 0.72rem; color: var(--eiq-text-secondary); white-space: nowrap; }
        .nr-headline { font-size: 0.92rem; font-weight: 700; color: var(--eiq-text); margin: 8px 0 6px; line-height: 1.4; }
        .nr-headline a { color: var(--eiq-text); text-decoration: none; }
        .nr-headline a:hover { color: var(--eiq-blue-hover); }
        .nr-summary { font-size: 0.82rem; color: var(--eiq-text-secondary); line-height: 1.6; margin-bottom: 8px; }
        .nr-reason {
            font-size: 0.8rem;
            color: var(--eiq-text-secondary);
            line-height: 1.5;
            padding: 10px 14px;
            background: var(--eiq-bg-alt);
            border-left: 3px solid var(--eiq-border);
            border-radius: 0 6px 6px 0;
            margin: 8px 0;
        }
        .nr-impact {
            font-size: 0.8rem;
            color: var(--eiq-text-secondary);
            line-height: 1.5;
            padding: 10px 14px;
            background: var(--eiq-warning-bg);
            border-left: 3px solid var(--eiq-warning-border);
            border-radius: 0 6px 6px 0;
            margin: 8px 0;
        }
        .nr-tickers { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
        .nr-ticker-tag {
            display: inline-block;
            background: var(--eiq-blue-pale);
            color: var(--eiq-blue-hover);
            border: 1px solid var(--eiq-blue-pale-border);
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
        .nr-read-more a { color: var(--eiq-blue-hover); text-decoration: none; font-weight: 600; }
        .nr-read-more a:hover { color: var(--eiq-blue); }

        /* === NEWS RADAR SUMMARY PANEL === */
        .nr-summary-card {
            background: var(--eiq-surface);
            border: 2px solid;
            border-radius: 14px;
            padding: 20px;
            text-align: center;
        }
        .nr-summary-label {
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--eiq-text-secondary);
            margin-bottom: 8px;
        }
        .nr-summary-value {
            font-size: 1.8rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }
        .nr-ai-summary {
            background: var(--eiq-blue-pale);
            border: 1px solid var(--eiq-blue-pale-border);
            border-radius: 14px;
            padding: 20px 24px;
            margin: 16px 0 8px;
        }
        .nr-ai-summary-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--eiq-blue-hover);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .nr-ai-summary-text {
            font-size: 0.88rem;
            color: var(--eiq-text);
            line-height: 1.7;
        }

        /* === SCREENER: header row === */
        .sc-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 6px; }
        .sc-header-actions { display: flex; }
        .st-key-sc_header_actions div[data-testid="stHorizontalBlock"] { gap: 8px !important; }
        .st-key-sc_reset .stButton > button, .st-key-sc_refresh .stButton > button, .st-key-sc_sidebar_toggle_wrap .stButton > button {
            background: var(--eiq-surface) !important;
            color: var(--eiq-text) !important;
            border: 1px solid var(--eiq-border) !important;
            height: 42px !important;
        }
        .st-key-sc_reset .stButton > button:hover, .st-key-sc_refresh .stButton > button:hover, .st-key-sc_sidebar_toggle_wrap .stButton > button:hover { border-color: var(--eiq-blue) !important; color: var(--eiq-blue-hover) !important; }
        .st-key-sc_run .stButton > button { height: 42px !important; }
        .sc-refresh-meta { font-size: 0.72rem; color: var(--eiq-text-secondary); margin-top: 4px; text-align: right; }

        /* === SCREENER: market universe card === */
        .sc-universe-card {
            background: var(--eiq-surface);
            border: 1px solid var(--eiq-border);
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 16px;
        }
        .sc-universe-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: var(--eiq-text-secondary); margin-bottom: 10px; }
        .st-key-sc_market_row div[data-testid="stHorizontalBlock"] { gap: 10px !important; }
        .st-key-sc_market_row div[data-testid="stCheckbox"] label {
            border: 1px solid var(--eiq-border) !important;
            border-radius: 20px !important;
            padding: 8px 16px !important;
            background: var(--eiq-bg-alt);
            transition: all 0.15s;
            cursor: pointer;
        }
        .st-key-sc_market_row div[data-testid="stCheckbox"] label[data-selected="true"] {
            background: var(--eiq-blue-pale) !important;
            border-color: var(--eiq-blue) !important;
        }
        .st-key-sc_market_row div[data-testid="stCheckbox"] label p {
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            color: var(--eiq-text) !important;
        }
        .st-key-sc_market_row div[data-testid="stCheckbox"] label[data-selected="true"] p { color: var(--eiq-blue-hover) !important; }
        .sc-universe-count { font-size: 0.82rem; color: var(--eiq-text-secondary); margin-top: 10px; }
        .sc-universe-count b { color: var(--eiq-text); font-weight: 700; }

        /* === SCREENER: filter sidebar === */
        .st-key-sc_sidebar {
            position: sticky;
            top: 84px;
            max-height: calc(100vh - 100px);
            overflow-y: auto;
            padding-right: 6px;
        }
        .sc-sidebar-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
        .sc-sidebar-title { font-size: 1rem; font-weight: 700; color: var(--eiq-text); display: flex; align-items: center; gap: 8px; }
        .sc-active-badge {
            background: var(--eiq-blue); color: #fff; font-size: 0.68rem; font-weight: 700;
            border-radius: 10px; padding: 1px 8px; min-width: 18px; text-align: center;
        }
        .st-key-sc_clear_all .stButton > button {
            background: transparent !important; border: none !important; color: var(--eiq-blue-hover) !important;
            font-size: 0.78rem !important; height: auto !important; padding: 2px 4px !important;
        }

        /* === SCREENER: accordions (active count + summary in header) === */
        .sc-accordion-badge {
            display: inline-block; background: var(--eiq-blue-pale); color: var(--eiq-blue-hover);
            font-size: 0.65rem; font-weight: 700; border-radius: 10px; padding: 1px 8px; margin-left: 8px;
        }
        .sc-accordion-summary { font-size: 0.72rem; color: var(--eiq-text-secondary); font-weight: 400; margin-top: 2px; }

        /* === SCREENER: active-filter chips === */
        .st-key-sc_active_chips div[data-testid="stVerticalBlock"] {
            flex-direction: row !important; flex-wrap: wrap !important; gap: 8px !important;
        }
        .st-key-sc_active_chips div[data-testid="stElementContainer"] { width: auto !important; }
        .st-key-sc_active_chips .stButton > button {
            background: var(--eiq-blue-pale) !important;
            color: var(--eiq-blue-hover) !important;
            border: 1px solid var(--eiq-blue-pale-border) !important;
            border-radius: 20px !important;
            padding: 5px 14px !important;
            height: auto !important;
            font-size: 0.76rem !important;
            font-weight: 600 !important;
        }
        .st-key-sc_active_chips .stButton > button:hover { background: var(--eiq-negative-bg) !important; color: var(--eiq-negative) !important; border-color: var(--eiq-negative-border) !important; }

        /* === SCREENER: compact summary cards === */
        .sc-summary-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 14px 0 20px; }
        .sc-summary-card {
            background: var(--eiq-surface); border: 1px solid var(--eiq-border); border-radius: 12px;
            padding: 14px 16px; display: flex; align-items: center; gap: 12px;
        }
        .sc-summary-icon {
            width: 34px; height: 34px; border-radius: 9px; background: var(--eiq-blue-pale);
            color: var(--eiq-blue-hover); display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        }
        .sc-summary-label { font-size: 0.68rem; color: var(--eiq-text-secondary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
        .sc-summary-value { font-size: 1.35rem; font-weight: 800; color: var(--eiq-text); font-family: 'JetBrains Mono', monospace; line-height: 1.2; }
        .sc-summary-help { font-size: 0.7rem; color: var(--eiq-text-secondary); }

        /* === SCREENER: results toolbar === */
        .st-key-sc_toolbar div[data-testid="stHorizontalBlock"] { align-items: center; gap: 10px !important; }

        /* === SCREENER: exchange badge in company cell context (dividend calendar etc.) === */
        .sc-exch-badge {
            display: inline-block; font-size: 0.62rem; font-weight: 700; padding: 1px 6px; border-radius: 4px;
            background: var(--eiq-bg-alt); color: var(--eiq-text-secondary); border: 1px solid var(--eiq-border);
            margin-left: 6px; vertical-align: middle;
        }

        @media (max-width: 1024px) {
            .sc-summary-row { grid-template-columns: repeat(2, 1fr); }
            .st-key-sc_sidebar { position: static; max-height: none; }
        }

        /* === RESPONSIVE === */
        @media (max-width: 900px) {
            .st-key-topbar_nav { display: none; }
            .st-key-topbar_login { display: none; }
            .st-key-topbar_hamburger { display: block !important; }
            .hero-sub-v2 { max-width: 100%; }
            .story-section { grid-template-columns: 1fr; gap: 28px; padding: 44px 20px; }
            .story-section.alt { direction: ltr; }
        }
        /* Below Streamlit's own ~640px column-stacking breakpoint, the topbar's
           logo/cta/hamburger columns wrap onto separate rows. Drop the standalone
           CTA here (it's duplicated inside the hamburger menu) so logo + hamburger
           stay on one compact row instead of a 3-line stack. */
        @media (max-width: 640px) {
            .st-key-topbar_cta { display: none; }
        }
        @media (max-width: 768px) {
            .hero-title-v2 { font-size: 2rem; }
            .st-key-hero_wrap { padding: 28px 16px 24px; }
            .ticker-strip { gap: 18px; }
            .health-breakdown { gap: 6px; }
            .health-pill { min-width: 90px; }
            .eiq-float-card { display: none; }
            .story-title { font-size: 1.5rem; }
        }
        </style>
    """, unsafe_allow_html=True)


CURRENCY_SYMBOLS = {
    "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥",
}


def currency_symbol(code):
    """Maps a currency code (e.g. from yfinance/AI extraction) to its display symbol."""
    return CURRENCY_SYMBOLS.get((code or "USD").upper(), "$")


def format_number(num, symbol="$"):
    """Formats large numbers into readable strings."""
    if num is None:
        return "N/A"
    try:
        num = float(num)
    except (ValueError, TypeError):
        return str(num)
    if abs(num) >= 1e12:
        return f"{symbol}{num / 1e12:.2f}T"
    if abs(num) >= 1e9:
        return f"{symbol}{num / 1e9:.2f}B"
    if abs(num) >= 1e6:
        return f"{symbol}{num / 1e6:.2f}M"
    if abs(num) >= 1e3:
        return f"{symbol}{num / 1e3:.1f}K"
    return f"{symbol}{num:.2f}"


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
