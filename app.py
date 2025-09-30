#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Madhav (https://github.com/madhav-mknc)


from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)
from werkzeug.utils import secure_filename
from functools import wraps
from waitress import serve
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf

# from google_auth_oauthlib.flow import Flow

from utils.enhanced_news_manager import enhanced_news_manager
from utils.file_utils import allowed_file, is_authenticated, handle_urls
import hashlib

import os
import json
from dotenv import load_dotenv
load_dotenv()

# Initialzing flask app
app = Flask(__name__)

# Enable CORS (restrict to configured origins)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")}})

# CSRF protection
csrf = CSRFProtect(app)
app.jinja_env.globals['csrf_token'] = generate_csrf

# secret key
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Change this to a strong random key in a production environment
# app.secret_key = str(unique_id()).replace("-","")

# Secure cookie/session settings
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

# server address
HOST = "0.0.0.0"
PORT = 8080


# only logged in access
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# # GOOGLE API AUTHENTICATION
# state = session['state']
# flow = Flow.from_client_secrets_file(
#     'client_secret.json',
#     scopes=['https://www.googleapis.com/auth/drive.readonly'],
#     state=state)
# flow.redirect_uri = url_for('oauth2callback', _external=True)

# authorization_response = request.url
# flow.fetch_token(authorization_response=authorization_response)

# # Store the credentials in the session.
# # ACTION ITEM for developers:
# #     Store user's access and refresh tokens in your data store if
# #     incorporating this code into your real app.
# credentials = flow.credentials
# session['credentials'] = {
#     'token': credentials.token,
#     'refresh_token': credentials.refresh_token,
#     'token_uri': credentials.token_uri,
#     'client_id': credentials.client_id,
#     'client_secret': credentials.client_secret,
#     'scopes': credentials.scopes}
# flow = Flow.from_client_secrets_file('client_secret.json', SCOPES)
# flow.redirect_uri = REDIRECT_URI




# Routes below:
"""
/           => index
/login      => admin login page
/dashboard  => admin dashboard
/upload     => for uploading files
/handle_url => fetch data from URLs
/delete     => for deleting a uploaded file
/chatbot    => redirect to chatbot
/get_chat_response => for fetching response from the chatbot
/logout     => admin logout
"""


# index
@app.route('/')
def index():
    return render_template('index.html')


# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('authenticated'):
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if is_authenticated(username, password):
            # Save the authenticated status in the session
            session['authenticated'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
            return render_template('login.html', error=error)
    return render_template('login.html')


# dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Check if the user is authenticated in the session
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    # Simple file listing - no AI database needed
    upload_dir = "uploads"
    files = []
    if os.path.exists(upload_dir):
        files = [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
    return render_template('dashboard.html', files=files)


# UPLOAD FILES from local storage
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if request.method == 'POST':
        files = request.files.getlist('file')

        if not files:
            flash('No files selected')
            return redirect(url_for('dashboard'))

        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
            else:
                flash('Invalid file type')
                return redirect(url_for('dashboard'))

        flash('Files uploaded successfully')
        return redirect(url_for('dashboard'))

# # GOOGLE DRIVE process files
# @app.route('/process_file_id', methods=['POST'])
# @login_required
# def process_file_id():
#     file_id = request.json.get('file_id')
#     # TODO: Your server side code to process files
#     print(file_id)
#     return jsonify({'message': 'File ID received'})

# # GOOGLE DRIVE route for OAuth 2.0 authorization
# @app.route('/login_google_drive')
# def login_google_drive():
#     auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', redirect_uri=REDIRECT_URIS[0])
#     return redirect(auth_url)

# @app.route('/login_google_drive')
# def login_google_drive():
#     auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
#     return redirect(auth_url)

# # GOOGLE DRIVE Callback route for handling OAuth 2.0 response
# @app.route('/oauth2callback')
# def oauth2callback():
#     flow.fetch_token(authorization_response=request.url)
#     session['credentials'] = flow.credentials.to_json()
#     return redirect(url_for('dashboard'))


# # GOOGLE DRIVE upload files
# @app.route('/upload_google_drive', methods=['POST'])
# @login_required
# def upload_google_drive():
#     try:
#         if 'file' not in request.files:
#             flash('No file selected')
#             return redirect(url_for('dashboard'))

#         file = request.files['file']
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(url_for('dashboard'))

#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(filename)

#             drive_service = authenticate_google_drive(session)
#             file_id = upload_to_google_drive(drive_service, filename)
#             flash(f'File uploaded to Google Drive with ID: {file_id}')
#             return redirect(url_for('dashboard'))
#         else:
#             flash('Invalid file type')
#             return redirect(url_for('dashboard'))

#     except Exception as e:
#         flash(f'Error uploading to Google Drive: {str(e)}')
#         return redirect(url_for('dashboard'))



# UPLOAD FILES as txt scraped URL
@app.route('/handle_url', methods=['POST'])
@login_required
def handle_url():
    if request.method == 'POST':
        url = request.form.get('url')
        result_message = handle_urls(url)
        flash(result_message)
    return redirect(url_for('dashboard'))


# delete an uploaded file
@app.route('/delete/<path:filename>', methods=['POST'])
@login_required
def delete(filename):
    # Simple file deletion from uploads directory
    upload_dir = "uploads"
    file_path = os.path.join(upload_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('File deleted successfully')
    else:
        flash('File not found')
    return redirect(url_for('dashboard'))


# Chatbot functionality removed - no longer using AI dependencies


# logout
@app.route('/logout')
def logout():
    # Clear the authenticated status from the session
    session.pop('authenticated', None)
    return redirect(url_for('index'))


# News routes
@app.route('/news')
@login_required
def news_dashboard():
    """Enhanced news intelligence dashboard"""
    return render_template('enhanced_news.html')

@app.route('/news/legacy')
@login_required
def legacy_news_dashboard():
    """Legacy news dashboard page"""
    return render_template('news.html')


@app.route('/api/news')
@login_required
def get_news():
    """API endpoint to get news articles with enhanced features"""
    category = request.args.get('category')
    source = request.args.get('source')
    count = int(request.args.get('count', 20))

    # Enhanced filtering
    filters = {}
    if category:
        filters['category'] = category
    if source:
        filters['source'] = source

    if filters:
        # Use enhanced search if filters applied
        news = enhanced_news_manager.search_articles("", filters)[:count]
    else:
        news = enhanced_news_manager.news_cache[:count]

    return jsonify(news)


@app.route('/api/news/summary')
@login_required
def get_news_summary():
    """API endpoint to get enhanced news summary"""
    summary = {
        'total_articles': len(enhanced_news_manager.news_cache),
        'last_update': enhanced_news_manager.last_update.isoformat() if enhanced_news_manager.last_update else None,
        'sources': list(set(article.get('api_source', 'unknown') for article in enhanced_news_manager.news_cache)),
        'categories': list(set(article.get('category', 'general') for article in enhanced_news_manager.news_cache)),
        'user_topics': list(enhanced_news_manager.user_topics.keys())
    }
    return jsonify(summary)


@app.route('/api/news/refresh', methods=['GET', 'POST'])
@login_required
def refresh_news():
    """API endpoint to manually refresh enhanced news cache"""
    enhanced_news_manager.update_enhanced_cache()
    return jsonify({'status': 'success', 'message': 'Enhanced news cache updated'})


@app.route('/api/news/sources')
@login_required
def get_news_sources():
    """API endpoint to get available news sources"""
    sources = {
        'free_apis': list(enhanced_news_manager.free_apis.keys()),
        'premium_apis': {
            'guardian': bool(enhanced_news_manager.guardian_api_key),
            'nytimes': bool(enhanced_news_manager.nytimes_api_key),
            'newsapi': bool(enhanced_news_manager.news_api_key)
        },
        'active_sources': list(set(article.get('api_source', 'unknown') for article in enhanced_news_manager.news_cache))
    }
    return jsonify(sources)


# Enhanced API endpoints for intelligent news features

@app.route('/api/news/search')
@login_required
def search_news():
    """Advanced news search with filters"""
    query = request.args.get('q', '')
    category = request.args.get('category')
    source = request.args.get('source')
    date_from = request.args.get('date_from')
    count = int(request.args.get('count', 20))

    filters = {}
    if category:
        filters['category'] = category
    if source:
        filters['source'] = source
    if date_from:
        filters['date_from'] = date_from

    results = enhanced_news_manager.search_articles(query, filters)[:count]

    return jsonify({
        'query': query,
        'filters': filters,
        'total_results': len(results),
        'articles': results
    })

@app.route('/api/news/topics')
@login_required
def get_user_topics():
    """Get user-defined topics"""
    return jsonify(enhanced_news_manager.user_topics)

@app.route('/api/news/topics', methods=['POST'])
@login_required
def create_topic():
    """Create a new custom topic"""
    try:
        data = request.json
        name = data.get('name')
        keywords = data.get('keywords', [])
        sources = data.get('sources', [])
        priority = data.get('priority', 1.0)

        if not name or not keywords:
            return jsonify({'status': 'error', 'message': 'Name and keywords required'}), 400

        message = enhanced_news_manager.add_custom_topic(name, keywords, sources, priority)
        return jsonify({'status': 'success', 'message': message})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/news/topics/<topic_name>')
@login_required
def get_topic_articles(topic_name):
    """Get articles for a specific topic"""
    count = int(request.args.get('count', 20))
    articles = enhanced_news_manager.get_topic_articles(topic_name, count)

    return jsonify({
        'topic': topic_name,
        'total_articles': len(articles),
        'articles': articles
    })

@app.route('/api/news/trending')
@login_required
def get_trending_topics():
    """Get trending topics analysis"""
    days = int(request.args.get('days', 7))
    trending = enhanced_news_manager.get_trending_topics(days)

    return jsonify({
        'period_days': days,
        'trending_topics': trending
    })

@app.route('/api/news/analytics')
@login_required
def get_news_analytics():
    """Get news analytics and insights"""
    articles = enhanced_news_manager.news_cache

    # Basic analytics
    analytics = {
        'total_articles': len(articles),
        'sources_breakdown': {},
        'categories_breakdown': {},
        'sentiment_breakdown': {'positive': 0, 'negative': 0, 'neutral': 0},
        'hourly_distribution': {},
        'top_keywords': []
    }

    # Source distribution
    for article in articles:
        source = article.get('api_source', 'unknown')
        analytics['sources_breakdown'][source] = analytics['sources_breakdown'].get(source, 0) + 1

    # Category distribution
    for article in articles:
        category = article.get('category', 'general')
        analytics['categories_breakdown'][category] = analytics['categories_breakdown'].get(category, 0) + 1

    # Sentiment distribution
    for article in articles:
        sentiment = article.get('sentiment', {}).get('label', 'neutral')
        analytics['sentiment_breakdown'][sentiment] += 1

    return jsonify(analytics)


# run server
def start_server():
    serve(app, host=HOST, port=PORT)


# Security headers and CSRF cookie for AJAX clients
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    try:
        token = generate_csrf()
        response.set_cookie(
            'csrf_token', token,
            httponly=False,
            samesite='Lax',
            secure=app.config['SESSION_COOKIE_SECURE']
        )
    except Exception:
        pass
    return response

if __name__ == '__main__':
    start_server()
