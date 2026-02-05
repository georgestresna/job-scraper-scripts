from flask import Flask, jsonify
from tasks import admin_scrape_task  # Corrected import based on our flat structure

app = Flask(__name__)

# 1. The Home Page (fixes the 404)
@app.route('/')
def home():
    return "<h1>Job Scraper System Online</h1><p>Visit /test-scrape to trigger a job!</p>"

# 2. A Test Route to trigger the Scraper
@app.route('/test-scrape')
def test_scrape():
    # This sends the task to Redis/Celery
    task = admin_scrape_task.apply_async(
        args=["Python Developer", "Romania", "r86400"], 
        priority=9
    )
    return jsonify({
        "status": "Task Sent to Chef!",
        "task_id": task.id,
        "priority": "High (Admin)"
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)