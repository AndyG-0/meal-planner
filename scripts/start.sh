#!/bin/bash
# Quick Start Script for Meal Planner

echo "🍽️  Meal Planner - Quick Start"
echo "================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update the SECRET_KEY in .env for production use!"
    echo ""
fi

# Start Docker Compose
echo "🚀 Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✨ Meal Planner is ready!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend:  http://localhost:3080"
echo "   Backend:   http://localhost:8180"
echo "   API Docs:  http://localhost:8180/docs"
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
