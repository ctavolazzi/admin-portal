# Real-Time News Dashboard

A comprehensive real-time news aggregation system integrated into your admin dashboard. This feature provides live news updates from multiple sources including RSS feeds, News API, Reddit, and financial data.

## Features

### 🚀 Real-Time News Sources
- **News API Integration** - Top headlines from various categories
- **RSS Feed Aggregation** - Customizable RSS feeds from your favorite sources
- **Reddit Integration** - Trending posts from popular subreddits
- **Financial Data** - Real-time stock market information
- **Background Updates** - Automatic refresh every 15 minutes

### 🎨 Modern UI/UX
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Grid & List Views** - Switch between different viewing modes
- **Advanced Filtering** - Filter by category, source, and search terms
- **Real-Time Updates** - Live notifications and auto-refresh
- **Beautiful Animations** - Smooth transitions and hover effects

### 🔧 Interactive Features
- **Article Actions** - Share and bookmark articles
- **Customizable Sources** - Add/remove RSS feeds and subreddits
- **Search Functionality** - Search across titles, descriptions, and sources
- **Time Tracking** - See when articles were published
- **Category Management** - Organize news by categories

## Setup Instructions

### 1. Install Dependencies

The news dashboard requires additional Python packages. Install them using:

```bash
pip install -r requirements.txt
```

### 2. API Keys (Optional but Recommended)

For full functionality, add the following API keys to your `.env` file:

#### News API (Free tier available)
1. Go to [https://newsapi.org/](https://newsapi.org/)
2. Sign up for a free account
3. Get your API key
4. Add to `.env`: `NEWS_API_KEY=your_api_key_here`

#### Reddit API (Optional)
1. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Create a new app (select "script")
3. Get your client ID and secret
4. Add to `.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=AdminDashboard/1.0
   ```

#### Alpha Vantage (Financial Data - Optional)
1. Go to [https://www.alphavantage.co/](https://www.alphavantage.co/)
2. Get a free API key
3. Add to `.env`: `ALPHA_VANTAGE_KEY=your_api_key_here`

### 3. Default Configuration

The system comes with pre-configured news sources:

#### RSS Feeds
- TechCrunch (Technology)
- BBC News (General)
- Reuters (General)
- Ars Technica (Technology)

#### Reddit Subreddits
- r/technology
- r/programming
- r/science
- r/worldnews
- r/business

#### News Categories
- Technology
- Business
- Science
- Health
- Entertainment

### 4. Customization

You can customize news sources through the web interface or by editing `news_sources.json`:

```json
{
  "rss_feeds": [
    {
      "name": "Your Feed Name",
      "url": "https://example.com/feed.xml",
      "category": "technology"
    }
  ],
  "reddit_subreddits": [
    "your_subreddit_name"
  ],
  "news_categories": [
    "your_category"
  ]
}
```

## Usage

### Accessing the News Dashboard

1. Start your Flask application: `python app.py`
2. Navigate to your admin dashboard
3. Click on the "News" link in the header
4. Or go directly to `/news`

### Dashboard Features

#### Summary Cards
- **Total Articles** - Number of articles in the cache
- **Last Update** - When the news was last refreshed
- **Categories** - Number of different news categories
- **Refresh Button** - Manually refresh news

#### Filtering & Search
- **Category Filter** - Filter by news category
- **Source Filter** - Filter by news source
- **Search Box** - Search across titles and descriptions
- **View Toggle** - Switch between grid and list views

#### Article Actions
- **Click Article** - Opens the full article in a new tab
- **Share Button** - Share article via native sharing or copy link
- **Bookmark Button** - Save article to local storage

### Managing News Sources

1. Click the "Configure Sources" button (if available)
2. Add/remove RSS feeds, Reddit subreddits, or news categories
3. Save changes to update your news sources
4. News will automatically refresh with new sources

## Technical Details

### Architecture

```
news_manager.py          # Core news management logic
├── NewsManager class    # Main news aggregation class
├── Background updates   # Scheduled news refresh
└── Multiple sources     # RSS, API, Reddit, Financial

app.py                   # Flask routes
├── /news               # News dashboard page
├── /api/news           # Get news articles
├── /api/news/summary   # Get news summary
├── /api/news/refresh   # Manual refresh
└── /api/news/sources   # Manage sources

templates/news.html      # News dashboard template
static/
├── news_style.css      # Styling for news dashboard
└── news.js            # Interactive JavaScript
```

### Data Flow

1. **Background Updates** - NewsManager runs scheduled updates every 15 minutes
2. **API Endpoints** - Flask routes serve news data to the frontend
3. **Frontend** - JavaScript handles display, filtering, and user interactions
4. **Caching** - News is cached in memory for fast access

### Performance

- **Caching** - News articles are cached in memory
- **Background Updates** - Non-blocking updates via threading
- **Pagination** - Load more articles as needed
- **Optimized Queries** - Efficient filtering and search

## Troubleshooting

### Common Issues

#### No News Loading
- Check if API keys are properly set in `.env`
- Verify internet connection
- Check browser console for errors
- Ensure Flask server is running

#### RSS Feeds Not Working
- Verify RSS feed URLs are accessible
- Check if feeds are properly formatted
- Some feeds may require authentication

#### Reddit Integration Issues
- Verify Reddit API credentials
- Check if subreddit names are correct
- Reddit API has rate limits

#### Financial Data Not Showing
- Verify Alpha Vantage API key
- Check if stock symbols are valid
- Financial data may be delayed

### Debug Mode

To enable debug logging, add to your Flask app:

```python
app.debug = True
```

### Manual Refresh

If automatic updates aren't working, you can manually refresh:

1. Click the "Refresh" button in the dashboard
2. Or call the API endpoint: `POST /api/news/refresh`

## API Reference

### GET /api/news
Get news articles with optional filtering.

**Query Parameters:**
- `category` (optional) - Filter by category
- `count` (optional) - Number of articles (default: 20)

**Response:**
```json
[
  {
    "title": "Article Title",
    "description": "Article description...",
    "url": "https://example.com/article",
    "source": "Source Name",
    "published_at": "2023-01-01T12:00:00Z",
    "category": "technology",
    "type": "news_api"
  }
]
```

### GET /api/news/summary
Get news summary statistics.

**Response:**
```json
{
  "total_articles": 50,
  "last_update": "2023-01-01T12:00:00Z",
  "categories": ["technology", "business"],
  "sources": ["TechCrunch", "BBC News"]
}
```

### POST /api/news/refresh
Manually refresh the news cache.

**Response:**
```json
{
  "status": "success",
  "message": "News cache updated"
}
```

### GET /api/news/sources
Get current news sources configuration.

### POST /api/news/sources
Update news sources configuration.

**Request Body:**
```json
{
  "rss_feeds": [...],
  "reddit_subreddits": [...],
  "news_categories": [...]
}
```

## Contributing

To add new news sources or features:

1. **New RSS Feed** - Add to `news_sources.json` or use the web interface
2. **New API Integration** - Extend the `NewsManager` class
3. **UI Improvements** - Modify `news_style.css` and `news.js`
4. **Backend Features** - Add new routes to `app.py`

## License

This news dashboard feature is part of the admin portal project and follows the same MIT license.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the browser console for JavaScript errors
3. Check Flask server logs for backend errors
4. Verify API keys and network connectivity