# Frontend Environment Configuration Guide

This guide explains how to configure the frontend to connect to different backend servers.

## 🚀 Quick Setup

### Option 1: Local Development (Recommended)
```bash
cd frontend
./setup-local.sh
npm start
```

### Option 2: Production Server
```bash
cd frontend
./setup-production.sh
npm start
```

### Option 3: Manual Configuration
Create a `.env` file in the `frontend` directory:

```bash
# For local development
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
EXPO_PUBLIC_GEMINI_API_KEY=your-api-key

# For production server
# EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000
# EXPO_PUBLIC_GEMINI_API_KEY=your-api-key
```

---

## 📋 Available Backend Servers

| Environment | URL | Use Case |
|-------------|-----|----------|
| **Local** | `http://localhost:8000` | Development on your machine |
| **Production** | `http://46.101.175.118:8000` | Live production server |
| **Mobile Testing** | `http://192.168.1.XXX:8000` | Testing on physical device |

---

## 🔧 Configuration Priority

The frontend checks for backend URL in this order:

1. **`.env` file** (Highest priority)
   - `EXPO_PUBLIC_BACKEND_URL=http://localhost:8000`
   
2. **`app.json` config**
   - `extra.BACKEND_URL`
   
3. **Default fallback**
   - `http://localhost:8000`

---

## 🔐 API Key Configuration

### Where to get Gemini API Key:
1. Visit: https://makersuite.google.com/app/apikey
2. Create new API key
3. Add to `.env` file

### Security Best Practices:
✅ **DO:** Store API key in `.env` file (ignored by git)
❌ **DON'T:** Commit API key to git
❌ **DON'T:** Put API key in `app.json` (it's tracked by git)

---

## 📱 Testing on Physical Mobile Device

If you want to test on your phone connected to the same WiFi:

1. Find your computer's IP address:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig
   ```

2. Update `.env`:
   ```bash
   EXPO_PUBLIC_BACKEND_URL=http://192.168.1.XXX:8000
   ```
   Replace `XXX` with your actual IP address.

3. Make sure backend allows connections:
   - Docker should bind to `0.0.0.0:8000` (not `127.0.0.1:8000`)
   - Check `docker-compose.yml`: `ports: - "8000:8000"`

---

## 🧪 Verify Configuration

### Check current backend URL:
```bash
# Start the app and check console logs
npm start

# Look for:
# [Config] Backend URL: http://localhost:8000
# [Config] Environment: LOCAL
```

### Test backend connection:
```bash
# Local
curl http://localhost:8000/api/health

# Production
curl http://46.101.175.118:8000/api/health

# Expected response: {"health":"ok"}
```

---

## 🔄 Switching Between Environments

### Switch to Local:
```bash
./setup-local.sh
# Restart Metro bundler
```

### Switch to Production:
```bash
./setup-production.sh
# Restart Metro bundler
```

### Or manually edit `.env`:
```bash
# Change this line:
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000

# To:
EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000
```

**Important:** Always restart Metro bundler after changing `.env`!

---

## 📝 Files Overview

```
frontend/
├── .env                    # Your configuration (NEVER commit!)
├── .env.example            # Template with all options
├── app.json                # Expo config (no secrets here!)
├── lib/config.ts           # Configuration loader
├── setup-local.sh          # Quick setup for local dev
└── setup-production.sh     # Quick setup for production
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" or "Network error"

**For Local Backend:**
1. Check if Docker is running: `docker ps`
2. Check if backend is running: `curl http://localhost:8000/api/health`
3. Check `.env` file exists and has correct URL
4. Restart Metro bundler

**For Production Backend:**
1. Check if production server is online: `curl http://46.101.175.118:8000/api/health`
2. Check your internet connection
3. Verify `.env` has production URL

### Issue: "API Key not configured"

1. Make sure `.env` file exists: `ls -la .env`
2. Check `.env` has: `EXPO_PUBLIC_GEMINI_API_KEY=...`
3. Variable must start with `EXPO_PUBLIC_`
4. Restart Metro bundler

### Issue: Changes not taking effect

1. Stop Metro bundler (Ctrl+C)
2. Clear cache: `npm start -- --clear`
3. Restart Metro bundler

### Issue: Mobile device can't connect to localhost

- `localhost` only works on the same machine
- Use your computer's IP address instead
- Example: `EXPO_PUBLIC_BACKEND_URL=http://192.168.1.100:8000`

---

## ✅ Environment Checklist

Before starting development:

- [ ] `.env` file exists
- [ ] `EXPO_PUBLIC_BACKEND_URL` is set
- [ ] `EXPO_PUBLIC_GEMINI_API_KEY` is set
- [ ] Backend server is running
- [ ] Backend health check passes
- [ ] Metro bundler shows correct backend URL in logs

---

## 🎯 Quick Reference

```bash
# Setup local development
./setup-local.sh && npm start

# Setup production server
./setup-production.sh && npm start

# Check current config
npm start # Look for [Config] logs

# Test backend
curl $(grep EXPO_PUBLIC_BACKEND_URL .env | cut -d '=' -f2)/api/health

# Clear cache and restart
npm start -- --clear
```

---

## 🔗 Related Documentation

- [Docker Setup](../docs/docker.md)
- [Backend API Documentation](http://localhost:8000/docs)
- [Expo Environment Variables](https://docs.expo.dev/guides/environment-variables/)
- [Backend-Frontend Integration](../docs/backend-frontend-integration.md)
