#!/bin/bash
# Populate database with sample data (Docker version)

echo "🍽️  Meal Planner - Populate Sample Data (Docker)"
echo "================================================"
echo ""

# Check if containers are running
if ! docker-compose ps | grep -q "mealplanner-backend.*Up"; then
    echo "❌ Backend container is not running. Please start services first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "📊 Populating database with sample data..."
docker-compose exec backend python populate_sample_data.py

echo ""
echo "✅ Done! You can now login with:"
echo "   Username: demo"
echo "   Password: password123"
echo ""
echo "Or try:"
echo "   Username: chef_alice"
echo "   Password: password123"
echo ""
