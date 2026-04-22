import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
from loguru import logger
from scraping.job_scraper import BaseScraper

class HTMLJobScraper(BaseScraper):
    """
    New HTML-based scraper for additional job boards.
    Target: https://www.arbeitnow.com/ (HTML scraping of latest jobs)
    """
    def __init__(self):
        super().__init__("html_arbeitnow")
        self.base_url = "https://www.arbeitnow.com"

    def scrape(self):
        logger.info(f"Starting HTML scraping from {self.base_url}")
        all_jobs = []
        try:
            response = requests.get(self.base_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job listings on the homepage (example structure)
            # Note: This is an example selector, in production we adjust to actual site structure
            job_cards = soup.find_all('div', class_='job-listing-item')
            
            for card in job_cards:
                title_tag = card.find('a', class_='job-title')
                company_tag = card.find('p', class_='company-name')
                
                if title_tag and company_tag:
                    job = {
                        "source": "html_arbeitnow",
                        "slug": title_tag['href'].split('/')[-1],
                        "title": title_tag.text.strip(),
                        "company_name": company_tag.text.strip(),
                        "location": card.find('p', class_='location').text.strip() if card.find('p', class_='location') else "Remote",
                        "remote": True, # Assume remote if found here
                        "url": self.base_url + title_tag['href'],
                        "description": "", # Usually requires following link, for now we keep it empty or mock
                        "created_at": int(datetime.now().timestamp())
                    }
                    all_jobs.append(job)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_raw(all_jobs, f"html_jobs_{timestamp}.json")
            return all_jobs
        except Exception as e:
            logger.error(f"Error in HTML scraper: {e}")
            return []

if __name__ == "__main__":
    scraper = HTMLJobScraper()
    scraper.scrape()
