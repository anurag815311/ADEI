import requests
import time
import json
import os
from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class BaseScraper:
    def __init__(self, source_name):
        self.source_name = source_name
        self.raw_data_path = "data/raw"
        os.makedirs(self.raw_data_path, exist_ok=True)
        logger.add(f"logs/{source_name}_scraper.log", rotation="500 MB")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_url(self, url, params=None):
        logger.info(f"Fetching {url} with params {params}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def save_raw(self, data, filename):
        filepath = os.path.join(self.raw_data_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Saved raw data to {filepath}")

class ArbeitnowScraper(BaseScraper):
    def __init__(self):
        super().__init__("arbeitnow")
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"

    def scrape(self, max_pages=5):
        all_jobs = []
        for page in range(1, max_pages + 1):
            try:
                data = self.fetch_url(self.base_url, params={"page": page})
                jobs = data.get("data", [])
                if not jobs:
                    break
                all_jobs.extend(jobs)
                # Rate limiting
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                break
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_raw(all_jobs, f"arbeitnow_{timestamp}.json")
        return all_jobs

class RemotiveScraper(BaseScraper):
    def __init__(self):
        super().__init__("remotive")
        self.base_url = "https://remotive.com/api/remote-jobs"

    def scrape(self):
        try:
            # Remotive usually returns all jobs or allows category filtering
            data = self.fetch_url(self.base_url)
            jobs = data.get("jobs", [])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_raw(jobs, f"remotive_{timestamp}.json")
            return jobs
        except Exception as e:
            logger.error(f"Error scraping Remotive: {e}")
            return []

if __name__ == "__main__":
    # Test scrape
    a_scraper = ArbeitnowScraper()
    a_scraper.scrape(max_pages=2)
    
    r_scraper = RemotiveScraper()
    r_scraper.scrape()
