"""
Pepper Bowl — Daily Pinterest & SEO Trend Reporter
Run: python3 daily_trends.py
Opens: reports/YYYY-MM-DD.html in your browser
"""

import os
import webbrowser
from datetime import datetime
from pytrends.request import TrendReq
import time
import random

# ── Niche Configuration ──────────────────────────────────────────────────────
SITE = "pepperbowl.com"
DA = 36
NICHE_KEYWORDS = [
    "jalapeno recipes",
    "cajun recipes",
    "spicy recipes",
    "hot honey recipe",
    "cajun shrimp",
    "jalapeno sauce",
    "spicy dip",
    "cajun seasoning",
]

SEED_TOPICS = [
    "jalapeno",
    "cajun food",
    "spicy food",
    "hot honey",
    "pepper sauce",
]

REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")

# ── Seasonal Fallback Data ────────────────────────────────────────────────────
def _seasonal_fallback() -> dict:
    """Curated niche trends when Google Trends API is rate-limited."""
    month = datetime.now().month
    # Spring/Summer (Apr–Aug)
    if 4 <= month <= 8:
        rising = [
            {"query": "jalapeno hot honey sauce", "value": 5000},
            {"query": "spicy watermelon jalapeno salad", "value": 4200},
            {"query": "cajun shrimp tacos spicy slaw", "value": 3800},
            {"query": "jalapeno smashed potatoes crispy", "value": 3500},
            {"query": "cajun crawfish etouffee easy", "value": 3200},
            {"query": "spicy grilled jalapeno poppers", "value": 2900},
            {"query": "cajun corn on the cob butter", "value": 2700},
            {"query": "hot honey jalapeno chicken wings", "value": 2500},
        ]
        top = [
            {"query": "cajun shrimp recipe", "value": 100},
            {"query": "spicy jalapeno dip", "value": 95},
            {"query": "easy cajun seasoning", "value": 90},
            {"query": "jalapeno sauce recipe", "value": 88},
            {"query": "cajun chicken breast recipe", "value": 85},
            {"query": "spicy salsa recipe jalapeno", "value": 80},
            {"query": "cajun butter sauce", "value": 76},
            {"query": "hot honey recipe easy", "value": 72},
        ]
        interest = {
            "jalapeno recipes": 82,
            "cajun recipes": 75,
            "spicy recipes": 88,
            "hot honey recipe": 91,
            "cajun shrimp": 79,
        }
        trending_us = [
            "grilled chicken recipes", "summer salad", "easy BBQ sides",
            "Cinco de Mayo recipes", "Memorial Day food ideas",
        ]
    # Fall/Winter (Sep–Mar)
    else:
        rising = [
            {"query": "cajun turkey brine spicy", "value": 5000},
            {"query": "jalapeno cheddar cornbread", "value": 4200},
            {"query": "spicy cajun gumbo easy", "value": 3800},
            {"query": "cajun chicken stew weeknight", "value": 3500},
            {"query": "jalapeno hot chocolate recipe", "value": 3200},
            {"query": "spicy chili jalapeno topping", "value": 2900},
            {"query": "cajun meatballs gravy", "value": 2700},
            {"query": "easy jalapeno soup recipe", "value": 2500},
        ]
        top = [
            {"query": "cajun chicken recipe easy", "value": 100},
            {"query": "spicy jalapeno sauce", "value": 95},
            {"query": "cajun seasoning recipe homemade", "value": 90},
            {"query": "jalapeno dip cream cheese", "value": 88},
            {"query": "cajun shrimp pasta", "value": 85},
            {"query": "spicy soup recipe", "value": 80},
            {"query": "cajun turkey seasoning", "value": 76},
            {"query": "jalapeno popper recipe", "value": 72},
        ]
        interest = {
            "jalapeno recipes": 78,
            "cajun recipes": 85,
            "spicy recipes": 80,
            "hot honey recipe": 70,
            "cajun shrimp": 72,
        }
        trending_us = [
            "Thanksgiving recipes", "holiday appetizers", "easy weeknight dinner",
            "comfort food recipes", "soup season recipes",
        ]

    return {
        "interest_7d": interest,
        "related": {
            "jalapeno recipes": {"rising": rising[:4], "top": top[:4]},
            "cajun recipes": {"rising": rising[4:], "top": top[4:]},
            "spicy recipes": {"rising": [], "top": []},
            "hot honey recipe": {"rising": [], "top": []},
        },
        "trending_us": trending_us,
        "source": "fallback",
    }


# ── Google Trends Fetcher ─────────────────────────────────────────────────────
def _try_pytrends_with_backoff(fn, retries=3):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait = (2 ** attempt) * 10 + random.uniform(1, 5)
                print(f"  Rate limited — waiting {wait:.0f}s before retry {attempt+2}/{retries}...")
                time.sleep(wait)
            else:
                raise


def fetch_trends():
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    results = {"source": "live"}
    api_failures = 0

    print("Fetching interest over time...")
    try:
        def _interest():
            pytrends.build_payload(NICHE_KEYWORDS[:5], cat=71, timeframe="now 7-d", geo="US")
            return pytrends.interest_over_time()
        interest = _try_pytrends_with_backoff(_interest)
        if not interest.empty:
            latest = interest.iloc[-1].drop("isPartial", errors="ignore")
            results["interest_7d"] = latest.to_dict()
        else:
            results["interest_7d"] = {}
        time.sleep(random.uniform(4, 7))
    except Exception as e:
        print(f"  Skipping interest data: {e}")
        results["interest_7d"] = {}
        api_failures += 1

    print("Fetching related queries...")
    related = {}
    for kw in NICHE_KEYWORDS[:4]:
        try:
            def _related(k=kw):
                pytrends.build_payload([k], cat=71, timeframe="today 1-m", geo="US")
                return pytrends.related_queries()
            rq = _try_pytrends_with_backoff(_related)
            rising = rq.get(kw, {}).get("rising")
            top = rq.get(kw, {}).get("top")
            related[kw] = {
                "rising": rising.head(5).to_dict("records") if rising is not None else [],
                "top": top.head(5).to_dict("records") if top is not None else [],
            }
            time.sleep(random.uniform(5, 9))
        except Exception as e:
            print(f"  Skipping related queries for '{kw}': {e}")
            related[kw] = {"rising": [], "top": []}
            api_failures += 1

    results["related"] = related

    print("Fetching trending searches...")
    try:
        def _trending():
            return pytrends.trending_searches(pn="united_states")
        trending = _try_pytrends_with_backoff(_trending)
        results["trending_us"] = trending[0].head(20).tolist()
    except Exception as e:
        print(f"  Skipping trending searches: {e}")
        results["trending_us"] = []
        api_failures += 1

    # If most API calls failed, use seasonal fallback data
    if api_failures >= 3:
        print("\n  ⚠️  Google Trends rate-limited — using curated seasonal data instead.")
        fallback = _seasonal_fallback()
        results["interest_7d"] = results["interest_7d"] or fallback["interest_7d"]
        for kw, val in results["related"].items():
            if not val["rising"] and not val["top"]:
                results["related"][kw] = fallback["related"].get(kw, {"rising": [], "top": []})
        results["trending_us"] = results["trending_us"] or fallback["trending_us"]
        results["source"] = "fallback"

    return results


# ── Opportunity Scorer ────────────────────────────────────────────────────────
def score_opportunity(query: str, volume_score: int) -> dict:
    """Score a keyword opportunity based on DA 36 and trend signal."""
    query_lower = query.lower()
    niche_match = any(
        term in query_lower
        for term in ["jalapeno", "cajun", "spicy", "pepper", "hot honey", "chili", "sauce", "dip"]
    )
    # Simple heuristic: shorter + niche-specific = lower competition
    word_count = len(query.split())
    long_tail = word_count >= 3
    competition = "Low" if long_tail and niche_match else ("Medium" if long_tail or niche_match else "High")
    feasible = competition in ("Low", "Medium") and DA >= 30

    return {
        "query": query,
        "volume_score": volume_score,
        "competition": competition,
        "niche_match": niche_match,
        "feasible": feasible,
        "pinterest_angle": _pinterest_angle(query),
    }


def _pinterest_angle(query: str) -> str:
    q = query.lower()
    if "sauce" in q or "dip" in q:
        return "Drizzle/pour shot over dish — high save rate"
    if "shrimp" in q or "chicken" in q:
        return "Close-up plated shot with garnish"
    if "salad" in q:
        return "Overhead colorful flat-lay"
    if "taco" in q or "wrap" in q:
        return "Cross-section cut shot showing filling"
    if "soup" in q or "stew" in q:
        return "Steam rising, rustic bowl shot"
    if "potato" in q or "fries" in q:
        return "Crispy overhead with dipping sauce"
    return "Step-by-step collage or hero dish shot"


# ── Report Generator ──────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pepper Bowl Trends — {date}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #fdf6f0; color: #2d2d2d; }}
  header {{ background: linear-gradient(135deg, #c0392b, #e74c3c);
            color: white; padding: 24px 32px; }}
  header h1 {{ font-size: 1.6rem; }}
  header p {{ opacity: 0.85; font-size: 0.9rem; margin-top: 4px; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-top: 20px; }}
  .card {{ background: white; border-radius: 12px; padding: 20px;
           box-shadow: 0 2px 8px rgba(0,0,0,0.07); }}
  .card h2 {{ font-size: 1rem; font-weight: 700; color: #c0392b;
              border-bottom: 2px solid #fde8e8; padding-bottom: 8px; margin-bottom: 14px; }}
  .kw-row {{ display: flex; justify-content: space-between; align-items: center;
             padding: 8px 0; border-bottom: 1px solid #f5f5f5; }}
  .kw-row:last-child {{ border: none; }}
  .kw-name {{ font-size: 0.88rem; font-weight: 500; flex: 1; }}
  .badge {{ font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 20px; margin-left: 6px; }}
  .low {{ background: #d4edda; color: #155724; }}
  .medium {{ background: #fff3cd; color: #856404; }}
  .high {{ background: #f8d7da; color: #721c24; }}
  .feasible {{ background: #d1ecf1; color: #0c5460; }}
  .score-bar {{ height: 6px; background: #f0f0f0; border-radius: 3px; width: 60px; margin-left: 8px; }}
  .score-fill {{ height: 100%; background: #e74c3c; border-radius: 3px; }}
  .pinterest-tip {{ font-size: 0.75rem; color: #888; margin-top: 3px; }}
  .trend-chip {{ display: inline-block; background: #fde8e8; color: #c0392b;
                 border-radius: 20px; padding: 4px 12px; font-size: 0.8rem;
                 margin: 4px 4px 0 0; }}
  .section-label {{ font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.05em; color: #999; margin: 12px 0 6px; }}
  .summary-stat {{ text-align: center; padding: 12px; }}
  .summary-stat .num {{ font-size: 2rem; font-weight: 800; color: #c0392b; }}
  .summary-stat .label {{ font-size: 0.78rem; color: #888; margin-top: 2px; }}
  .stats-row {{ display: flex; gap: 0; border-bottom: 1px solid #f5f5f5; }}
  .stats-row:last-child {{ border: none; }}
</style>
</head>
<body>
<header>
  <h1>🌶 Pepper Bowl — Daily Trend Report</h1>
  <p>{site} &nbsp;|&nbsp; DA {da} &nbsp;|&nbsp; {date} &nbsp;|&nbsp; Jalapeño · Cajun · Spicy American &nbsp;|&nbsp; <span style="opacity:0.75">{data_source}</span></p>
</header>
<div class="container">

  <div class="grid" style="grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 8px;">
    <div class="card summary-stat"><div class="num">{total_opportunities}</div><div class="label">Low/Med Opportunities</div></div>
    <div class="card summary-stat"><div class="num">{niche_hits}</div><div class="label">Niche-Matched Keywords</div></div>
    <div class="card summary-stat"><div class="num">{rising_count}</div><div class="label">Rising Queries Found</div></div>
    <div class="card summary-stat"><div class="num">{top_trend}</div><div class="label">Top Trend Score</div></div>
  </div>

  <div class="grid">

    <!-- Rising Queries -->
    <div class="card">
      <h2>🔥 Rising Queries This Month</h2>
      <p style="font-size:0.78rem;color:#888;margin-bottom:10px;">Breakout searches in your niche — act fast</p>
      {rising_html}
    </div>

    <!-- Top Queries -->
    <div class="card">
      <h2>📈 Top Stable Keywords</h2>
      <p style="font-size:0.78rem;color:#888;margin-bottom:10px;">High-volume, consistent search demand</p>
      {top_html}
    </div>

    <!-- 7-Day Interest -->
    <div class="card">
      <h2>📊 7-Day Interest Scores</h2>
      <p style="font-size:0.78rem;color:#888;margin-bottom:10px;">Google Trends interest (0–100) this week</p>
      {interest_html}
    </div>

    <!-- Trending US -->
    <div class="card">
      <h2>🇺🇸 US Trending Searches Today</h2>
      <p style="font-size:0.78rem;color:#888;margin-bottom:10px;">Filter for food/recipe crossover opportunities</p>
      {trending_html}
    </div>

  </div>

  <!-- Pinterest Strategy -->
  <div class="card" style="margin-top:20px;">
    <h2>📌 Pinterest Pin Strategy — This Week</h2>
    <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0; margin-top: 0;">
      {pin_strategy_html}
    </div>
  </div>

</div>
</body>
</html>"""


def build_report(data: dict) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")
    today = datetime.now().strftime("%Y-%m-%d")

    # Rising queries
    all_rising = []
    for kw, qdata in data["related"].items():
        for item in qdata["rising"]:
            scored = score_opportunity(item["query"], item.get("value", 0))
            scored["source_kw"] = kw
            all_rising.append(scored)
    all_rising.sort(key=lambda x: (x["feasible"], x["niche_match"]), reverse=True)

    rising_html = ""
    for item in all_rising[:8]:
        comp_class = item["competition"].lower()
        rising_html += f"""
        <div class="kw-row">
          <div style="flex:1">
            <div class="kw-name">{item['query']}</div>
            <div class="pinterest-tip">{item['pinterest_angle']}</div>
          </div>
          <span class="badge {comp_class}">{item['competition']}</span>
          {'<span class="badge feasible">✓ Publish</span>' if item['feasible'] else ''}
        </div>"""

    if not rising_html:
        rising_html = "<p style='color:#888;font-size:0.85rem;padding:10px 0'>No rising queries found — try again later.</p>"

    # Top queries
    all_top = []
    for kw, qdata in data["related"].items():
        for item in qdata["top"]:
            scored = score_opportunity(item["query"], item.get("value", 0))
            scored["source_kw"] = kw
            all_top.append(scored)

    top_html = ""
    for item in all_top[:8]:
        comp_class = item["competition"].lower()
        fill_width = min(100, item.get("volume_score", 50))
        top_html += f"""
        <div class="kw-row">
          <div style="flex:1">
            <div class="kw-name">{item['query']}</div>
            <div class="pinterest-tip">{item['pinterest_angle']}</div>
          </div>
          <div class="score-bar"><div class="score-fill" style="width:{fill_width}%"></div></div>
          <span class="badge {comp_class}">{item['competition']}</span>
        </div>"""

    if not top_html:
        top_html = "<p style='color:#888;font-size:0.85rem;padding:10px 0'>No top queries found.</p>"

    # 7-day interest
    interest_html = ""
    for kw, score in sorted(data.get("interest_7d", {}).items(), key=lambda x: x[1], reverse=True):
        fill = min(100, int(score))
        interest_html += f"""
        <div class="kw-row">
          <div class="kw-name">{kw}</div>
          <div class="score-bar"><div class="score-fill" style="width:{fill}%"></div></div>
          <span style="font-size:0.8rem;font-weight:700;color:#c0392b;margin-left:8px">{int(score)}</span>
        </div>"""

    if not interest_html:
        interest_html = "<p style='color:#888;font-size:0.85rem;padding:10px 0'>No interest data available.</p>"

    # US Trending
    trending_html = ""
    food_terms = ["recipe", "food", "cook", "eat", "chicken", "shrimp", "salad",
                  "soup", "sauce", "taco", "potato", "pepper", "spicy", "cajun"]
    food_trending = [t for t in data.get("trending_us", [])
                     if any(f in t.lower() for f in food_terms)]
    other_trending = [t for t in data.get("trending_us", []) if t not in food_trending]

    if food_trending:
        trending_html += '<div class="section-label">Food/Recipe Related</div>'
        for t in food_trending[:5]:
            trending_html += f'<span class="trend-chip">🍴 {t}</span>'

    if other_trending[:10]:
        trending_html += '<div class="section-label" style="margin-top:12px">General Trending (crossover check)</div>'
        for t in other_trending[:10]:
            trending_html += f'<span class="trend-chip">{t}</span>'

    if not trending_html:
        trending_html = "<p style='color:#888;font-size:0.85rem;padding:10px 0'>No trending data available.</p>"

    # Pin strategy from rising + top opportunities
    best = [i for i in (all_rising + all_top) if i["feasible"] and i["niche_match"]][:5]
    if not best:
        best = (all_rising + all_top)[:5]

    pin_strategy_html = ""
    for i, item in enumerate(best, 1):
        pin_strategy_html += f"""
        <div style="padding:14px;border-right:1px solid #f5f5f5;">
          <div style="font-size:0.72rem;color:#e74c3c;font-weight:700;text-transform:uppercase">Pin #{i}</div>
          <div style="font-weight:600;margin:4px 0;font-size:0.9rem">{item['query'].title()}</div>
          <div style="font-size:0.78rem;color:#555">📸 {item['pinterest_angle']}</div>
          <div style="font-size:0.75rem;color:#888;margin-top:4px">Source: {item.get('source_kw','—')}</div>
        </div>"""

    if not pin_strategy_html:
        pin_strategy_html = "<p style='color:#888;padding:12px'>No pin recommendations today.</p>"

    # Stats
    total_opp = len([i for i in (all_rising + all_top) if i["feasible"]])
    niche_hits = len([i for i in (all_rising + all_top) if i["niche_match"]])
    rising_count = len(all_rising)
    top_score = max((v for v in data.get("interest_7d", {}).values()), default=0)

    source_label = "📡 Live Google Trends" if data.get("source") != "fallback" else "📋 Curated Seasonal Data"

    html = HTML_TEMPLATE.format(
        date=date_str,
        site=SITE,
        da=DA,
        data_source=source_label,
        total_opportunities=total_opp,
        niche_hits=niche_hits,
        rising_count=rising_count,
        top_trend=int(top_score),
        rising_html=rising_html,
        top_html=top_html,
        interest_html=interest_html,
        trending_html=trending_html,
        pin_strategy_html=pin_strategy_html,
    )

    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, f"{today}.html")
    with open(report_path, "w") as f:
        f.write(html)

    return report_path


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🌶  Pepper Bowl Daily Trend Reporter")
    print(f"    Site: {SITE}  |  DA: {DA}")
    print(f"    Date: {datetime.now().strftime('%B %d, %Y')}\n")

    print("Fetching Google Trends data (this takes ~30 seconds)...")
    data = fetch_trends()

    print("Building HTML report...")
    path = build_report(data)

    print(f"\n✅ Report saved: {path}")
    print("Opening in browser...\n")
    webbrowser.open(f"file://{path}")
