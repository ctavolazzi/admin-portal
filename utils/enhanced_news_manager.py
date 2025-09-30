#!/usr/bin/env python3
"""
Enhanced News Intelligence Manager
Supports multiple free APIs, custom topics, and smart filtering
"""

import os
import json
import time
import threading
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlencode
import requests
from collections import defaultdict, Counter

class EnhancedNewsManager:
    def __init__(self):
        # API Keys (optional - works without them)
        self.guardian_api_key = os.getenv('GUARDIAN_API_KEY')
        self.nytimes_api_key = os.getenv('NYTIMES_API_KEY')
        self.news_api_key = os.getenv('NEWS_API_KEY')

        # Free APIs (no key required)
        self.free_apis = {
            'hackernews': 'https://hacker-news.firebaseio.com/v0/',
            'github_trending': 'https://api.github.com/search/repositories',
            'lobsters': 'https://lobste.rs/',
            'coingecko': 'https://api.coingecko.com/api/v3/'
        }

        # Data storage
        self.news_cache = []
        self.user_topics = self._load_user_topics()
        self.search_cache = {}
        self.last_update = None

        # Smart features
        self.duplicate_detector = DuplicateDetector()
        self.topic_tracker = TopicTracker()
        self.sentiment_analyzer = SentimentAnalyzer()

        # Start background updates
        self.start_enhanced_updates()

    def _load_user_topics(self) -> Dict[str, Any]:
        """Load user-defined topics and search terms"""
        default_topics = {
            "technology": {
                "keywords": ["AI", "machine learning", "blockchain", "crypto", "programming"],
                "sources": ["hackernews", "github", "techcrunch"],
                "priority": 1.0,
                "created": datetime.now().isoformat(),
                "alerts": True
            },
            "business": {
                "keywords": ["startup", "funding", "IPO", "market", "economy"],
                "sources": ["guardian", "nytimes", "reuters"],
                "priority": 0.8,
                "created": datetime.now().isoformat(),
                "alerts": False
            },
            "science": {
                "keywords": ["research", "discovery", "climate", "space", "health"],
                "sources": ["guardian", "nytimes"],
                "priority": 0.6,
                "created": datetime.now().isoformat(),
                "alerts": False
            }
        }

        try:
            with open('user_topics.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            with open('user_topics.json', 'w') as f:
                json.dump(default_topics, f, indent=2)
            return default_topics

    def save_user_topics(self):
        """Save user topics to file"""
        with open('user_topics.json', 'w') as f:
            json.dump(self.user_topics, f, indent=2)

    def add_custom_topic(self, name: str, keywords: List[str], sources: List[str] = None, priority: float = 1.0):
        """Add a new custom topic for tracking"""
        self.user_topics[name] = {
            "keywords": keywords,
            "sources": sources or ["all"],
            "priority": priority,
            "created": datetime.now().isoformat(),
            "alerts": False
        }
        self.save_user_topics()
        return f"✅ Added topic '{name}' with {len(keywords)} keywords"

    def get_guardian_articles(self, query: str = None, count: int = 10) -> List[Dict]:
        """Get articles from Guardian API"""
        if not self.guardian_api_key:
            return self._get_mock_guardian_articles(count)

        try:
            params = {
                'api-key': self.guardian_api_key,
                'page-size': count,
                'show-fields': 'headline,trailText,thumbnail,short-url',
                'order-by': 'newest'
            }

            if query:
                params['q'] = query

            url = f"https://content.guardianapis.com/search?{urlencode(params)}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            articles = []

            for item in data.get('response', {}).get('results', []):
                articles.append({
                    'title': item.get('webTitle', ''),
                    'description': item.get('fields', {}).get('trailText', ''),
                    'url': item.get('webUrl', ''),
                    'source': 'The Guardian',
                    'published_at': item.get('webPublicationDate', ''),
                    'category': item.get('sectionName', 'general'),
                    'type': 'guardian',
                    'thumbnail': item.get('fields', {}).get('thumbnail', ''),
                    'api_source': 'guardian'
                })

            return articles

        except Exception as e:
            print(f"Error fetching Guardian articles: {e}")
            return self._get_mock_guardian_articles(count)

    def _get_mock_guardian_articles(self, count: int) -> List[Dict]:
        """Generate mock Guardian articles"""
        mock_articles = [
            {
                'title': 'Climate Summit Reaches Historic Agreement on Carbon Reduction',
                'description': 'World leaders commit to ambitious new targets for greenhouse gas emissions in landmark deal.',
                'url': 'https://www.theguardian.com/environment/mock-climate-summit',
                'source': 'The Guardian',
                'published_at': datetime.now().isoformat(),
                'category': 'environment',
                'type': 'guardian',
                'api_source': 'guardian_mock'
            },
            {
                'title': 'Tech Giants Face New Privacy Regulations in Europe',
                'description': 'European Union introduces stricter data protection rules affecting major technology companies.',
                'url': 'https://www.theguardian.com/technology/mock-privacy-rules',
                'source': 'The Guardian',
                'published_at': datetime.now().isoformat(),
                'category': 'technology',
                'type': 'guardian',
                'api_source': 'guardian_mock'
            },
            {
                'title': 'Breakthrough in Quantum Computing Research',
                'description': 'Scientists achieve new milestone in quantum processor development with 99% accuracy.',
                'url': 'https://www.theguardian.com/science/mock-quantum-breakthrough',
                'source': 'The Guardian',
                'published_at': datetime.now().isoformat(),
                'category': 'science',
                'type': 'guardian',
                'api_source': 'guardian_mock'
            }
        ]
        return mock_articles[:count]

    def get_hackernews_articles(self, count: int = 10) -> List[Dict]:
        """Get trending articles from Hacker News (completely free)"""
        try:
            # Get top stories
            top_stories_url = f"{self.free_apis['hackernews']}topstories.json"
            response = requests.get(top_stories_url, timeout=10)
            response.raise_for_status()

            story_ids = response.json()[:count]
            articles = []

            for story_id in story_ids:
                try:
                    story_url = f"{self.free_apis['hackernews']}item/{story_id}.json"
                    story_response = requests.get(story_url, timeout=5)
                    story_data = story_response.json()

                    if story_data and story_data.get('type') == 'story':
                        articles.append({
                            'title': story_data.get('title', ''),
                            'description': f"HN Score: {story_data.get('score', 0)} | Comments: {story_data.get('descendants', 0)}",
                            'url': story_data.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                            'source': 'Hacker News',
                            'published_at': datetime.fromtimestamp(story_data.get('time', 0)).isoformat(),
                            'category': 'technology',
                            'type': 'hackernews',
                            'score': story_data.get('score', 0),
                            'comments': story_data.get('descendants', 0),
                            'api_source': 'hackernews'
                        })
                except Exception as e:
                    continue

            return articles

        except Exception as e:
            print(f"Error fetching Hacker News articles: {e}")
            return self._get_mock_hackernews_articles(count)

    def _get_mock_hackernews_articles(self, count: int) -> List[Dict]:
        """Generate mock Hacker News articles"""
        mock_articles = [
            {
                'title': 'New JavaScript Framework Promises Zero Bundle Size',
                'description': 'HN Score: 234 | Comments: 89',
                'url': 'https://news.ycombinator.com/item?id=mock1',
                'source': 'Hacker News',
                'published_at': datetime.now().isoformat(),
                'category': 'technology',
                'type': 'hackernews',
                'score': 234,
                'comments': 89,
                'api_source': 'hackernews_mock'
            },
            {
                'title': 'Ask HN: Best practices for system design interviews?',
                'description': 'HN Score: 156 | Comments: 67',
                'url': 'https://news.ycombinator.com/item?id=mock2',
                'source': 'Hacker News',
                'published_at': datetime.now().isoformat(),
                'category': 'technology',
                'type': 'hackernews',
                'score': 156,
                'comments': 67,
                'api_source': 'hackernews_mock'
            }
        ]
        return mock_articles[:count]

    def get_github_trending(self, language: str = None, count: int = 10) -> List[Dict]:
        """Get trending repositories from GitHub (free, no auth required)"""
        try:
            # Search for trending repos (starred in last week)
            date_filter = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            query = f"stars:>1 created:>{date_filter}"

            if language:
                query += f" language:{language}"

            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': count
            }

            url = f"{self.free_apis['github_trending']}?{urlencode(params)}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            articles = []

            for repo in data.get('items', []):
                articles.append({
                    'title': f"🚀 {repo.get('name')} - {repo.get('description', '')[:100]}",
                    'description': f"⭐ {repo.get('stargazers_count')} stars | Language: {repo.get('language', 'Unknown')}",
                    'url': repo.get('html_url', ''),
                    'source': 'GitHub Trending',
                    'published_at': repo.get('created_at', ''),
                    'category': 'programming',
                    'type': 'github',
                    'stars': repo.get('stargazers_count', 0),
                    'language': repo.get('language', ''),
                    'api_source': 'github'
                })

            return articles

        except Exception as e:
            print(f"Error fetching GitHub trending: {e}")
            return self._get_mock_github_articles(count)

    def _get_mock_github_articles(self, count: int) -> List[Dict]:
        """Generate mock GitHub trending articles"""
        mock_articles = [
            {
                'title': '🚀 awesome-ai-tools - Curated list of AI development tools',
                'description': '⭐ 1,234 stars | Language: Python',
                'url': 'https://github.com/mock/awesome-ai-tools',
                'source': 'GitHub Trending',
                'published_at': datetime.now().isoformat(),
                'category': 'programming',
                'type': 'github',
                'stars': 1234,
                'language': 'Python',
                'api_source': 'github_mock'
            },
            {
                'title': '🚀 fast-api-template - Production-ready FastAPI template',
                'description': '⭐ 567 stars | Language: Python',
                'url': 'https://github.com/mock/fast-api-template',
                'source': 'GitHub Trending',
                'published_at': datetime.now().isoformat(),
                'category': 'programming',
                'type': 'github',
                'stars': 567,
                'language': 'Python',
                'api_source': 'github_mock'
            }
        ]
        return mock_articles[:count]

    def get_crypto_news(self, count: int = 5) -> List[Dict]:
        """Get cryptocurrency news from CoinGecko (completely free)"""
        try:
            url = f"{self.free_apis['coingecko']}coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': count,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            articles = []

            for coin in data:
                price_change = coin.get('price_change_percentage_24h', 0)
                trend = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"

                articles.append({
                    'title': f"{trend} {coin.get('name')} ({coin.get('symbol', '').upper()}): ${coin.get('current_price', 0):.2f}",
                    'description': f"24h Change: {price_change:.2f}% | Market Cap: ${coin.get('market_cap', 0):,.0f}",
                    'url': f"https://www.coingecko.com/en/coins/{coin.get('id')}",
                    'source': 'CoinGecko',
                    'published_at': datetime.now().isoformat(),
                    'category': 'cryptocurrency',
                    'type': 'crypto',
                    'price': coin.get('current_price', 0),
                    'change_24h': price_change,
                    'api_source': 'coingecko'
                })

            return articles

        except Exception as e:
            print(f"Error fetching crypto news: {e}")
            return []

    def search_articles(self, query: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """Advanced search with filters"""
        filters = filters or {}

        # Check cache first
        cache_key = f"{query}_{hash(str(filters))}"
        if cache_key in self.search_cache:
            cached_result, cached_time = self.search_cache[cache_key]
            if (datetime.now() - cached_time).seconds < 300:  # 5 minute cache
                return cached_result

        # Search across all cached articles
        results = []
        query_lower = query.lower()

        for article in self.news_cache:
            # Text matching
            if (query_lower in article.get('title', '').lower() or
                query_lower in article.get('description', '').lower()):

                # Apply filters
                if self._article_matches_filters(article, filters):
                    # Add relevance score
                    article['relevance_score'] = self._calculate_relevance(article, query)
                    results.append(article)

        # Sort by relevance and date
        results.sort(key=lambda x: (x.get('relevance_score', 0), x.get('published_at', '')), reverse=True)

        # Cache results
        self.search_cache[cache_key] = (results, datetime.now())

        return results

    def _article_matches_filters(self, article: Dict, filters: Dict) -> bool:
        """Check if article matches applied filters"""
        if filters.get('category') and article.get('category') != filters['category']:
            return False

        if filters.get('source') and article.get('source') != filters['source']:
            return False

        if filters.get('date_from'):
            try:
                article_date = datetime.fromisoformat(article.get('published_at', '').replace('Z', '+00:00'))
                filter_date = datetime.fromisoformat(filters['date_from'])
                if article_date < filter_date:
                    return False
            except:
                pass

        return True

    def _calculate_relevance(self, article: Dict, query: str) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = query.lower()

        # Title match (higher weight)
        if query_lower in article.get('title', '').lower():
            score += 2.0

        # Description match
        if query_lower in article.get('description', '').lower():
            score += 1.0

        # Boost for certain sources
        if article.get('source') in ['Hacker News', 'The Guardian']:
            score += 0.5

        return score

    def get_trending_topics(self, days: int = 7) -> List[Dict]:
        """Analyze trending topics from recent articles"""
        return self.topic_tracker.get_trending_topics(self.news_cache, days)

    def update_enhanced_cache(self):
        """Enhanced cache update with multiple sources"""
        print("🔄 Updating enhanced news cache...")

        all_articles = []

        # Collect from all sources
        try:
            all_articles.extend(self.get_guardian_articles(count=15))
            all_articles.extend(self.get_hackernews_articles(count=10))
            all_articles.extend(self.get_github_trending(count=8))
            all_articles.extend(self.get_crypto_news(count=5))

            # Add topic-based searches
            for topic_name, topic_data in self.user_topics.items():
                for keyword in topic_data.get('keywords', [])[:3]:  # Limit API calls
                    all_articles.extend(self.get_guardian_articles(query=keyword, count=3))

        except Exception as e:
            print(f"Error updating cache: {e}")

        # Process articles
        unique_articles = self.duplicate_detector.remove_duplicates(all_articles)
        analyzed_articles = self.sentiment_analyzer.analyze_articles(unique_articles)

        # Sort by date and relevance
        analyzed_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)

        self.news_cache = analyzed_articles[:100]  # Keep top 100
        self.last_update = datetime.now()

        print(f"✅ Updated cache with {len(self.news_cache)} unique articles")

    def start_enhanced_updates(self):
        """Start enhanced background updates"""
        def update_job():
            self.update_enhanced_cache()

        # Initial update
        update_job()

        # Background updates every 10 minutes
        def background_updater():
            while True:
                time.sleep(600)  # 10 minutes
                update_job()

        update_thread = threading.Thread(target=background_updater, daemon=True)
        update_thread.start()

    def get_topic_articles(self, topic_name: str, count: int = 20) -> List[Dict]:
        """Get articles for a specific user-defined topic"""
        if topic_name not in self.user_topics:
            return []

        topic_data = self.user_topics[topic_name]
        keywords = topic_data.get('keywords', [])

        # Search for articles matching topic keywords
        results = []
        for keyword in keywords:
            results.extend(self.search_articles(keyword))

        # Remove duplicates and sort by relevance
        seen = set()
        unique_results = []
        for article in results:
            if article['url'] not in seen:
                seen.add(article['url'])
                unique_results.append(article)

        return unique_results[:count]


class DuplicateDetector:
    """Smart duplicate detection for articles"""

    def remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles using multiple strategies"""
        seen_urls = set()
        seen_titles = set()
        unique_articles = []

        for article in articles:
            url = article.get('url', '')
            title = article.get('title', '').lower().strip()

            # Skip if exact URL or title match
            if url in seen_urls or title in seen_titles:
                continue

            # Check for similar titles (simple similarity)
            is_similar = False
            for seen_title in seen_titles:
                if self._titles_similar(title, seen_title):
                    is_similar = True
                    break

            if not is_similar:
                seen_urls.add(url)
                seen_titles.add(title)
                unique_articles.append(article)

        return unique_articles

    def _titles_similar(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two titles are similar"""
        # Simple word overlap similarity
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        if not words1 or not words2:
            return False

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union > threshold


class TopicTracker:
    """Track trending topics and keywords"""

    def get_trending_topics(self, articles: List[Dict], days: int = 7) -> List[Dict]:
        """Analyze trending topics from articles"""
        # Simple keyword frequency analysis
        word_freq = Counter()

        cutoff_date = datetime.now() - timedelta(days=days)

        for article in articles:
            try:
                pub_date = datetime.fromisoformat(article.get('published_at', '').replace('Z', '+00:00'))
                if pub_date < cutoff_date:
                    continue
            except:
                continue

            # Extract keywords from title and description
            text = f"{article.get('title', '')} {article.get('description', '')}"
            words = [word.lower().strip('.,!?;:"()[]') for word in text.split()]

            # Filter out common words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall', 'this', 'that', 'these', 'those'}

            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] += 1

        # Convert to trending topics format
        trending = []
        for word, count in word_freq.most_common(20):
            trending.append({
                'topic': word.title(),
                'frequency': count,
                'trend_score': count / len(articles) if articles else 0
            })

        return trending


class SentimentAnalyzer:
    """Simple sentiment analysis for articles"""

    def __init__(self):
        # Simple sentiment words (in real implementation, use proper NLP)
        self.positive_words = {'good', 'great', 'excellent', 'positive', 'success', 'breakthrough', 'innovation', 'growth', 'win', 'achievement'}
        self.negative_words = {'bad', 'terrible', 'negative', 'failure', 'crisis', 'problem', 'decline', 'loss', 'threat', 'risk'}

    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """Add sentiment analysis to articles"""
        for article in articles:
            sentiment = self._analyze_text(f"{article.get('title', '')} {article.get('description', '')}")
            article['sentiment'] = sentiment
            article['sentiment_score'] = sentiment['score']

        return articles

    def _analyze_text(self, text: str) -> Dict:
        """Simple sentiment analysis"""
        text_lower = text.lower()

        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)

        if positive_count > negative_count:
            return {'label': 'positive', 'score': 0.7}
        elif negative_count > positive_count:
            return {'label': 'negative', 'score': -0.7}
        else:
            return {'label': 'neutral', 'score': 0.0}


# Global enhanced instance
enhanced_news_manager = EnhancedNewsManager()