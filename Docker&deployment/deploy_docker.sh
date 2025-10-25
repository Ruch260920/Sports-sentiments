#!/bin/bash

# Docker Deployment Script for OMNI News Pipeline
echo "🐳 OMNI News Pipeline - Docker Deployment"
echo "========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    exit 1
fi

echo "🔧 Building and starting services..."

# Build images
echo "📦 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service status:"
docker-compose ps

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=20

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📱 Your services are now available at:"
echo "  Main App: http://localhost:5000"
echo "  Webhook Server: http://localhost:5001"
echo "  Flower Dashboard: http://localhost:5555"
echo ""
echo "🐳 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Scale workers: docker-compose up -d --scale celery-twitter=3" 