import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

# 🔥 FIXED API URL (production + local)
API_URL = os.getenv("API_URL") or f"http://localhost:{os.getenv('API_PORT', 8000)}"

# --- UI CONFIG ---
st.set_page_config(
    page_title="Job Market Intelligence Pro",
    page_icon="🚀",
    layout="wide"
)

# --- STYLING ---
st.markdown("""
<style>

/* -------- GLOBAL -------- */
body {
    font-family: 'Inter', sans-serif;
}

/* -------- MAIN BACKGROUND -------- */
.main {
    background-color: #f5f7fb;
}

/* -------- TITLE -------- */
h1 {
    font-weight: 700;
    letter-spacing: -0.5px;
}

/* -------- METRIC CARDS -------- */
.stMetric {
    background: #ffffff;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    transition: all 0.2s ease-in-out;
}

.stMetric:hover {
    transform: translateY(-2px);
}

/* -------- SIDEBAR -------- */
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

/* -------- INPUT FIELDS -------- */
input, textarea {
    border-radius: 8px !important;
    border: 1px solid #d1d5db !important;
}

/* -------- SELECT BOX -------- */
div[data-baseweb="select"] {
    border-radius: 8px;
}

/* -------- RADIO -------- */
div[role="radiogroup"] > label {
    padding: 6px 8px;
    border-radius: 6px;
}

/* -------- BUTTON -------- */
.stButton > button {
    background: #2563eb;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #1d4ed8;
    transform: scale(1.02);
}

/* -------- DATAFRAME -------- */
[data-testid="stDataFrame"] {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}

/* -------- TABS -------- */
button[role="tab"] {
    font-weight: 500;
}

button[aria-selected="true"] {
    border-bottom: 2px solid #2563eb !important;
}

/* -------- ALERT BOX -------- */
.stAlert {
    border-radius: 10px;
}

/* -------- DIVIDER -------- */
hr {
    border: none;
    border-top: 1px solid #e5e7eb;
}

</style>
""", unsafe_allow_html=True)

# --- HELPERS ---
@st.cache_data(ttl=300)
def fetch(endpoint, params=None):
    try:
        res = requests.get(f"{API_URL}/{endpoint}", params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except:
        return None

# --- SIDEBAR ---
st.sidebar.title("🔎 Filters")

search = st.sidebar.text_input("Search Jobs")
source = st.sidebar.selectbox("Source", ["All", "arbeitnow", "remotive"])
remote = st.sidebar.radio("Work Type", ["All", "Remote", "On-site"])

if st.sidebar.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

# --- MAIN ---
st.title("🚀 Job Market Intelligence Pro")
st.caption("Real-time B2B hiring intelligence dashboard")

# --- FETCH DATA ---
params = {}
if source != "All":
    params["source"] = source
if remote == "Remote":
    params["remote"] = True
elif remote == "On-site":
    params["remote"] = False

data = fetch("data", params)

if data:
    df = pd.DataFrame(data)

    # --- FILTER ---
    if search:
        df = df[df["title"].str.contains(search, case=False) | 
                df["company"].str.contains(search, case=False)]

    # --- METRICS ---
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Jobs", len(df))
    col2.metric("Companies", df["company"].nunique())

    remote_pct = (df["remote"].sum() / len(df)) * 100 if len(df) else 0
    col3.metric("Remote %", f"{remote_pct:.1f}%")

    col4.metric("Sources", df["source"].nunique())

    st.divider()

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📈 Trends", "🛠 Skills", "🌍 Locations"])

    # --- TRENDS ---
    with tab1:
        trends = fetch("trends")
        if trends:
            tdf = pd.DataFrame(trends)
            fig = px.area(tdf, x="day", y="count", title="Job Trends")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data")

    # --- SKILLS ---
    with tab2:
        skills = fetch("top-skills", {"limit": 30})
        if skills:
            sdf = pd.DataFrame(skills)
            sdf = sdf[sdf["count"] > 1].head(10)

            if not sdf.empty:
                fig = px.bar(
                    sdf.sort_values("count"),
                    x="count",
                    y="skill",
                    orientation="h",
                    title="Top Skills",
                    color="count"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough skill data yet")
        else:
            st.info("Skill data unavailable")

    # --- LOCATIONS ---
    with tab3:
        insights = fetch("insights")
        if insights and "top_locations" in insights:
            loc_df = pd.DataFrame(
                list(insights["top_locations"].items()),
                columns=["Location", "Jobs"]
            )
            fig = px.pie(loc_df, values="Jobs", names="Location")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No location data")

    st.divider()

    # --- TABLE ---
    st.subheader("📋 Job Listings")
    st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ No data found")

    # 🔥 IMPROVED SCRAPE BUTTON
    if st.button("🚀 Run Initial Scrape"):
        with st.spinner("Running pipeline..."):
            res = fetch("run-scrape")
            if res:
                st.success("✅ Pipeline started! Refresh in 20–30 sec")
            else:
                st.error("❌ Failed to trigger pipeline")

st.caption("Sources: Arbeitnow • Remotive")