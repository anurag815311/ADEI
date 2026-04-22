from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from db.models import JobListing, SessionLocal
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os

app = FastAPI(title="Job Intelligence API")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class JobSchema(BaseModel):
    id: int
    source: str
    title: str
    company: str
    location: Optional[str]
    remote: bool
    tags: Optional[str]
    posted_at: datetime
    url: str

    class Config:
        orm_mode = True

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

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
