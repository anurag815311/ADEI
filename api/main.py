from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import JobListing, SessionLocal, init_db
from api.schemas import JobSchema
from typing import List, Optional
import uvicorn
import os
import threading
from pipeline.orchestrator import run_job_pipeline

app = FastAPI(
    title="Job Intelligence API",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
def startup_event():
    # Ensure tables are created
    init_db()
    # Run the pipeline in a background thread to keep the service free on Render
    # This avoids the need for a separate paid 'Worker' instance
    thread = threading.Thread(target=run_job_pipeline, daemon=True)
    thread.start()

@app.get("/")
def health_check():
    return {"status": "online", "message": "Job Intelligence API is running"}

@app.get("/run-scrape")
def trigger_scrape():
    # Manual trigger for the pipeline
    try:
        thread = threading.Thread(target=run_job_pipeline, daemon=True)
        thread.start()
        return {"status": "success", "message": "Scraper triggered successfully in background"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/data", response_model=List[JobSchema])
def get_jobs(
    skip: int = 0, 
    limit: int = 100, 
    source: Optional[str] = None,
    remote: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(JobListing)
    if source:
        query = query.filter(JobListing.source == source)
    if remote is not None:
        query = query.filter(JobListing.remote == remote)
    
    return query.order_by(JobListing.posted_at.desc()).offset(skip).limit(limit).all()

@app.get("/insights")
def get_insights(db: Session = Depends(get_db)):
    # Job count by source
    counts = db.query(JobListing.source, func.count(JobListing.id)).group_by(JobListing.source).all()
    remote_stats = db.query(JobListing.remote, func.count(JobListing.id)).group_by(JobListing.remote).all()
    
    # Top 10 Locations
    locations = db.query(JobListing.location, func.count(JobListing.id))\
        .filter(JobListing.location != None)\
        .group_by(JobListing.location)\
        .order_by(func.count(JobListing.id).desc())\
        .limit(10).all()

    # Tag Analysis (simple split for SQLite)
    all_tags = db.query(JobListing.tags).all()
    tag_counts = {}
    for (tags_str,) in all_tags:
        if tags_str:
            for tag in tags_str.split(','):
                tag = tag.strip().lower()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "count_by_source": dict(counts),
        "remote_vs_onsite": dict(remote_stats),
        "top_locations": dict(locations),
        "top_tags": dict(top_tags)
    }

@app.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    # Jobs over time (daily)
    if SessionLocal().bind.dialect.name == 'sqlite':
        trends = db.query(
            func.strftime('%Y-%m-%d', JobListing.posted_at).label('day'),
            func.count(JobListing.id)
        ).group_by('day').order_by('day').all()
    else:
        trends = db.query(
            func.date_trunc('day', JobListing.posted_at).label('day'),
            func.count(JobListing.id)
        ).group_by('day').order_by('day').all()
    
    return [{"day": t[0], "count": t[1]} for t in trends]

@app.get("/top-skills")
def get_top_skills(limit: int = 15, db: Session = Depends(get_db)):
    all_skills = db.query(JobListing.skills).all()
    skill_counts = {}
    for (skills_str,) in all_skills:
        if skills_str:
            for skill in skills_str.split(','):
                skill = skill.strip().lower()
                if skill:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"skill": k, "count": v} for k, v in top_skills]

@app.get("/hiring-trends")
def get_hiring_trends(db: Session = Depends(get_db)):
    # Group by month for hiring trends
    if SessionLocal().bind.dialect.name == 'sqlite':
        trends = db.query(
            func.strftime('%Y-%m', JobListing.posted_at).label('month'),
            func.count(JobListing.id)
        ).group_by('month').order_by('month').all()
    else:
        trends = db.query(
            func.to_char(JobListing.posted_at, 'YYYY-MM').label('month'),
            func.count(JobListing.id)
        ).group_by('month').order_by('month').all()
    return [{"month": t[0], "count": t[1]} for t in trends]

@app.get("/remote-ratio")
def get_remote_ratio(db: Session = Depends(get_db)):
    total = db.query(func.count(JobListing.id)).scalar() or 1
    remote_count = db.query(func.count(JobListing.id)).filter(JobListing.remote == True).scalar() or 0
    return {
        "remote": remote_count,
        "onsite": total - remote_count,
        "ratio": round(remote_count / total, 2)
    }

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
