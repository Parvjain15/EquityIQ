import streamlit as st
import yfinance as yf
import datetime
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Indian tickers: Nifty 50 + Nifty Next 50 ─────────────────────────────────
INDIAN_TICKERS = [
    # Nifty 50
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFOSYS.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS",
    "BAJFINANCE.NS", "HCLTECH.NS", "KOTAKBANK.NS", "MARUTI.NS", "AXISBANK.NS",
    "ASIANPAINT.NS", "SUNPHARMA.NS", "TITAN.NS", "WIPRO.NS", "ULTRACEMCO.NS",
    "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "TATAMOTORS.NS",
    "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "ADANIPORTS.NS", "BAJAJFINSV.NS",
    "NESTLEIND.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS",
    "EICHERMOT.NS", "HEROMOTOCO.NS", "M&M.NS", "TATACONSUM.NS", "BRITANNIA.NS",
    "INDUSINDBK.NS", "GRASIM.NS", "TECHM.NS", "BPCL.NS", "ADANIENT.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "SHRIRAMFIN.NS", "LTIM.NS", "BEL.NS",
    # Nifty Next 50
    "DMART.NS", "ZOMATO.NS", "NYKAA.NS", "PAYTM.NS", "POLICYBZR.NS",
    "PERSISTENT.NS", "MPHASIS.NS", "COFORGE.NS", "OFSS.NS", "LTTS.NS",
    "HAVELLS.NS", "POLYCAB.NS", "TRENT.NS", "IRCTC.NS", "ATGL.NS",
    "CHOLAFIN.NS", "MUTHOOTFIN.NS", "BAJAJ-AUTO.NS", "GODREJCP.NS", "MARICO.NS",
    "DABUR.NS", "COLPAL.NS", "PIDILITIND.NS", "BERGEPAINT.NS", "SIEMENS.NS",
    "ABB.NS", "BANKBARODA.NS", "PNB.NS", "CANARABANK.NS", "IDFCFIRSTB.NS",
    "FEDERALBNK.NS", "SAIL.NS", "NMDC.NS", "VEDL.NS", "GAIL.NS",
    "IOC.NS", "TATAPOWER.NS", "ADANIGREEN.NS", "TORNTPHARM.NS", "LUPIN.NS",
    "AUROPHARMA.NS", "ALKEM.NS", "LICI.NS", "PFC.NS", "RECLTD.NS",
    "NAUKRI.NS", "PAGEIND.NS", "VBL.NS", "CONCOR.NS", "PIIND.NS",
]

# ── US fallback list (used if Wikipedia is unreachable) ──────────────────────
_US_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMD", "INTC", "ORCL", "CRM", "ADBE", "QCOM", "TXN",
    "AVGO", "MU", "AMAT", "KLAC", "LRCX", "CSCO", "IBM", "NOW", "SNOW", "PLTR",
    "SHOP", "NET", "DDOG", "ZS", "PANW", "FTNT", "WDAY", "TEAM", "UBER", "SQ",
    "PYPL", "COIN", "RBLX", "GOOGL", "META", "NFLX", "DIS", "T", "VZ", "CMCSA",
    "SNAP", "PINS", "SPOT", "EA", "TTWO", "JPM", "BAC", "GS", "WFC", "V",
    "MA", "AXP", "BLK", "C", "MS", "USB", "TFC", "PNC", "COF", "DFS",
    "SCHW", "SPGI", "MCO", "CME", "ICE", "BX", "KKR", "AFL", "MET", "PRU",
    "TRV", "ALL", "CB", "AON", "JNJ", "PFE", "UNH", "ABBV", "MRK", "LLY",
    "AMGN", "GILD", "BMY", "CVS", "CI", "HUM", "MDT", "ABT", "TMO", "DHR",
    "ISRG", "BSX", "SYK", "REGN", "BIIB", "VRTX", "MRNA", "XOM", "CVX", "COP",
    "SLB", "EOG", "OXY", "PSX", "VLO", "MPC", "HAL", "WMT", "COST", "PG",
    "KO", "PEP", "CL", "MO", "PM", "MDLZ", "GIS", "HSY", "EL", "KMB",
    "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "TJX", "BURL",
    "ROST", "F", "GM", "ABNB", "BKNG", "MAR", "HLT", "CMG", "RCL", "CCL",
    "BA", "CAT", "GE", "HON", "LMT", "RTX", "UPS", "FDX", "DE", "EMR",
    "ETN", "ITW", "MMM", "GD", "NOC", "WM", "CTAS", "ADP", "AMT", "PLD",
    "EQIX", "CCI", "PSA", "O", "VICI", "NEE", "DUK", "SO", "EXC", "SRE",
    "LIN", "APD", "SHW", "ECL", "FCX", "NEM", "DOW", "PPG", "ALB", "NUE",
]


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_sp500_tickers() -> list:
    """Fetch live S&P 500 constituent tickers from Wikipedia. Cached 24 hours."""
    try:
        tables = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            attrs={"id": "constituents"},
        )
        tickers = [t.replace(".", "-") for t in tables[0]["Symbol"].tolist()]
        return tickers
    except Exception as e:
        print(f"S&P 500 Wikipedia fetch error: {e}")
        return _US_FALLBACK


def get_all_tickers(include_us: bool = True, include_india: bool = True) -> list:
    """Returns deduplicated list of tickers based on selected markets."""
    result = []
    if include_us:
        result.extend(fetch_sp500_tickers())
    if include_india:
        result.extend(INDIAN_TICKERS)
    return list(dict.fromkeys(result))


@st.cache_data(ttl=900, show_spinner=False)
def fetch_screener_data(tickers_tuple: tuple) -> list:
    """Parallel-fetch screener metrics for all tickers (cached 15 min)."""

    def _fetch_one(ticker: str):
        try:
            stock = yf.Ticker(ticker)
            info  = stock.info
            if not info:
                return None
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if not price:
                return None

            de_raw = info.get("debtToEquity")
            de = (de_raw / 100 if de_raw and de_raw > 10 else de_raw) if de_raw is not None else None

            def ts2date(ts):
                if not ts:
                    return ""
                try:
                    return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
                except Exception:
                    return ""

            def _to_date(v):
                """Convert calendar value (datetime / date / str) to date, or None."""
                if v is None:
                    return None
                if isinstance(v, datetime.date) and not isinstance(v, datetime.datetime):
                    return v
                if isinstance(v, datetime.datetime):
                    return v.date()
                if isinstance(v, str):
                    try:
                        return datetime.date.fromisoformat(v[:10])
                    except ValueError:
                        return None
                return None

            today = datetime.date.today()

            # stock.calendar returns UPCOMING events; info['exDividendDate'] is PAST
            ex_div_date = ""
            pay_date    = ""
            try:
                cal = stock.calendar
                if isinstance(cal, dict):
                    ex_d = _to_date(cal.get("Ex-Dividend Date"))
                    pa_d = _to_date(cal.get("Dividend Date"))
                    if ex_d and ex_d >= today:
                        ex_div_date = ex_d.isoformat()
                    if pa_d:
                        pay_date = pa_d.isoformat()
            except Exception:
                pass

            # Fallback to info timestamp — only accept if date is still upcoming
            if not ex_div_date:
                ts_str = ts2date(info.get("exDividendDate"))
                if ts_str:
                    try:
                        if datetime.date.fromisoformat(ts_str) >= today:
                            ex_div_date = ts_str
                    except ValueError:
                        pass

            if not pay_date:
                pay_date = ts2date(info.get("dividendDate"))

            return {
                "ticker":            ticker,
                "company":           info.get("longName") or info.get("shortName") or ticker,
                "sector":            info.get("sector") or "",
                "industry":          info.get("industry") or "",
                "country":           info.get("country") or "",
                "exchange":          info.get("exchange") or "",
                "price":             price,
                "market_cap":        info.get("marketCap"),
                # Valuation
                "pe_ratio":          info.get("trailingPE") or info.get("forwardPE"),
                "pb_ratio":          info.get("priceToBook"),
                "ps_ratio":          info.get("priceToSalesTrailing12Months"),
                # Dividends (ex_div_date / pay_date = upcoming only, set above)
                "dividend_yield":    info.get("dividendYield"),
                "dividend_rate":     info.get("dividendRate"),
                "ex_div_date":       ex_div_date,
                "pay_date":          pay_date,
                "payout_ratio":      info.get("payoutRatio"),
                # Quality
                "roe":               info.get("returnOnEquity"),
                "roa":               info.get("returnOnAssets"),
                "profit_margin":     info.get("profitMargins"),
                "operating_margin":  info.get("operatingMargins"),
                "free_cash_flow":    info.get("freeCashflow"),
                # Growth
                "revenue_growth":    info.get("revenueGrowth"),
                "earnings_growth":   info.get("earningsGrowth"),
                "earnings_q_growth": info.get("earningsQuarterlyGrowth"),
                # Risk
                "debt_to_equity":    de,
                "current_ratio":     info.get("currentRatio"),
                "beta":              info.get("beta"),
                # 52-week range
                "w52_high":          info.get("fiftyTwoWeekHigh"),
                "w52_low":           info.get("fiftyTwoWeekLow"),
                # Analyst
                "analyst_rating":    (info.get("recommendationKey") or "").lower(),
                "analyst_count":     info.get("numberOfAnalystOpinions") or 0,
                "target_price":      info.get("targetMeanPrice"),
            }
        except Exception as e:
            print(f"Screener {ticker}: {e}")
            return None

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_fetch_one, tk): tk for tk in tickers_tuple}
        for future in as_completed(futures):
            r = future.result()
            if r:
                results.append(r)

    return sorted(results, key=lambda x: x.get("market_cap") or 0, reverse=True)


def compute_health_score(d: dict) -> tuple:
    """Returns (score 0-100, grade A-F, color hex)."""
    score = 0
    avail = 0

    def chk(pts, cond):
        nonlocal score, avail
        avail += pts
        if cond:
            score += pts

    pm = d.get("profit_margin")
    if pm is not None:
        chk(15, pm > 0.10)

    roe = d.get("roe")
    if roe is not None:
        chk(15, roe > 0.15)

    roa = d.get("roa")
    if roa is not None:
        chk(10, roa > 0.05)

    rg = d.get("revenue_growth")
    if rg is not None:
        chk(15, rg > 0.05)

    pe = d.get("pe_ratio")
    if pe is not None:
        chk(10, 0 < pe < 30)

    de = d.get("debt_to_equity")
    if de is not None:
        chk(15, de < 1.0)

    cr = d.get("current_ratio")
    if cr is not None:
        chk(10, cr > 1.5)

    fcf = d.get("free_cash_flow")
    if fcf is not None:
        chk(10, fcf > 0)

    if avail == 0:
        return 50, "N/A", "#94a3b8"

    final = round((score / avail) * 100)
    if final >= 80:
        return final, "A", "#16a34a"
    elif final >= 65:
        return final, "B", "#00b386"
    elif final >= 50:
        return final, "C", "#d97706"
    elif final >= 35:
        return final, "D", "#ea580c"
    return final, "F", "#dc2626"


def get_upcoming_dividends(stocks: list, days: int = 60) -> list:
    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days)
    result = []
    for d in stocks:
        s = d.get("ex_div_date", "")
        if not s:
            continue
        try:
            ex = datetime.date.fromisoformat(s)
        except ValueError:
            continue
        if today <= ex <= cutoff:
            result.append({**d, "_days_until": (ex - today).days})
    return sorted(result, key=lambda x: x["_days_until"])


# ── Dividend enrichment: Finnhub (US) + NSE India (Indian stocks) ──────────────

@st.cache_data(ttl=3600, show_spinner=False)
def enrich_dividends_finnhub(finnhub_key: str, us_tickers: tuple) -> dict:
    """
    Fetches upcoming dividend dates from Finnhub for US tickers.
    Returns dict: ticker → {ex_div_date, pay_date, dividend_rate}
    Free tier: 60 req/min, no daily cap.
    """
    if not finnhub_key or not us_tickers:
        return {}

    today     = datetime.date.today()
    from_date = today.isoformat()
    to_date   = (today + datetime.timedelta(days=120)).isoformat()
    result    = {}

    for ticker in us_tickers:
        try:
            url  = (
                f"https://finnhub.io/api/v1/stock/dividend"
                f"?symbol={ticker}&from={from_date}&to={to_date}"
                f"&token={finnhub_key}"
            )
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200:
                continue
            data = resp.json()
            if not data:
                continue
            # Finnhub returns list sorted desc by exDate; get the soonest upcoming
            for entry in sorted(data, key=lambda x: x.get("exDate", "")):
                ex_s = entry.get("exDate", "")
                try:
                    ex_d = datetime.date.fromisoformat(ex_s)
                except ValueError:
                    continue
                if ex_d >= today:
                    result[ticker] = {
                        "ex_div_date":   ex_s,
                        "pay_date":      entry.get("paymentDate", ""),
                        "dividend_rate": entry.get("amount"),
                        "_source":       "Finnhub",
                    }
                    break
        except Exception as e:
            print(f"Finnhub dividend {ticker}: {e}")

    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_nse_dividend_calendar(days_ahead: int = 90) -> list:
    """
    Fetches upcoming NSE corporate dividend actions from NSE India's official API.
    Returns list of dicts: {symbol, company, ex_div_date, dividend_amount, purpose}
    Free, no API key required.
    """
    today    = datetime.date.today()
    to_date  = today + datetime.timedelta(days=days_ahead)
    fmt      = "%d-%m-%Y"
    from_str = today.strftime(fmt)
    to_str   = to_date.strftime(fmt)

    session  = requests.Session()
    headers  = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept":          "application/json, text/plain, */*",
        "Referer":         "https://www.nseindia.com/",
    }

    try:
        # Prime cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url  = (
            f"https://www.nseindia.com/api/corporates-corp-actions"
            f"?index=equities&from_date={from_str}&to_date={to_str}&corp_action=dividends"
        )
        resp = session.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        raw = resp.json()
        data = raw if isinstance(raw, list) else raw.get("data", [])
        results = []
        for item in data:
            ex_s = item.get("exDate") or item.get("Ex_Date") or ""
            if not ex_s:
                continue
            # Parse various NSE date formats
            for fmt_try in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    ex_d = datetime.datetime.strptime(ex_s, fmt_try).date()
                    ex_s = ex_d.isoformat()
                    break
                except ValueError:
                    continue
            results.append({
                "symbol":          (item.get("symbol") or "").upper(),
                "company":         item.get("comp") or item.get("companyName") or "",
                "ex_div_date":     ex_s,
                "dividend_amount": item.get("subject") or item.get("purpose") or "",
                "_source":         "NSE India",
            })
        return results
    except Exception as e:
        print(f"NSE dividend calendar error: {e}")
        return []
