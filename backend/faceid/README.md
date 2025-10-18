# Face Verification System

This module implements real-time face verification using DeepFace library.

## Features

- ✅ **Real-time Camera Capture**: Users can verify their identity using their device camera
- ✅ **Multiple Face Matching**: Compares captured face against all registered faces in the database
- ✅ **High Accuracy**: Uses VGG-Face model with cosine similarity metric
- ✅ **Beautiful UI**: Modern React Native interface with camera preview and face guide
- ✅ **Detailed Results**: Shows confidence score, matched person, and verification status

## How It Works

1. **Backend**: Loops through all images in `backend/faceid/images/` folder
2. **Frontend**: User captures their face in real-time using device camera
3. **Verification**: DeepFace compares the captured image with all registered faces
4. **Result**: Returns the best match with confidence score

## Setup

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Add face images to register:
   - Place face images in `backend/faceid/images/` folder
   - Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`
   - Name the files with person's name (e.g., `john_doe.jpg`, `jane_smith.jpg`)
   - **Important**: Use clear, well-lit photos with visible faces

3. Run the backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Update API URL in `frontend/app/(tabs)/face-verify.tsx`:
```typescript
const API_URL = 'http://YOUR_BACKEND_IP:8000/api/faceid';
```

3. Run the app:
```bash
npx expo start
```

## API Endpoints

### POST `/api/faceid/verify`
Verify a face against all registered faces.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (image file)

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

### GET `/api/faceid/registered-count`
Get the number of registered faces.

**Response:**
```json
{
  "success": true,
  "count": 5,
  "message": "Found 5 registered face(s)"
}
```

### GET `/api/faceid/health`
Health check for the face verification service.

**Response:**
```json
{
  "status": "healthy",
  "service": "Face Verification",
  "model": "VGG-Face",
  "detector": "opencv",
  "metric": "cosine"
}
```

## Configuration

You can customize the face recognition model in `backend/faceid/service.py`:

```python
face_service = FaceVerificationService(
    model_name="VGG-Face",        # Options: VGG-Face, Facenet, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace
    detector_backend="opencv",     # Options: opencv, ssd, dlib, mtcnn, retinaface, mediapipe
    distance_metric="cosine"       # Options: cosine, euclidean, euclidean_l2
)
```

## Tips for Best Results

1. **Image Quality**:
   - Use high-resolution images (minimum 640x480)
   - Ensure good lighting conditions
   - Face should be clearly visible and centered

2. **Registration**:
   - Use frontal face images for registration
   - Avoid sunglasses, masks, or heavy makeup
   - One face per image

3. **Verification**:
   - Position face within the oval guide
   - Ensure good lighting
   - Look directly at the camera
   - Remove accessories if possible

## Troubleshooting

### "No face detected" error
- Ensure the image has a clear, visible face
- Try different lighting conditions
- Check if the face detector backend is working

### Low confidence scores
- Improve image quality
- Use better lighting
- Ensure face is centered and frontal
- Consider using a different model (e.g., Facenet512)

### Connection error on mobile
- Make sure backend is accessible from mobile device
- Update API_URL with correct IP address
- Check if firewall is blocking connections
- Use `http://` not `https://` for local development

## Models Performance

| Model | Speed | Accuracy | Size |
|-------|-------|----------|------|
| VGG-Face | Medium | High | Large |
| Facenet | Fast | High | Medium |
| OpenFace | Very Fast | Medium | Small |
| ArcFace | Medium | Very High | Large |
| DeepFace | Slow | High | Large |

## Security Notes

- Face embeddings are not stored, only compared in real-time
- Images are temporarily stored during verification and deleted immediately
- Use HTTPS in production
- Implement rate limiting to prevent abuse
- Add authentication to protect API endpoints

## References

- [DeepFace GitHub](https://github.com/serengil/deepface)
- [DeepFace Documentation](https://github.com/serengil/deepface#readme)

