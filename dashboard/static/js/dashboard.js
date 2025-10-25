// Dashboard JavaScript

class Dashboard {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.charts = {};
        this.filters = {
            sentiment: '',
            source: '',
            entity: '',
            search: ''
        };
        
        this.init();
    }
    
    init() {
        this.loadStats();
        this.loadCharts();
        this.loadArticles();
        this.loadFilters();
        this.setupEventListeners();
        this.updateLastUpdated();
        
        // Auto-refresh every 5 minutes
        setInterval(() => {
            this.loadStats();
            this.loadArticles();
        }, 300000);
    }
    
    setupEventListeners() {
        // Search functionality
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.debounce(() => this.loadArticles(), 500);
        });
        
        // Filter changes
        document.getElementById('sentiment-filter').addEventListener('change', (e) => {
            this.filters.sentiment = e.target.value;
            this.loadArticles();
        });
        
        document.getElementById('source-filter').addEventListener('change', (e) => {
            this.filters.source = e.target.value;
            this.loadArticles();
        });
        
        document.getElementById('entity-filter').addEventListener('change', (e) => {
            this.filters.entity = e.target.value;
            this.loadArticles();
        });
        
        // Apply filters button
        document.getElementById('apply-filters').addEventListener('click', () => {
            this.loadArticles();
        });
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading stats:', data.error);
                return;
            }
            
            // Update stat cards
            document.getElementById('total-articles').textContent = data.total_articles.toLocaleString();
            document.getElementById('recent-articles').textContent = data.recent_articles.toLocaleString();
            document.getElementById('total-sources').textContent = data.total_sources.toLocaleString();
            document.getElementById('total-entities').textContent = data.total_entities.toLocaleString();
            
            // Update sentiment pie chart if it exists
            if (this.charts.sentimentPie) {
                this.updateSentimentPieChart(data.sentiment_distribution);
            }
            
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    async loadCharts() {
        await Promise.all([
            this.loadSentimentTimeline(),
            this.loadSourceDistribution(),
            this.loadRelevanceDistribution(),
            this.loadSentimentPieChart()
        ]);
    }
    
    async loadSentimentTimeline() {
        try {
            const response = await fetch('/api/charts/sentiment-timeline');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading sentiment timeline:', data.error);
                return;
            }
            
            const ctx = document.getElementById('sentimentChart').getContext('2d');
            
            if (this.charts.sentimentTimeline) {
                this.charts.sentimentTimeline.destroy();
            }
            
            this.charts.sentimentTimeline = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        {
                            label: 'Positive',
                            data: data.positive,
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Negative',
                            data: data.negative,
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Neutral',
                            data: data.neutral,
                            borderColor: '#6c757d',
                            backgroundColor: 'rgba(108, 117, 125, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error loading sentiment timeline:', error);
        }
    }
    
    async loadSourceDistribution() {
        try {
            const response = await fetch('/api/charts/source-distribution');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading source distribution:', data.error);
                return;
            }
            
            const ctx = document.getElementById('sourceChart').getContext('2d');
            
            if (this.charts.sourceDistribution) {
                this.charts.sourceDistribution.destroy();
            }
            
            this.charts.sourceDistribution = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.sources,
                    datasets: [{
                        data: data.counts,
                        backgroundColor: [
                            '#667eea', '#764ba2', '#f093fb', '#f5576c',
                            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error loading source distribution:', error);
        }
    }
    
    async loadRelevanceDistribution() {
        try {
            const response = await fetch('/api/charts/relevance-distribution');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading relevance distribution:', data.error);
                return;
            }
            
            const ctx = document.getElementById('relevanceChart').getContext('2d');
            
            if (this.charts.relevanceDistribution) {
                this.charts.relevanceDistribution.destroy();
            }
            
            this.charts.relevanceDistribution = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Articles',
                        data: data.counts,
                        backgroundColor: '#667eea',
                        borderColor: '#5a6fd8',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error loading relevance distribution:', error);
        }
    }
    
    async loadSentimentPieChart() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading sentiment pie chart:', data.error);
                return;
            }
            
            const ctx = document.getElementById('sentimentPieChart').getContext('2d');
            
            if (this.charts.sentimentPie) {
                this.charts.sentimentPie.destroy();
            }
            
            const sentimentData = data.sentiment_distribution;
            const labels = Object.keys(sentimentData);
            const values = Object.values(sentimentData);
            
            this.charts.sentimentPie = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            '#28a745', '#dc3545', '#6c757d'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error loading sentiment pie chart:', error);
        }
    }
    
    updateSentimentPieChart(sentimentData) {
        if (!this.charts.sentimentPie) return;
        
        const labels = Object.keys(sentimentData);
        const values = Object.values(sentimentData);
        
        this.charts.sentimentPie.data.labels = labels;
        this.charts.sentimentPie.data.datasets[0].data = values;
        this.charts.sentimentPie.update();
    }
    
    async loadArticles() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.filters
            });
            
            const response = await fetch(`/api/articles?${params}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading articles:', data.error);
                return;
            }
            
            this.renderArticles(data.articles);
            this.renderPagination(data.total, data.page, data.per_page);
            this.updatePaginationText(data.total, data.page, data.per_page);
            
        } catch (error) {
            console.error('Error loading articles:', error);
        }
    }
    
    renderArticles(articles) {
        const tbody = document.getElementById('articles-table-body');
        
        if (articles.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No articles found</td></tr>';
            return;
        }
        
        tbody.innerHTML = articles.map(article => `
            <tr>
                <td>
                    <a href="#" class="article-title" onclick="dashboard.showArticleModal(${article.id})">
                        ${this.escapeHtml(article.title)}
                    </a>
                    ${article.summary ? `<br><small class="text-muted">${this.escapeHtml(article.summary.substring(0, 100))}...</small>` : ''}
                </td>
                <td>
                    <span class="source-badge">${this.escapeHtml(article.source.name)}</span>
                </td>
                <td class="date-text">
                    ${article.published_date ? this.formatDate(article.published_date) : 'N/A'}
                </td>
                <td>
                    <span class="sentiment-badge sentiment-${article.sentiment_label || 'neutral'}">
                        ${article.sentiment_label || 'neutral'}
                    </span>
                </td>
                <td>
                    <span class="relevance-score relevance-${this.getRelevanceClass(article.relevance_score)}">
                        ${article.relevance_score ? (article.relevance_score * 100).toFixed(1) + '%' : 'N/A'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary btn-action" onclick="dashboard.showArticleModal(${article.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <a href="${article.url}" target="_blank" class="btn btn-sm btn-outline-secondary btn-action">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </td>
            </tr>
        `).join('');
    }
    
    renderPagination(total, currentPage, perPage) {
        const totalPages = Math.ceil(total / perPage);
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let paginationHtml = '';
        
        // Previous button
        paginationHtml += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="dashboard.goToPage(${currentPage - 1})">Previous</a>
            </li>
        `;
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="dashboard.goToPage(${i})">${i}</a>
                </li>
            `;
        }
        
        // Next button
        paginationHtml += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="dashboard.goToPage(${currentPage + 1})">Next</a>
            </li>
        `;
        
        pagination.innerHTML = paginationHtml;
    }
    
    updatePaginationText(total, currentPage, perPage) {
        const start = (currentPage - 1) * perPage + 1;
        const end = Math.min(currentPage * perPage, total);
        document.getElementById('pagination-text').textContent = `Showing ${start}-${end} of ${total} articles`;
    }
    
    async loadFilters() {
        try {
            const [sourcesResponse, entitiesResponse] = await Promise.all([
                fetch('/api/sources'),
                fetch('/api/entities')
            ]);
            
            const sources = await sourcesResponse.json();
            const entities = await entitiesResponse.json();
            
            // Populate source filter
            const sourceFilter = document.getElementById('source-filter');
            sources.forEach(source => {
                const option = document.createElement('option');
                option.value = source.name;
                option.textContent = `${source.name} (${source.article_count})`;
                sourceFilter.appendChild(option);
            });
            
            // Populate entity filter
            const entityFilter = document.getElementById('entity-filter');
            entities.forEach(entity => {
                const option = document.createElement('option');
                option.value = entity.name;
                option.textContent = `${entity.name} (${entity.article_count})`;
                entityFilter.appendChild(option);
            });
            
        } catch (error) {
            console.error('Error loading filters:', error);
        }
    }
    
    goToPage(page) {
        if (page < 1) return;
        this.currentPage = page;
        this.loadArticles();
    }
    
    showArticleModal(articleId) {
        // This would load article details and show in modal
        // For now, just show a placeholder
        document.getElementById('modal-title').textContent = 'Article Details';
        document.getElementById('modal-body').innerHTML = '<p>Article details would be loaded here...</p>';
        document.getElementById('modal-link').href = '#';
        
        const modal = new bootstrap.Modal(document.getElementById('articleModal'));
        modal.show();
    }
    
    updateLastUpdated() {
        const now = new Date();
        document.getElementById('last-updated').textContent = now.toLocaleString();
    }
    
    getRelevanceClass(score) {
        if (!score) return 'low';
        if (score >= 0.7) return 'high';
        if (score >= 0.4) return 'medium';
        return 'low';
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
}); 