# app/tasks.py
from celery import Celery
from celery.schedules import crontab
import os
from scraper import run_scraper, cleanup_expired_jobs

celery_app = Celery('scraper', broker=os.getenv('CELERY_BROKER_URL'))
celery_app.conf.broker_transport_options = {
    'priority_steps': list(range(10)),
    'queue_order_strategy': 'priority',
}

celery_app.conf.beat_schedule = {
    'bi-weekly-maintenance': {
        'task': 'app.tasks.scheduled_scan_task',
        'schedule': crontab(day_of_week='mon,thu', hour=3, minute=0),
    },
}

# tasks
@celery_app.task(bind=True, priority=9)  # HIGHEST PRIORITY (Admin)
def admin_scrape_task(self, job_title, location, timeframe):
    print(f"[*] [ADMIN] Starting high priority scrape for: well see")
    return run_scraper(job_title=job_title, location=location, timeframe=timeframe)

@celery_app.task(bind=True, priority=5)  # MEDIUM PRIORITY (Scheduled)
def scheduled_scan_task(self):
    run_scraper(job_title="Software Engineer", location="Romania")
    
    # Step B: Find another category
    run_scraper(job_title="Data Scientist", location="Romania")
    cleanup_expired_jobs()
    return "Complete maintenance"

@celery_app.task(bind=True, priority=1)  # LOW PRIORITY (Viewer)
def viewer_check_task(self, url):
    print(f"[*] [VIEWER] Queueing low priority check: {url}")
    return run_scraper()