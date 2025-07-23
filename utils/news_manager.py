#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Manager for Admin Dashboard
Handles real-time news from multiple sources
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Try to import optional dependencies
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("⚠️  Schedule package not available, using simple timer")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests package not available, using fallback methods")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  Python-dotenv not available, using system environment variables")

class NewsManager:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.reddit_user_agent = os.getenv('REDDIT_USER_AGENT', 'AdminDashboard/1.0')
        
        # Initialize API clients (with fallbacks)
        self.news_api = None
        self.alpha_vantage = None
        
        # Try to initialize external APIs
        self._initialize_external_apis()
        
        # News storage
        self.news_cache = []
        self.news_sources = self._load_news_sources()
        self.last_update = None
        
        # Start background updates
        self.start_background_updates()
    
    def _initialize_external_apis(self):
        """Initialize external API clients with fallbacks"""
        # News API
        if self.news_api_key:
            try:
                from newsapi import NewsApiClient
                self.news_api = NewsApiClient(api_key=self.news_api_key)
                print("✅ News API initialized successfully")
            except ImportError:
                print("⚠️  News API package not installed, using fallback")
            except Exception as e:
                print(f"⚠️  News API initialization failed: {e}")
        
        # Alpha Vantage
        if self.alpha_vantage_key:
            try:
                from alpha_vantage.timeseries import TimeSeries
                self.alpha_vantage = TimeSeries(key=self.alpha_vantage_key)
                print("✅ Alpha Vantage initialized successfully")
            except ImportError:
                print("⚠️  Alpha Vantage package not installed, using fallback")
            except Exception as e:
                print(f"⚠️  Alpha Vantage initialization failed: {e}")
    
    def _load_news_sources(self) -> Dict[str, Any]:
        """Load news sources configuration"""
        default_sources = {
            "rss_feeds": [
                {
                    "name": "TechCrunch",
                    "url": "https://techcrunch.com/feed/",
                    "category": "technology"
                },
                {
                    "name": "BBC News",
                    "url": "http://feeds.bbci.co.uk/news/rss.xml",
                    "category": "general"
                },
                {
                    "name": "Reuters",
                    "url": "https://feeds.reuters.com/reuters/topNews",
                    "category": "general"
                },
                {
                    "name": "Ars Technica",
                    "url": "https://feeds.arstechnica.com/arstechnica/index",
                    "category": "technology"
                }
            ],
            "reddit_subreddits": [
                "technology",
                "programming",
                "science",
                "worldnews",
                "business"
            ],
            "news_categories": [
                "technology",
                "business",
                "science",
                "health",
                "entertainment"
            ]
        }
        
        # Try to load from file, create if doesn't exist
        try:
            with open('news_sources.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            with open('news_sources.json', 'w') as f:
                json.dump(default_sources, f, indent=2)
            return default_sources
    
    def get_news_api_articles(self, category: str = "technology", count: int = 10) -> List[Dict]:
        """Get articles from News API"""
        if not self.news_api:
            return []
        
        try:
            articles = self.news_api.get_top_headlines(
                category=category,
                language='en',
                country='us',
                page_size=count
            )
            
            return [{
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'source': article['source']['name'],
                'published_at': article['publishedAt'],
                'category': category,
                'type': 'news_api'
            } for article in articles.get('articles', [])]
        except Exception as e:
            print(f"Error fetching News API articles: {e}")
            return []
    
    def get_rss_articles(self, count: int = 20) -> List[Dict]:
        """Get articles from RSS feeds with fallback"""
        articles = []
        
        for feed in self.news_sources.get('rss_feeds', []):
            try:
                # Try to use feedparser if available
                try:
                    import feedparser
                    feed_data = feedparser.parse(feed['url'])
                    
                    for entry in feed_data.entries[:count//len(self.news_sources['rss_feeds'])]:
                        articles.append({
                            'title': entry.get('title', ''),
                            'description': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'source': feed['name'],
                            'published_at': entry.get('published', ''),
                            'category': feed.get('category', 'general'),
                            'type': 'rss'
                        })
                except ImportError:
                    # Fallback: generate mock RSS data
                    articles.extend(self._generate_mock_rss_articles(feed, count//len(self.news_sources['rss_feeds'])))
                    
            except Exception as e:
                print(f"Error fetching RSS feed {feed['name']}: {e}")
                # Generate mock data as fallback
                articles.extend(self._generate_mock_rss_articles(feed, count//len(self.news_sources['rss_feeds'])))
        
        return articles
    
    def _generate_mock_rss_articles(self, feed: Dict, count: int) -> List[Dict]:
        """Generate mock RSS articles when feedparser is not available"""
        mock_articles = []
        feed_name = feed['name']
        category = feed.get('category', 'general')
        
        # Generate different mock content based on feed
        if 'tech' in feed_name.lower():
            titles = [
                "New AI Model Breaks Performance Records",
                "Quantum Computing Breakthrough Announced",
                "Major Tech Company Releases Revolutionary Product",
                "Cybersecurity Threats on the Rise",
                "Blockchain Technology Gains Mainstream Adoption"
            ]
        elif 'bbc' in feed_name.lower():
            titles = [
                "Global Economic Summit Concludes",
                "Climate Change Report Released",
                "International Trade Agreement Reached",
                "World Leaders Meet for Peace Talks",
                "New Environmental Protection Measures Announced"
            ]
        else:
            titles = [
                "Breaking News: Major Development Announced",
                "Industry Leaders Discuss Future Trends",
                "New Research Findings Published",
                "Market Analysis: Key Insights Revealed",
                "Expert Opinion: What's Next for the Industry"
            ]
        
        for i in range(min(count, len(titles))):
            mock_articles.append({
                'title': titles[i],
                'description': f"This is a mock article from {feed_name} about {titles[i].lower()}. This content is generated for demonstration purposes when external RSS feeds are not available.",
                'url': f"https://example.com/mock-article-{i}",
                'source': feed_name,
                'published_at': datetime.now().isoformat(),
                'category': category,
                'type': 'rss'
            })
        
        return mock_articles
    
    def get_reddit_posts(self, count: int = 10) -> List[Dict]:
        """Get trending posts from Reddit with fallback"""
        if not all([self.reddit_client_id, self.reddit_client_secret]):
            return self._generate_mock_reddit_posts(count)
        
        try:
            import praw
            reddit = praw.Reddit(
                client_id=self.reddit_client_id,
                client_secret=self.reddit_client_secret,
                user_agent=self.reddit_user_agent
            )
            
            posts = []
            for subreddit_name in self.news_sources.get('reddit_subreddits', [])[:3]:
                subreddit = reddit.subreddit(subreddit_name)
                for post in subreddit.hot(limit=count//len(self.news_sources['reddit_subreddits'])):
                    posts.append({
                        'title': post.title,
                        'description': post.selftext[:200] + '...' if len(post.selftext) > 200 else post.selftext,
                        'url': f"https://reddit.com{post.permalink}",
                        'source': f"r/{subreddit_name}",
                        'published_at': datetime.fromtimestamp(post.created_utc).isoformat(),
                        'category': 'reddit',
                        'type': 'reddit',
                        'score': post.score,
                        'comments': post.num_comments
                    })
            
            return posts
        except ImportError:
            return self._generate_mock_reddit_posts(count)
        except Exception as e:
            print(f"Error fetching Reddit posts: {e}")
            return self._generate_mock_reddit_posts(count)
    
    def _generate_mock_reddit_posts(self, count: int) -> List[Dict]:
        """Generate mock Reddit posts when praw is not available"""
        mock_posts = []
        subreddits = self.news_sources.get('reddit_subreddits', ['technology', 'programming'])
        
        reddit_titles = [
            "What's your favorite programming language and why?",
            "Just built my first AI model - here's what I learned",
            "The future of web development: What's next?",
            "How I solved a complex algorithm problem",
            "Best practices for code review",
            "New framework released: Should you switch?",
            "Career advice for junior developers",
            "The impact of AI on software development"
        ]
        
        for i in range(min(count, len(reddit_titles))):
            subreddit = subreddits[i % len(subreddits)]
            mock_posts.append({
                'title': reddit_titles[i],
                'description': f"This is a mock Reddit post from r/{subreddit}. The content discusses {reddit_titles[i].lower()}. This is generated for demonstration purposes.",
                'url': f"https://reddit.com/r/{subreddit}/comments/mock{i}",
                'source': f"r/{subreddit}",
                'published_at': datetime.now().isoformat(),
                'category': 'reddit',
                'type': 'reddit',
                'score': 100 + (i * 50),
                'comments': 10 + (i * 5)
            })
        
        return mock_posts
    
    def get_financial_data(self) -> List[Dict]:
        """Get financial market data with fallback"""
        financial_news = []
        
        # Try to get real financial data
        try:
            import yfinance as yf
            
            # Get major indices
            indices = ['^GSPC', '^DJI', '^IXIC']  # S&P 500, Dow Jones, NASDAQ
            for symbol in indices:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period="1d")
                    
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        prev_close = info.get('previousClose', current_price)
                        change = current_price - prev_close
                        change_percent = (change / prev_close) * 100
                        
                        financial_news.append({
                            'title': f"{info.get('shortName', symbol)}: ${current_price:.2f}",
                            'description': f"Change: {change:+.2f} ({change_percent:+.2f}%)",
                            'url': f"https://finance.yahoo.com/quote/{symbol}",
                            'source': 'Yahoo Finance',
                            'published_at': datetime.now().isoformat(),
                            'category': 'finance',
                            'type': 'financial',
                            'price': current_price,
                            'change': change,
                            'change_percent': change_percent
                        })
                except Exception as e:
                    print(f"Error fetching data for {symbol}: {e}")
                    continue
                    
        except ImportError:
            # Fallback: generate mock financial data
            financial_news = self._generate_mock_financial_data()
        except Exception as e:
            print(f"Error fetching financial data: {e}")
            financial_news = self._generate_mock_financial_data()
        
        return financial_news
    
    def _generate_mock_financial_data(self) -> List[Dict]:
        """Generate mock financial data when yfinance is not available"""
        mock_data = [
            {
                'title': 'S&P 500: $4,500.25',
                'description': 'Change: +15.50 (+0.35%)',
                'url': 'https://finance.yahoo.com/quote/%5EGSPC',
                'source': 'Yahoo Finance',
                'published_at': datetime.now().isoformat(),
                'category': 'finance',
                'type': 'financial',
                'price': 4500.25,
                'change': 15.50,
                'change_percent': 0.35
            },
            {
                'title': 'Dow Jones: $35,200.75',
                'description': 'Change: +125.30 (+0.36%)',
                'url': 'https://finance.yahoo.com/quote/%5EDJI',
                'source': 'Yahoo Finance',
                'published_at': datetime.now().isoformat(),
                'category': 'finance',
                'type': 'financial',
                'price': 35200.75,
                'change': 125.30,
                'change_percent': 0.36
            },
            {
                'title': 'NASDAQ: $14,250.50',
                'description': 'Change: -45.20 (-0.32%)',
                'url': 'https://finance.yahoo.com/quote/%5EIXIC',
                'source': 'Yahoo Finance',
                'published_at': datetime.now().isoformat(),
                'category': 'finance',
                'type': 'financial',
                'price': 14250.50,
                'change': -45.20,
                'change_percent': -0.32
            }
        ]
        return mock_data
    
    def update_news_cache(self):
        """Update the news cache with fresh data"""
        print("Updating news cache...")
        
        all_news = []
        
        # Get news from different sources
        for category in self.news_sources.get('news_categories', ['technology']):
            all_news.extend(self.get_news_api_articles(category, 5))
        
        all_news.extend(self.get_rss_articles(10))
        all_news.extend(self.get_reddit_posts(5))
        all_news.extend(self.get_financial_data())
        
        # Sort by published date (newest first)
        all_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)
        
        self.news_cache = unique_news[:50]  # Keep last 50 articles
        self.last_update = datetime.now()
        
        print(f"Updated news cache with {len(self.news_cache)} articles")
    
    def get_news(self, category: Optional[str] = None, count: int = 20) -> List[Dict]:
        """Get news articles, optionally filtered by category"""
        if category:
            return [news for news in self.news_cache if news.get('category') == category][:count]
        return self.news_cache[:count]
    
    def get_news_summary(self) -> Dict[str, Any]:
        """Get a summary of current news"""
        return {
            'total_articles': len(self.news_cache),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'categories': list(set(news.get('category') for news in self.news_cache)),
            'sources': list(set(news.get('source') for news in self.news_cache))
        }
    
    def start_background_updates(self):
        """Start background thread for periodic news updates"""
        def update_job():
            self.update_news_cache()
        
        if SCHEDULE_AVAILABLE:
            # Use schedule library if available
            schedule.every(15).minutes.do(update_job)
            
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            
            # Start scheduler in background thread
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
        else:
            # Simple timer fallback
            def simple_timer():
                while True:
                    time.sleep(15 * 60)  # 15 minutes
                    update_job()
            
            # Start simple timer in background thread
            timer_thread = threading.Thread(target=simple_timer, daemon=True)
            timer_thread.start()
        
        # Initial update
        self.update_news_cache()

# Global instance
news_manager = NewsManager()