"""
Test routes for Face Recognition System
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from pathlib import Path

# Import database dependency
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db

# Create router
router = APIRouter(prefix="/api/faceid", tags=["Face Recognition Test"])


@router.get("/test-image")
async def get_test_image():
    """
    Get test image for demonstration
    """
    try:
        # Path to test image
        test_image_path = Path(__file__).parent / "images" / "almas.jpg"
        
        if not test_image_path.exists():
            raise HTTPException(status_code=404, detail="Test image not found")
        
        return FileResponse(
            path=str(test_image_path),
            media_type="image/jpeg",
            filename="test_face.jpg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-image/{image_name}")
async def get_test_image_by_name(image_name: str):
    """
    Get specific test image by name
    """
    try:
        # Path to test image
        test_image_path = Path(__file__).parent / "images" / image_name
        
        if not test_image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {image_name} not found")
        
        return FileResponse(
            path=str(test_image_path),
            media_type="image/jpeg",
            filename=image_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enroll-test-image")
async def enroll_test_image(db: Session = Depends(get_db)):
    """
    Enroll the test image as a sample person
    """
    try:
        from .face_service import face_service
        import cv2
        
        # Path to test image
        test_image_path = Path(__file__).parent / "images" / "almas.jpg"
        
        if not test_image_path.exists():
            raise HTTPException(status_code=404, detail="Test image not found")
        
        # Load image
        image = cv2.imread(str(test_image_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Failed to load test image")
        
        # Enroll as "Almas"
        result = face_service.enroll_person(
            images=[image],
            id_person="almas_test",
            name="Almas",
            db_session=db,
            metadata={"source": "test_image", "description": "Test enrollment"}
        )
        
        return {
            "success": True,
            "message": "Test image enrolled successfully",
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-verification")
async def test_verification(db: Session = Depends(get_db)):
    """
    Test verification with the enrolled test image
    """
    try:
        from .face_service import face_service
        import cv2
        
        # Path to test image
        test_image_path = Path(__file__).parent / "images" / "almas.jpg"
        
        if not test_image_path.exists():
            raise HTTPException(status_code=404, detail="Test image not found")
        
        # Load image
        image = cv2.imread(str(test_image_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Failed to load test image")
        
        # Verify the image
        result = face_service.verify_face(
            image=image,
            db_session=db,
            check_liveness=True
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enroll-all-from-images")
async def enroll_all_from_images(db: Session = Depends(get_db)):
    """
    Автоматическая регистрация всех людей из папки images
    Создает векторные эмбеддинги для каждого фото
    """
    try:
        from .face_service import face_service
        import cv2
        
        # Список всех людей
        people = [
            {"id": "almas", "name": "Almas", "photo": "almas.jpg"},
            {"id": "beknur", "name": "Beknur", "photo": "beknur.jpg"},
            {"id": "sultan", "name": "Sultan", "photo": "sultan.jpg"},
            {"id": "turarbek", "name": "Turarbek", "photo": "turarbek.jpg"}
        ]
        
        results = []
        images_dir = Path(__file__).parent / "images"
        
        for person_data in people:
            person_id = person_data["id"]
            name = person_data["name"]
            photo_name = person_data["photo"]
            
            photo_path = images_dir / photo_name
            
            if not photo_path.exists():
                results.append({
                    "name": name,
                    "status": "error",
                    "message": f"Фото не найдено: {photo_name}"
                })
                continue
            
            # Загружаем изображение
            image = cv2.imread(str(photo_path))
            if image is None:
                results.append({
                    "name": name,
                    "status": "error",
                    "message": "Не удалось загрузить изображение"
                })
                continue
            
            try:
                # Регистрируем
                result = face_service.enroll_person(
                    images=[image],
                    id_person=person_id,
                    name=name,
                    db_session=db,
                    metadata={"source": "images_folder", "photo": photo_name}
                )
                
                results.append({
                    "name": name,
                    "status": "success",
                    "message": f"✅ Создан эмбеддинг (вектор 512 чисел)"
                })
                
            except ValueError as e:
                if "already" in str(e).lower():
                    results.append({
                        "name": name,
                        "status": "exists",
                        "message": "Уже зарегистрирован"
                    })
                else:
                    results.append({
                        "name": name,
                        "status": "error",
                        "message": str(e)
                    })
            except Exception as e:
                results.append({
                    "name": name,
                    "status": "error",
                    "message": str(e)
                })
        
        # Подсчет статистики
        from .models import Person
        total_persons = db.query(Person).filter(Person.is_active == True).count()
        
        return {
            "success": True,
            "message": "✅ Регистрация завершена!",
            "results": results,
            "total_registered": total_persons
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embeddings")
async def get_embeddings(db: Session = Depends(get_db)):
    """
    Показать все эмбеддинги (векторы) в базе данных
    """
    try:
        from .models import Person, FaceEmbedding
        from .utils import binary_to_embedding
        import numpy as np
        
        # Получаем всех людей с их эмбеддингами
        persons = db.query(Person).filter(Person.is_active == True).all()
        
        result = {
            "total_persons": len(persons),
            "embeddings": []
        }
        
        for person in persons:
            person_data = {
                "id_person": person.id_person,
                "name": person.name,
                "photo_count": person.photo_count,
                "enrolled_at": person.enrolled_at.isoformat(),
                "embeddings": []
            }
            
            for embedding_record in person.embeddings:
                # Конвертируем из binary обратно в numpy array
                embedding_vector = binary_to_embedding(
                    embedding_record.embedding,
                    dtype=np.float32
                )
                
                embedding_data = {
                    "photo_id": embedding_record.photo_id,
                    "embedding_dimension": len(embedding_vector),
                    "embedding_norm": float(embedding_record.embedding_norm),
                    "first_10_values": embedding_vector[:10].tolist(),  # Первые 10 чисел
                    "last_10_values": embedding_vector[-10:].tolist(),  # Последние 10 чисел
                    "min_value": float(np.min(embedding_vector)),
                    "max_value": float(np.max(embedding_vector)),
                    "mean_value": float(np.mean(embedding_vector)),
                    "created_at": embedding_record.created_at.isoformat(),
                    "quality_metrics": embedding_record.quality_metrics
                }
                
                person_data["embeddings"].append(embedding_data)
            
            result["embeddings"].append(person_data)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embeddings/{person_id}")
async def get_person_embeddings(person_id: str, db: Session = Depends(get_db)):
    """
    Показать эмбеддинги конкретного человека
    """
    try:
        from .models import Person, FaceEmbedding
        from .utils import binary_to_embedding
        import numpy as np
        
        person = db.query(Person).filter(Person.id_person == person_id).first()
        
        if not person:
            raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
        
        result = {
            "id_person": person.id_person,
            "name": person.name,
            "photo_count": person.photo_count,
            "enrolled_at": person.enrolled_at.isoformat(),
            "embeddings": []
        }
        
        for embedding_record in person.embeddings:
            # Конвертируем из binary обратно в numpy array
            embedding_vector = binary_to_embedding(
                embedding_record.embedding,
                dtype=np.float32
            )
            
            embedding_data = {
                "photo_id": embedding_record.photo_id,
                "embedding_dimension": len(embedding_vector),
                "embedding_norm": float(embedding_record.embedding_norm),
                "full_embedding": embedding_vector.tolist(),  # Полный вектор!
                "created_at": embedding_record.created_at.isoformat(),
                "quality_metrics": embedding_record.quality_metrics
            }
            
            result["embeddings"].append(embedding_data)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
