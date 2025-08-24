#!/bin/bash

echo "🚀 Starting SEO Agent Backend with Docker..."

# Build and start backend service
cd backend
docker-compose up --build -d

echo "✅ Backend service started!"
echo ""
echo "📊 Service Status:"
echo "  Backend API: http://localhost:3001"
echo ""
echo "📋 Next steps:"
echo "  1. Start lighthouse service: cd ../lighthouse-service && node server.js"
echo "  2. Start frontend: cd ../seo-agent-demo && npm run dev"
echo ""
echo "🔍 Testing backend..."
sleep 3

# Test if backend is running
echo "Testing backend API..."
curl -s http://localhost:3001/health || echo "Backend not ready yet"

echo ""
echo "🎉 Backend ready! Now start other services manually."
