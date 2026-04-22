from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    skills: Optional[str]

    class Config:
        from_attributes = True

class InsightSchema(BaseModel):
    count_by_source: dict
    remote_vs_onsite: dict
    top_locations: dict
    top_tags: dict

class SkillTrendSchema(BaseModel):
    skill: str
    count: int
