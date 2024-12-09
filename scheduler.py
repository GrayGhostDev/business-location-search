from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from utils import DataCollector, merge_data_sources
from database import DatabaseManager
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataUpdateScheduler:
    def __init__(self, db_manager: DatabaseManager):
        self.scheduler = BackgroundScheduler()
        self.db_manager = db_manager
        self.collector = DataCollector(google_api_key=os.getenv('GOOGLE_MAPS_API_KEY', ''))
        self.business_types = ["Marketing Firms", "Lawyers", "Paralegal"]
        self.default_location = "Oakland County, Michigan"

    def start(self):
        """Start the scheduler with predefined jobs"""
        # Schedule daily update at 2 AM
        self.scheduler.add_job(
            self.update_data,
            trigger=CronTrigger(hour=2),
            id='daily_update',
            name='Daily data update',
            replace_existing=True
        )
        
        # Schedule weekly full refresh on Sunday at 3 AM
        self.scheduler.add_job(
            self.full_refresh,
            trigger=CronTrigger(day_of_week='sun', hour=3),
            id='weekly_refresh',
            name='Weekly full refresh',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def update_data(self):
        """Update data for all business types"""
        try:
            logger.info(f"Starting scheduled data update at {datetime.now()}")
            all_data = []
            
            for business_type in self.business_types:
                yelp_data = self.collector.scrape_yelp(business_type, self.default_location)
                google_data = []
                
                if os.getenv('GOOGLE_MAPS_API_KEY'):
                    google_data = self.collector.get_google_places_data(
                        business_type, 
                        self.default_location
                    )
                
                merged_data = merge_data_sources(yelp_data, google_data)
                all_data.extend(merged_data)
            
            if all_data:
                saved_count = self.db_manager.save_businesses(all_data)
                logger.info(f"Successfully updated {saved_count} records")
            else:
                logger.warning("No new data collected during update")
                
        except Exception as e:
            logger.error(f"Error during scheduled update: {str(e)}")

    async def full_refresh(self):
        """Perform a full data refresh"""
        try:
            logger.info(f"Starting full data refresh at {datetime.now()}")
            
            # Clear existing data
            self.db_manager.clear_database()
            
            # Perform fresh data collection
            await self.update_data()
            
            logger.info("Full refresh completed successfully")
            
        except Exception as e:
            logger.error(f"Error during full refresh: {str(e)}")

    def get_next_run_time(self, job_id: str) -> str:
        """Get the next scheduled run time for a specific job"""
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return "Not scheduled"

    def get_scheduler_status(self) -> dict:
        """Get the current status of all scheduled jobs"""
        return {
            'running': self.scheduler.running,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "Not scheduled"
                }
                for job in self.scheduler.get_jobs()
            ]
        }
