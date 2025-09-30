# 🚀 Admin Portal

A clean, lightweight admin dashboard for file management and news aggregation. Built with Flask and Poetry for modern Python dependency management.

## ✨ Features

### 🔐 **Admin Authentication**
- Secure login system with hashed passwords
- Session-based authentication
- Simple user management via JSON config

### 📁 **File Management**
- Upload multiple files (txt, pdf, doc, docx, csv)
- Simple file storage in `uploads/` directory
- File deletion with confirmation
- URL content extraction and saving

### 📰 **News Dashboard**
- Real-time news aggregation from multiple sources
- RSS feeds (TechCrunch, BBC, Reuters, etc.)
- Financial data (stocks, market info)
- Social media integration (Reddit, Twitter)
- Responsive, modern UI

### 🌐 **Web Scraping**
- Extract text content from any URL
- Clean HTML parsing with BeautifulSoup
- Automatic content saving

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Poetry (for dependency management)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd admin-portal

# Start the application (auto-installs dependencies)
./run.sh
```

**That's it!** The application will be available at http://localhost:8080

### Manual Setup (Alternative)

```bash
# Install dependencies
poetry install

# Create environment file
cp .env.example .env

# Start the application
poetry run python start.py
```

## 🔧 Configuration

### Admin Users
Edit `admin_users.json` to manage admin accounts:

```json
[
  {
    "username": "admin1",
    "password": "1234"
  }
]
```

### Environment Variables (Optional)
Copy `.env.example` to `.env` and configure:

- `FLASK_SECRET_KEY` - Required for sessions
- `NEWS_API_KEY` - For enhanced news features
- `REDDIT_CLIENT_ID/SECRET` - For Reddit integration
- Other API keys for extended functionality

## 📱 Usage

1. **Login**: Use `admin1` / `1234` (default)
2. **Upload Files**: Drag & drop or browse files
3. **Extract from URLs**: Paste any URL to extract content
4. **View News**: Real-time news dashboard
5. **Manage Files**: View and delete uploaded files

## 🛠️ Development

### Project Structure
```
admin-portal/
├── app.py              # Main Flask application
├── start.py            # Startup script
├── run.sh              # Setup & run script
├── pyproject.toml      # Poetry dependencies
├── utils/
│   ├── file_utils.py   # File & auth utilities
│   └── news_manager.py # News aggregation
├── templates/          # HTML templates
├── static/            # CSS, JS assets
└── uploads/           # File storage
```

### Adding Dependencies
```bash
poetry add package-name
```

### Development Tools
```bash
# Code formatting
poetry run black .

# Linting
poetry run flake8

# Tests
poetry run pytest
```

## 🎯 What's Different

This is a **simplified, focused version** that removes heavy AI/ML dependencies:

### ❌ **Removed:**
- LangChain (AI processing)
- Pinecone (vector database)
- OpenAI API integration
- AI chatbot functionality
- Complex document processing

### ✅ **Kept:**
- Clean file management
- News aggregation
- Web scraping
- Admin authentication
- Modern UI/UX

## 🚀 Deployment

### Production Setup
1. Set strong `FLASK_SECRET_KEY` in `.env`
2. Update admin passwords in `admin_users.json`
3. Configure reverse proxy (nginx)
4. Use gunicorn or waitress for production serving

### Docker (Optional)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install poetry && poetry install --no-dev
CMD ["poetry", "run", "python", "start.py"]
```

## 📄 License

MIT License - feel free to use and modify as needed.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Enjoy your clean, fast admin portal! 🎉**