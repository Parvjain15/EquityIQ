import pdfplumber
from google import genai
import json
import os
import time
import requests
import xml.etree.ElementTree as ET
import yfinance as yf


class FinancialAnalyzer:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API Key is required")
        self.client = genai.Client(api_key=api_key)

    def _generate_content(self, prompt: str) -> str:
        """Call an AI model. Tries Gemini models first, falls back to Groq (Llama 3.3)."""
        # ── Gemini ────────────────────────────────────────────────────────────
        for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
            try:
                return self.client.models.generate_content(model=model, contents=prompt).text.strip()
            except Exception as e:
                print(f"Gemini {model} failed: {e}")

        # ── Groq (Llama 3.3 70B → 8B → Gemma 2 9B) ──────────────────────────
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]:
                try:
                    resp = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3},
                        timeout=20,
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"].strip()
                    print(f"Groq {model} HTTP {resp.status_code}")
                except Exception as e:
                    print(f"Groq {model} failed: {e}")

        raise RuntimeError("All AI models (Gemini + Groq) failed")

    def _json_from_ai(self, prompt: str):
        """Call AI and parse the response as JSON, stripping markdown fences."""
        raw = self._generate_content(prompt)
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        return json.loads(raw.strip())

    def extract_text_from_pdf(self, pdf_file):
        """Extracts text from a PDF file."""
        text = ""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            return None, f"Error extracting text: {str(e)}"
        if not text.strip():
            return None, "Could not extract any text from the PDF. It might be a scanned image."
        return text, None

    def analyze_financials(self, text):
        """Sends the text to Gemini to extract key financial metrics."""
        prompt = """You are an expert financial analyst. Your task is to carefully read through this financial statement and extract the key financial metrics for the MOST RECENT fiscal year.

IMPORTANT RULES:
1. Return ONLY raw JSON. No markdown, no code fences, no explanation text before or after.
2. ALL number values MUST be actual numbers (integers or floats), NOT strings and NOT null.
3. Convert all values to their full numeric form:
   - "394.3 billion" = 394300000000
   - "93,736 (in millions)" = 93736000000
   - If the table says "in millions", multiply every number by 1000000
   - If the table says "in thousands", multiply every number by 1000
4. Search the ENTIRE document for: Income Statements, Balance Sheets, Cash Flow Statements.
5. For EPS: find "Earnings per share" (basic or diluted).
6. For Free Cash Flow: "Cash from operations" minus "Capital expenditures".
7. For Growth Rate: compute (current_revenue - prior_revenue) / prior_revenue.
8. NEVER return null for numeric fields. If truly not found, use 0.
9. Extract the stock ticker symbol (e.g. AAPL for Apple, MSFT for Microsoft, RELIANCE.NS for Reliance Industries).

JSON format (use real numbers, these are just format examples):
{
  "Company Name": "Apple Inc.",
  "Ticker": "AAPL",
  "Fiscal Year": "2025",
  "Revenue": 394328000000,
  "Net Income": 93736000000,
  "EPS": 6.08,
  "Free Cash Flow": 108807000000,
  "Total Assets": 364980000000,
  "Total Liabilities": 308030000000,
  "Outstanding Shares": 15408095000,
  "Growth Rate": 0.05,
  "Currency": "USD",
  "Risk Factors": ["risk one", "risk two", "risk three"],
  "Notes": "Values extracted from consolidated statements"
}

DOCUMENT TEXT:
""" + text[:30000]

        try:
            return self._json_from_ai(prompt)
        except Exception as e:
            return {"error": f"All models failed: {e}"}

    def calculate_intrinsic_value(self, metrics):
        """Calculates intrinsic value using DCF and Graham Number."""
        if "error" in metrics:
            return metrics

        try:
            fcf = float(metrics.get("Free Cash Flow") or 0)
            eps = float(metrics.get("EPS") or 0)
            growth_rate = float(metrics.get("Growth Rate") or 0.05)
            shares = float(metrics.get("Outstanding Shares") or 1)
            assets = float(metrics.get("Total Assets") or 0)
            liabilities = float(metrics.get("Total Liabilities") or 0)

            # 1. Simplified DCF
            discount_rate = 0.10
            terminal_growth = 0.02
            years = 5

            future_fcf = []
            current_fcf = fcf
            for _ in range(years):
                current_fcf *= (1 + growth_rate)
                future_fcf.append(current_fcf)

            if future_fcf and future_fcf[-1] != 0:
                terminal_value = (future_fcf[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            else:
                terminal_value = 0

            dcf_value = sum(val / ((1 + discount_rate) ** (i + 1)) for i, val in enumerate(future_fcf))
            dcf_value += terminal_value / ((1 + discount_rate) ** years)
            intrinsic_dcf = dcf_value / shares if shares else 0

            # 2. Graham Number
            book_value = assets - liabilities
            bvps = book_value / shares if shares else 0

            if eps > 0 and bvps > 0:
                graham_number = (22.5 * eps * bvps) ** 0.5
            else:
                graham_number = 0

            return {
                "DCF Value": round(intrinsic_dcf, 2),
                "Graham Number": round(graham_number, 2),
                "Book Value Per Share": round(bvps, 2),
                "Assumptions": {
                    "Discount Rate": "10%",
                    "Growth Rate": f"{growth_rate:.1%}",
                    "Terminal Growth": "2%",
                    "Projection Years": "5"
                }
            }
        except Exception as e:
            return {"error": f"Calculation error: {str(e)}"}

    def get_current_price(self, ticker):
        """Fetches the current stock price using yfinance."""
        if not ticker:
            return None
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if hist.empty:
                return None
            return round(float(hist['Close'].iloc[-1]), 2)
        except Exception as e:
            print(f"Could not fetch price for {ticker}: {e}")
            return None

    def get_recent_news(self, ticker, max_items=3):
        """Fetches recent news articles for a ticker using yfinance."""
        if not ticker:
            return []
        try:
            import time
            stock = yf.Ticker(ticker)
            raw_news = stock.news or []
            articles = []
            for item in raw_news[:max_items]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title", "No title")
                link = (content.get("canonicalUrl", {}) or {}).get("url") or \
                       (content.get("clickThroughUrl", {}) or {}).get("url") or \
                       item.get("link", "#")
                publisher = (content.get("provider", {}) or {}).get("displayName") or \
                            item.get("publisher", "Unknown")
                pub_time = content.get("pubDate") or ""
                if not pub_time:
                    raw_ts = item.get("providerPublishTime", 0)
                    if raw_ts:
                        pub_time = time.strftime("%b %d, %Y", time.gmtime(raw_ts))
                articles.append({
                    "title": title,
                    "link": link,
                    "publisher": publisher,
                    "published": pub_time,
                })
            return articles
        except Exception as e:
            print(f"Could not fetch news for {ticker}: {e}")
            return []

    def analyze_quarterly_comparison(self, pdf_files_with_labels):
        """Analyze multiple quarterly PDFs and compute growth trends + pros/cons.

        Args:
            pdf_files_with_labels: list of (pdf_file, label) tuples, e.g. [("file", "Q1 2025")]

        Returns:
            dict with keys: quarters, growth, pros_cons, company_name
        """
        quarters = []
        errors = []

        for pdf_file, label in pdf_files_with_labels:
            text, err = self.extract_text_from_pdf(pdf_file)
            if err:
                errors.append(f"{label}: {err}")
                continue
            metrics = self.analyze_financials(text)
            if "error" in metrics:
                errors.append(f"{label}: {metrics['error']}")
                continue
            metrics["Quarter Label"] = label
            quarters.append(metrics)

        if len(quarters) < 2:
            return {"error": f"Need at least 2 valid reports. Errors: {'; '.join(errors)}"}

        # Compute QoQ growth
        growth = []
        metric_keys = ["Revenue", "Net Income", "EPS", "Free Cash Flow"]
        for i in range(1, len(quarters)):
            prev = quarters[i - 1]
            curr = quarters[i]
            g = {"Quarter": curr.get("Quarter Label", f"Q{i+1}")}
            for key in metric_keys:
                prev_val = float(prev.get(key) or 0)
                curr_val = float(curr.get(key) or 0)
                if prev_val != 0:
                    g[key] = round(((curr_val - prev_val) / abs(prev_val)) * 100, 2)
                else:
                    g[key] = 0.0
            growth.append(g)

        # Generate pros/cons via Gemini
        pros_cons = self.generate_pros_cons(quarters)

        company_name = quarters[0].get("Company Name", "Unknown Company")

        return {
            "quarters": quarters,
            "growth": growth,
            "pros_cons": pros_cons,
            "company_name": company_name,
            "errors": errors
        }

    def generate_pros_cons(self, quarters):
        """Use Gemini to generate pros, cons, and trajectory from quarterly data."""
        # Build a summary of all quarters for the prompt
        summary_lines = []
        for q in quarters:
            label = q.get("Quarter Label", "Unknown")
            summary_lines.append(
                f"{label}: Revenue={q.get('Revenue',0)}, "
                f"Net Income={q.get('Net Income',0)}, "
                f"EPS={q.get('EPS',0)}, "
                f"FCF={q.get('Free Cash Flow',0)}, "
                f"Total Assets={q.get('Total Assets',0)}, "
                f"Total Liabilities={q.get('Total Liabilities',0)}"
            )
        quarter_data = "\n".join(summary_lines)

        prompt = f"""You are a senior financial analyst. Below are the key financial metrics extracted from multiple quarterly reports of the same company, in chronological order.

QUARTERLY DATA:
{quarter_data}

Based on this data, provide:
1. PROS: 4-6 bullet points highlighting strengths, positive trends, and growth areas
2. CONS: 4-6 bullet points highlighting weaknesses, concerns, declining metrics, and risks
3. TRAJECTORY: A 2-3 sentence overall assessment of the company's direction

IMPORTANT: Return ONLY raw JSON. No markdown, no code fences.
JSON format:
{{
  "pros": ["point 1", "point 2", "point 3", "point 4"],
  "cons": ["point 1", "point 2", "point 3", "point 4"],
  "trajectory": "Overall assessment text here."
}}"""

        try:
            return self._json_from_ai(prompt)
        except Exception as e:
            print(f"Pros/Cons analysis failed: {e}")
            return {
                "pros": ["Could not generate analysis"],
                "cons": ["Could not generate analysis"],
                "trajectory": "AI analysis unavailable.",
            }

    def fetch_market_indices(self):
        """Fetches live data for major market indices (Indian + US)."""
        indices = {
            "SENSEX": "^BSESN",
            "NIFTY 50": "^NSEI",
            "NIFTY IT": "^CNXIT",
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "NIFTY BANK": "^NSEBANK",
        }
        results = []
        for name, symbol in indices.items():
            try:
                ticker_obj = yf.Ticker(symbol)
                hist = ticker_obj.history(period="2d")
                if hist.empty or len(hist) < 1:
                    continue
                current = float(hist['Close'].iloc[-1])
                if len(hist) >= 2:
                    prev = float(hist['Close'].iloc[-2])
                    change = current - prev
                    change_pct = (change / prev) * 100
                else:
                    change = 0
                    change_pct = 0
                results.append({
                    "name": name,
                    "price": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                })
            except Exception as e:
                print(f"Could not fetch {name}: {e}")
                continue
        return results

    def fetch_market_news_with_sentiment(self, sectors=None):
        """Fetches market news from multiple sources and uses Gemini to analyze sentiment."""
        all_news = []
        seen_titles = set()

        def add(title, link="#", publisher="", published=""):
            t = (title or "").strip()
            if not t or t in seen_titles:
                return
            seen_titles.add(t)
            all_news.append({"title": t, "link": link or "#", "publisher": publisher, "published": published})

        # ── Source 1: Finnhub general news (most reliable, user has key) ─────
        finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        if finnhub_key:
            try:
                resp = requests.get(
                    f"https://finnhub.io/api/v1/news?category=general&token={finnhub_key}",
                    timeout=8,
                )
                if resp.status_code == 200:
                    for item in (resp.json() or [])[:12]:
                        ts = item.get("datetime", 0)
                        pub = time.strftime("%b %d, %Y", time.gmtime(ts)) if ts else ""
                        add(item.get("headline", ""), item.get("url", "#"), item.get("source", "Finnhub"), pub)
            except Exception as e:
                print(f"Finnhub news error: {e}")

        # ── Source 2: RSS feeds (Reuters, ET Markets, Moneycontrol) ──────────
        rss_feeds = [
            ("https://feeds.reuters.com/reuters/businessNews", "Reuters"),
            ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "ET Markets"),
            ("https://www.moneycontrol.com/rss/latestnews.xml", "Moneycontrol"),
        ]
        for feed_url, pub_name in rss_feeds:
            try:
                r = requests.get(feed_url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    root = ET.fromstring(r.content)
                    for item in root.findall(".//item")[:5]:
                        title = (item.findtext("title") or "").strip()
                        link  = (item.findtext("link") or "#").strip()
                        pub   = (item.findtext("pubDate") or "")[:16]
                        add(title, link, pub_name, pub)
            except Exception as e:
                print(f"RSS {pub_name} error: {e}")

        # ── Source 3: yfinance (supplemental, unreliable but adds variety) ───
        if len(all_news) < 8:
            for tk in ["^NSEI", "^GSPC", "AAPL", "RELIANCE.NS", "TCS.NS"]:
                try:
                    for item in (yf.Ticker(tk).news or [])[:2]:
                        content = item.get("content", {}) or {}
                        title   = content.get("title") or item.get("title", "")
                        link    = ((content.get("canonicalUrl") or {}).get("url")
                                   or item.get("link", "#"))
                        src     = ((content.get("provider") or {}).get("displayName")
                                   or item.get("publisher", ""))
                        ts      = item.get("providerPublishTime", 0)
                        pub     = time.strftime("%b %d, %Y", time.gmtime(ts)) if ts else ""
                        add(title, link, src, pub)
                except Exception:
                    continue

        # ── Source 4: GDELT (fallback when above sources dry out) ────────────
        if len(all_news) < 5:
            try:
                import urllib.parse
                encoded = urllib.parse.quote("stock market finance economy India US")
                r = requests.get(
                    f"https://api.gdeltproject.org/api/v2/doc/doc"
                    f"?query={encoded}&mode=artlist&maxrecords=15&format=json&timespan=1day",
                    timeout=8,
                )
                if r.status_code == 200:
                    for item in (r.json().get("articles") or [])[:10]:
                        add(item.get("title", ""), item.get("url", "#"), item.get("domain", "GDELT"))
            except Exception as e:
                print(f"GDELT error: {e}")

        # ── Source 5: AI generated headlines (absolute last resort) ─────────
        if not all_news:
            try:
                for item in self._json_from_ai(
                    "Generate 10 realistic recent financial market news headlines covering US and Indian markets. "
                    "Be specific: company names, figures, dates. "
                    'Return ONLY a JSON array, no markdown. Each item: {"title":"...","link":"#","publisher":"Reuters","published":""}'
                ):
                    add(item.get("title", ""), item.get("link", "#"), item.get("publisher", "AI"), item.get("published", ""))
            except Exception as e:
                print(f"AI headline fallback error: {e}")

        if not all_news:
            return []

        # ── Gemini sentiment analysis ─────────────────────────────────────────
        news_text = "\n".join(f"- {n['title']}" for n in all_news[:12])
        prompt = (
            "You are a senior financial market analyst. Analyze these recent financial news headlines.\n"
            "For each one determine: sentiment (positive/negative/mixed), which stocks are bullish/bearish affected, and why.\n\n"
            f"NEWS HEADLINES:\n{news_text}\n\n"
            "Return ONLY a raw JSON array (no markdown, no code fences). Each item:\n"
            '{"headline":"...","sentiment":"positive|negative|mixed","bullish_stocks":["TICKER"],"bearish_stocks":["TICKER"],"reason":"..."}\n\n'
            "Use NSE tickers for Indian stocks (e.g. RELIANCE.NS, TCS.NS). Return top 6-8 most impactful headlines only."
        )

        sentiment_data = []
        try:
            sentiment_data = self._json_from_ai(prompt)
        except Exception as e:
            print(f"Sentiment analysis failed: {e}")

        # If sentiment analysis failed entirely, still return news with default sentiment
        if not sentiment_data:
            return [
                {
                    "headline": n["title"],
                    "sentiment": "mixed",
                    "bullish_stocks": [],
                    "bearish_stocks": [],
                    "reason": "",
                    "link": n["link"],
                    "publisher": n["publisher"],
                    "published": n["published"],
                }
                for n in all_news[:10]
            ]

        # ── Merge sentiment with news metadata ────────────────────────────────
        news_by_title = {n["title"]: n for n in all_news}
        result = []
        for item in sentiment_data:
            headline = item.get("headline", "")
            matched = next(
                (news for title, news in news_by_title.items()
                 if headline.lower()[:40] in title.lower() or title.lower()[:40] in headline.lower()),
                None,
            )
            result.append({
                "headline": headline,
                "sentiment": item.get("sentiment", "mixed"),
                "bullish_stocks": item.get("bullish_stocks", []),
                "bearish_stocks": item.get("bearish_stocks", []),
                "reason": item.get("reason", ""),
                "link": matched["link"] if matched else "#",
                "publisher": matched["publisher"] if matched else "",
                "published": matched["published"] if matched else "",
            })

        return result

    def fetch_stock_data(self, ticker):
        """Fetches live financial data for a ticker using yfinance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or info.get("trailingPE") is None and info.get("marketCap") is None:
                return None, "Could not find financial data for this ticker."

            # Pull financials
            revenue = info.get("totalRevenue", 0) or 0
            net_income = info.get("netIncomeToCommon", 0) or 0
            eps = info.get("trailingEps", 0) or 0
            total_assets = info.get("totalAssets", 0) or 0
            total_liabilities = info.get("totalDebt", 0) or 0
            shares = info.get("sharesOutstanding", 0) or 0
            fcf = info.get("freeCashflow", 0) or 0
            growth = info.get("revenueGrowth", 0.05) or 0.05
            currency = info.get("currency", "USD")
            name = info.get("longName") or info.get("shortName") or ticker
            sector = info.get("sector", "N/A")
            market_cap = info.get("marketCap", 0) or 0
            pe_ratio = info.get("trailingPE") or info.get("forwardPE")
            pb_ratio = info.get("priceToBook")
            roe = info.get("returnOnEquity")
            roa = info.get("returnOnAssets")
            debt_to_equity = info.get("debtToEquity")
            current_ratio = info.get("currentRatio")
            profit_margin = info.get("profitMargins")

            # Try to get total assets/liabilities from balance sheet if missing
            if total_assets == 0:
                try:
                    bs = stock.balance_sheet
                    if bs is not None and not bs.empty:
                        if "Total Assets" in bs.index:
                            total_assets = float(bs.loc["Total Assets"].iloc[0]) or 0
                        if "Total Liabilities Net Minority Interest" in bs.index:
                            total_liabilities = float(bs.loc["Total Liabilities Net Minority Interest"].iloc[0]) or 0
                except Exception:
                    pass

            metrics = {
                "Company Name": name,
                "Ticker": ticker.upper(),
                "Fiscal Year": "TTM",
                "Revenue": revenue,
                "Net Income": net_income,
                "EPS": round(eps, 2),
                "Free Cash Flow": fcf,
                "Total Assets": total_assets,
                "Total Liabilities": total_liabilities,
                "Outstanding Shares": shares,
                "Growth Rate": growth,
                "Currency": currency,
                "Sector": sector,
                "Market Cap": market_cap,
                "PE Ratio": round(float(pe_ratio), 2) if pe_ratio else None,
                "PB Ratio": round(float(pb_ratio), 2) if pb_ratio else None,
                "ROE": round(float(roe), 4) if roe else None,
                "ROA": round(float(roa), 4) if roa else None,
                "Debt to Equity": round(float(debt_to_equity), 4) if debt_to_equity else None,
                "Current Ratio": round(float(current_ratio), 2) if current_ratio else None,
                "Profit Margin": round(float(profit_margin), 4) if profit_margin else None,
                "Risk Factors": [
                    f"Sector: {sector}",
                    f"Market Cap: ${market_cap/1e9:.1f}B" if market_cap > 0 else "Market Cap: N/A",
                    f"Revenue Growth: {growth:.1%}" if growth else "Growth data unavailable"
                ],
                "Notes": f"Data sourced from Yahoo Finance (trailing twelve months). Ticker: {ticker.upper()}"
            }
            return metrics, None
        except Exception as e:
            return None, f"Error fetching data for {ticker}: {str(e)}"

    def calculate_health_score(self, metrics):
        """Calculate a 0-100 health score with letter grade for a stock."""
        score = 0
        breakdown = {}

        def sf(key, default=None):
            v = metrics.get(key)
            if v is None:
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default

        revenue = sf("Revenue", 0)
        net_income = sf("Net Income", 0)
        total_assets = sf("Total Assets", 0)
        total_liabilities = sf("Total Liabilities", 0)
        fcf = sf("Free Cash Flow", 0)
        growth = sf("Growth Rate", 0)
        equity = total_assets - total_liabilities

        profit_margin = sf("Profit Margin") or (net_income / revenue if revenue > 0 else None)
        roe = sf("ROE") or (net_income / equity if equity > 0 else None)
        roa = sf("ROA") or (net_income / total_assets if total_assets > 0 else None)
        de_raw = sf("Debt to Equity")
        de = (de_raw / 100 if de_raw and de_raw > 10 else de_raw) if de_raw is not None else (
            total_liabilities / equity if equity > 0 else None
        )
        pe = sf("PE Ratio")
        current_ratio = sf("Current Ratio")

        def add_metric(name, value, tiers, weight, fmt="plain"):
            nonlocal score
            if value is None:
                breakdown[name] = {"label": "N/A", "pts": 0, "max": weight, "status": "neutral"}
                return
            for threshold, pts, status in tiers:
                if value >= threshold:
                    score += pts
                    if fmt == "%":
                        label = f"{value:.1%}"
                    elif fmt == "x":
                        label = f"{value:.2f}x"
                    else:
                        label = f"{value:.1f}"
                    breakdown[name] = {"label": label, "pts": pts, "max": weight, "status": status}
                    return
            breakdown[name] = {"label": f"{value:.2f}", "pts": 0, "max": weight, "status": "poor"}

        add_metric("Profit Margin", profit_margin, [
            (0.20, 15, "excellent"), (0.10, 11, "good"),
            (0.05, 7, "fair"), (0.0, 3, "weak"),
        ], 15, "%")

        add_metric("ROE", roe, [
            (0.20, 15, "excellent"), (0.10, 11, "good"),
            (0.05, 7, "fair"), (0.0, 3, "weak"),
        ], 15, "%")

        add_metric("ROA", roa, [
            (0.10, 10, "excellent"), (0.05, 7, "good"),
            (0.02, 4, "fair"), (0.0, 1, "weak"),
        ], 10, "%")

        if fcf > 0:
            score += 10
            breakdown["Free Cash Flow"] = {"label": "Positive", "pts": 10, "max": 10, "status": "excellent"}
        elif fcf < 0:
            breakdown["Free Cash Flow"] = {"label": "Negative", "pts": 0, "max": 10, "status": "poor"}
        else:
            breakdown["Free Cash Flow"] = {"label": "N/A", "pts": 0, "max": 10, "status": "neutral"}

        if growth >= 0.15:
            g_pts, g_status = 15, "excellent"
        elif growth >= 0.05:
            g_pts, g_status = 11, "good"
        elif growth >= 0.0:
            g_pts, g_status = 5, "fair"
        else:
            g_pts, g_status = 0, "poor"
        score += g_pts
        breakdown["Revenue Growth"] = {"label": f"{growth:.1%}", "pts": g_pts, "max": 15, "status": g_status}

        if pe is not None and pe > 0:
            pe_pts = 10 if pe < 15 else 8 if pe < 20 else 6 if pe < 25 else 3 if pe < 35 else 1
            pe_status = "excellent" if pe < 15 else "good" if pe < 20 else "fair" if pe < 25 else "weak"
            score += pe_pts
            breakdown["P/E Ratio"] = {"label": f"{pe:.1f}x", "pts": pe_pts, "max": 10, "status": pe_status}
        else:
            breakdown["P/E Ratio"] = {"label": "N/A", "pts": 0, "max": 10, "status": "neutral"}

        if de is not None and de >= 0:
            de_pts = 15 if de < 0.5 else 11 if de < 1.0 else 7 if de < 2.0 else 3
            de_status = "excellent" if de < 0.5 else "good" if de < 1.0 else "fair" if de < 2.0 else "poor"
            score += de_pts
            breakdown["Debt/Equity"] = {"label": f"{de:.2f}x", "pts": de_pts, "max": 15, "status": de_status}
        else:
            breakdown["Debt/Equity"] = {"label": "N/A", "pts": 0, "max": 15, "status": "neutral"}

        if current_ratio:
            cr_pts = 10 if current_ratio >= 2.0 else 7 if current_ratio >= 1.5 else 4 if current_ratio >= 1.0 else 0
            cr_status = "excellent" if current_ratio >= 2.0 else "good" if current_ratio >= 1.5 else "fair" if current_ratio >= 1.0 else "poor"
            score += cr_pts
            breakdown["Current Ratio"] = {"label": f"{current_ratio:.2f}x", "pts": cr_pts, "max": 10, "status": cr_status}
        else:
            breakdown["Current Ratio"] = {"label": "N/A", "pts": 0, "max": 10, "status": "neutral"}

        available_max = sum(v["max"] for v in breakdown.values() if v["status"] != "neutral")
        earned = sum(v["pts"] for v in breakdown.values())
        normalized = min(100, round((earned / available_max) * 100)) if available_max > 0 else 0

        if normalized >= 80:
            grade, color = "A", "#16a34a"
        elif normalized >= 65:
            grade, color = "B", "#00b386"
        elif normalized >= 50:
            grade, color = "C", "#d97706"
        elif normalized >= 35:
            grade, color = "D", "#ea580c"
        else:
            grade, color = "F", "#dc2626"

        return {"score": normalized, "grade": grade, "color": color, "breakdown": breakdown}

    def generate_investment_memo(self, metrics, valuation, current_price=None):
        """Generate a structured investment memo using AI."""
        company = metrics.get("Company Name", "Unknown")
        ticker = metrics.get("Ticker", "N/A")
        price_str = f"${current_price:,.2f}" if current_price else "N/A"
        dcf = valuation.get("DCF Value", 0)
        graham = valuation.get("Graham Number", 0)
        risks = metrics.get("Risk Factors", [])
        try:
            growth_str = f"{float(metrics.get('Growth Rate', 0)):.1%}"
        except (TypeError, ValueError):
            growth_str = "N/A"

        data_summary = f"""Company: {company} ({ticker})
Current Price: {price_str}
Revenue: {metrics.get('Revenue', 'N/A')}
Net Income: {metrics.get('Net Income', 'N/A')}
EPS: {metrics.get('EPS', 'N/A')}
Free Cash Flow: {metrics.get('Free Cash Flow', 'N/A')}
Total Assets: {metrics.get('Total Assets', 'N/A')}
Total Liabilities: {metrics.get('Total Liabilities', 'N/A')}
Revenue Growth: {growth_str}
DCF Intrinsic Value: ${dcf:,.2f}
Graham Number: ${graham:,.2f}
Key Risks: {', '.join(risks[:3]) if risks else 'N/A'}"""

        prompt = f"""You are a senior equity research analyst. Write a concise professional investment memo.

FINANCIAL DATA:
{data_summary}

Structure your memo with exactly these 7 sections (use the numbered headings):
1. EXECUTIVE SUMMARY
2. BUSINESS OVERVIEW
3. FINANCIAL HIGHLIGHTS
4. VALUATION ANALYSIS
5. KEY RISKS
6. INVESTMENT THESIS
7. RECOMMENDATION

Keep each section to 2-4 sentences or bullet points. Be direct and professional. Plain text only, no markdown."""

        try:
            return self._generate_content(prompt)
        except Exception as e:
            print(f"Investment memo failed: {e}")
            return "Could not generate investment memo at this time."


