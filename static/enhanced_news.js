// Enhanced News Intelligence Dashboard JavaScript

class NewsIntelligenceDashboard {
    constructor() {
        this.articles = [];
        this.currentView = 'grid';
        this.filters = {};
        this.charts = {};

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
    }

    bindEvents() {
        // Search and filter events
        document.getElementById('searchBtn').addEventListener('click', () => this.performSearch());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });

        document.getElementById('categoryFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('sourceFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('dateFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('clearFilters').addEventListener('click', () => this.clearFilters());

        // View control events
        document.getElementById('gridViewBtn').addEventListener('click', () => this.switchView('grid'));
        document.getElementById('listViewBtn').addEventListener('click', () => this.switchView('list'));

        // Action events
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshData());
        document.getElementById('addTopicBtn').addEventListener('click', () => this.showAddTopicModal());

        // Modal events
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        document.getElementById('addTopicForm').addEventListener('submit', (e) => this.handleAddTopic(e));

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('addTopicModal');
            if (e.target === modal) {
                this.closeModal();
            }
        });
    }

    async loadInitialData() {
        this.showLoading(true);

        try {
            await Promise.all([
                this.loadArticles(),
                this.loadSummary(),
                this.loadTopics(),
                this.loadTrending(),
                this.loadAnalytics()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.showLoading(false);
        }
    }

    async loadArticles() {
        try {
            const response = await fetch('/api/news?count=50');
            const articles = await response.json();
            this.articles = articles;
            this.renderArticles(articles);
        } catch (error) {
            console.error('Error loading articles:', error);
        }
    }

    async loadSummary() {
        try {
            const response = await fetch('/api/news/summary');
            const summary = await response.json();
            this.updateStats(summary);
        } catch (error) {
            console.error('Error loading summary:', error);
        }
    }

    async loadTopics() {
        try {
            const response = await fetch('/api/news/topics');
            const topics = await response.json();
            this.renderTopics(topics);
        } catch (error) {
            console.error('Error loading topics:', error);
        }
    }

    async loadTrending() {
        try {
            const response = await fetch('/api/news/trending');
            const data = await response.json();
            this.renderTrending(data.trending_topics);
        } catch (error) {
            console.error('Error loading trending topics:', error);
        }
    }

    async loadAnalytics() {
        try {
            const response = await fetch('/api/news/analytics');
            const analytics = await response.json();
            this.updateAnalytics(analytics);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    updateStats(summary) {
        document.getElementById('totalArticles').textContent = summary.total_articles || 0;
        document.getElementById('totalSources').textContent = summary.sources?.length || 0;

        if (summary.last_update) {
            const updateTime = new Date(summary.last_update);
            const timeAgo = this.getTimeAgo(updateTime);
            document.getElementById('lastUpdate').textContent = timeAgo;
        }
    }

    renderTopics(topics) {
        const container = document.getElementById('topicsList');
        container.innerHTML = '';

        Object.entries(topics).forEach(([name, data]) => {
            const topicElement = document.createElement('div');
            topicElement.className = 'topic-item';
            topicElement.innerHTML = `
                <div>
                    <div class="topic-name">${name}</div>
                    <div class="topic-keywords">${data.keywords?.slice(0, 3).join(', ')}</div>
                </div>
                <div class="topic-stats">
                    Priority: ${data.priority || 1.0}
                </div>
            `;

            topicElement.addEventListener('click', () => this.loadTopicArticles(name));
            container.appendChild(topicElement);
        });
    }

    renderTrending(trending) {
        const container = document.getElementById('trendingTopics');
        container.innerHTML = '';

        trending.slice(0, 10).forEach(item => {
            const trendingElement = document.createElement('div');
            trendingElement.className = 'trending-item';
            trendingElement.innerHTML = `
                <div class="trending-topic">${item.topic}</div>
                <div class="trending-score">${item.frequency}</div>
            `;
            container.appendChild(trendingElement);
        });
    }

    updateAnalytics(analytics) {
        // Update sentiment bars
        const total = analytics.sentiment_breakdown.positive +
                     analytics.sentiment_breakdown.neutral +
                     analytics.sentiment_breakdown.negative;

        if (total > 0) {
            const positivePercent = (analytics.sentiment_breakdown.positive / total) * 100;
            const neutralPercent = (analytics.sentiment_breakdown.neutral / total) * 100;
            const negativePercent = (analytics.sentiment_breakdown.negative / total) * 100;

            document.getElementById('positiveBar').style.width = `${positivePercent}%`;
            document.getElementById('neutralBar').style.width = `${neutralPercent}%`;
            document.getElementById('negativeBar').style.width = `${negativePercent}%`;

            document.getElementById('positiveValue').textContent = `${Math.round(positivePercent)}%`;
            document.getElementById('neutralValue').textContent = `${Math.round(neutralPercent)}%`;
            document.getElementById('negativeValue').textContent = `${Math.round(negativePercent)}%`;
        }

        // Update source distribution chart
        this.updateSourceChart(analytics.sources_breakdown);
    }

    updateSourceChart(sourcesData) {
        const ctx = document.getElementById('sourceChart').getContext('2d');

        if (this.charts.sourceChart) {
            this.charts.sourceChart.destroy();
        }

        const labels = Object.keys(sourcesData);
        const data = Object.values(sourcesData);
        const colors = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
        ];

        this.charts.sourceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    renderArticles(articles) {
        const container = document.getElementById('articlesContainer');
        container.innerHTML = '';

        if (!articles || articles.length === 0) {
            container.innerHTML = '<div class="no-articles">No articles found</div>';
            return;
        }

        articles.forEach(article => {
            const articleElement = this.createArticleElement(article);
            container.appendChild(articleElement);
        });
    }

    createArticleElement(article) {
        const element = document.createElement('div');
        element.className = 'article-card';

        const publishedDate = new Date(article.published_at);
        const timeAgo = this.getTimeAgo(publishedDate);

        const sentiment = article.sentiment || { label: 'neutral', score: 0 };
        const sentimentClass = sentiment.label;

        element.innerHTML = `
            <div class="article-header">
                <div>
                    <span class="article-source">${article.source || 'Unknown'}</span>
                    <span class="article-category">${article.category || 'general'}</span>
                </div>
                <div class="sentiment-indicator ${sentimentClass}" title="Sentiment: ${sentiment.label}"></div>
            </div>

            <h3 class="article-title">
                <a href="${article.url}" target="_blank" rel="noopener noreferrer">
                    ${article.title}
                </a>
            </h3>

            <p class="article-description">
                ${article.description || 'No description available'}
            </p>

            <div class="article-meta">
                <div class="article-date">
                    <i class="fas fa-clock"></i>
                    ${timeAgo}
                </div>
                <div class="article-score">
                    ${article.score ? `<div class="score-item"><i class="fas fa-arrow-up"></i> ${article.score}</div>` : ''}
                    ${article.comments ? `<div class="score-item"><i class="fas fa-comments"></i> ${article.comments}</div>` : ''}
                    ${article.relevance_score ? `<div class="score-item">Relevance: ${Math.round(article.relevance_score * 100)}%</div>` : ''}
                </div>
            </div>
        `;

        return element;
    }

    async performSearch() {
        const query = document.getElementById('searchInput').value.trim();
        if (!query) return;

        this.showLoading(true);

        try {
            const params = new URLSearchParams({ q: query, count: 50 });

            // Add filters to search
            if (this.filters.category) params.append('category', this.filters.category);
            if (this.filters.source) params.append('source', this.filters.source);
            if (this.filters.date_from) params.append('date_from', this.filters.date_from);

            const response = await fetch(`/api/news/search?${params}`);
            const data = await response.json();

            this.renderArticles(data.articles);
            this.showSearchResults(data.total_results, query);
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed');
        } finally {
            this.showLoading(false);
        }
    }

    applyFilters() {
        this.filters = {
            category: document.getElementById('categoryFilter').value,
            source: document.getElementById('sourceFilter').value,
            date_from: document.getElementById('dateFilter').value
        };

        // Filter current articles
        let filteredArticles = this.articles;

        if (this.filters.category) {
            filteredArticles = filteredArticles.filter(article =>
                article.category === this.filters.category);
        }

        if (this.filters.source) {
            filteredArticles = filteredArticles.filter(article =>
                article.api_source === this.filters.source);
        }

        if (this.filters.date_from) {
            const filterDate = new Date(this.filters.date_from);
            filteredArticles = filteredArticles.filter(article => {
                const articleDate = new Date(article.published_at);
                return articleDate >= filterDate;
            });
        }

        this.renderArticles(filteredArticles);
    }

    clearFilters() {
        document.getElementById('categoryFilter').value = '';
        document.getElementById('sourceFilter').value = '';
        document.getElementById('dateFilter').value = '';
        document.getElementById('searchInput').value = '';

        this.filters = {};
        this.renderArticles(this.articles);
    }

    switchView(view) {
        this.currentView = view;

        const container = document.getElementById('articlesContainer');
        const gridBtn = document.getElementById('gridViewBtn');
        const listBtn = document.getElementById('listViewBtn');

        if (view === 'grid') {
            container.className = 'articles-grid';
            gridBtn.classList.add('active');
            listBtn.classList.remove('active');
        } else {
            container.className = 'articles-list';
            listBtn.classList.add('active');
            gridBtn.classList.remove('active');
        }
    }

    async refreshData() {
        document.getElementById('refreshBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';

        try {
            const token = document.cookie.split('; ').find(r => r.startsWith('csrf_token='))?.split('=')[1];
            await fetch('/api/news/refresh', { method: 'POST', headers: { 'X-CSRFToken': token || '' } });
            await this.loadInitialData();
            this.showSuccess('Data refreshed successfully');
        } catch (error) {
            console.error('Refresh error:', error);
            this.showError('Failed to refresh data');
        } finally {
            document.getElementById('refreshBtn').innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }
    }

    async loadTopicArticles(topicName) {
        this.showLoading(true);

        try {
            const response = await fetch(`/api/news/topics/${encodeURIComponent(topicName)}?count=20`);
            const data = await response.json();

            this.renderArticles(data.articles);
            this.showSearchResults(data.total_articles, `Topic: ${topicName}`);
        } catch (error) {
            console.error('Error loading topic articles:', error);
            this.showError('Failed to load topic articles');
        } finally {
            this.showLoading(false);
        }
    }

    showAddTopicModal() {
        document.getElementById('addTopicModal').style.display = 'block';
    }

    closeModal() {
        document.getElementById('addTopicModal').style.display = 'none';
    }

    async handleAddTopic(event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const topicData = {
            name: document.getElementById('topicName').value,
            keywords: document.getElementById('topicKeywords').value.split(',').map(k => k.trim()),
            sources: Array.from(document.getElementById('topicSources').selectedOptions).map(o => o.value),
            priority: parseFloat(document.getElementById('topicPriority').value)
        };

        try {
            const response = await fetch('/api/news/topics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(topicData)
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showSuccess(result.message);
                this.closeModal();
                this.loadTopics(); // Reload topics
                event.target.reset(); // Clear form
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Error creating topic:', error);
            this.showError('Failed to create topic');
        }
    }

    showLoading(show) {
        const indicator = document.getElementById('loadingIndicator');
        indicator.style.display = show ? 'block' : 'none';
    }

    showSearchResults(count, query) {
        // You could add a results summary here
        console.log(`Found ${count} results for "${query}"`);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        // Simple notification - you could enhance this with a proper notification system
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? '#28a745' : '#dc3545'};
            color: white;
            border-radius: 8px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    getTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}d ago`;
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return 'Just now';
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.newsIntelligence = new NewsIntelligenceDashboard();
});

// Close modal function for onclick handler
function closeModal() {
    document.getElementById('addTopicModal').style.display = 'none';
}