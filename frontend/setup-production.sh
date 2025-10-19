#!/bin/bash

# Quick Setup Script for Production Server
# This script configures the frontend to use the production backend server

echo "🌐 Setting up frontend for PRODUCTION server..."
echo ""

# Create .env file with production configuration
cat > .env << EOF
# Frontend Environment Variables - PRODUCTION SERVER
# Generated: $(date)

# Backend API URL - Production server
EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000

# Gemini API Key - Get from https://makersuite.google.com/app/apikey
EXPO_PUBLIC_GEMINI_API_KEY=AIzaSyDvPoCG5MQP_9QNujTH7C9XbWKi3Uw6_8c

# Environment indicator
ENV=production
EOF

echo "✅ Created .env file with PRODUCTION configuration"
echo ""
echo "📋 Configuration:"
echo "   Backend URL: http://46.101.175.118:8000"
echo "   Environment: PRODUCTION"
echo ""
echo "🚀 Next steps:"
echo "   1. Start Metro bundler: npm start"
echo "   2. Test backend connection: curl http://46.101.175.118:8000/api/health"
echo ""
echo "⚠️  WARNING: You are using PRODUCTION server"
echo "   - Changes will affect production data"
echo "   - Make sure production server is running"
echo ""
echo "💡 To switch back to LOCAL, run: ./setup-local.sh"
echo ""
