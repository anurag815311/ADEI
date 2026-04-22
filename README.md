# 🚀 Tech Hiring Intelligence Pipeline (B2B)

A production-grade **Job Market Intelligence** system for businesses. It scrapes, processes (NLP skill extraction), and visualizes tech hiring trends to provide actionable market intelligence.

## 🏗️ Architecture (Upgraded)

1.  **Hybrid Scrapers**: API-based (Arbeitnow, Remotive) + **BeautifulSoup HTML Scraper**.
2.  **Intelligence Layer**: NLP-based **Skill Extraction** from job descriptions.
3.  **Enhanced ETL**: Incremental loading, deduplication, and PostgreSQL indexing.
4.  **Multi-Model ML**: 
    *   `DemandModel`: RandomForest for volume prediction.
    *   `HiringForecast`: Linear Time-Series forecasting for market trends.
5.  **Analytics API**: Extended FastAPI endpoints for Skill Demand and Remote Ratios.
6.  **Business Dashboard**: Advanced Streamlit UI with Skill Heatmaps and Hiring Hotspots.

## 🛠️ Tech Stack

*   **Backend**: FastAPI, SQLAlchemy, PostgreSQL
*   **Pipeline**: APScheduler, Pandas, BeautifulSoup4
*   **Frontend**: Streamlit, Plotly
*   **Deployment**: Docker, Docker Compose

## 🚀 Getting Started

### Prerequisites

*   Docker and Docker Compose installed.

### Setup & Run (One Command)

```bash
docker-compose up --build
```

This will start:
*   **PostgreSQL**: `localhost:5432`
*   **FastAPI Backend**: `localhost:8000`
*   **Streamlit Dashboard**: `localhost:8501`
*   **Pipeline**: Automated background process

## 📊 Features

*   **Real-time Scrapping**: Automatically pulls the latest jobs from multiple sources.
*   **Data Integrity**: Handles HTML cleaning, deduplication, and schema validation.
*   **Insights**: Track remote vs. on-site ratios and hiring trends over time.
*   **Forecasting**: Predicts future job posting volumes using machine learning.

## 📁 Project Structure

```text
ADEI/
├── api/             # FastAPI Backend
├── dashboard/       # Streamlit UI
├── db/              # Database Models & Session
├── ml/              # Machine Learning Model & Training
├── pipeline/        # ETL & Orchestration
├── scraping/        # API Scrapers
├── data/            # Raw & Processed Data (Volume mapped)
├── logs/            # Application Logs
├── Dockerfile       # Container definition
└── docker-compose.yml # Service orchestration
```

## 📝 API Endpoints

*   `GET /data`: List job listings with filters.
*   `GET /insights`: Market distribution statistics.
*   `GET /trends`: Daily job posting volume trends.


## 🌐 Deployment

### Option 1: Render (Recommended)
This project is pre-configured for [Render](https://render.com).
1. Connect your GitHub repository to Render.
2. Render will automatically detect the `render.yaml` file.
3. Click **Create New Resources** to spin up the Database, API, Dashboard, and Pipeline.

### Option 2: Docker
```bash
docker-compose up --build
```

### Option 3: Manual Local Run
1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python -m pipeline.orchestrator`
3. Start API: `python -m api.main`
4. Start Dashboard: `streamlit run dashboard/app.py`

---
