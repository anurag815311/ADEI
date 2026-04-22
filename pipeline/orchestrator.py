import time
from apscheduler.schedulers.blocking import BlockingScheduler
from scraping.job_scraper import ArbeitnowScraper, RemotiveScraper
from pipeline.preprocess import DataPipeline
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

def run_job_pipeline():
    logger.info("Starting Job Pipeline Run...")
    
    # 1. Scrape
    logger.info("Step 1: Scraping...")
    a_scraper = ArbeitnowScraper()
    a_scraper.scrape(max_pages=5)
    
    r_scraper = RemotiveScraper()
    r_scraper.scrape()
    
    # 2. Process
    logger.info("Step 2: Processing and Loading...")
    pipeline = DataPipeline()
    pipeline.process_all_raw()
    
    logger.info("Pipeline Run Completed Successfully.")

if __name__ == "__main__":
    # For initial run
    run_job_pipeline()
    
    interval = int(os.getenv("SCRAPE_INTERVAL_HOURS", 24))
    scheduler = BlockingScheduler()
    scheduler.add_job(run_job_pipeline, 'interval', hours=interval)
    
    logger.info(f"Scheduler started. Running every {interval} hours.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
