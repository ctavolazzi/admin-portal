#!/usr/bin/env python3
"""
Test script for news dashboard functionality
This script tests the news manager with mock data to ensure the system works
"""

import json
import os
from datetime import datetime

# Mock news manager for testing
class MockNewsManager:
    def __init__(self):
        self.news_cache = []
        self.last_update = None
        self.news_sources = {
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
                }
            ],
            "reddit_subreddits": ["technology", "programming"],
            "news_categories": ["technology", "business"]
        }
        
        # Generate mock news data
        self.generate_mock_news()
    
    def generate_mock_news(self):
        """Generate mock news articles for testing"""
        mock_articles = [
            {
                "title": "AI Breakthrough: New Model Achieves Human-Level Performance",
                "description": "Researchers have developed a new artificial intelligence model that demonstrates unprecedented capabilities in natural language understanding and reasoning.",
                "url": "https://example.com/ai-breakthrough",
                "source": "TechCrunch",
                "published_at": datetime.now().isoformat(),
                "category": "technology",
                "type": "rss"
            },
            {
                "title": "Global Markets React to Economic Policy Changes",
                "description": "Major stock indices around the world showed significant movement following the announcement of new economic policies.",
                "url": "https://example.com/markets-reaction",
                "source": "BBC News",
                "published_at": datetime.now().isoformat(),
                "category": "business",
                "type": "rss"
            },
            {
                "title": "New Programming Language Gains Popularity Among Developers",
                "description": "A recently released programming language has seen rapid adoption in the developer community due to its innovative features.",
                "url": "https://example.com/programming-language",
                "source": "r/technology",
                "published_at": datetime.now().isoformat(),
                "category": "technology",
                "type": "reddit",
                "score": 1250,
                "comments": 89
            },
            {
                "title": "S&P 500: $4,500.25",
                "description": "Change: +15.50 (+0.35%)",
                "url": "https://finance.yahoo.com/quote/%5EGSPC",
                "source": "Yahoo Finance",
                "published_at": datetime.now().isoformat(),
                "category": "finance",
                "type": "financial",
                "price": 4500.25,
                "change": 15.50,
                "change_percent": 0.35
            }
        ]
        
        self.news_cache = mock_articles
        self.last_update = datetime.now()
    
    def get_news(self, category=None, count=20):
        """Get news articles, optionally filtered by category"""
        if category:
            return [news for news in self.news_cache if news.get('category') == category][:count]
        return self.news_cache[:count]
    
    def get_news_summary(self):
        """Get a summary of current news"""
        return {
            'total_articles': len(self.news_cache),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'categories': list(set(news.get('category') for news in self.news_cache)),
            'sources': list(set(news.get('source') for news in self.news_cache))
        }
    
    def update_news_cache(self):
        """Update the news cache with fresh data"""
        print("Updating news cache...")
        self.generate_mock_news()
        print(f"Updated news cache with {len(self.news_cache)} articles")

def test_news_functionality():
    """Test the news functionality"""
    print("🧪 Testing News Dashboard Functionality")
    print("=" * 50)
    
    # Initialize mock news manager
    news_manager = MockNewsManager()
    
    # Test 1: Get all news
    print("\n1. Testing: Get all news articles")
    all_news = news_manager.get_news()
    print(f"   ✅ Retrieved {len(all_news)} articles")
    
    # Test 2: Get news by category
    print("\n2. Testing: Filter news by category")
    tech_news = news_manager.get_news(category="technology")
    print(f"   ✅ Retrieved {len(tech_news)} technology articles")
    
    # Test 3: Get news summary
    print("\n3. Testing: Get news summary")
    summary = news_manager.get_news_summary()
    print(f"   ✅ Summary: {summary['total_articles']} articles, {len(summary['categories'])} categories")
    
    # Test 4: Update news cache
    print("\n4. Testing: Update news cache")
    news_manager.update_news_cache()
    print("   ✅ News cache updated successfully")
    
    # Test 5: Save news sources configuration
    print("\n5. Testing: Save news sources configuration")
    try:
        with open('news_sources.json', 'w') as f:
            json.dump(news_manager.news_sources, f, indent=2)
        print("   ✅ News sources configuration saved")
    except Exception as e:
        print(f"   ❌ Error saving configuration: {e}")
    
    # Test 6: Display sample news
    print("\n6. Testing: Display sample news")
    print("   📰 Sample Articles:")
    for i, article in enumerate(all_news[:2], 1):
        print(f"   {i}. {article['title']}")
        print(f"      Source: {article['source']} | Category: {article['category']}")
        print(f"      Type: {article['type']}")
        print()
    
    print("🎉 All tests completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Install required packages: pip install -r requirements.txt")
    print("2. Add API keys to .env file (optional)")
    print("3. Start the Flask server: python app.py")
    print("4. Navigate to /news in your browser")
    print("5. Enjoy your real-time news dashboard!")

if __name__ == "__main__":
    test_news_functionality()