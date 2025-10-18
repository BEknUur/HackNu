"""
Face Recognition Service

Использует простую версию с OpenCV
Работает без компиляторов C++ и InsightFace
"""

# Используем простую версию с OpenCV
from .simple_face_service import face_service
print("✅ Загружен Simple Face Service (OpenCV)")
