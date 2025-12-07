#!/bin/bash

# Script to start the microservices system
# Usage: ./start.sh [service_name]

echo "🚀 Starting Student Study Plan Recommendation System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

<<<<<<< HEAD
# Start the Flask application with Gunicorn
echo "Starting Flask application with Gunicorn..."
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - app:app 
=======
# Start services
if [ -z "$1" ]; then
    echo "📦 Starting all services..."
    docker-compose up -d --build
else
    echo "📦 Starting service: $1"
    docker-compose up -d --build "$1"
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
echo "🔍 Checking service health..."
curl -s http://localhost:5000/health | python -m json.tool || echo "API Gateway not ready yet"

echo ""
echo "✅ Services started!"
echo ""
echo "📋 Useful commands:"
echo "  docker-compose ps          # Check status"
echo "  docker-compose logs -f     # View logs"
echo "  docker-compose down        # Stop services"
echo ""
echo "🌐 Access points:"
echo "  Frontend: http://localhost:8080"
echo "  API Gateway: http://localhost:5000"
echo "  Health Check: http://localhost:5000/health"
>>>>>>> 1210fb40b81258e877cf6203cb6bedb9733593b9
