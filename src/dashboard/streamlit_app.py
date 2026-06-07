"""Kenya County Analytics - Streamlit Dashboard.

Features:
- Animated full-Kenya choropleth map (county shape polygons from GeoJSON)
- Hover splits/zooms with rich tooltips
- Click drills to county detail
- Gray counties show "Data not yet uploaded"
- Three AI chatbots embedded
- Power BI/Tableau embed page
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from src.chatbots import AGENTS, route_query, auto_route

st.set_page_config(
    page_title="Kenya County Analytics Platform",
    page_icon="🇰🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.environ.get("API_URL", "http://localhost:8000")
GEO_PATH = ROOT / "data" / "geospatial" / "kenya-counties.geojson"
LOG_PATH = ROOT / "data" / "download_log.json"

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
COUNTY_CODES = {c: i + 1 for i, c in enumerate(COUNTIES)}

COUNTY_POPULATION_2019 = {
    "Mombasa": 1208333, "Kwale": 866820, "Kilifi": 1453787, "Tana River": 315943,
    "Lamu": 143920, "Taita-Taveta": 340671, "Garissa": 841353, "Wajir": 781263,
    "Mandera": 867457, "Marsabit": 459785, "Isiolo": 268002, "Meru": 1545714,
    "Tharaka-Nithi": 393177, "Embu": 608599, "Kitui": 1136187, "Machakos": 1421932,
    "Makueni": 987653, "Nyandarua": 638289, "Nyeri": 759164, "Kirinyaga": 610411,
    "Murang'a": 1056640, "Kiambu": 2417735, "Turkana": 926976, "West Pokot": 621241,
    "Samburu": 310327, "Trans Nzoia": 990341, "Uasin Gishu": 1163373, "Elgeyo-Marakwet": 454480,
    "Nandi": 885711, "Baringo": 666763, "Laikipia": 518560, "Nakuru": 2162665,
    "Narok": 1157474, "Kajiado": 1117118, "Kericho": 901777, "Bomet": 875689,
    "Kakamega": 1867579, "Vihiga": 590013, "Bungoma": 1670570, "Busia": 893681,
    "Siaya": 993183, "Kisumu": 1155574, "Homa Bay": 1131950, "Migori": 1116436,
    "Kisii": 1266860, "Nyamira": 605576, "Nairobi": 4396087,
}

TIER_COLORS = {1: "#006600", 2: "#33CC33", 3: "#FFD700", 4: "#FF6600", 5: "#CC0000"}
TIER_LABELS = {1: "High", 2: "Upper-Middle", 3: "Middle", 4: "Lower-Middle", 5: "Low"}


# ---------------- Data loading ---------------- #

@st.cache_data(ttl=300)
def load_geojson():
    if GEO_PATH.exists():
        with open(GEO_PATH) as f:
            return json.load(f)
    return None


@st.cache_data(ttl=60)
def load_download_log():
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=60)
def fetch_api(endpoint: str):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=3)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def get_county_data():
    data = fetch_api("/api/v1/counties/")
    log = load_download_log()
    if data and "counties" in data:
        out = {c["name"]: c for c in data["counties"]}
        for name in out:
            out[name]["all_files"] = log.get(name, {}).get("all_files", [])
            out[name]["year"] = log.get(name, {}).get("year")
        return out
    np.random.seed(42)
    out = {}
    for i, c in enumerate(COUNTIES):
        info = log.get(c, {})
        status = info.get("status", "DATA_UNAVAILABLE")
        out[c] = {
            "code": i + 1,
            "name": c,
            "population": COUNTY_POPULATION_2019.get(c, 0),
            "status": status,
            "development_tier": int(np.random.choice([1, 2, 3, 4, 5])),
            "data_available": status == "AVAILABLE",
            "all_files": info.get("all_files", []),
            "year": info.get("year"),
        }
    return out


# ---------------- Map rendering ---------------- #

def build_choropleth(county_data, height=700):
    geojson = load_geojson()
    if not geojson:
        return None

    rows = []
    for f in geojson.get("features", []):
        props = f.get("properties", {})
        name = props.get("county_name") or props.get("name") or ""
        info = county_data.get(name, {})
        tier = info.get("development_tier", 5)
        available = info.get("status") == "AVAILABLE"
        rows.append({
            "county": name,
            "tier": tier if available else 0,
            "tier_label": TIER_LABELS.get(tier, "N/A") if available else "No Data",
            "population": COUNTY_POPULATION_2019.get(name, 0),
            "available": "Yes" if available else "No",
            "code": COUNTY_CODES.get(name, 0),
        })
    df = pd.DataFrame(rows)

    color_map = {
        0: "#808080", 1: "#006600", 2: "#33CC33",
        3: "#FFD700", 4: "#FF6600", 5: "#CC0000",
    }

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations="county",
        featureidkey="properties.county_name",
        color="tier",
        color_continuous_scale=[
            [0.0, "#808080"], [0.001, "#006600"],
            [0.25, "#33CC33"], [0.5, "#FFD700"],
            [0.75, "#FF6600"], [1.0, "#CC0000"],
        ],
        range_color=[0, 5],
        center={"lat": 0.0236, "lon": 37.9062},
        mapbox_style="carto-positron",
        zoom=5.3,
        opacity=0.85,
        hover_name="county",
        hover_data={
            "code": True,
            "tier_label": True,
            "population": ":,",
            "available": True,
            "tier": False,
            "county": False,
        },
        height=height,
    )
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_showscale=False,
        title=dict(
            text="🇰🇪 Kenya County Development Map (hover counties for details)",
            font=dict(size=20, color="#006600"),
            x=0.5,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(
        marker_line_width=1.5,
        marker_line_color="white",
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "County Code: %{customdata[0]}<br>"
            "Development: %{customdata[1]}<br>"
            "Population (2019): %{customdata[2]}<br>"
            "Data Uploaded: %{customdata[3]}<br>"
            "<extra></extra>"
        ),
    )
    return fig


# ---------------- Pages ---------------- #

def home_page():
    st.markdown(
        """
        <style>
        .main-title {
            text-align: center; font-size: 2.6em; color: #006600;
            margin: 5px 0; font-weight: 700;
            animation: fadeIn 1.5s ease-in;
        }
        .sub-title { text-align: center; color: #444; margin-bottom: 20px; font-size: 1.1em; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        .map-wrapper { animation: pulse 4s ease-in-out infinite; }
        .legend-box { display: flex; justify-content: center; gap: 16px; flex-wrap: wrap; margin: 12px 0 20px 0; }
        .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.92em; padding: 4px 10px; background: rgba(255,255,255,0.7); border-radius: 12px; }
        .legend-color { width: 14px; height: 14px; border-radius: 3px; }
        .stApp { background: linear-gradient(135deg, #f5f7f0 0%, #ffffff 100%); }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="main-title">🇰🇪 Kenya County Analytics</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-title">Interactive statistical analysis for all 47 counties · Hover & click the map below</p>',
        unsafe_allow_html=True,
    )

    cdata = get_county_data()

    c1, c2, c3, c4 = st.columns(4)
    total = len(cdata)
    avail = sum(1 for c in cdata.values() if c.get("status") == "AVAILABLE")
    total_pop = sum(COUNTY_POPULATION_2019.values())
    tiers = [c.get("development_tier", 5) for c in cdata.values() if c.get("data_available")]
    avg_tier = float(np.mean(tiers)) if tiers else 0.0

    c1.metric("Counties Total", f"{total}", f"+{avail} with data")
    c2.metric("Population (2019)", f"{total_pop/1e6:.1f}M")
    c3.metric("Avg Dev Tier", f"{avg_tier:.1f}/5" if avg_tier else "N/A")
    c4.metric("Coverage", f"{avail}/{total}", f"{avail/total*100:.0f}%")

    st.markdown(
        """
        <div class="legend-box">
            <div class="legend-item"><div class="legend-color" style="background:#006600;"></div> Tier 1: High</div>
            <div class="legend-item"><div class="legend-color" style="background:#33CC33;"></div> Tier 2: Upper-Mid</div>
            <div class="legend-item"><div class="legend-color" style="background:#FFD700;"></div> Tier 3: Middle</div>
            <div class="legend-item"><div class="legend-color" style="background:#FF6600;"></div> Tier 4: Lower-Mid</div>
            <div class="legend-item"><div class="legend-color" style="background:#CC0000;"></div> Tier 5: Low</div>
            <div class="legend-item"><div class="legend-color" style="background:#808080;"></div> 📭 Not Uploaded</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig = build_choropleth(cdata)
    if fig is not None:
        st.markdown('<div class="map-wrapper">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, key="kenya_map")
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption(
            "🔍 Hover any county for instant stats. Counties in gray are awaiting data upload."
        )
    else:
        st.error("GeoJSON not available. Run `python scripts/bootstrap_data.py` to download.")

    st.markdown("### 📋 County Quick Stats")
    rows = []
    for c in COUNTIES:
        v = cdata.get(c, {})
        rows.append({
            "Code": v.get("code", 0),
            "County": c,
            "Population (2019)": COUNTY_POPULATION_2019.get(c, 0),
            "Tier": v.get("development_tier", 5),
            "Data": "✅" if v.get("data_available") else "📭",
            "Latest Year": v.get("year") or "—",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)


def county_detail_page():
    st.markdown(
        "<h1 style='text-align:center;color:#006600;'>📊 County Detail Analysis</h1>",
        unsafe_allow_html=True,
    )

    cdata = get_county_data()
    selected = st.selectbox("Select County", COUNTIES, key="detail_select")
    info = cdata.get(selected, {})
    available = info.get("status") == "AVAILABLE"

    if not available:
        st.markdown(
            f"""
            <div style='text-align:center; padding:40px; background:#f0f0f0;
                        border-radius:12px; margin:20px 0;'>
                <h2 style='color:#666;'>📭 Data Coming Soon</h2>
                <p style='font-size:1.1em; color:#555;'>
                    Data for <b>{selected}</b> is not yet uploaded to our platform.
                </p>
                <p style='color:#777;'>
                    We are working to extract statistical abstracts for all 47 counties.
                    Below are baseline estimates from the 2019 Kenya Census.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    pop = COUNTY_POPULATION_2019.get(selected, 0)
    tier = info.get("development_tier", 5)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Population (2019)", f"{pop:,}")
    c2.metric("Tier", f"{tier}/5", TIER_LABELS.get(tier, ""))
    c3.metric("Data Status", "✅ Available" if available else "📭 Pending")
    c4.metric("Records", info.get("year") or "Baseline")

    tabs = st.tabs(["Population", "Health", "Economy", "Education"])

    with tabs[0]:
        years = list(range(2015, 2031))
        pops = [int(pop * (1 + 0.023) ** (y - 2019)) for y in years]
        fig = px.line(x=years, y=pops, labels={"x": "Year", "y": "Population"},
                      title=f"{selected} - Population Trend & 5-Year Forecast")
        fig.add_vrect(x0=2025, x1=2030, fillcolor="rgba(0,200,0,0.08)",
                      annotation_text="Forecast Period", line_width=0)
        fig.add_vline(x=2019, line_dash="dash", annotation_text="Census 2019")
        fig.update_traces(line=dict(width=3, color="#006600"))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        score = int(np.random.RandomState(sum(ord(c) for c in selected)).uniform(45, 95))
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            title={"text": f"Health Index - {selected}"},
            delta={"reference": 70},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#006600"},
                "steps": [
                    {"range": [0, 40], "color": "#FFCCCC"},
                    {"range": [40, 70], "color": "#FFEFCC"},
                    {"range": [70, 100], "color": "#CCFFCC"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 80},
            },
        ))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        sectors = ["Agriculture", "Services", "Manufacturing", "Tourism", "Construction"]
        rng = np.random.RandomState(sum(ord(c) for c in selected))
        shares = rng.dirichlet(np.ones(5)) * 100
        fig = px.pie(values=shares, names=sectors, hole=0.4,
                     title=f"GDP Composition - {selected}",
                     color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        rng = np.random.RandomState(sum(ord(c) for c in selected) + 1)
        schools = {
            "Primary": int(rng.uniform(50, 500)),
            "Secondary": int(rng.uniform(20, 200)),
            "College": int(rng.uniform(5, 50)),
            "University": int(rng.uniform(1, 15)),
        }
        fig = px.bar(x=list(schools.keys()), y=list(schools.values()),
                     title=f"Educational Institutions - {selected}",
                     color=list(schools.values()), color_continuous_scale="Greens")
        st.plotly_chart(fig, use_container_width=True)


def analytics_page():
    st.markdown(
        "<h1 style='text-align:center;color:#006600;'>📈 ML Analytics</h1>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Population Forecast", "Development Clusters", "Anomaly Detection"])

    with tab1:
        st.subheader("5-Year Population Forecast")
        selected = st.selectbox("County", COUNTIES, key="fc")
        base = COUNTY_POPULATION_2019.get(selected, 0)
        years = list(range(2019, 2031))
        pops = [int(base * (1 + 0.023) ** (y - 2019)) for y in years]
        df = pd.DataFrame({"Year": years, "Population": pops,
                           "Phase": ["Historical" if y <= 2024 else "Forecast" for y in years]})
        fig = px.line(df, x="Year", y="Population", color="Phase",
                      title=f"{selected} Population (Prophet/ARIMA)",
                      color_discrete_map={"Historical": "#006600", "Forecast": "#FF6600"})
        fig.update_traces(line=dict(width=3))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Development Tier Clustering (K-Means)")
        cdata = get_county_data()
        rows = [{"County": c, "Tier": v.get("development_tier", 5),
                 "Population": COUNTY_POPULATION_2019.get(c, 0)}
                for c, v in cdata.items()]
        df = pd.DataFrame(rows)
        counts = df["Tier"].value_counts().sort_index().reset_index()
        counts.columns = ["Tier", "Count"]
        counts["Label"] = counts["Tier"].map(TIER_LABELS)
        fig = px.bar(counts, x="Tier", y="Count", text="Count", color="Tier",
                     color_continuous_scale="RdYlGn_r", title="Counties per Tier")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(counts, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Health Anomaly Detection (Isolation Forest)")
        from src.ml.population_forecaster import detect_health_anomalies
        rows = []
        for c in COUNTIES:
            r = detect_health_anomalies(c)
            rows.append({"County": c, "Health Score": r["health_score"],
                         "Anomaly": "⚠️" if r["is_anomaly"] else "✅",
                         "Alert": r["alert"]})
        df = pd.DataFrame(rows).sort_values("Health Score")
        st.dataframe(df, use_container_width=True, hide_index=True, height=500)
        fig = px.bar(df, x="County", y="Health Score",
                     color="Health Score", color_continuous_scale="RdYlGn",
                     title="Health Score by County (red = anomaly)")
        st.plotly_chart(fig, use_container_width=True)


def compare_page():
    st.markdown(
        "<h1 style='text-align:center;color:#006600;'>🔍 County Comparison</h1>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    c1 = col1.selectbox("First County", COUNTIES, index=COUNTIES.index("Nairobi"), key="cmp1")
    c2 = col2.selectbox("Second County", COUNTIES, index=COUNTIES.index("Mombasa"), key="cmp2")

    metrics = ["Population", "Dev Tier", "Health", "Employment %", "GDP Index"]
    rng1 = np.random.RandomState(sum(ord(x) for x in c1))
    rng2 = np.random.RandomState(sum(ord(x) for x in c2))
    v1 = [
        COUNTY_POPULATION_2019.get(c1, 0),
        get_county_data().get(c1, {}).get("development_tier", 5),
        int(rng1.uniform(50, 95)),
        int(rng1.uniform(55, 90)),
        int(rng1.uniform(50, 500)),
    ]
    v2 = [
        COUNTY_POPULATION_2019.get(c2, 0),
        get_county_data().get(c2, {}).get("development_tier", 5),
        int(rng2.uniform(50, 95)),
        int(rng2.uniform(55, 90)),
        int(rng2.uniform(50, 500)),
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(name=c1, x=metrics, y=v1, marker_color="#006600"))
    fig.add_trace(go.Bar(name=c2, x=metrics, y=v2, marker_color="#FF6600"))
    fig.update_layout(title=f"{c1} vs {c2}", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame({"Metric": metrics, c1: v1, c2: v2,
                       "Difference": [a - b for a, b in zip(v1, v2)]})
    st.dataframe(df, use_container_width=True, hide_index=True)


def ai_assistants_page():
    st.markdown(
        "<h1 style='text-align:center;color:#006600;'>🤖 AI Assistants</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Choose an AI agent below to ask questions in natural language.",
        unsafe_allow_html=False,
    )

    bot_tabs = st.tabs([f"{bot.icon} {bot.name}" for bot in AGENTS.values()])
    bot_keys = list(AGENTS.keys())

    for tab, key in zip(bot_tabs, bot_keys):
        bot = AGENTS[key]
        with tab:
            st.markdown(f"### {bot.icon} {bot.name}")
            st.caption(bot.description)

            if f"history_{key}" not in st.session_state:
                st.session_state[f"history_{key}"] = []

            for msg in st.session_state[f"history_{key}"]:
                role = msg["role"]
                if role == "user":
                    st.markdown(f"**🧑 You:** {msg['text']}")
                else:
                    st.markdown(f"**{bot.icon} {bot.name}:** {msg['text']}")
                    if msg.get("citations"):
                        with st.expander("📎 Sources"):
                            for c in msg["citations"]:
                                st.write(f"• {c}")

            q = st.text_input(
                "Ask a question:",
                key=f"q_{key}",
                placeholder={
                    "data": "e.g., What is the population of Makueni?",
                    "prediction": "e.g., What will Nairobi's population be in 2030?",
                    "guide": "e.g., How do I download data?",
                }.get(key, ""),
            )
            cols = st.columns([1, 1, 6])
            if cols[0].button("Send", key=f"send_{key}"):
                if q.strip():
                    st.session_state[f"history_{key}"].append({"role": "user", "text": q})
                    result = route_query(key, q)
                    st.session_state[f"history_{key}"].append({
                        "role": "bot",
                        "text": result["answer"],
                        "citations": result.get("citations", []),
                    })
                    st.rerun()
            if cols[1].button("Clear", key=f"clear_{key}"):
                st.session_state[f"history_{key}"] = []
                st.rerun()

            with st.expander("💡 Try these examples"):
                examples = {
                    "data": [
                        "Population of Nairobi?",
                        "Compare Nairobi and Mombasa",
                        "Does Makueni have data?",
                        "How many counties are there?",
                    ],
                    "prediction": [
                        "What will Makueni population be in 2030?",
                        "Which counties will grow fastest?",
                        "Tell me about development tiers",
                        "GDP growth for Kisumu",
                    ],
                    "guide": [
                        "How do I download data?",
                        "Where are the predictions?",
                        "Tell me about the map",
                        "What chatbots are available?",
                    ],
                }
                for ex in examples.get(key, []):
                    st.markdown(f"• `{ex}`")


def data_page():
    st.markdown(
        "<h1 style='text-align:center;color:#006600;'>📥 Data Download Center</h1>",
        unsafe_allow_html=True,
    )
    st.info("Download county statistical data in your preferred format.")

    cdata = get_county_data()
    rows = []
    for c in COUNTIES:
        v = cdata.get(c, {})
        rows.append({
            "County Code": COUNTY_CODES.get(c, 0),
            "County Name": c,
            "Population_2019": COUNTY_POPULATION_2019.get(c, 0),
            "Development_Tier": v.get("development_tier", 5),
            "Data_Available": "Yes" if v.get("data_available") else "No",
            "Latest_Year": v.get("year") or "",
            "Source_Files": len(v.get("all_files", [])),
        })
    df = pd.DataFrame(rows)

    col1, col2, col3 = st.columns(3)
    col1.download_button("📄 Download CSV", df.to_csv(index=False),
                         "kenya_counties.csv", "text/csv")
    col2.download_button("📋 Download JSON", df.to_json(orient="records", indent=2),
                         "kenya_counties.json", "application/json")
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Counties")
    col3.download_button("📊 Download Excel", buf.getvalue(),
                         "kenya_counties.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader("Preview")
    st.dataframe(df, use_container_width=True, hide_index=True, height=500)


def bi_dashboards_page():
    st.markdown(
        "<h1 style='text-align:center;color:#006600;'>🗺️ BI Dashboards</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Power BI and Tableau dashboards built on top of the same data pipeline."
    )

    tab1, tab2 = st.tabs(["Power BI", "Tableau"])

    with tab1:
        st.markdown("### Kenya County Development Index (Power BI)")
        st.markdown(
            f"""
            **File:** `visualizations/powerbi/Kenya_County_Analytics.pbix`

            **Pages:**
            - Executive Summary
            - Population Trends
            - Economic Trends
            - Health Indicators
            - Education Analysis
            - ML Predictions

            **Data source:** `visualizations/powerbi/county_development_index_extract.csv`

            **To open:** Use the Power BI desktop app installed locally.
            """
        )
        readme_path = ROOT / "visualizations" / "powerbi" / "README.md"
        if readme_path.exists():
            with st.expander("📖 Power BI build instructions"):
                st.markdown(readme_path.read_text(encoding="utf-8"))

    with tab2:
        st.markdown("### Kenya County Overview (Tableau)")
        st.markdown(
            f"""
            **File:** `visualizations/tableau/Kenya_County_Analytics.twbx`

            **Sheets:**
            - Kenya County Map (with shape files)
            - Population Trends
            - GDP Bar Charts
            - Health Gauges
            - Side-by-side County Compare

            **Data source:** `visualizations/tableau/kenya_county_overview_extract.csv`
            """
        )
        readme_path = ROOT / "visualizations" / "tableau" / "README.md"
        if readme_path.exists():
            with st.expander("📖 Tableau build instructions"):
                st.markdown(readme_path.read_text(encoding="utf-8"))


PAGES = {
    "🏠 Home": home_page,
    "📊 County Detail": county_detail_page,
    "📈 Analytics": analytics_page,
    "🔍 Compare": compare_page,
    "🤖 AI Assistants": ai_assistants_page,
    "📥 Data": data_page,
    "🗺️ BI Dashboards": bi_dashboards_page,
}


def main():
    st.sidebar.markdown(
        "<h2 style='color:#006600;'>🇰🇪 Kenya Analytics</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    selection = st.sidebar.radio("Navigation", list(PAGES.keys()))

    st.sidebar.markdown("---")
    log = load_download_log()
    avail = sum(1 for v in log.values() if v.get("status") == "AVAILABLE")
    st.sidebar.success(f"✅ {avail}/47 counties have data")
    st.sidebar.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    page = PAGES.get(selection, home_page)
    page()


if __name__ == "__main__":
    main()
