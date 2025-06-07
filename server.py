from flask import Flask
from flask_apscheduler import APScheduler
from crawl_pipeline import Crawl_Pipeline

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
crawl_pipeline = Crawl_Pipeline()

scheduler.add_job(
    id='daily_job',
    func=crawl_pipeline.process_crawl_pdf,
    trigger='cron',
    hour=0,
    minute=0
)

scheduler.add_job(
    id='weekly_job',
    func=crawl_pipeline.process_crawl_profile,
    trigger='cron',
    day_of_week='mon',
    hour=0, minute=0
)

scheduler.start()


@app.route("/")
def index():
    return "⏰ Flask APScheduler is running!"


if __name__ == "__main__":
    app.run(debug=True)
