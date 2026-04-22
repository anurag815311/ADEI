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
.main {background-color: #0f172a;}
.block-container {padding-top: 2rem;}
.metric-card {
    background: #1e293b;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
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