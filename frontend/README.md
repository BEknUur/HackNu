# Frontend - ZamanBank with RAG Integration

React Native Expo application with Gemini Live integration and RAG tools.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Expo CLI

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

### Environment Configuration

Create a `.env` file in the frontend directory (if not using app.json defaults):

```bash
# Backend API URL (defaults to server if not set)
EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000

# Gemini API Key
EXPO_PUBLIC_GEMINI_API_KEY=your-gemini-api-key-here
```

**Note**: The app is pre-configured to use the production server at `http://46.101.175.118:8000`. You only need to set `EXPO_PUBLIC_BACKEND_URL` if you want to use a different backend.

## 📱 Features

### 1. Live Chat with RAG
- **Voice interaction** with Gemini Live
- **RAG tools integration**: vector_search and web_search
- **Multimodal**: Camera and screen sharing support
- **Multi-language**: English and Russian

### 2. Face Verification
- Face ID registration
- Face verification with confidence scores
- Real-time camera capture

### 3. E-commerce
- Product browsing
- Shopping cart
- Transactions

## 🔧 Configuration

### Backend URL

The backend URL is configured in multiple places (in priority order):

1. **Environment variable** (`.env` file):
   ```bash
   EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000
   ```

2. **App config** (`app.json`):
   ```json
   {
     "expo": {
       "extra": {
         "BACKEND_URL": "http://46.101.175.118:8000"
       }
     }
   }
   ```

3. **Default fallback**: `http://46.101.175.118:8000`

### Gemini API Key

Set your Gemini API key in `app.json`:

```json
{
  "expo": {
    "extra": {
      "GEMINI_API_KEY": "your-key-here"
    }
  }
}
```

## 🧠 RAG Integration

The Live Chat is integrated with the backend RAG system:

### How it works

1. User speaks or types a question
2. Gemini analyzes and decides which tools to call
3. Frontend intercepts tool calls and routes to backend
4. Backend executes tools (vector_search or web_search)
5. Results returned to Gemini
6. Gemini synthesizes answer with sources

### Tool Selection

- **vector_search**: Company policies, internal documents
- **web_search**: Current events, public information

### RAG Health Indicator

Look for the **🧠 RAG** indicator in the Live Chat header:
- **Green**: RAG tools are healthy and ready
- **Red**: RAG tools have issues (check backend)

## 📂 Project Structure

```
frontend/
├── app/                    # Screens (Expo Router)
│   ├── (tabs)/
│   │   ├── index.tsx      # Home
│   │   ├── explore.tsx    # Products
│   │   ├── live-chat.tsx  # Gemini Live + RAG
│   │   └── face-verify.tsx
│   └── _layout.tsx
├── components/            # Reusable components
├── hooks/                # Custom hooks
│   ├── use-live-api-with-rag.ts
│   └── use-rag-tools.ts
├── lib/                  # Libraries and utilities
│   ├── config.ts         # Configuration management
│   ├── rag-tools-client.ts
│   └── genai-live-client.ts
├── contexts/             # React contexts
└── constants/            # App constants
```

## 🎯 Available Scripts

```bash
# Start development server
npm start

# Start on specific platform
npm run ios
npm run android
npm run web

# Lint code
npm run lint

# Reset project (clean cache)
npm run reset-project
```

## 🐛 Debugging

### Check Backend Connection

```bash
# Check if backend is reachable
curl http://46.101.175.118:8000/api/health

# Check RAG tools status
curl http://46.101.175.118:8000/api/rag/live/health
```

### Console Logs

Look for these logs in the browser/expo console:

```
[Config] Backend URL: http://46.101.175.118:8000
[RAG Tools Client] Initialized with URL: http://46.101.175.118:8000
[RAG Tools] Loading function declarations...
[RAG Tools] Loaded tools: vector_search, web_search
[RAG Tools] Health status: { status: 'healthy' }
```

### Common Issues

**RAG tools not loading:**
- Check backend is running
- Verify backend URL in config
- Check network connectivity

**Gemini not calling tools:**
- Verify tools are registered (check logs)
- Ensure Gemini API key is valid
- Check system prompts include tool instructions

**Face verification not working:**
- Check camera permissions
- Verify backend faceid endpoint is accessible
- Check API URL configuration

## 🌐 Environment Modes

### Development (Local)
```bash
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Production (Server)
```bash
EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000
```

Default is production mode.

## 📝 Notes

- The app uses Expo Router for navigation
- Configuration is centralized in `lib/config.ts`
- RAG tools are automatically loaded when Live Chat connects
- Face verification requires camera permissions

## 🔗 Related Documentation

- [Gemini Live + RAG Integration](../docs/gemini-live-rag-integration.md)
- [Backend API Docs](http://46.101.175.118:8000/docs)
- [Expo Documentation](https://docs.expo.dev)

## 📄 License

MIT
