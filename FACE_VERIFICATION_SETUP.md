# 🔐 Face Verification System - Quick Setup Guide

Complete face verification system with real-time camera detection using DeepFace.

## 📋 Overview

This system allows users to:
- Register faces by placing images in the `backend/faceid/images/` folder
- Verify identity in real-time using device camera
- Get confidence scores and match results

## 🚀 Quick Start

### 1️⃣ Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Add face images to register
# Place images in backend/faceid/images/
# Name them like: john_doe.jpg, jane_smith.jpg

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2️⃣ Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Expo
npx expo start
```

### 3️⃣ Update API URL (Important!)

Edit `frontend/app/(tabs)/face-verify.tsx`:

```typescript
// For local development
const API_URL = 'http://YOUR_LOCAL_IP:8000/api/faceid';

// Examples:
// const API_URL = 'http://192.168.1.100:8000/api/faceid';  // Replace with your IP
// const API_URL = 'http://localhost:8000/api/faceid';      // For web/simulator
```

**To find your local IP:**
- Mac/Linux: `ifconfig | grep "inet "`
- Windows: `ipconfig`
- Or check in Expo dev tools

## 📸 Adding Face Images

1. Navigate to `backend/faceid/images/`
2. Add face photos (supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`)
3. **Naming convention**: Use person's name as filename
   - ✅ Good: `john_doe.jpg`, `jane_smith.jpg`, `alice.png`
   - ❌ Bad: `IMG_1234.jpg`, `photo.jpg`

**Photo Tips:**
- Clear, frontal face
- Good lighting
- No sunglasses or masks
- High resolution (at least 640x480)
- One face per image

## 🧪 Testing

### Test Backend API:

```bash
cd backend

# Test health and registered count
python faceid/test_api.py

# Test face verification with an image
python faceid/test_api.py path/to/test/image.jpg
```

### Test with cURL:

```bash
# Health check
curl http://localhost:8000/api/faceid/health

# Get registered count
curl http://localhost:8000/api/faceid/registered-count

# Verify a face
curl -X POST http://localhost:8000/api/faceid/verify \
  -F "file=@/path/to/image.jpg"
```

## 📱 Using the App

1. Open the app and go to **Face ID** tab
2. Tap **Start Verification**
3. Grant camera permissions
4. Position your face in the oval guide
5. Tap the capture button
6. Wait for verification results

## 🎯 API Endpoints

### Health Check
```
GET /api/faceid/health
```

### Get Registered Faces Count
```
GET /api/faceid/registered-count
```

### Verify Face
```
POST /api/faceid/verify
Content-Type: multipart/form-data
Body: file (image file)
```

**Response:**
```json
{
  "success": true,
  "message": "Verification completed successfully",
  "result": {
    "verified": true,
    "confidence": 0.8523,
    "matched_person": "john_doe",
    "distance": 0.2341,
    "threshold": 0.4,
    "model": "VGG-Face",
    "detector_backend": "opencv",
    "similarity_metric": "cosine"
  }
}
```

## ⚙️ Configuration

### Backend Configuration

Edit `backend/faceid/service.py` to change models:

```python
face_service = FaceVerificationService(
    model_name="VGG-Face",        # VGG-Face, Facenet, Facenet512, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace
    detector_backend="opencv",     # opencv, ssd, dlib, mtcnn, retinaface, mediapipe
    distance_metric="cosine"       # cosine, euclidean, euclidean_l2
)
```

**Model Recommendations:**
- **Fastest**: OpenFace, Dlib
- **Best Accuracy**: ArcFace, Facenet512
- **Balanced**: VGG-Face (default), Facenet

## 🔧 Troubleshooting

### "No registered faces found"
- Add at least one face image to `backend/faceid/images/`
- Check file extensions (must be .jpg, .jpeg, .png, .bmp, or .gif)

### "No face detected"
- Ensure good lighting
- Face should be clearly visible
- Remove sunglasses/masks
- Try different angles

### "Connection Error" on mobile
- Update `API_URL` with your computer's local IP
- Make sure backend is running
- Check firewall settings
- Both devices must be on the same network

### Low confidence scores
- Use better quality images
- Ensure consistent lighting between registration and verification
- Face should be centered and frontal
- Try a different model (e.g., Facenet512)

### Camera not working
- Grant camera permissions in device settings
- Restart the app
- Check if other apps can use the camera

## 📊 Performance

| Model | Speed | Accuracy | Memory |
|-------|-------|----------|--------|
| VGG-Face | Medium | High (98.9%) | 500MB |
| Facenet | Fast | High (99.2%) | 90MB |
| Facenet512 | Fast | Very High (99.6%) | 100MB |
| OpenFace | Very Fast | Medium (93.8%) | 25MB |
| ArcFace | Medium | Very High (99.4%) | 140MB |
| DeepFace | Slow | High (97.5%) | 600MB |

## 🔒 Security Best Practices

1. **Production Deployment:**
   - Use HTTPS instead of HTTP
   - Add authentication middleware
   - Implement rate limiting
   - Use environment variables for API URLs

2. **Data Privacy:**
   - Embeddings are not stored (only compared in real-time)
   - Temporary images are deleted immediately after verification
   - No face data is logged

3. **Access Control:**
   - Protect API endpoints with authentication
   - Implement user roles and permissions
   - Monitor for suspicious activity

## 📚 References

- [DeepFace GitHub](https://github.com/serengil/deepface)
- [Expo Camera Documentation](https://docs.expo.dev/versions/latest/sdk/camera/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 💡 Tips

1. **Better Results:**
   - Register multiple images per person (different angles/lighting)
   - Use high-quality images
   - Maintain consistent lighting conditions

2. **Performance:**
   - OpenFace is fastest for mobile apps
   - VGG-Face offers best balance
   - ArcFace for maximum accuracy (but slower)

3. **User Experience:**
   - Show loading indicators during verification
   - Provide clear feedback on camera positioning
   - Handle errors gracefully

## 🎨 UI Features

- ✅ Real-time camera preview
- ✅ Face oval guide for positioning
- ✅ Flip camera (front/back)
- ✅ Loading indicators
- ✅ Result cards with confidence scores
- ✅ Beautiful, modern design
- ✅ Permission handling

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the README in `backend/faceid/`
3. Test with the provided test script

---

Made with ❤️ using DeepFace, FastAPI, and Expo

