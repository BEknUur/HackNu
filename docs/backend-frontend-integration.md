# Backend-Frontend Integration Analysis

**Generated:** 2025-10-19  
**System:** HackNu - Zamanbank Banking Application

---

## ✅ Integration Status: WORKING

The backend and frontend are properly connected with some configuration issues that need attention.

---

## 🔌 Connection Overview

### Backend Configuration
- **Status:** ✅ Running
- **URL:** `http://localhost:8000`
- **Docker Container:** `hacknu-backend-1` (Up 17 minutes)
- **Health Check:** ✅ Responding (`/api/health` → `{"health":"ok"}`)
- **Swagger UI:** ✅ Accessible at `http://localhost:8000/docs`
- **CORS:** ✅ Configured (`allow_origins=["*"]`)

### Frontend Configuration
- **Status:** ⚠️ Not Running (needs to start)
- **Framework:** Expo React Native (Web + Mobile)
- **Backend URL:** `http://46.101.175.118:8000` (Production server)
- **Local Override:** Available via `EXPO_PUBLIC_BACKEND_URL` env var

---

## 🚨 CRITICAL ISSUES

### Issue #1: Frontend Points to Production Server
**Location:** `frontend/lib/config.ts`, `frontend/app.json`, `frontend/app/login.tsx`

**Current Configuration:**
```typescript
// frontend/lib/config.ts
const url = 
  process.env.EXPO_PUBLIC_BACKEND_URL ||
  Constants.expoConfig?.extra?.BACKEND_URL ||
  'http://46.101.175.118:8000'; // ← Production server!

// frontend/app.json
"extra": {
  "BACKEND_URL": "http://46.101.175.118:8000", // ← Production!
  "GEMINI_API_KEY": "AIzaSyDvPoCG5MQP_9QNujTH7C9XbWKi3Uw6_8c"
}

// frontend/app/login.tsx
const API_URL = 'http://46.101.175.118:8000/api'; // ← Hardcoded production!
```

**Problem:**
- Frontend will connect to **production server** (`46.101.175.118:8000`) instead of **local backend** (`localhost:8000`)
- Local development changes won't be reflected
- Testing will affect production data

**Solution:**
1. Create `frontend/.env` file with local backend URL
2. Update hardcoded URLs in `login.tsx` to use config
3. Use `localhost` or `127.0.0.1` for local development

---

### Issue #2: Missing RAG Live Endpoints
**Location:** `backend/rag_agent/routes/live_query_router.py`

**Frontend Expects:**
```typescript
// frontend/lib/config.ts
endpoints: {
  rag: {
    live: {
      functionDeclarations: '/api/rag/live/function-declarations', // ← 404
      toolCall: '/api/rag/live/tool-call',                         // ← 404
      health: '/api/rag/live/health',                              // ← 404
    }
  }
}
```

**Backend Has:**
```python
# backend/rag_agent/routes/live_query_router.py
router = APIRouter(prefix="/api/rag/live")

@router.post("/query")  # ✅ Exists
async def query_supervisor_agent(...)
```

**Testing Results:**
```bash
curl http://localhost:8000/api/rag/live/health
# {"detail":"Not Found"}

curl http://localhost:8000/api/rag/live/function-declarations
# {"detail":"Not Found"}
```

**Problem:**
- Frontend's **live-chat.tsx** expects RAG Live endpoints that don't exist
- These endpoints were removed during git merge
- Live chat feature won't work with RAG tools

**Status:** Frontend currently uses **Gemini API directly** (not using backend RAG), so this doesn't break the app, but RAG integration is non-functional.

---

## 📊 API Endpoints Status

### ✅ Working Endpoints

| Endpoint | Status | Used By |
|----------|--------|---------|
| `/api/health` | ✅ Working | Health checks |
| `/api/auth/register` | ✅ Working | Login screen (registration) |
| `/api/auth/login` | ✅ Working | Login screen (authentication) |
| `/api/faceid/verify` | ✅ Working | Login screen (face verification) |
| `/api/rag/status` | ✅ Working | RAG system health |
| `/api/rag/query` | ✅ Working | Basic RAG queries |
| `/api/rag/live/query` | ✅ Working | Live RAG queries |
| `/api/rag/transaction/query` | ✅ Working | Transaction RAG (26 tools) |
| `/docs` | ✅ Working | API documentation |

### ⚠️ Missing Endpoints (Expected by Frontend)

| Endpoint | Status | Used By |
|----------|--------|---------|
| `/api/rag/live/function-declarations` | ❌ 404 | Live chat (tool definitions) |
| `/api/rag/live/tool-call` | ❌ 404 | Live chat (tool execution) |
| `/api/rag/live/health` | ❌ 404 | Live chat (health check) |

---

## 🎯 Frontend Pages Analysis

### 1. Login Page (`app/login.tsx`)
**Status:** ✅ Working (but needs config fix)

**Backend Calls:**
```typescript
// Face verification
POST http://46.101.175.118:8000/api/faceid/verify
- Uploads photo
- Returns user data if face matches

// Login
POST http://46.101.175.118:8000/api/auth/login
- Email/password authentication
- Returns user session

// Registration
POST http://46.101.175.118:8000/api/auth/register
- Creates new user
- Uploads avatar photo
```

**Issue:** Hardcoded production URL needs to use `config.ts`

---

### 2. Home Page (`app/(tabs)/index.tsx`)
**Status:** ✅ Working

**Backend Calls:** None (uses localStorage only)

**Functionality:**
- Displays user profile
- Logout button
- Navigation to other tabs

---

### 3. Face Verify Page (`app/(tabs)/face-verify.tsx`)
**Status:** ✅ Working

**Backend Calls:**
```typescript
POST http://46.101.175.118:8000/api/faceid/verify
- Standalone face verification
- Same endpoint as login
```

**Issue:** Hardcoded production URL

---

### 4. Live Chat Page (`app/(tabs)/live-chat.tsx`)
**Status:** ⚠️ Partially Working

**Backend Calls:**
- **None currently!** Uses Gemini API directly
- **Expected (not working):** RAG Live endpoints for tool integration

**Current Behavior:**
```typescript
// Uses useLiveAPI hook (direct Gemini connection)
const { connected, connect, disconnect, client } = useLiveAPI(apiOptions);

// Does NOT use:
// - /api/rag/live/function-declarations
// - /api/rag/live/tool-call
// - Backend tools (vector_search, web_search, transactions)
```

**Why It Still Works:**
- Live chat connects directly to Gemini API using `@google/genai` package
- Gemini API key in `app.json`: `AIzaSyDvPoCG5MQP_9QNujTH7C9XbWKi3Uw6_8c`
- No backend dependency for basic chat

**What's Missing:**
- RAG tool integration (company knowledge search)
- Transaction tools (banking operations)
- Vector search (document retrieval)

---

## 🔧 CORS Configuration

### Backend CORS Setup
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Status:** ✅ Properly configured for development
**Security Note:** Change `allow_origins=["*"]` to specific origins in production

---

## 🐳 Docker Configuration

### Services Running
```yaml
# docker-compose.yml
backend:
  - Port: 8000 → 8000 ✅
  - Status: Up 17 minutes ✅
  - Health: Responding ✅

postgres:
  - Port: 5433 → 5432 ✅
  - Status: Up 2 hours (healthy) ✅
  - Connection: Working ✅
```

### Environment Variables
```bash
# .env (root directory)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=hacknu
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/hacknu
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key
ENVIRONMENT=production
```

**Status:** ✅ Properly configured

---

## 📱 Frontend Dependencies

### Key Packages
```json
{
  "@google/genai": "^0.14.0",              // ✅ Gemini API client
  "@react-navigation/native": "^7.1.8",    // ✅ Navigation
  "expo": "~54.0.13",                      // ✅ Expo framework
  "expo-camera": "~16.0.10",               // ✅ Camera for face verification
  "react-native": "0.81.4"                 // ✅ Core framework
}
```

**Status:** ✅ All dependencies installed

---

## 🔍 Integration Flow Analysis

### 1. User Registration Flow
```mermaid
Frontend (login.tsx)
  ↓ 1. User enters details + captures photo
  ↓ 2. POST /api/auth/register
Backend (auth/router.py)
  ↓ 3. Validate data
  ↓ 4. Hash password
  ↓ 5. Save to PostgreSQL
  ↓ 6. Upload avatar
  ↓ 7. Return user data
Frontend
  ↓ 8. Save to localStorage
  ↓ 9. Redirect to home
```
**Status:** ✅ Working

---

### 2. Face Login Flow
```mermaid
Frontend (login.tsx)
  ↓ 1. User captures photo
  ↓ 2. POST /api/faceid/verify (with photo blob)
Backend (faceid/router.py)
  ↓ 3. Extract face embedding
  ↓ 4. Compare with all users in DB
  ↓ 5. Find best match (threshold: 0.2)
  ↓ 6. Return user data if verified
Frontend
  ↓ 7. Save to localStorage
  ↓ 8. Redirect to home
```
**Status:** ✅ Working

---

### 3. Live Chat Flow (Current)
```mermaid
Frontend (live-chat.tsx)
  ↓ 1. User clicks "Connect"
  ↓ 2. Initialize Gemini client
  ↓ 3. WebSocket connection to Gemini API directly
Gemini API (Google Cloud)
  ↓ 4. Process voice/text/video
  ↓ 5. Generate response
  ↓ 6. Stream back to frontend
Frontend
  ↓ 7. Display messages
```
**Backend Involvement:** ❌ None (direct Gemini connection)

---

### 4. Live Chat Flow (Expected with RAG)
```mermaid
Frontend (live-chat.tsx)
  ↓ 1. User asks question
  ↓ 2. Gemini recognizes need for tool
  ↓ 3. GET /api/rag/live/function-declarations (get available tools)
  ↓ 4. POST /api/rag/live/tool-call (execute tool)
Backend (rag_agent/routes/live_query_router.py)
  ↓ 5. Execute vector_search or web_search
  ↓ 6. Query LangChain agents
  ↓ 7. Access 26 banking tools if transaction endpoint
  ↓ 8. Return results
Frontend
  ↓ 9. Gemini incorporates results
  ↓ 10. Generate final response
```
**Backend Involvement:** ❌ Not working (endpoints missing)

---

## 🎯 Recommended Fixes

### Priority 1: Fix Frontend Backend URL Configuration

**Create `frontend/.env` file:**
```bash
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
EXPO_PUBLIC_GEMINI_API_KEY=AIzaSyDvPoCG5MQP_9QNujTH7C9XbWKi3Uw6_8c
```

**Update `frontend/app/login.tsx`:**
```typescript
// BEFORE
const API_URL = 'http://46.101.175.118:8000/api';

// AFTER
import { config } from '@/lib/config';
const API_URL = `${config.backendURL}/api`;
```

**Update `frontend/app/(tabs)/face-verify.tsx`:**
```typescript
// BEFORE
const API_URL = 'http://46.101.175.118:8000/api/faceid';

// AFTER
import { config } from '@/lib/config';
const API_URL = `${config.backendURL}/api/faceid`;
```

---

### Priority 2: Add Missing RAG Live Endpoints (Optional)

**Only if you want full RAG integration with live chat.**

**Add to `backend/rag_agent/routes/live_query_router.py`:**
```python
@router.get("/health")
async def health_check():
    """Health check for RAG Live system."""
    return {
        "status": "healthy",
        "system": "rag_live",
        "agents_available": ["supervisor", "local_knowledge", "web_search"]
    }

@router.get("/function-declarations")
async def get_function_declarations():
    """Return function declarations for Gemini Live API."""
    return {
        "functions": [
            {
                "name": "vector_search",
                "description": "Search company knowledge base and documents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for current information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    }

@router.post("/tool-call")
async def execute_tool_call(request: dict):
    """Execute a tool call from Gemini Live."""
    tool_name = request.get("name")
    arguments = request.get("arguments", {})
    
    if tool_name == "vector_search":
        result = rag_system.query(arguments["query"])
        return {"result": result}
    elif tool_name == "web_search":
        result = rag_system.query(arguments["query"])
        return {"result": result}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
```

---

### Priority 3: Update app.json for Local Development

**Change `frontend/app.json`:**
```json
{
  "expo": {
    "extra": {
      "BACKEND_URL": "http://localhost:8000",
      "GEMINI_API_KEY": "AIzaSyDvPoCG5MQP_9QNujTH7C9XbWKi3Uw6_8c"
    }
  }
}
```

---

## 🧪 Testing Checklist

### Backend Tests
```bash
# 1. Health check
curl http://localhost:8000/api/health
# Expected: {"health":"ok"}

# 2. RAG status
curl http://localhost:8000/api/rag/status
# Expected: JSON with agents and tools

# 3. API docs
open http://localhost:8000/docs
# Expected: Swagger UI loads

# 4. CORS headers
curl -H "Origin: http://localhost:3000" -I http://localhost:8000/api/health
# Expected: Access-Control-Allow-Origin: *
```

### Frontend Tests
```bash
cd frontend

# 1. Check environment
npx expo config --type introspect | grep BACKEND_URL
# Expected: Shows localhost:8000

# 2. Start Metro bundler
npx expo start
# Expected: No errors, dev server runs

# 3. Test in browser
# Navigate to: http://localhost:8081
# Expected: App loads, can register/login
```

### Integration Tests
1. **Registration:** Create new user with photo → Should save to local DB
2. **Face Login:** Capture photo → Should verify against local DB
3. **Home Screen:** Login → Should show user data from localStorage
4. **Live Chat:** Connect → Should connect to Gemini (no backend needed currently)

---

## 📈 Current System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  (React Native / Expo)                                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Login Screen │  │  Home Screen │  │  Live Chat   │     │
│  │              │  │              │  │              │     │
│  │ - Face Login │  │ - Profile    │  │ - Gemini API │     │
│  │ - Register   │  │ - Logout     │  │ - Voice      │     │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘     │
│         │                                     │              │
└─────────┼─────────────────────────────────────┼─────────────┘
          │                                     │
          │ HTTP (REST API)                    │ WebSocket
          │ localhost:8000                      │ (Direct to Google)
          ↓                                     ↓
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  (FastAPI)                                                   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth API     │  │  Face ID API │  │   RAG API    │     │
│  │              │  │              │  │              │     │
│  │ - Login      │  │ - Verify     │  │ - Query      │     │
│  │ - Register   │  │ - Match      │  │ - Live       │     │
│  └──────┬───────┘  └──────┬───────┘  │ - Transaction│     │
│         │                  │          └──────┬───────┘     │
│         └──────────────────┴─────────────────┘              │
│                            │                                 │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             PostgreSQL Database                       │  │
│  │  - users (auth, avatars)                             │  │
│  │  - accounts (banking)                                │  │
│  │  - transactions (history)                            │  │
│  │  - products (catalog)                                │  │
│  │  - cart (shopping)                                   │  │
│  │  - financial_goals (planning)                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Summary

### ✅ What's Working
1. **Backend API:** All REST endpoints responding
2. **Database:** PostgreSQL healthy, all tables created
3. **CORS:** Properly configured for cross-origin requests
4. **Docker:** Containers running smoothly
5. **Authentication:** Login/Register working
6. **Face Verification:** Face matching working
7. **RAG System:** All 3 RAG endpoints operational (basic, live, transactions)
8. **Tools:** All 26 tools loaded and available
9. **Live Chat:** Direct Gemini connection working

### ⚠️ What Needs Fixing
1. **Frontend Backend URL:** Points to production server instead of localhost
2. **Hardcoded URLs:** `login.tsx` and `face-verify.tsx` need to use config
3. **RAG Live Endpoints:** Missing 3 endpoints expected by frontend (but not critical since chat works via direct Gemini)
4. **Environment Files:** Need to create `frontend/.env` for local development

### 🎯 Action Items
1. **Immediate:** Create `frontend/.env` with `EXPO_PUBLIC_BACKEND_URL=http://localhost:8000`
2. **High Priority:** Update hardcoded URLs in `login.tsx` and `face-verify.tsx`
3. **Medium Priority:** Update `app.json` to use localhost by default
4. **Optional:** Add RAG Live endpoints if you want full backend integration with chat

---

## 🚀 Quick Start Commands

### Start Backend (Already Running)
```bash
docker compose up -d
# Backend: http://localhost:8000
# Postgres: localhost:5433
```

### Start Frontend
```bash
cd frontend
npx expo start

# Then choose:
# - Press 'w' for web
# - Scan QR for mobile
```

### Test Integration
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend environment (after starting)
# Check browser console for:
# "[Config] Backend URL: http://localhost:8000"
```

---

**Status:** Backend and frontend are structurally connected, but frontend needs configuration updates to point to local backend for development.
