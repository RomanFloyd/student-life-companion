#!/bin/bash

# Harbour Space Admin Panel - Quick Start Script
# This script helps you get started quickly with Docker

echo "🚀 Harbour Space Admin Panel - Quick Start"
echo "==========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""


# Start MongoDB container
echo "🐳 Starting MongoDB container..."
docker compose up -d

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
sleep 5

# Check if MongoDB is running
if docker ps | grep -q harbour-space-mongodb; then
    echo "✅ MongoDB is running!"
    echo ""
    echo "📊 MongoDB Details:"
    echo "   - Container: harbour-space-mongodb"
    echo "   - Host: localhost"
    echo "   - Port: 27017"
    echo "   - Username: admin"
    echo "   - Password: admin123"
    echo "   - Database: harbour-space"
    echo ""
else
    echo "❌ MongoDB failed to start. Check logs with:"
    echo "   docker compose logs mongodb"
    exit 1
fi

echo "🎉 Setup complete! You can now start the application:"
echo ""
echo "   npm run dev"
echo ""
echo "📱 Then visit: http://localhost:3000"
echo ""
echo "💡 Useful commands:"
echo "   docker compose logs -f mongodb  - View MongoDB logs"
echo "   docker compose down             - Stop MongoDB"
echo "   docker compose restart mongodb  - Restart MongoDB"
echo ""
