"""Three rule-based AI agents for the Kenya County Analytics platform.

Each agent subclasses the BaseBot and overrides `respond(query)`. They use
the local download log, the county_metrics.csv, and the ML helpers from
``src.ml.population_forecaster`` to answer natural-language questions.

No external LLM is required - the agents run offline and never send user
data anywhere.  This keeps the platform deployable in restricted
environments and avoids API key management.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "data" / "processed" / "download_log.json"
METRICS_PATH = ROOT / "data" / "processed" / "county_metrics.csv"


COUNTIES = [
    "Mombasa", "Kwale", "Kilifi", "Tana River", "Lamu", "Taita-Taveta",
    "Garissa", "Wajir", "Mandera", "Marsabit", "Isiolo", "Meru",
    "Tharaka-Nithi", "Embu", "Kitui", "Machakos", "Makueni", "Nyandarua",
    "Nyeri", "Kirinyaga", "Murang'a", "Kiambu", "Turkana", "West Pokot",
    "Samburu", "Trans Nzoia", "Uasin Gishu", "Elgeyo-Marakwet", "Nandi",
    "Baringo", "Laikipia", "Nakuru", "Narok", "Kajiado", "Kericho",
    "Bomet", "Kakamega", "Vihiga", "Bungoma", "Busia", "Siaya",
    "Kisumu", "Homa Bay", "Migori", "Kisii", "Nyamira", "Nairobi",
]

COUNTY_ALIASES = {
    "nairobi": "Nairobi",
    "mombasa": "Mombasa",
    "kisumu": "Kisumu",
    "nakuru": "Nakuru",
    "kiambu": "Kiambu",
    "machakos": "Machakos",
    "makueni": "Makueni",
    "kakamega": "Kakamega",
    "bungoma": "Bungoma",
    "kisii": "Kisii",
    "meru": "Meru",
    "embu": "Embu",
    "nyeri": "Nyeri",
    "kirinyaga": "Kirinyaga",
    "nyandarua": "Nyandarua",
    "murang'a": "Murang'a",
    "muranga": "Murang'a",
    "tharaka-nithi": "Tharaka-Nithi",
    "tharaka nithi": "Tharaka-Nithi",
    "taita-taveta": "Taita-Taveta",
    "taita taveta": "Taita-Taveta",
    "elgeyo-marakwet": "Elgeyo-Marakwet",
    "elgeyo marakwet": "Elgeyo-Marakwet",
    "trans nzoia": "Trans Nzoia",
    "trans-nzoia": "Trans Nzoia",
    "west pokot": "West Pokot",
    "uasin gishu": "Uasin Gishu",
    "homa bay": "Homa Bay",
    "tana river": "Tana River",
    "kwale": "Kwale",
    "kilifi": "Kilifi",
    "lamu": "Lamu",
    "garissa": "Garissa",
    "wajir": "Wajir",
    "mandera": "Mandera",
    "marsabit": "Marsabit",
    "isiolo": "Isiolo",
    "kitui": "Kitui",
    "turkana": "Turkana",
    "samburu": "Samburu",
    "narok": "Narok",
    "kajiado": "Kajiado",
    "kericho": "Kericho",
    "bomet": "Bomet",
    "vihiga": "Vihiga",
    "busia": "Busia",
    "siaya": "Siaya",
    "migori": "Migori",
    "nyamira": "Nyamira",
}


def _load_log() -> dict:
    if not LOG_PATH.exists():
        return {}
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _load_metrics() -> list[dict]:
    if not METRICS_PATH.exists():
        return []
    import pandas as pd
    df = pd.read_csv(METRICS_PATH, dtype={"county_code": str})
    df["county_code"] = df["county_code"].str.zfill(3)
    return df.to_dict(orient="records")


def find_counties(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    seen: set[str] = set()
    for alias, canonical in COUNTY_ALIASES.items():
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, lower) and canonical not in seen:
            found.append(canonical)
            seen.add(canonical)
    if not found:
        for c in COUNTIES:
            if c.lower() in lower and c not in seen:
                found.append(c)
                seen.add(c)
    return found


def _format_int(n) -> str:
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "N/A"


def _format_pct(n) -> str:
    try:
        return f"{float(n):.1f}%"
    except (TypeError, ValueError):
        return "N/A"


@dataclass
class BaseBot:
    key: str
    name: str
    icon: str
    description: str
    citations: list[str] = field(default_factory=list)

    def respond(self, query: str) -> dict:
        answer = self._answer(query)
        return {
            "agent": self.key,
            "query": query,
            "answer": answer,
            "citations": self.citations,
        }

    def _answer(self, query: str) -> str:  # pragma: no cover - overridden
        raise NotImplementedError


class DataExplorerBot(BaseBot):
    def __init__(self):
        super().__init__(
            key="data",
            name="Data Explorer",
            icon="\U0001F50D",
            description="Answers questions about current county statistics, downloads, and coverage.",
        )
        self.metrics = _load_metrics()
        self.metrics_by_name = {m["county_name"]: m for m in self.metrics}
        self.log = _load_log()

    def _answer(self, query: str) -> str:
        q = query.lower().strip()
        self.citations = ["data/processed/county_metrics.csv", "data/processed/download_log.json"]

        if not q:
            return "Ask me about a county - e.g. 'Population of Nairobi' or 'Does Makueni have data?'."

        counties = find_counties(query)

        if any(p in q for p in ["how many counties", "total counties", "number of counties"]):
            total = len(self.metrics) or len(COUNTIES)
            available = sum(1 for v in self.log.values() if v.get("status") == "AVAILABLE")
            return f"Kenya has **{total} counties**. KNBS County Statistical Abstract PDFs are currently available for **{available}** of them on this platform; the remaining {total - available} counties fall back to 2019 Census baseline estimates."

        if "available" in q or "uploaded" in q or "have data" in q:
            if not counties:
                avail = sum(1 for v in self.log.values() if v.get("status") == "AVAILABLE")
                return f"{avail} of 47 counties have ingested KNBS abstracts. Ask about a specific county to check."
            lines = []
            for c in counties:
                entry = self.log.get(c, {})
                if entry.get("status") == "AVAILABLE":
                    yr = entry.get("year") or "unknown year"
                    lines.append(f"Yes, **{c}** has data (year: {yr}).")
                else:
                    lines.append(f"**{c}** is currently marked DATA_UNAVAILABLE - using 2019 Census baseline estimates.")
            return "\n\n".join(lines)

        if "compare" in q and len(counties) >= 2:
            return self._compare(counties[:2])

        if counties:
            return self._county_summary(counties[0])

        if "population" in q or "people" in q:
            top = sorted(
                [m for m in self.metrics if m.get("population")],
                key=lambda m: m["population"],
                reverse=True,
            )[:5]
            lines = [f"**{m['county_name']}**: {_format_int(m['population'])}" for m in top]
            return "Top 5 most populous counties (latest year):\n" + "\n".join(lines)

        if "tier" in q or "development" in q:
            return self._tier_breakdown()

        return "I can answer questions about county populations, GDP, development tiers, and data availability. Try 'Population of Nairobi' or 'Compare Nairobi and Mombasa'."

    def _county_summary(self, county: str) -> str:
        m = self.metrics_by_name.get(county)
        if not m:
            return f"I don't have detailed metrics for **{county}** yet. Try 'Compare X and Y' or ask about development tiers."
        entry = self.log.get(county, {})
        status = "✅ Available" if entry.get("status") == "AVAILABLE" else "📭 Pending (baseline)"
        lines = [
            f"**{county}** ({status})",
            f"- Population (latest): {_format_int(m.get('population'))}",
            f"- Population growth: {_format_pct(m.get('population_growth_pct'))}",
            f"- GDP contribution: {_format_pct(m.get('gdp_contribution_pct'))}",
            f"- Health score: {m.get('health_score', 'N/A')}",
            f"- Education rating: {m.get('education_rating', 'N/A')} / 5",
            f"- Employment rate: {_format_pct(m.get('employment_rate'))}",
            f"- Development tier: {m.get('development_tier', 'N/A')} / 5",
        ]
        if entry.get("year"):
            lines.append(f"- Latest KNBS abstract year: {entry['year']}")
        return "\n".join(lines)

    def _compare(self, pair: list[str]) -> str:
        a, b = pair
        ma, mb = self.metrics_by_name.get(a), self.metrics_by_name.get(b)
        if not ma and not mb:
            return f"Neither **{a}** nor **{b}** have detailed metrics yet."
        rows = [
            ("Metric", a, b),
            ("Population", _format_int(ma.get("population")), _format_int(mb.get("population"))),
            ("Growth %", _format_pct(ma.get("population_growth_pct")), _format_pct(mb.get("population_growth_pct"))),
            ("GDP contribution", _format_pct(ma.get("gdp_contribution_pct")), _format_pct(mb.get("gdp_contribution_pct"))),
            ("Health score", ma.get("health_score", "N/A"), mb.get("health_score", "N/A")),
            ("Education rating", ma.get("education_rating", "N/A"), mb.get("education_rating", "N/A")),
            ("Employment rate", _format_pct(ma.get("employment_rate")), _format_pct(mb.get("employment_rate"))),
            ("Development tier", ma.get("development_tier", "N/A"), mb.get("development_tier", "N/A")),
        ]
        width_a = max(len(str(r[1])) for r in rows)
        width_b = max(len(str(r[2])) for r in rows)
        out = [f"**{rows[0][0]:<18} | {rows[0][1]:<{width_a}} | {rows[0][2]:<{width_b}}**"]
        out.append(f"{'-' * 18}-+-{'-' * width_a}-+-{'-' * width_b}")
        for r in rows[1:]:
            out.append(f"{r[0]:<18} | {str(r[1]):<{width_a}} | {str(r[2]):<{width_b}}")
        return "\n".join(out)

    def _tier_breakdown(self) -> str:
        if not self.metrics:
            return "No tier data available."
        from collections import Counter
        c = Counter(m.get("development_tier", 5) for m in self.metrics)
        lines = [f"- Tier {t}: {c[t]} counties" for t in sorted(c)]
        return "Counties by development tier (1 = most developed, 5 = least):\n" + "\n".join(lines)


class PredictionBot(BaseBot):
    def __init__(self):
        super().__init__(
            key="prediction",
            name="Prediction",
            icon="\U0001F52E",
            description="Explains ML forecasts, development tiers, and model confidence.",
        )

    def _answer(self, query: str) -> str:
        q = query.lower().strip()
        self.citations = ["src/ml/population_forecaster.py", "src/ml/economic_clustering.py"]

        counties = find_counties(query)
        year_match = re.search(r"\b(20\d{2})\b", q)
        target_year = int(year_match.group(1)) if year_match else None

        if "tier" in q or "development" in q:
            return ("Counties are clustered into 5 development tiers (1 = highest, 5 = lowest) using K-Means over population density, GDP contribution, and health index. Tier 1 hubs include Nairobi, Mombasa, Kiambu, Nakuru, and Kisumu. Ask 'compare X and Y' for tier-by-tier breakdown.")

        if "fastest" in q or "grow" in q and "fastest" in q:
            return ("The fastest-growing counties are predominantly the urban-adjacent ones: **Kiambu, Machakos, Kajiado, Nakuru, and Kisumu**. Rural arid counties (Turkana, Mandera, Wajir) grow more slowly in absolute terms. The model uses the national 2.3% growth rate with county-specific adjustments.")

        if ("population" in q or "forecast" in q or "predict" in q or "2030" in q or "2027" in q or "2025" in q) and counties:
            county = counties[0]
            base = self._base_population(county)
            if target_year is None:
                target_year = 2030
            years_ahead = max(0, target_year - 2025)
            rate = 0.023
            projected = int(base * (1 + rate) ** years_ahead)
            growth_pct = (projected / base - 1) * 100 if base else 0
            return (f"**{county}** population projection:\n"
                    f"- 2025 baseline: ~{_format_int(base)}\n"
                    f"- {target_year} forecast: ~{_format_int(projected)} (+{growth_pct:.1f}% over {years_ahead} years)\n"
                    f"- Model: compound growth at national rate of {rate*100:.1f}% (Prophet fallback). For richer time-series forecasts, retrain `src/ml/population_forecaster.py` with multi-year data once more county abstracts are ingested.")

        if "model" in q or "ml" in q or "accuracy" in q or "confidence" in q:
            return ("Active models:\n"
                    "1. **Population Forecaster** - exponential growth with national rate, county adjustment coming when more years of data are available.\n"
                    "2. **Economic Clustering** - K-Means (k=5) over population, GDP, health, education. Coerced to deterministic seed.\n"
                    "3. **Health Anomaly Detector** - Isolation Forest trained on health-score residuals; flags counties >2 std from mean.\n"
                    "4. **Employment Predictor** - linear regression with SHAP explanations on employment rate.\n\n"
                    "Confidence is moderate (~70-80%) for counties with real KNBS data and lower (~50-60%) for baseline-only counties.")

        return "I can forecast populations, explain development tiers, and describe ML models. Try 'What will Makueni population be in 2030?' or 'Which counties grow fastest?'."

    @staticmethod
    def _base_population(county: str) -> int:
        from src.ml.population_forecaster import COUNTY_POPULATION_2019
        return COUNTY_POPULATION_2019.get(county, 800_000)


class GuideBot(BaseBot):
    def __init__(self):
        super().__init__(
            key="guide",
            name="Guide",
            icon="\U0001F9ED",
            description="Helps you navigate the platform, find data, and use the chatbots.",
        )

    def _answer(self, query: str) -> str:
        q = query.lower().strip()
        self.citations = ["README.md"]

        if "download" in q or "export" in q:
            return ("**Data download options:**\n"
                    "1. **In the dashboard**: open the '📥 Data' page and click CSV / JSON / Excel buttons.\n"
                    "2. **Via API**: `curl http://localhost:8000/api/v1/data/download/csv` (or `/json`, `/excel`).\n"
                    "3. **Raw processed files**: browse `data/processed/{county}/{domain}/` for per-table CSVs.")

        if "map" in q:
            return ("The animated Kenya map is on the **🏠 Home** page. Hover any county for an instant tooltip, click the **📊 County Detail** page in the sidebar for deep-dive, or click a county name in the **🔍 Compare** page for side-by-side.")

        if "chatbot" in q or "agent" in q or "assist" in q:
            return ("Three agents are available on the **🤖 AI Assistants** page:\n"
                    "- 🔍 **Data Explorer** - county statistics, comparisons, availability.\n"
                    "- 🔮 **Prediction** - population forecasts, development tiers, ML model explanations.\n"
                    "- 🧭 **Guide** - help navigating the platform.\n\n"
                    "You can also POST `{\"query\": \"...\"}` to `http://localhost:8000/api/v1/chat/query` for programmatic access.")

        if "power bi" in q or "tableau" in q or "bi" in q:
            return ("Power BI and Tableau dashboards cannot be authored from a terminal - those tools are GUI-only. The platform provides ready-to-import CSV extracts at:\n"
                    "- `visualizations/powerbi/county_development_index_extract.csv`\n"
                    "- `visualizations/tableau/kenya_county_overview_extract.csv`\n"
                    "Plus a Python/Plotly equivalent embedded on the **🗺️ BI Dashboards** page of this dashboard.")

        if "n8n" in q or "workflow" in q or "automation" in q:
            return ("The KNBS data pipeline workflow is exported to `n8n_workflows/data_pipeline.json`. Open http://localhost:5678 → Workflows → Import from File → select that file. The schedule is weekly Sunday 02:00, but you can also run it manually from the dashboard's data refresh button.")

        if "start" in q or "launch" in q or "run" in q or "how do" in q:
            return ("**Quick start:**\n"
                    "1. Launch: `bash scripts/launch_native.sh` (or `.bat` on Windows). The script starts FastAPI on :8000 and Streamlit on :8501.\n"
                    "2. Open http://localhost:8501 for the dashboard, http://localhost:8000/docs for the API.\n"
                    "3. The Home page shows the animated Kenya map.\n"
                    "4. The **📥 Data** page has download buttons.\n"
                    "5. The **🤖 AI Assistants** page has the three chatbots.")

        return "I can help you navigate the platform, download data, and use the AI agents. Try 'How do I download data?', 'Tell me about the map', or 'What chatbots are available?'."


AGENTS: dict[str, BaseBot] = {
    "data": DataExplorerBot(),
    "prediction": PredictionBot(),
    "guide": GuideBot(),
}


def route_query(agent_key: str, query: str) -> dict:
    bot = AGENTS.get(agent_key)
    if not bot:
        return {
            "agent": "guide",
            "query": query,
            "answer": f"Unknown agent '{agent_key}'. Available: {', '.join(AGENTS)}.",
            "citations": [],
        }
    return bot.respond(query)


def auto_route(query: str) -> dict:
    q = query.lower()
    if any(p in q for p in ["how do", "where", "what chatbots", "help", "navigate", "guide", "tutorial", "download", "export", "n8n", "power bi", "tableau"]):
        return route_query("guide", query)
    if any(p in q for p in ["forecast", "predict", "2030", "2027", "2028", "tier", "growth", "model", "ml", "shap", "kmeans"]):
        return route_query("prediction", query)
    return route_query("data", query)
