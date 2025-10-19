#!/bin/bash

# Quick Setup Script for Local Development
# This script configures the frontend to use the local backend server

echo "🔧 Setting up frontend for LOCAL development..."
echo ""

# Create .env file with local configuration
cat > .env << EOF
# Frontend Environment Variables - LOCAL DEVELOPMENT
# Generated: $(date)

# Backend API URL - Local Docker container
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000

# Gemini API Key - Get from https://makersuite.google.com/app/apikey
EXPO_PUBLIC_GEMINI_API_KEY=AIzaSyDvPoCG5MQP_9QNujTH7C9XbWKi3Uw6_8c

# Environment indicator
ENV=local
EOF

echo "✅ Created .env file with LOCAL configuration"
echo ""
echo "📋 Configuration:"
echo "   Backend URL: http://localhost:8000"
echo "   Environment: LOCAL"
echo ""
echo "🚀 Next steps:"
echo "   1. Make sure Docker backend is running: docker compose up -d"
echo "   2. Start Metro bundler: npm start"
echo "   3. Test backend connection: curl http://localhost:8000/api/health"
echo ""
echo "💡 To switch to PRODUCTION, run: ./setup-production.sh"
echo ""
