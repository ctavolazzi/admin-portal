# Simple file utilities for admin portal
# No AI/ML dependencies - just basic file and auth operations

import os
import json
import hashlib
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'csv'}

# Load admin users from JSON file
def load_admin_users():
    """Load admin users from admin_users.json"""
    admin_users_file = 'admin_users.json'
    if os.path.exists(admin_users_file):
        with open(admin_users_file, 'r') as file:
            users = json.load(file)
            # Migrate plaintext passwords to hashed-at-rest (one-time)
            changed = False
            for user in users:
                pwd = user.get('password', '')
                # Heuristic: bcrypt/werkzeug hashes start with method prefix e.g., pbkdf2:sha256:
                if pwd and not str(pwd).startswith('pbkdf2:'):
                    user['password'] = generate_password_hash(pwd)
                    changed = True
            if changed:
                with open(admin_users_file, 'w') as wf:
                    json.dump(users, wf, indent=2)
            return users
    else:
        print(f"[ERROR] {admin_users_file} NOT FOUND")
        return []

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_authenticated(username, password):
    """Check if username/password combination is valid"""
    admin_users = load_admin_users()
    for admin_user in admin_users:
        if admin_user['username'] == username:
            stored = admin_user.get('password', '')
            # Support both migrated hashes and legacy SHA256 compare (fallback)
            try:
                if stored.startswith('pbkdf2:') and check_password_hash(stored, password):
                    return True
            except Exception:
                pass
            # Legacy fallback (will be phased out after migration)
            legacy_ok = hashlib.sha256(stored.encode()).hexdigest() == hashlib.sha256(password.encode()).hexdigest()
            if legacy_ok:
                return True
    return False

def is_url(text):
    """Check if text is a valid URL"""
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except:
        return False

def handle_urls(url):
    """Fetch and extract text content from URL"""
    try:
        if not is_url(url):
            return "Invalid URL format"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text
        text = soup.get_text()

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Save extracted content to uploads directory
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Create filename from URL
        domain = urlparse(url).netloc.replace('www.', '')
        filename = f"url_content_{domain}_{hash(url) % 10000}.txt"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n\n")
            f.write(text[:5000])  # Limit to first 5000 characters

        return f"Content extracted and saved as {filename}"

    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {str(e)}"
    except Exception as e:
        return f"Error processing content: {str(e)}"