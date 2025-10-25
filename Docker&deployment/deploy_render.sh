#!/bin/bash

# Render.com Deployment Script for OMNI News Pipeline
echo "🚀 OMNI News Pipeline - Render.com Deployment"
echo "=============================================="

# Check if required environment variables are set
if [ -z "$RENDER_TOKEN" ]; then
    echo "❌ Error: RENDER_TOKEN environment variable not set"
    echo "Please set your Render API token:"
    echo "export RENDER_TOKEN='your_render_token_here'"
    exit 1
fi

if [ -z "$TWITTER_API_KEY" ]; then
    echo "❌ Error: TWITTER_API_KEY environment variable not set"
    echo "Please set your twitterapi.io API key:"
    echo "export TWITTER_API_KEY='your_twitter_api_key_here'"
    exit 1
fi

# Render.com configuration
RENDER_API_URL="https://api.render.com/v1"
SERVICE_NAME="omni-news-pipeline"
WEBHOOK_SERVICE_NAME="omni-webhook-server"
WORKER_SERVICE_NAME="omni-celery-worker"

echo "📋 Configuration:"
echo "  Service Name: $SERVICE_NAME"
echo "  Webhook Service: $WEBHOOK_SERVICE_NAME"
echo "  Worker Service: $WORKER_SERVICE_NAME"
echo "  Render API: $RENDER_API_URL"

# Function to create/update a Render service
create_or_update_service() {
    local service_name=$1
    local service_type=$2
    local command=$3
    local env_vars=$4
    
    echo "🔧 Creating/updating $service_name ($service_type)..."
    
    # Check if service exists
    if curl -s -H "Authorization: Bearer $RENDER_TOKEN" \
        "$RENDER_API_URL/services" | grep -q "\"name\":\"$service_name\""; then
        
        echo "  ✅ Service $service_name already exists, updating..."
        # Get service ID and update
        service_id=$(curl -s -H "Authorization: Bearer $RENDER_TOKEN" \
            "$RENDER_API_URL/services" | \
            jq -r ".services[] | select(.name==\"$service_name\") | .id")
        
        # Update service
        curl -X PATCH \
            -H "Authorization: Bearer $RENDER_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"envVars\": $env_vars,
                \"buildCommand\": \"pip install -r requirements.txt\",
                \"startCommand\": \"$command\"
            }" \
            "$RENDER_API_URL/services/$service_id"
            
    else
        echo "  🆕 Creating new service $service_name..."
        
        # Create new service
        curl -X POST \
            -H "Authorization: Bearer $RENDER_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"$service_name\",
                \"type\": \"$service_type\",
                \"envVars\": $env_vars,
                \"buildCommand\": \"pip install -r requirements.txt\",
                \"startCommand\": \"$command\",
                \"plan\": \"starter\"
            }" \
            "$RENDER_API_URL/services"
    fi
    
    echo "  ✅ $service_name configured"
}

# Environment variables for all services
ENV_VARS='[
    {"key": "TWITTER_API_KEY", "value": "'$TWITTER_API_KEY'"},
    {"key": "DATABASE_URL", "value": "postgresql://omni_user:omni_password@postgres:5432/omni_news"},
    {"key": "CELERY_BROKER_URL", "value": "redis://redis:6379/0"},
    {"key": "CELERY_RESULT_BACKEND", "value": "redis://redis:6379/0"},
    {"key": "WEBHOOK_BASE_URL", "value": "https://'$WEBHOOK_SERVICE_NAME'.onrender.com"},
    {"key": "PYTHONPATH", "value": "/opt/render/project/src"}
]'

# Create/update services
echo ""
echo "🏗️  Deploying services to Render.com..."

# 1. Webhook server (Web Service)
create_or_update_service \
    "$WEBHOOK_SERVICE_NAME" \
    "web_service" \
    "python webhook_endpoints.py" \
    "$ENV_VARS"

# 2. Celery worker (Background Worker)
create_or_update_service \
    "$WORKER_SERVICE_NAME" \
    "background_worker" \
    "celery worker --app=tasks.celery_app:celery_app --loglevel=info --concurrency=2" \
    "$ENV_VARS"

# 3. Main application (Web Service)
create_or_update_service \
    "$SERVICE_NAME" \
    "web_service" \
    "python main.py dashboard" \
    "$ENV_VARS"

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📱 Your services are now available at:"
echo "  Main App: https://$SERVICE_NAME.onrender.com"
echo "  Webhook Server: https://$WEBHOOK_SERVICE_NAME.onrender.com"
echo "  Celery Worker: $WORKER_SERVICE_NAME (background service)"
echo ""
echo "🔗 Webhook URLs for twitterapi.io:"
echo "  - https://$WEBHOOK_SERVICE_NAME.onrender.com/webhook/twitter/{username}"
echo ""
echo "📊 Monitor your services at: https://dashboard.render.com"
echo ""
echo "⚠️  Important:"
echo "  1. Update your twitterapi.io webhook URLs to use the new Render.com URLs"
echo "  2. Set up your database and Redis instances on Render.com"
echo "  3. Configure your environment variables in the Render.com dashboard"
echo ""
echo "🚀 Ready to receive real-time tweets!" 