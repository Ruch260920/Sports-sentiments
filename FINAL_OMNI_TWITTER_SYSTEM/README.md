# 🚀 OMNI Twitter Webhook System

A complete, production-ready Twitter webhook system that integrates with the OMNI news pipeline for real-time tweet ingestion and analysis.

## 📁 **Project Structure**

```
FINAL_OMNI_TWITTER_SYSTEM/
├── core_app/                 # Main application files
│   ├── main.py              # CLI interface and main app
│   ├── init_db.py           # Database initialization
│   ├── config.py            # Configuration settings
│   └── requirements.txt     # Python dependencies
├── models/                   # Database models and schema
│   ├── models.py            # SQLAlchemy models (Entity, Tweet, Webhook)
│   ├── database.py          # Database connection and setup
│   ├── __init__.py          # Package initialization
│   └── migrations.py        # Database migration utilities
├── services/                 # Business logic services
│   ├── twitter_webhook_service.py  # Twitter webhook management
│   ├── sentiment_analyzer.py       # Sentiment analysis
│   ├── relevance_scorer.py         # Content relevance scoring
│   └── __init__.py                 # Package initialization
├── tasks/                    # Celery background tasks
│   ├── twitter_tasks.py     # Twitter-specific Celery tasks
│   ├── celery_app.py        # Celery application configuration
│   ├── scraping_tasks.py    # News scraping tasks
│   └── __init__.py          # Package initialization
├── webhook_server/           # Webhook HTTP endpoints
│   ├── webhook_endpoints.py # Full-featured webhook server
│   └── simple_webhook_server.py # Simplified test server
├── docker_deployment/        # Docker and deployment files
│   ├── docker-compose.yml   # Development environment
│   ├── docker-compose.prod.yml # Production environment
│   ├── Dockerfile           # Application container
│   ├── deploy_render.sh     # Render.com deployment
│   └── deploy_docker.sh     # Local Docker deployment
├── celery_management/        # Celery worker management
│   ├── celery_worker_manager.py # Worker process manager
│   └── __init__.py          # Package initialization
└── documentation/            # System documentation
    ├── README_TWITTER_WEBHOOKS.md # Twitter system guide
    └── README.md             # Original project README
```

## 🚀 **Quick Start**

### **1. Environment Setup**
```bash
# Set environment variables
export TWITTER_API_KEY="your_twitter_api_key"
export WEBHOOK_BASE_URL="http://localhost:5001"
export DATABASE_URL="sqlite:///omni_twitter.db"
export CELERY_BROKER_URL="redis://localhost:6379/0"
```

### **2. Install Dependencies**
```bash
pip install -r core_app/requirements.txt
```

### **3. Initialize Database**
```bash
python core_app/init_db.py
```

### **4. Start Webhook Server**
```bash
# Simple test server
python webhook_server/simple_webhook_server.py

# Full-featured server (requires all dependencies)
python webhook_server/webhook_endpoints.py
```

### **5. Start Celery Workers**
```bash
python celery_management/celery_worker_manager.py start-all
```

## 🔧 **System Features**

### **✅ Real-Time Twitter Data Ingestion**
- **Webhook endpoints** for receiving tweets from twitterapi.io
- **Automatic tweet processing** and storage
- **Metadata extraction** (likes, retweets, replies, quotes)
- **Raw data preservation** for additional processing

### **✅ Intelligent Content Analysis**
- **Sentiment analysis** of tweets and articles
- **Relevance scoring** for entity tracking
- **Engagement metrics** tracking and analysis
- **Content classification** and tagging

### **✅ Scalable Architecture**
- **Celery background tasks** for async processing
- **Redis message broker** for task queuing
- **PostgreSQL/SQLite** database support
- **Docker containerization** for easy deployment

### **✅ Production Ready**
- **Health check endpoints** for monitoring
- **Error handling** and logging
- **Docker Compose** configurations
- **Render.com deployment** scripts

## 🐦 **Twitter Webhook Integration**

### **Webhook Endpoints**
- `POST /webhook/twitter/receive` - Receive tweet webhooks
- `GET /webhook/twitter/health` - Health check
- `GET /webhook/twitter/test` - Test endpoint
- `GET /webhook/twitter/data` - View received data
- `POST /webhook/twitter/simulate` - Simulate webhook

### **Data Flow**
```
Twitter Webhook → Flask Server → Celery Queue → Background Processing → Database Storage
```

## 🐳 **Docker Deployment**

### **Development Environment**
```bash
cd docker_deployment
./deploy_docker.sh
```

### **Production Environment**
```bash
cd docker_deployment
./deploy_render.sh
```

## 📊 **Database Schema**

### **Core Tables**
- **`entities`** - Tracked entities (people, organizations)
- **`tweets`** - Twitter data with engagement metrics
- **`twitter_webhooks`** - Webhook subscription management
- **`articles`** - News articles with analysis
- **`sources`** - News sources and domains

### **Key Features**
- **JSON storage** for raw Twitter data
- **Indexed fields** for fast queries
- **Foreign key relationships** for data integrity
- **Timestamp tracking** for all data points

## 🔍 **Testing the System**

### **1. Database Test**
```bash
python test_twitter_system.py
```

### **2. Webhook Simulation**
```bash
curl -X POST http://localhost:5001/webhook/twitter/simulate
```

### **3. Health Check**
```bash
curl -X GET http://localhost:5001/webhook/twitter/health
```

## 🚀 **Production Deployment**

### **Render.com (Recommended)**
```bash
cd docker_deployment
./deploy_render.sh
```

### **Local Docker**
```bash
cd docker_deployment
./deploy_docker.sh
```

### **Manual Setup**
```bash
# Start Redis
redis-server

# Start Celery workers
celery -A tasks.celery_app worker --loglevel=info

# Start webhook server
python webhook_server/webhook_endpoints.py
```

## 📈 **Monitoring and Analytics**

### **Celery Flower Dashboard**
- **Task monitoring** and status
- **Worker health** checks
- **Queue management** and scaling
- **Performance metrics** and analytics

### **System Health**
- **Webhook endpoint** status
- **Database connection** health
- **Celery worker** status
- **Task processing** metrics

## 🔐 **Security Features**

- **Webhook signature verification** (configurable)
- **Rate limiting** and request validation
- **Error handling** without data exposure
- **Environment variable** configuration

## 📝 **Configuration**

### **Environment Variables**
```bash
TWITTER_API_KEY=your_api_key_here
WEBHOOK_BASE_URL=http://your-domain.com
DATABASE_URL=postgresql://user:pass@host:port/db
CELERY_BROKER_URL=redis://localhost:6379/0
```

### **Database Configuration**
- **SQLite** (development)
- **PostgreSQL** (production)
- **Automatic migrations** and schema updates

## 🎯 **Use Cases**

### **Sports Analytics**
- **Real-time athlete tweets** monitoring
- **Sentiment analysis** of fan reactions
- **Engagement tracking** for marketing insights

### **News Monitoring**
- **Breaking news** detection via Twitter
- **Source verification** and credibility scoring
- **Trend analysis** and prediction

### **Brand Monitoring**
- **Mention tracking** and sentiment analysis
- **Crisis detection** and alerting
- **Competitive intelligence** gathering

## 🆘 **Troubleshooting**

### **Common Issues**
1. **Import errors** - Check Python path and dependencies
2. **Database connection** - Verify DATABASE_URL
3. **Redis connection** - Ensure Redis server is running
4. **Webhook failures** - Check endpoint accessibility

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python webhook_server/simple_webhook_server.py
```

## 📞 **Support**

For issues and questions:
1. Check the **documentation/** folder
2. Review **error logs** and stack traces
3. Verify **environment configuration**
4. Test with **simple_webhook_server.py** first

## 🎉 **Success Metrics**

- ✅ **Real-time data ingestion** working
- ✅ **Database storage** operational
- ✅ **Background processing** functional
- ✅ **Webhook endpoints** responding
- ✅ **Docker deployment** ready
- ✅ **Production scaling** supported

---

**🚀 Your Twitter webhook system is ready for production deployment!** 