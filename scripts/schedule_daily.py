# Use AWS EventBridge for daily triggers
# Or add to cron jobs for local deployment

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

def daily_processing_job():
    """Run daily at 2 AM"""
    print(f"Starting daily processing at {datetime.now()}")
    main(papers_dir='project/papers/new', output_dir=f'project/outputs/{datetime.now().strftime("%Y%m%d")}')

scheduler = BackgroundScheduler()
scheduler.add_job(daily_processing_job, 'cron', hour=2, minute=0)
scheduler.start()