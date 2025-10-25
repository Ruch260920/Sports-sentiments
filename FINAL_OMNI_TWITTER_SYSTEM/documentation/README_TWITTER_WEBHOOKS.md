# Twitter Webhook Integration for OMNI News Pipeline

## 🚀 Overview

This document describes the new **real-time Twitter webhook system** that replaces the previous scraping approach. Instead of actively polling Twitter for new tweets, we now receive real-time notifications via webhooks from `twitterapi.io`.

## ✨ Key Benefits

- **Real-time data**: Receive tweets instantly when they're posted
- **Cost-effective**: No more API budget waste from constant polling
- **Scalable**: Webhook-based architecture handles high tweet volumes
- **Reliable**: Built-in retry mechanisms and health monitoring
- **Efficient**: Only process new tweets, no duplicate work

## 🏗️ Architecture

```
twitterapi.io → Webhook Endpoint → Celery Queue → Tweet Processing → Database
     ↓              ↓                ↓              ↓              ↓
  Real-time    Fast Response    Async Task     Sentiment      Persistent
   Tweets      (< 100ms)       Processing     Analysis       Storage
```

## 📁 New Files & Components

### 1. Database Models (`models/models.py`)
- **Tweet**: Stores individual tweets with metadata
- **TwitterWebhook**: Tracks webhook subscriptions and health
- **Entity**: Enhanced with Twitter tracking capabilities

### 2. Twitter Service (`services/twitter_webhook_service.py`)
- Webhook creation/deletion
- Tweet processing and storage
- Sentiment analysis integration
- Health monitoring

### 3. Celery Tasks (`tasks/twitter_tasks.py`)
- `process_twitter_webhook`: Handles incoming webhooks
- `analyze_tweet`: Sentiment and relevance analysis
- `create_twitter_webhook`: Sets up new subscriptions
- `monitor_webhook_health`: Health checks and alerts

### 4. Webhook Endpoints (`webhook_endpoints.py`)
- `/webhook/twitter/<username>`: Receives tweets for specific accounts
- `/webhook/twitter/health`: Health monitoring
- `/webhook/twitter/manage`: Webhook management
- `/webhook/twitter/test`: Testing and debugging

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Required environment variables
export TWITTER_API_KEY="your_twitterapi.io_key_here"
export WEBHOOK_BASE_URL="https://your-domain.com"
export DATABASE_URL="postgresql://user:pass@host:port/db"
export CELERY_BROKER_URL="redis://localhost:6379/0"
```

### 2. Database Migration

```bash
# Update your database with new tables
python init_db.py
```

### 3. Start Services

```bash
# Option 1: Docker Compose (recommended)
docker-compose up -d

# Option 2: Manual startup
python webhook_endpoints.py &          # Webhook server (port 5001)
celery worker --app=tasks.celery_app:celery_app --queues=twitter &
celery beat --app=tasks.celery_app:celery_app &
python main.py dashboard               # Main app (port 5000)
```

### 4. Create Your First Webhook

```python
from services.twitter_webhook_service import TwitterWebhookService

service = TwitterWebhookService()

# Follow @NBA account
result = service.create_webhook(
    target_username="NBA",
    target_user_id="NBA_user_id_here",
    events=["tweet"]
)

print(f"Webhook created: {result}")
```

## 🔧 Configuration

### Webhook Settings

```python
# Events you can listen for
events = [
    "tweet",           # New tweets
    "retweet",         # Retweets
    "reply",           # Replies
    "quote",           # Quote tweets
    "like",            # Likes
    "follow"           # Follow events
]

# Webhook URL format
webhook_url = f"{WEBHOOK_BASE_URL}/webhook/twitter/{username}"
```

### Celery Queue Configuration

```python
# Dedicated queues for different task types
task_routes = {
    'tasks.twitter_tasks.process_twitter_webhook': {'queue': 'twitter'},
    'tasks.twitter_tasks.analyze_tweet': {'queue': 'analysis'},
    'tasks.twitter_tasks.create_twitter_webhook': {'queue': 'twitter'},
    'tasks.twitter_tasks.monitor_webhook_health': {'queue': 'monitoring'},
}
```

## 📊 Monitoring & Health

### Health Check Endpoints

```bash
# Check webhook health
curl https://your-domain.com/webhook/twitter/health

# List active webhooks
curl https://your-domain.com/webhook/twitter/list

# Monitor Celery tasks
curl https://your-domain.com:5555  # Flower dashboard
```

### Health Metrics

- **Webhook Status**: Active/inactive webhooks
- **Failure Count**: Webhooks with processing errors
- **Last Activity**: Recent webhook activity
- **Queue Depth**: Pending tweet processing tasks

## 🚀 Deployment

### Render.com Deployment

```bash
# Set your Render API token
export RENDER_TOKEN="your_render_token_here"

# Run deployment script
chmod +x deploy_render.sh
./deploy_render.sh
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale workers as needed
docker-compose up -d --scale celery-twitter=3
```

## 🔍 Testing

### Test Webhook Endpoint

```bash
# Send test webhook payload
curl -X POST https://your-domain.com/webhook/twitter/test \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "id": "test_123",
      "text": "Test tweet content",
      "author_id": {"username": "testuser", "id": "123"},
      "created_at": "2024-01-01T00:00:00Z"
    }
  }'
```

### Local Testing

```python
from services.twitter_webhook_service import TwitterWebhookService

# Test tweet processing locally
service = TwitterWebhookService()
test_payload = {...}  # Your test payload
result = service.process_webhook_payload(test_payload)
print(result)
```

## 📈 Performance & Scaling

### Queue Management

- **Twitter Queue**: High-priority webhook processing
- **Analysis Queue**: CPU-intensive sentiment analysis
- **Maintenance Queue**: Background cleanup tasks

### Worker Scaling

```bash
# Scale Twitter workers for high tweet volume
celery worker --app=tasks.celery_app:celery_app --queues=twitter --concurrency=4

# Scale analysis workers for sentiment processing
celery worker --app=tasks.celery_app:celery_app --queues=analysis --concurrency=8
```

## 🛠️ Troubleshooting

### Common Issues

1. **Webhook Not Receiving Tweets**
   - Check webhook URL accessibility
   - Verify twitterapi.io webhook configuration
   - Check webhook health endpoint

2. **Tweets Not Processing**
   - Monitor Celery worker logs
   - Check queue depths
   - Verify database connectivity

3. **High Memory Usage**
   - Reduce worker concurrency
   - Enable task result expiration
   - Monitor tweet storage growth

### Debug Commands

```bash
# Check webhook status
curl https://your-domain.com/webhook/twitter/health

# Monitor Celery queues
celery -A tasks.celery_app:celery_app inspect active

# Check worker status
celery -A tasks.celery_app:celery_app inspect stats
```

## 🔐 Security Considerations

- **Webhook Authentication**: Implement signature verification
- **Rate Limiting**: Protect against webhook spam
- **Input Validation**: Sanitize all incoming webhook data
- **Database Access**: Use connection pooling and prepared statements

## 📚 API Reference

### Webhook Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook/twitter/<username>` | POST | Receive tweets for specific account |
| `/webhook/twitter/health` | GET | Webhook health status |
| `/webhook/twitter/manage` | POST | Create/delete webhooks |
| `/webhook/twitter/list` | GET | List active webhooks |
| `/webhook/twitter/test` | POST | Test webhook processing |

### Celery Tasks

| Task | Queue | Description |
|------|-------|-------------|
| `process_twitter_webhook` | twitter | Process incoming webhooks |
| `analyze_tweet` | analysis | Analyze tweet sentiment |
| `create_twitter_webhook` | twitter | Set up new webhook |
| `monitor_webhook_health` | monitoring | Health monitoring |

## 🎯 Next Steps

1. **Set up your twitterapi.io account** and get API key
2. **Deploy the webhook system** using Docker or Render.com
3. **Create webhooks** for accounts you want to track
4. **Monitor the system** using health endpoints and Flower
5. **Scale workers** based on tweet volume

## 📞 Support

- **Documentation**: Check the main README.md
- **Issues**: Use GitHub issues for bug reports
- **Discussions**: GitHub discussions for questions
- **Twitter**: Follow @your_handle for updates

---

**🎉 Congratulations!** You now have a real-time Twitter data pipeline that's more efficient, scalable, and cost-effective than traditional scraping approaches. 