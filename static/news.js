// News Dashboard JavaScript
class NewsDashboard {
    constructor() {
        this.currentPage = 1;
        this.articlesPerPage = 20;
        this.currentView = 'grid';
        this.currentFilters = {
            category: '',
            source: '',
            search: ''
        };
        this.allNews = [];
        this.filteredNews = [];

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadNews();
        this.loadSummary();
        this.setupAutoRefresh();
    }

    bindEvents() {
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshNews();
        });

        // View controls
        document.getElementById('grid-view').addEventListener('click', () => {
            this.setView('grid');
        });

        document.getElementById('list-view').addEventListener('click', () => {
            this.setView('list');
        });

        // Filters
        document.getElementById('category-filter').addEventListener('change', (e) => {
            this.currentFilters.category = e.target.value;
            this.applyFilters();
        });

        document.getElementById('source-filter').addEventListener('change', (e) => {
            this.currentFilters.source = e.target.value;
            this.applyFilters();
        });

        // Search
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.currentFilters.search = e.target.value;
            this.applyFilters();
        });

        // Load more button
        document.getElementById('load-more-btn').addEventListener('click', () => {
            this.loadMoreNews();
        });

        // Modal events
        this.setupModalEvents();
    }

    async loadNews() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/news');
            const news = await response.json();

            this.allNews = news;
            this.filteredNews = [...this.allNews];
            this.updateNewsDisplay();
            this.populateFilters();
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading news:', error);
            this.showError('Failed to load news. Please try again.');
            this.showLoading(false);
        }
    }

    async loadSummary() {
        try {
            const response = await fetch('/api/news/summary');
            const summary = await response.json();

            document.getElementById('total-articles').textContent = summary.total_articles;
            document.getElementById('categories-count').textContent = summary.categories.length;

            if (summary.last_update) {
                const lastUpdate = new Date(summary.last_update);
                document.getElementById('last-update').textContent =
                    lastUpdate.toLocaleTimeString();
            }
        } catch (error) {
            console.error('Error loading summary:', error);
        }
    }

    async refreshNews() {
        try {
            const refreshBtn = document.getElementById('refresh-btn');
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';

            const token = document.cookie.split('; ').find(r => r.startsWith('csrf_token='))?.split('=')[1];
            await fetch('/api/news/refresh', { method: 'POST', headers: { 'X-CSRFToken': token || '' } });
            await this.loadNews();
            await this.loadSummary();

            this.showSuccess('News refreshed successfully!');
        } catch (error) {
            console.error('Error refreshing news:', error);
            this.showError('Failed to refresh news.');
        } finally {
            const refreshBtn = document.getElementById('refresh-btn');
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }
    }

    applyFilters() {
        this.filteredNews = this.allNews.filter(article => {
            // Category filter
            if (this.currentFilters.category && article.category !== this.currentFilters.category) {
                return false;
            }

            // Source filter
            if (this.currentFilters.source && article.source !== this.currentFilters.source) {
                return false;
            }

            // Search filter
            if (this.currentFilters.search) {
                const searchTerm = this.currentFilters.search.toLowerCase();
                const title = article.title.toLowerCase();
                const description = article.description.toLowerCase();
                const source = article.source.toLowerCase();

                if (!title.includes(searchTerm) &&
                    !description.includes(searchTerm) &&
                    !source.includes(searchTerm)) {
                    return false;
                }
            }

            return true;
        });

        this.currentPage = 1;
        this.updateNewsDisplay();
    }

    updateNewsDisplay() {
        const container = document.getElementById('news-container');
        const startIndex = 0;
        const endIndex = this.currentPage * this.articlesPerPage;
        const displayNews = this.filteredNews.slice(startIndex, endIndex);

        if (displayNews.length === 0) {
            container.innerHTML = `
                <div class="no-news">
                    <i class="fas fa-newspaper"></i>
                    <h3>No news found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = displayNews.map(article => this.createNewsCard(article)).join('');

        // Show/hide load more button
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (endIndex < this.filteredNews.length) {
            loadMoreBtn.style.display = 'inline-flex';
        } else {
            loadMoreBtn.style.display = 'none';
        }
    }

    createNewsCard(article) {
        const publishedDate = new Date(article.published_at);
        const timeAgo = this.getTimeAgo(publishedDate);

        let cardClass = 'news-card';
        if (article.type === 'financial') {
            cardClass += ' financial';
            if (article.change_percent > 0) {
                cardClass += ' positive';
            } else if (article.change_percent < 0) {
                cardClass += ' negative';
            }
        } else if (article.type === 'reddit') {
            cardClass += ' reddit';
        }

        let scoreHtml = '';
        if (article.type === 'reddit' && article.score) {
            scoreHtml = `<span class="reddit-score">${article.score} ↑</span>`;
        }

        return `
            <div class="${cardClass}" onclick="window.open('${article.url}', '_blank')">
                <div class="news-content">
                    <div class="news-meta">
                        <span class="news-source">${article.source}</span>
                        <span class="news-category">${article.category}</span>
                        ${scoreHtml}
                    </div>
                    <h3 class="news-title">${article.title}</h3>
                    <p class="news-description">${article.description}</p>
                    <div class="news-footer">
                        <div class="news-time">
                            <i class="fas fa-clock"></i>
                            <span>${timeAgo}</span>
                        </div>
                        <div class="news-actions">
                            <button class="action-btn" onclick="event.stopPropagation(); this.shareArticle('${article.title}', '${article.url}')">
                                <i class="fas fa-share"></i>
                            </button>
                            <button class="action-btn" onclick="event.stopPropagation(); this.bookmarkArticle('${article.title}', '${article.url}')">
                                <i class="fas fa-bookmark"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes}m ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days}d ago`;
        }
    }

    populateFilters() {
        const categories = [...new Set(this.allNews.map(article => article.category))];
        const sources = [...new Set(this.allNews.map(article => article.source))];

        const categoryFilter = document.getElementById('category-filter');
        const sourceFilter = document.getElementById('source-filter');

        // Clear existing options except the first one
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        sourceFilter.innerHTML = '<option value="">All Sources</option>';

        // Add new options
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
            categoryFilter.appendChild(option);
        });

        sources.forEach(source => {
            const option = document.createElement('option');
            option.value = source;
            option.textContent = source;
            sourceFilter.appendChild(option);
        });
    }

    setView(view) {
        this.currentView = view;
        const container = document.getElementById('news-container');

        // Update button states
        document.getElementById('grid-view').classList.toggle('active', view === 'grid');
        document.getElementById('list-view').classList.toggle('active', view === 'list');

        // Update container class
        container.classList.toggle('list-view', view === 'list');

        // Re-render news with new view
        this.updateNewsDisplay();
    }

    loadMoreNews() {
        this.currentPage++;
        this.updateNewsDisplay();
    }

    showLoading(show) {
        const spinner = document.getElementById('loading-spinner');
        if (show) {
            spinner.style.display = 'block';
        } else {
            spinner.style.display = 'none';
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => notification.classList.add('show'), 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    setupAutoRefresh() {
        // Auto-refresh every 5 minutes
        setInterval(() => {
            this.loadNews();
            this.loadSummary();
        }, 5 * 60 * 1000);
    }

    setupModalEvents() {
        const modal = document.getElementById('sources-modal');
        const closeBtn = modal.querySelector('.close');
        const cancelBtn = document.getElementById('cancel-sources');
        const saveBtn = document.getElementById('save-sources');

        // Close modal
        [closeBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        });

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });

        // Save sources
        saveBtn.addEventListener('click', async () => {
            try {
                const sources = this.collectSourcesFromModal();
                const response = await fetch('/api/news/sources', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(sources)
                });

                if (response.ok) {
                    this.showSuccess('News sources updated successfully!');
                    modal.style.display = 'none';
                    // Refresh news with new sources
                    setTimeout(() => this.refreshNews(), 1000);
                } else {
                    throw new Error('Failed to update sources');
                }
            } catch (error) {
                console.error('Error updating sources:', error);
                this.showError('Failed to update news sources.');
            }
        });

        // Add source buttons
        document.getElementById('add-rss-feed').addEventListener('click', () => {
            this.addSourceItem('rss-feeds-list', 'rss');
        });

        document.getElementById('add-reddit-subreddit').addEventListener('click', () => {
            this.addSourceItem('reddit-subreddits-list', 'reddit');
        });

        document.getElementById('add-news-category').addEventListener('click', () => {
            this.addSourceItem('news-categories-list', 'category');
        });
    }

    addSourceItem(containerId, type) {
        const container = document.getElementById(containerId);
        const item = document.createElement('div');
        item.className = 'source-item';

        if (type === 'rss') {
            item.innerHTML = `
                <input type="text" placeholder="Feed name" class="source-name">
                <input type="url" placeholder="RSS URL" class="source-url">
                <input type="text" placeholder="Category" class="source-category">
                <button class="remove-source" onclick="this.parentElement.remove()">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        } else {
            item.innerHTML = `
                <input type="text" placeholder="${type === 'reddit' ? 'Subreddit name' : 'Category name'}">
                <button class="remove-source" onclick="this.parentElement.remove()">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        }

        container.appendChild(item);
    }

    collectSourcesFromModal() {
        const sources = {
            rss_feeds: [],
            reddit_subreddits: [],
            news_categories: []
        };

        // Collect RSS feeds
        document.querySelectorAll('#rss-feeds-list .source-item').forEach(item => {
            const name = item.querySelector('.source-name')?.value;
            const url = item.querySelector('.source-url')?.value;
            const category = item.querySelector('.source-category')?.value;

            if (name && url) {
                sources.rss_feeds.push({ name, url, category: category || 'general' });
            }
        });

        // Collect Reddit subreddits
        document.querySelectorAll('#reddit-subreddits-list .source-item input').forEach(input => {
            if (input.value) {
                sources.reddit_subreddits.push(input.value);
            }
        });

        // Collect news categories
        document.querySelectorAll('#news-categories-list .source-item input').forEach(input => {
            if (input.value) {
                sources.news_categories.push(input.value);
            }
        });

        return sources;
    }

    // Utility methods for article actions
    shareArticle(title, url) {
        if (navigator.share) {
            navigator.share({
                title: title,
                url: url
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(url).then(() => {
                this.showSuccess('Link copied to clipboard!');
            });
        }
    }

    bookmarkArticle(title, url) {
        // Simple bookmark storage in localStorage
        const bookmarks = JSON.parse(localStorage.getItem('newsBookmarks') || '[]');
        const bookmark = { title, url, date: new Date().toISOString() };

        if (!bookmarks.find(b => b.url === url)) {
            bookmarks.push(bookmark);
            localStorage.setItem('newsBookmarks', JSON.stringify(bookmarks));
            this.showSuccess('Article bookmarked!');
        } else {
            this.showError('Article already bookmarked!');
        }
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.newsDashboard = new NewsDashboard();
});

// Add notification styles
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        z-index: 3000;
        max-width: 300px;
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification.success {
        background: #48bb78;
    }

    .notification.error {
        background: #e53e3e;
    }

    .no-news {
        grid-column: 1 / -1;
        text-align: center;
        padding: 3rem;
        color: #718096;
    }

    .no-news i {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    .no-news h3 {
        margin-bottom: 0.5rem;
        color: #4a5568;
    }
`;
document.head.appendChild(style);