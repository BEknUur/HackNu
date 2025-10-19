# 🚀 Quick Start Cheat Sheet

## Start Development (Local Backend)
```bash
cd frontend
./setup-local.sh
npm start
```

## Switch to Production
```bash
cd frontend
./setup-production.sh
npm start
```

## Quick Commands
```bash
# Test local backend
curl http://localhost:8000/api/health

# Test production backend
curl http://46.101.175.118:8000/api/health

# Check current config
cat frontend/.env

# Clear Metro cache
cd frontend && npm start -- --clear
```

## Files You Care About
```
frontend/.env          ← Your configuration (edit this!)
frontend/.env.example  ← Template/reference
frontend/ENV_SETUP.md  ← Full documentation
```

## Troubleshooting
```bash
# Backend not responding?
docker compose up -d

# Changes not taking effect?
# Ctrl+C to stop Metro, then:
npm start -- --clear

# Mobile can't connect?
# Use your computer's IP instead of localhost
ifconfig | grep "inet "
# Then edit .env: EXPO_PUBLIC_BACKEND_URL=http://192.168.1.XXX:8000
```

## Important URLs
- Local API Docs: http://localhost:8000/docs
- Production API Docs: http://46.101.175.118:8000/docs
- Gemini API Keys: https://makersuite.google.com/app/apikey
