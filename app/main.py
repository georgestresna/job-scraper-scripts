import os
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import or_

# Import your local modules
from database import SessionLocal, Job, init_db
from tasks import admin_scrape_task, celery_app

app = Flask(__name__)

# --- Configuration ---
app.secret_key = os.getenv("FLASK_SECRET_KEY", "temporary-dev-key")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password123")

init_db()

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USER:
        return User(user_id)
    return None

# --- Helper Function for Filtering ---
def get_filtered_jobs(request_args):
    """
    Applies filters from the URL arguments to the database query.
    Returns the filtered list of Job objects.
    """
    db = SessionLocal()
    query = db.query(Job)

    # 1. Location Filter (Bucharest vs Not Bucharest)
    loc_filter = request_args.get('loc_filter')
    if loc_filter == 'bucharest':
        query = query.filter(Job.location.ilike('%Bucharest%'))
    elif loc_filter == 'not_bucharest':
        query = query.filter(~Job.location.ilike('%Bucharest%'))

    # 2. Level Filter (Internship / Junior)
    level_filter = request_args.get('level_filter')
    if level_filter:
        # Search for term in Title OR Description
        term = level_filter.lower()
        query = query.filter(
            or_(
                Job.title.ilike(f'%{term}%'),
                Job.description.ilike(f'%{term}%')
            )
        )

    # 3. Text Search (Matches ANY word in Title OR Description)
    search_text = request_args.get('search', '').strip()
    if search_text:
        words = search_text.split()
        for word in words:
            query = query.filter(
                or_(
                    Job.title.ilike(f'%{word}%'),
                    Job.description.ilike(f'%{word}%')
                )
            )

    # Get results
    jobs = query.order_by(Job.id.desc()).all()
    db.close()
    return jobs

# --- Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            login_user(User(ADMIN_USER))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    # 1. Get Filtered Jobs
    jobs = get_filtered_jobs(request.args)

    # 2. Inspect Celery Queue
    queue_count = 0
    try:
        inspector = celery_app.control.inspect()
        active = inspector.active() or {}
        reserved = inspector.reserved() or {}
        queue_count = sum(len(tasks) for tasks in active.values()) + \
                      sum(len(tasks) for tasks in reserved.values())
    except Exception:
        pass # Fail silently if Redis is down

    return render_template('index.html', jobs=jobs, queue_count=queue_count)

@app.route('/export')
def export_csv():
    # 1. Get the EXACT same jobs the user is seeing right now
    jobs = get_filtered_jobs(request.args)

    # 2. Convert to DataFrame using Pandas
    data = [{
        "ID": j.id,
        "Title": j.title,
        "Company": j.company,
        "Location": j.location,
        "Link": j.link
        # Add "Description": j.description if you want the full text in the CSV
    } for j in jobs]

    df = pd.DataFrame(data)

    # 3. Create CSV in memory
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)

    return send_file(
        output, 
        mimetype='text/csv', 
        as_attachment=True, 
        download_name='filtered_jobs.csv'
    )

@app.route('/scrape', methods=['POST'])
@login_required
def scrape():
    title = request.form.get('title')
    loc = request.form.get('location')
    time = request.form.get('timeframe')

    admin_scrape_task.apply_async(args=[title, loc, time], priority=9)
    
    flash(f"Started scraping for {title} in {loc}...")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)