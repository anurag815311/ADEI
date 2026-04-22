import pandas as pd
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger
from db.models import JobListing, SessionLocal, init_db
from pipeline.skill_extractor import SkillExtractor
from sqlalchemy.dialects.postgresql import insert

class DataPipeline:
    def __init__(self):
        self.raw_path = "data/raw"
        self.processed_path = "data/processed"
        os.makedirs(self.processed_path, exist_ok=True)
        self.extractor = SkillExtractor()
        init_db()

    def clean_html(self, html):
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=' ')

    def parse_date(self, date_str):
        if not date_str:
            return datetime.now()
        try:
            # Handle Remotive format (usually ISO or similar)
            if isinstance(date_str, int): # Remotive timestamp
                return datetime.fromtimestamp(date_str)
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return datetime.now()

    def transform_arbeitnow(self, raw_data):
        transformed = []
        for item in raw_data:
            desc = self.clean_html(item.get("description"))
            transformed.append({
                "source": "arbeitnow",
                "external_id": item.get("slug"),
                "title": item.get("title"),
                "company": item.get("company_name"),
                "location": item.get("location"),
                "remote": item.get("remote", False),
                "tags": ",".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else "",
                "job_type": ",".join(item.get("job_types", [])) if isinstance(item.get("job_types"), list) else "",
                "url": item.get("url"),
                "description": desc,
                "posted_at": self.parse_date(item.get("created_at")),
                "category": None,
                "skills": ",".join(self.extractor.extract_skills(desc))
            })
        return transformed

    def transform_remotive(self, raw_data):
        transformed = []
        for item in raw_data:
            desc = self.clean_html(item.get("description"))
            transformed.append({
                "source": "remotive",
                "external_id": str(item.get("id")),
                "title": item.get("title"),
                "company": item.get("company_name"),
                "location": item.get("candidate_required_location"),
                "remote": True,
                "tags": ",".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else "",
                "job_type": ",".join([item.get("job_type")]) if item.get("job_type") else "",
                "url": item.get("url"),
                "description": desc,
                "posted_at": self.parse_date(item.get("publication_date")),
                "category": item.get("category"),
                "skills": ",".join(self.extractor.extract_skills(desc))
            })
        return transformed

    def transform_html_scraper(self, raw_data):
        transformed = []
        for item in raw_data:
            # HTML scraper might have limited desc, but we still try
            desc = item.get("description", "")
            transformed.append({
                "source": item.get("source"),
                "external_id": item.get("slug"),
                "title": item.get("title"),
                "company": item.get("company_name"),
                "location": item.get("location"),
                "remote": item.get("remote", False),
                "tags": "",
                "job_type": "",
                "url": item.get("url"),
                "description": desc,
                "posted_at": self.parse_date(item.get("created_at")),
                "category": None,
                "skills": ",".join(self.extractor.extract_skills(f"{item.get('title')} {desc}"))
            })
        return transformed

    def load_to_db(self, data):
        db = SessionLocal()
        count = 0
        try:
            for item in data:
                stmt = insert(JobListing).values(**item)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['external_id'],
                    set_={
                        "title": item["title"],
                        "description": item["description"],
                        "posted_at": item["posted_at"]
                    }
                )
                db.execute(stmt)
                count += 1
            db.commit()
            logger.info(f"Successfully loaded {count} records to database.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error loading to DB: {e}")
        finally:
            db.close()

    def process_all_raw(self):
        for file in os.listdir(self.raw_path):
            if not file.endswith(".json"):
                continue
            
            filepath = os.path.join(self.raw_path, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            if "arbeitnow" in file and "html" not in file:
                transformed = self.transform_arbeitnow(raw_data)
            elif "remotive" in file:
                transformed = self.transform_remotive(raw_data)
            elif "html_arbeitnow" in file:
                transformed = self.transform_html_scraper(raw_data)
            else:
                continue
            
            self.load_to_db(transformed)
            # Move or rename file to mark as processed (optional)
            # os.rename(filepath, filepath + ".processed")

if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.process_all_raw()
