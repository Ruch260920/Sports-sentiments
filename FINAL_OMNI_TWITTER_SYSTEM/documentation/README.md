# Sean McVay News Scraping Pipeline

A complete Python pipeline for periodically scraping news articles about Sean McVay using Celery and storing them in PostgreSQL with sentiment analysis and relevance scoring.

## Features

- **Automated Scraping**: Celery-based periodic scraping of news articles
- **Multiple Sources**: Scrapes from ESPN, NFL.com, Sports Illustrated, Bleacher Report, NBC Sports, and more
- **Sentiment Analysis**: Uses TextBlob for sentiment analysis of articles
- **Relevance Scoring**: Intelligent scoring system to determine article relevance
- **Interactive Dashboard**: Modern web dashboard with charts and analytics
- **Scalable Architecture**: Easy to add new entities and sources
- **Redis Integration**: Uses Redis as message broker for Celery
- **PostgreSQL Storage**: Robust database storage with SQLAlchemy ORM

## Architecture

```
OMNI/
├── models/           # SQLAlchemy database models
├── scraper/          # Web scraping logic
├── services/         # Sentiment analysis and utilities
├── tasks/           # Celery tasks
├── dashboard/       # Flask web dashboard
├── main.py          # Main entry point
├── scheduler.py     # Entity management
└── requirements.txt # Dependencies
```

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- pip

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OMNI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your database and Redis credentials
   ```

4. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE news_scraper_db;
   CREATE USER news_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE news_scraper_db TO news_user;
   ```

5. **Initialize the database**
   ```bash
   python main.py setup
   ```

## Configuration

Edit the `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/news_scraper_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=news_scraper_db
DB_USER=username
DB_PASSWORD=password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Scraping Configuration
SCRAPING_INTERVAL_HOURS=6
MAX_ARTICLES_PER_ENTITY=50

# Optional API Keys
BING_API_KEY=your_bing_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

## Usage

### Quick Start

1. **Start Redis**
   ```bash
   redis-server
   ```

2. **Start Celery worker**
   ```bash
   python main.py worker
   ```

3. **Start Celery beat scheduler**
   ```bash
   python main.py beat
   ```

4. **Start the dashboard**
   ```bash
   python main.py dashboard
   ```

5. **Run initial scraping**
   ```bash
   python main.py scrape
   ```

### Command Line Interface

The `main.py` script provides several commands:

```bash
# Initialize database and create tables
python main.py setup

# Run a one-time scraping job
python main.py scrape

# Start Celery worker
python main.py worker

# Start Celery beat scheduler
python main.py beat

# Start the Flask dashboard
python main.py dashboard

# Run tests for all components
python main.py test

# Show system status
python main.py status
```

### Entity Management

Use the `scheduler.py` script to manage entities:

```bash
# Add a new entity
python scheduler.py add --name "Tom Brady" --description "NFL quarterback" --interval 4

# List all entities
python scheduler.py list

# Update entity configuration
python scheduler.py update --name "Sean McVay" --interval 3 --max-articles 30

# Run scraping for specific entity
python scheduler.py scrape --name "Sean McVay"

# Run scraping for all active entities
python scheduler.py scrape-all

# Check which entities need scraping
python scheduler.py check

# Get statistics for an entity
python scheduler.py stats --name "Sean McVay"
```

## Dashboard

The web dashboard provides:

- **Real-time Statistics**: Total articles, recent articles, sources, entities
- **Interactive Charts**: Sentiment timeline, source distribution, relevance scores
- **Article Management**: Search, filter, and paginate articles
- **Sentiment Analysis**: Visualize sentiment distribution over time
- **Source Analytics**: Track article distribution by source

Access the dashboard at `http://localhost:5000`

## Database Schema

### Entities Table
- `id`: Primary key
- `name`: Entity name (e.g., "Sean McVay")
- `description`: Entity description
- `is_active`: Whether entity is active for scraping
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Sources Table
- `id`: Primary key
- `name`: Source name (e.g., "ESPN")
- `domain`: Source domain
- `url`: Source URL
- `is_verified`: Whether source is verified
- `created_at`: Creation timestamp

### Articles Table
- `id`: Primary key
- `title`: Article title
- `summary`: Article summary
- `url`: Article URL
- `content`: Full article content
- `published_date`: Original publication date
- `scraped_date`: When article was scraped
- `entity_id`: Foreign key to entities
- `source_id`: Foreign key to sources
- `relevance_score`: Calculated relevance score (0-1)
- `sentiment_score`: Sentiment score (-1 to 1)
- `sentiment_label`: Sentiment label (positive/negative/neutral)

## API Endpoints

The dashboard provides REST API endpoints:

- `GET /api/stats` - Overall statistics
- `GET /api/articles` - Paginated articles with filtering
- `GET /api/sources` - All sources with article counts
- `GET /api/entities` - All entities with article counts
- `GET /api/charts/sentiment-timeline` - Sentiment data over time
- `GET /api/charts/source-distribution` - Article distribution by source
- `GET /api/charts/relevance-distribution` - Relevance score distribution
- `GET /api/search` - Search articles by title/content

## Celery Tasks

### Main Tasks

- `scrape_entity_articles`: Scrape articles for a specific entity
- `analyze_article`: Re-analyze sentiment and relevance for an article
- `cleanup_old_articles`: Remove old articles from database
- `update_entity_status`: Update entity active status

### Task Configuration

Tasks are configured in `tasks/celery_app.py`:

- **Broker**: Redis
- **Result Backend**: Redis
- **Concurrency**: 2 workers
- **Queues**: scraping, analysis
- **Schedule**: Every 6 hours (configurable)

## Sentiment Analysis

Uses TextBlob for sentiment analysis:

- **Positive**: Score > 0.1
- **Negative**: Score < -0.1
- **Neutral**: Score between -0.1 and 0.1

## Relevance Scoring

The relevance scorer considers:

1. **Entity Mentions**: Frequency of entity name in text
2. **Keyword Matching**: Football/NFL related keywords
3. **Title Relevance**: Entity name in title
4. **Content Analysis**: Overall content relevance

## Adding New Sources

To add new news sources:

1. Update `scraper/news_scraper.py` in `_get_news_sources()`
2. Add source-specific parsing logic in `scraper/article_parser.py`
3. Test with `python main.py test`

## Adding New Entities

To add new entities for scraping:

```bash
python scheduler.py add --name "Aaron Rodgers" --description "NFL quarterback" --interval 4
```

## Monitoring and Logging

- **Celery Logs**: Check worker logs for task execution
- **Dashboard**: Real-time monitoring via web interface
- **Database**: Query articles table for detailed analysis

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Redis Connection Error**
   - Verify Redis is running
   - Check Redis configuration in `.env`

3. **Scraping Fails**
   - Check internet connection
   - Verify source websites are accessible
   - Review scraping logs for errors

4. **Dashboard Not Loading**
   - Ensure Flask app is running
   - Check port 5000 is available
   - Verify all dependencies are installed

### Debug Mode

Run components in debug mode:

```bash
# Debug scraping
python -c "from scraper.news_scraper import NewsScraper; s = NewsScraper(); print(s.scrape_articles('Sean McVay', 5))"

# Debug sentiment analysis
python -c "from services.sentiment_analyzer import SentimentAnalyzer; a = SentimentAnalyzer(); print(a.analyze_sentiment('Sean McVay is great!'))"
```

## Performance Optimization

- **Database Indexing**: Add indexes on frequently queried columns
- **Caching**: Implement Redis caching for dashboard data
- **Concurrency**: Adjust Celery worker concurrency based on system resources
- **Batch Processing**: Process articles in batches for better performance

## Security Considerations

- **API Keys**: Store sensitive keys in environment variables
- **Database Security**: Use strong passwords and limit database access
- **Rate Limiting**: Implement rate limiting for web scraping
- **Input Validation**: Validate all user inputs in dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the logs for error messages
- Open an issue on GitHub

---

**Note**: This pipeline is designed for educational and research purposes. Please respect website terms of service and implement appropriate rate limiting when scraping external websites. 