import os
import json
import time
import requests
import yfinance as yf
from google import genai


SECTOR_TICKERS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN"],
    "Semiconductors": ["NVDA", "AMD", "INTC", "TSM", "QCOM", "AVGO"],
    "EV & Clean Energy": ["TSLA", "RIVN", "NIO", "F", "GM", "LCID"],
    "Banking": ["JPM", "BAC", "WFC", "GS", "MS", "C"],
    "Energy": ["XOM", "CVX", "COP", "BP", "SHEL", "SLB"],
    "Healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK", "LLY"],
    "Retail & E-Commerce": ["AMZN", "WMT", "TGT", "COST", "HD", "BABA"],
    "Media & Telecom": ["NFLX", "DIS", "T", "VZ", "CMCSA", "SNAP"],
    "Indian Markets": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "WIPRO.NS"],
    "Aerospace & Defense": ["LMT", "RTX", "BA", "NOC", "GD"],
}

IMPACT_CATEGORIES = [
    "Earnings", "Guidance", "Regulation", "Lawsuit", "Product Launch",
    "Management Change", "M&A", "Macroeconomy", "Geopolitics",
    "Supply Chain", "Commodity Prices", "Other",
]

REGIONS = ["Global", "US", "Europe", "China", "India"]


class NewsRadarAnalyzer:
    def __init__(self, gemini_api_key):
        self.client = genai.Client(api_key=gemini_api_key)
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        self.marketaux_key = os.getenv("MARKETAUX_API_KEY", "")

    # ── Private fetchers ──────────────────────────────────────────────────

    def _yfinance_news(self, ticker, max_items=8):
        articles = []
        try:
            stock = yf.Ticker(ticker)
            for item in (stock.news or [])[:max_items]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title", "")
                if not title:
                    continue
                link = (
                    (content.get("canonicalUrl") or {}).get("url")
                    or (content.get("clickThroughUrl") or {}).get("url")
                    or item.get("link", "#")
                )
                publisher = (
                    (content.get("provider") or {}).get("displayName")
                    or item.get("publisher", "Unknown")
                )
                raw_ts = item.get("providerPublishTime", 0)
                pub_time = time.strftime("%b %d, %Y", time.gmtime(raw_ts)) if raw_ts else ""
                description = (content.get("summary") or "")[:400]
                articles.append({
                    "title": title, "url": link, "source": publisher,
                    "publishedAt": pub_time, "description": description,
                })
        except Exception as e:
            print(f"yfinance news error for {ticker}: {e}")
        return articles

    def _finnhub_news(self, ticker):
        if not self.finnhub_key:
            return []
        import datetime
        try:
            today = datetime.date.today()
            from_date = (today - datetime.timedelta(days=7)).isoformat()
            url = (
                f"https://finnhub.io/api/v1/company-news"
                f"?symbol={ticker}&from={from_date}&to={today.isoformat()}"
                f"&token={self.finnhub_key}"
            )
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200:
                return []
            articles = []
            for item in resp.json()[:8]:
                title = item.get("headline", "")
                if not title:
                    continue
                articles.append({
                    "title": title,
                    "url": item.get("url", "#"),
                    "source": item.get("source", "Finnhub"),
                    "publishedAt": time.strftime("%b %d, %Y", time.gmtime(item.get("datetime", 0))),
                    "description": (item.get("summary") or "")[:400],
                })
            return articles
        except Exception as e:
            print(f"Finnhub error: {e}")
            return []

    def _marketaux_news(self, query):
        if not self.marketaux_key:
            return []
        try:
            url = (
                f"https://api.marketaux.com/v1/news/all"
                f"?symbols={query}&filter_entities=true&language=en"
                f"&api_token={self.marketaux_key}"
            )
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200:
                return []
            articles = []
            for item in resp.json().get("data", [])[:8]:
                title = item.get("title", "")
                if not title:
                    continue
                articles.append({
                    "title": title,
                    "url": item.get("url", "#"),
                    "source": item.get("source", "Marketaux"),
                    "publishedAt": (item.get("published_at") or "")[:10],
                    "description": (item.get("description") or "")[:400],
                })
            return articles
        except Exception as e:
            print(f"Marketaux error: {e}")
            return []

    def _gdelt_news(self, query):
        """GDELT — completely free, no API key, very broad coverage."""
        import urllib.parse
        try:
            encoded = urllib.parse.quote(f"{query} stock market finance")
            url = (
                f"https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={encoded}&mode=artlist&maxrecords=10"
                f"&format=json&timespan=1week"
            )
            resp = requests.get(url, timeout=8)
            if resp.status_code != 200:
                return []
            data = resp.json()
            articles = []
            for item in (data.get("articles") or [])[:10]:
                title = item.get("title", "")
                if not title:
                    continue
                raw_date = item.get("seendate", "")
                pub = raw_date[:8] if len(raw_date) >= 8 else ""
                if pub:
                    try:
                        pub = f"{pub[4:6]}/{pub[6:8]}/{pub[:4]}"
                    except Exception:
                        pass
                articles.append({
                    "title": title,
                    "url": item.get("url", "#"),
                    "source": item.get("domain", "GDELT"),
                    "publishedAt": pub,
                    "description": "",
                })
            return articles
        except Exception as e:
            print(f"GDELT error: {e}")
            return []

    def _gemini_tickers_for_query(self, query):
        """Ask Gemini which tickers are most relevant for an unrecognized query."""
        prompt = (
            f'Return a JSON array of 5-6 major stock ticker symbols most relevant to "{query}". '
            'Example: ["NVDA","AMD","INTC"]. Return ONLY the raw JSON array, nothing else.'
        )
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                resp = self.client.models.generate_content(model=model, contents=prompt)
                data = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```")
                return json.loads(data)
            except Exception:
                continue
        return []

    def _gemini_news_fallback(self, query, query_type):
        """Generate news summaries from Gemini knowledge when APIs return nothing."""
        prompt = f"""You are a financial news analyst. Provide 7 recent significant news items about "{query}" ({'stock ticker' if query_type == 'ticker' else 'industry sector'}).

Base these on real recent events you know about. Be factual and specific.

Return ONLY a raw JSON array (no markdown) where each object has:
- title: the headline
- source: major outlet name (Reuters, Bloomberg, CNBC, WSJ, Financial Times, etc.)
- publishedAt: approximate recent date like "May 10, 2025"
- description: 2-sentence factual summary of the development"""

        for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
            try:
                resp = self.client.models.generate_content(model=model, contents=prompt)
                data = resp.text.strip()
                if data.startswith("```json"):
                    data = data[7:]
                elif data.startswith("```"):
                    data = data[3:]
                if data.endswith("```"):
                    data = data[:-3]
                articles = json.loads(data.strip())
                for a in articles:
                    a.setdefault("url", "#")
                    a["_ai_generated"] = True
                return articles
            except Exception as e:
                print(f"Gemini fallback {model} failed: {e}")
                continue
        return []

    # ── Public interface ──────────────────────────────────────────────────

    def _match_sector(self, query):
        """Case-insensitive + partial match for sector names."""
        q = query.lower().strip()
        # Exact match
        for key in SECTOR_TICKERS:
            if key.lower() == q:
                return key
        # Starts-with match
        for key in SECTOR_TICKERS:
            if key.lower().startswith(q) or q.startswith(key.lower().split()[0]):
                return key
        # Contains match
        for key in SECTOR_TICKERS:
            if q in key.lower() or key.lower().split()[0] in q:
                return key
        return None

    def fetch_news(self, query, query_type="ticker"):
        """Fetch and deduplicate news from all available sources with smart fallbacks."""
        raw_articles = []
        seen = set()

        def add(new_articles):
            for a in new_articles:
                t = a.get("title", "")
                if t and t not in seen:
                    seen.add(t)
                    raw_articles.append(a)

        if query_type == "ticker":
            add(self._yfinance_news(query))
            add(self._finnhub_news(query))
            add(self._marketaux_news(query))
            # GDELT for broader coverage
            if len(raw_articles) < 5:
                add(self._gdelt_news(query))

        else:  # sector search
            matched = self._match_sector(query)
            tickers = SECTOR_TICKERS.get(matched, []) if matched else []

            # If no known sector, ask Gemini for relevant tickers
            if not tickers:
                tickers = self._gemini_tickers_for_query(query)

            for tk in tickers[:5]:
                add(self._yfinance_news(tk, max_items=4))

            add(self._marketaux_news(query))

            # GDELT with the sector query
            if len(raw_articles) < 5:
                add(self._gdelt_news(matched or query))

        # Last resort: use Gemini knowledge base to generate news
        if len(raw_articles) < 3:
            add(self._gemini_news_fallback(query, query_type))

        return raw_articles[:15]

    def classify_with_ai(self, articles, query, query_type):
        """Batch-classify all articles with Gemini: sentiment, category, urgency, impact."""
        if not articles:
            return []

        context_tickers = SECTOR_TICKERS.get(query, [query]) if query_type == "sector" else [query]

        articles_text = "\n\n".join([
            f"[{i+1}] Title: {a['title']}\n"
            f"    Source: {a.get('source','')}\n"
            f"    Description: {(a.get('description') or '')[:250]}"
            for i, a in enumerate(articles)
        ])

        prompt = f"""You are a senior market research analyst. Analyze these {len(articles)} news articles about "{query}" ({query_type}).

Context tickers: {context_tickers}

For EACH article provide exactly:
- sentiment: "positive" | "negative" | "neutral" | "mixed"
- impact_category: one of {json.dumps(IMPACT_CATEGORIES)}
- urgency: "low" | "medium" | "high"
- summary: 1-2 sentence plain-English summary
- reason: 1-2 sentence explanation of the sentiment assignment
- possible_impact: 1-2 sentence explanation of potential market impact
- affected_tickers: array of relevant ticker symbols (include relevant ones from {context_tickers[:4]})
- sector: primary sector (e.g. "Semiconductors", "Technology", "Banking")
- region: "US" | "Europe" | "China" | "India" | "Global"

ARTICLES:
{articles_text}

Return ONLY a raw JSON array of exactly {len(articles)} objects in the same order. No markdown, no code fences."""

        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
            try:
                response = self.client.models.generate_content(model=model_name, contents=prompt)
                data = response.text.strip()
                if data.startswith("```json"):
                    data = data[7:]
                elif data.startswith("```"):
                    data = data[3:]
                if data.endswith("```"):
                    data = data[:-3]
                classifications = json.loads(data.strip())
                result = []
                for i, art in enumerate(articles):
                    cls = classifications[i] if i < len(classifications) else {}
                    result.append({**art, **cls})
                return result
            except Exception as e:
                print(f"Classification {model_name} failed: {e}")
                continue

        return [{
            **a,
            "sentiment": "neutral", "urgency": "low",
            "impact_category": "Other",
            "reason": "AI classification unavailable.",
            "possible_impact": "", "affected_tickers": [],
            "sector": "", "region": "Global",
            "summary": a.get("title", ""),
        } for a in articles]

    def generate_summary(self, classified_articles, query):
        """Overall sentiment, counts, AI 'what changed today' summary, and top-3 urgent."""
        if not classified_articles:
            return {
                "overall": "No Data", "counts": {},
                "summary": "No recent news found.", "top3": [],
            }

        sentiments = [a.get("sentiment", "neutral") for a in classified_articles]
        counts = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral"),
            "mixed": sentiments.count("mixed"),
        }

        pos, neg = counts["positive"], counts["negative"]
        if pos > neg * 1.5 and pos > 1:
            overall = "Positive"
        elif neg > pos * 1.5 and neg > 1:
            overall = "Negative"
        elif pos > 0 and neg > 0:
            overall = "Mixed"
        else:
            overall = "Neutral"

        urgency_rank = {"high": 3, "medium": 2, "low": 1}
        top3 = sorted(
            classified_articles,
            key=lambda x: urgency_rank.get(x.get("urgency", "low"), 1),
            reverse=True,
        )[:3]

        headlines = "\n".join([f"- {a['title']}" for a in classified_articles[:8]])
        summary_prompt = (
            f"Summarize in 2-3 sentences what is happening today for {query} "
            f"based on these news headlines. Be specific about key developments. "
            f"Write as if briefing a portfolio manager.\n\nHeadlines:\n{headlines}\n\n"
            "Return only the summary text, no labels or preamble."
        )

        ai_summary = f"Recent news shows {overall.lower()} sentiment for {query}."
        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                response = self.client.models.generate_content(model=model_name, contents=summary_prompt)
                ai_summary = response.text.strip()
                break
            except Exception:
                continue

        return {
            "overall": overall,
            "counts": counts,
            "summary": ai_summary,
            "top3": top3,
        }
