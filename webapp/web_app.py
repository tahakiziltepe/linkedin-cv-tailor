import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for, flash
from datetime import timedelta
from src.tracker import JobTracker
from src.status_logger import StatusLogger
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
import json
import logging
import os
import uuid
from datetime import datetime

# .env varsa yükle (SECRET_KEY ve kullanıcı kodunu buradan okuyoruz)
load_dotenv()

logger = logging.getLogger(__name__)

app = Flask(__name__)

# SECRET_KEY zorunlu: yoksa panel session'larını güvenli tutamaz.
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY işlemede kayıtlı değil. webapp klasöründe .env dosyasına veya "
        "kabuk ortamına SECRET_KEY=<rastgele-uzun-dize> ekleyip yeniden başlatın. "
        "(Üretmek için: python -c \"import secrets; print(secrets.token_hex(32))\")"
    )
app.secret_key = secret_key
app.permanent_session_lifetime = timedelta(days=1)

# Config
DATA_DIR = BASE_DIR / 'data'
DATABASE_DIR = DATA_DIR / 'database'
OUTPUT_DIR = DATA_DIR / 'output'
BLOCKED_COMPANIES_FILE = DATA_DIR / 'blocked_companies.json'
USERS_FILE = DATABASE_DIR / 'users.json'

tracker = JobTracker(DATABASE_DIR)
status_logger = StatusLogger(DATABASE_DIR)

def load_users():
    if not USERS_FILE.exists():
        return []
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load users: {e}")
        return []

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes:
        if 'logged_in' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        for user in users:
            if user.get('username') != username:
                continue
            cached = user.get('password', '')
            if check_password_hash(cached, password) or cached == password:
                # Not: ikinci koşul, henüz hash'e geçirilmemiş eski kayıtlar için
                # toleranstır; hash'e yükseltmek için:
                #   uv run python tools/hash_users.py
                session.permanent = True
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))
                
        flash('Geçersiz kullanıcı adı veya şifre.', 'error')
    
    # If already logged in, redirect to dashboard
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



def load_blocked_companies():
    if not BLOCKED_COMPANIES_FILE.exists():
        return []
    try:
        with open(BLOCKED_COMPANIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load blocked companies: {e}")
        return []


def save_blocked_companies(companies):
    with open(BLOCKED_COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)

@app.route('/')
def dashboard():
    history = tracker.load_history()
    
    # Calculate status counts
    status_counts = {}
    for job in history:
        status = job.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    jobs_json = json.dumps(history, default=str)
    blocked_companies = load_blocked_companies()
    return render_template('dashboard.html', jobs=history, status_counts=status_counts, jobs_json=jobs_json,
                           blocked_companies=blocked_companies)

@app.route('/api/update_status', methods=['POST'])
def update_status():
    data = request.json
    job_url = data.get('url')
    new_status = data.get('status')
    
    if not job_url or not new_status:
        return jsonify({'error': 'Missing parameters'}), 400
        
    history = tracker.load_history()
    updated = False
    
    for job in history:
        if job.get('url') == job_url:
            old_status = job.get('status', 'Unknown')
            if old_status != new_status:
                status_logger.log_status_change(job_url, old_status, new_status)
                job['status'] = new_status
                updated = True
            break
            
    if updated:
        tracker.save_history(history)
        # If status changed to Blocked Company, add employer to blocked list
        if new_status == 'Blocked Company':
            job_entry = next((j for j in history if j.get('url') == job_url), None)
            if job_entry:
                company = job_entry.get('company', '').strip()
                if company:
                    blocked = load_blocked_companies()
                    if company not in blocked:
                        blocked.append(company)
                        save_blocked_companies(blocked)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/update_notes', methods=['POST'])
def update_notes():
    data = request.json
    job_url = data.get('url')
    new_notes = data.get('notes')
    
    if not job_url or new_notes is None:
        return jsonify({'error': 'Missing parameters'}), 400
        
    history = tracker.load_history()
    updated = False
    
    for job in history:
        if job.get('url') == job_url:
            job['notes'] = new_notes
            updated = True
            break
            
    if updated:
        tracker.save_history(history)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/delete_job', methods=['POST'])
def delete_job():
    data = request.json
    job_url = data.get('url')
    
    if not job_url:
        return jsonify({'error': 'Missing parameters'}), 400
        
    if tracker.delete_job(job_url):
        return jsonify({'success': True})
        
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/add_job', methods=['POST'])
def add_job():
    data = request.json
    company = data.get('company')
    title = data.get('title')
    
    # Validate required fields
    if not company or not title:
        return jsonify({'error': 'Company and title are required'}), 400
    
    # Get optional fields
    url = data.get('url', '').strip()
    
    # If no URL provided, generate a unique identifier
    if not url:
        url = f"manual-job-{uuid.uuid4()}"
    
    # Create job data with defaults
    job_data = {
        'company': company,
        'title': title,
        'url': url,
        'pdf_path': None,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'query': '',
        'status': 'Applied',
        'notes': ''
    }
    
    tracker.add_job(job_data)
    return jsonify({'success': True, 'job': job_data})

@app.route('/api/blocked_companies', methods=['GET'])
def get_blocked_companies():
    return jsonify(load_blocked_companies())

@app.route('/api/blocked_companies', methods=['POST'])
def update_blocked_companies():
    data = request.json
    if data is None or 'companies' not in data:
        return jsonify({'error': 'Missing companies list'}), 400
    companies = [c.strip() for c in data['companies'] if isinstance(c, str) and c.strip()]
    save_blocked_companies(companies)
    return jsonify({'success': True, 'companies': companies})

@app.route('/download/<path:filename>')
def download_file(filename):
    download_name = request.args.get('name')
    if download_name:
        return send_from_directory(OUTPUT_DIR, filename, as_attachment=True, download_name=download_name)
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
