import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = f"http://localhost:{os.getenv('API_PORT', 8000)}"

# --- UI Configuration ---
st.set_page_config(
    page_title="Job Market Intelligence Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stHeader {
        font-family: 'Inter', sans-serif;
        color: #1e293b;
    }
    div[data-testid="stExpander"] {
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_data(ttl=300)
def fetch_data(source=None, remote=None, search=None):
    params = {}
    if source and source != "All":
        params["source"] = source
    if remote == "Remote":
        params["remote"] = True
    elif remote == "On-site":
        params["remote"] = False
    
    try:
        response = requests.get(f"{API_URL}/data", params=params)
        df = pd.DataFrame(response.json())
        if not df.empty and search:
            df = df[df['title'].str.contains(search, case=False) | df['company'].str.contains(search, case=False)]
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_insights():
    try:
        return requests.get(f"{API_URL}/insights").json()
    except:
        return {}

@st.cache_data(ttl=300)
def fetch_trends():
    try:
        return pd.DataFrame(requests.get(f"{API_URL}/trends").json())
    except:
        return pd.DataFrame()

# --- Sidebar ---
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
st.sidebar.title("Filters")

search_query = st.sidebar.text_input("🔍 Search Jobs/Companies", placeholder="e.g. Python, Google")
source_filter = st.sidebar.selectbox("🌐 Data Source", ["All", "arbeitnow", "remotive"])
remote_filter = st.sidebar.radio("🏠 Work Environment", ["All", "Remote", "On-site"])

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# --- Main Dashboard ---
st.title("🚀 Job Market Intelligence Pro")
st.markdown("##### Real-time B2B insights into hiring trends and tech demands.")

# 1. Top Metrics Row
insights = fetch_insights()
jobs_df = fetch_data(source_filter, remote_filter, search_query)

if not jobs_df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Listings", len(jobs_df), help="Total jobs in current view")
    
    remote_pct = (jobs_df['remote'].sum() / len(jobs_df) * 100) if len(jobs_df) > 0 else 0
    m2.metric("Remote Share", f"{remote_pct:.1f}%", help="% of jobs that are fully remote")
    
    unique_companies = jobs_df['company'].nunique()
    m3.metric("Companies", unique_companies, help="Unique hiring organizations")
    
    avg_posts_day = len(jobs_df) / 7 # Approximation
    m4.metric("Weekly Velocity", f"{avg_posts_day:.0f} jobs", help="Estimated jobs per week")

    # 2. Charts Section
    st.markdown("### 📊 Market Analytics")
    tab1, tab2, tab3 = st.tabs(["📈 Growth Trends", "🛠️ Skill Demand", "📍 Geographics"])

    with tab1:
        trends_df = fetch_trends()
        if not trends_df.empty:
            fig_trends = px.area(trends_df, x="day", y="count", 
                                title="Daily Job Ingestion Volume",
                                color_discrete_sequence=['#3b82f6'])
            fig_trends.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trends, use_container_width=True)
        else:
            st.info("No trend data available.")

    with tab2:
        # Fetch Top Skills from new endpoint
        try:
            # Get slightly more so we can filter and still have 10
            top_skills_resp = requests.get(f"{API_URL}/top-skills?limit=30").json()
            if top_skills_resp:
                skills_data = pd.DataFrame(top_skills_resp)
                
                # Data Filtering: Remove skills with count < 2
                skills_data = skills_data[skills_data['count'] >= 2]
                
                # Keep Top 10
                skills_data = skills_data.head(10)
                
                if not skills_data.empty:
                    # Sort ascending for plotly horizontal bar chart
                    skills_data = skills_data.sort_values(by='count', ascending=True)
                    fig_skills = px.bar(skills_data, x="count", y="skill", orientation='h',
                                     title="Top 10 Technical Skills Demand",
                                     color="count", color_continuous_scale='Magma')
                    st.plotly_chart(fig_skills, use_container_width=True)
                else:
                    st.info("Not enough skill data to show meaningful trends (requires count >= 2).")
            else:
                st.info("Gathering skill intelligence...")
        except Exception as e:
            st.error(f"Could not fetch skill analytics: {e}")

    with tab3:
        if insights and "top_locations" in insights:
            loc_data = pd.DataFrame(list(insights["top_locations"].items()), columns=["Location", "Jobs"])
            fig_loc = px.pie(loc_data, values='Jobs', names='Location',
                                title="Hiring Hotspots (Top 10 Locations)",
                                hole=0.4)
            st.plotly_chart(fig_loc, use_container_width=True)
        else:
            st.info("Geographical data not found.")

    # 3. Data Table
    st.markdown("### 📋 Detailed Listings")
    cols_to_show = ["title", "company", "location", "remote", "posted_at", "url"]
    st.dataframe(
        jobs_df[cols_to_show].sort_values("posted_at", ascending=False),
        column_config={
            "url": st.column_config.LinkColumn("Apply Link"),
            "posted_at": st.column_config.DatetimeColumn("Date Posted"),
            "remote": st.column_config.CheckboxColumn("Remote?")
        },
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("⚠️ No matching data found. Try adjusting filters or search query.")
    if st.button("Run Initial Scrape"):
        st.info("Starting background scraper...")
        # In a real app, we'd trigger a subprocess or API call here

st.markdown("---")
st.markdown(" Data sources: Arbeitnow, Remotive")
