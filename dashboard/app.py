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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* -------- GLOBAL -------- */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* -------- MAIN BACKGROUND -------- */
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }

    /* -------- METRIC CARDS -------- */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
    }
    
    .stMetric {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stMetric:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }

    /* -------- TABS -------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0px;
        color: #64748b;
        font-weight: 600;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
    }

    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 2px solid #2563eb !important;
    }

    /* -------- BUTTONS -------- */
    .stButton > button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 8px 15px rgba(37, 99, 235, 0.3);
        transform: translateY(-1px);
    }

    /* -------- DATAFRAME -------- */
    [data-testid="stDataFrame"] {
        padding: 10px;
        background: white;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
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
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("Market Filters")
    st.markdown("Customize your intelligence view.")
    
    search = st.text_input("🔍 Search Keyword", placeholder="e.g. Senior, Python")
    source = st.selectbox("🌐 Provider", ["All", "arbeitnow", "remotive"])
    remote = st.radio("🏠 Work Mode", ["All", "Remote", "On-site"], horizontal=True)
    
    st.markdown("---")
    if st.button("🔄 Sync Live Data"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN ---
st.title("🚀 Tech Hiring Intelligence")
st.markdown("##### Enterprise B2B Dashboard for Real-time Market Signals")

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
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Active Roles", len(df))
    m2.metric("Key Players", df["company"].nunique())
    
    remote_pct = (df["remote"].sum() / len(df)) * 100 if len(df) else 0
    m3.metric("Remote Volume", f"{remote_pct:.1f}%")
    
    m4.metric("Market Sources", df["source"].nunique())

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ANALYTICS ---
    st.subheader("📊 Deep Dive Analysis")
    tab1, tab2, tab3 = st.tabs(["📈 Demand Trends", "🛠 Tech Stack Heatmap", "🌍 Hiring Hubs"])

    with tab1:
        trends = fetch("trends")
        if trends:
            tdf = pd.DataFrame(trends)
            fig = px.area(tdf, x="day", y="count", 
                         title="Daily Hiring Momentum",
                         color_discrete_sequence=['#3b82f6'],
                         template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Trend analysis pending data accumulation.")

    with tab2:
        skills = fetch("top-skills", {"limit": 30})
        if skills:
            sdf = pd.DataFrame(skills)
            sdf = sdf[sdf["count"] > 1].head(12)

            if not sdf.empty:
                fig = px.bar(
                    sdf.sort_values("count"),
                    x="count",
                    y="skill",
                    orientation="h",
                    title="Top Technical Skills in Demand",
                    color="count",
                    color_continuous_scale='Blues',
                    template="plotly_white"
                )
                fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=450)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient skill signals detected.")
        else:
            st.info("Intelligence service busy...")

    with tab3:
        insights = fetch("insights")
        if insights and "top_locations" in insights:
            loc_df = pd.DataFrame(
                list(insights["top_locations"].items()),
                columns=["Location", "Jobs"]
            )
            fig = px.pie(loc_df, values="Jobs", names="Location",
                        title="Geographic Talent Centers",
                        hole=0.6,
                        color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=450)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Mapping location hotspots...")

    # --- LISTINGS ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Intelligence Feed")
    
    # Custom Table Configuration
    st.dataframe(
        df[["title", "company", "location", "remote", "posted_at", "url"]].sort_values("posted_at", ascending=False),
        column_config={
            "title": "Position Title",
            "company": "Organization",
            "location": "HQ / Region",
            "remote": st.column_config.CheckboxColumn("Remote?"),
            "posted_at": st.column_config.DateColumn("Intelligence Date"),
            "url": st.column_config.LinkColumn("Deep Link")
        },
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("⚠️ No intelligence signals found for current filters.")

    if st.button("🚀 Execute Global Market Sync"):
        with st.spinner("Synchronizing with global job boards..."):
            try:
                # IMPORTANT: We use requests.get directly here because this is an ACTION, not a fetch.
                # We do NOT want to cache this call.
                res = requests.get(f"{API_URL}/run-scrape", timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("status") == "success":
                        st.success(f"✅ {data.get('message', 'Sync successful!')}")
                        st.info("The feed will update automatically in about 30-60 seconds.")
                    else:
                        st.error(f"❌ Server reported an error: {data.get('message')}")
                else:
                    st.error(f"❌ Failed to reach API (Status: {res.status_code})")
            except Exception as e:
                st.error(f"❌ Synchronization interrupted: {str(e)}")

st.divider()
st.caption("Powered by Tech Hiring Intelligence Engine • Sources: Arbeitnow, Remotive")