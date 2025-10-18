#!/usr/bin/env python3
"""
Скрипт для регистрации всех лиц из папки images
Создает эмбеддинги (векторные представления) для каждого фото
"""
import cv2
import sys
import os
from pathlib import Path

# Добавляем путь к модулю faceid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from faceid.face_service import face_service

# Папка с изображениями
IMAGES_DIR = Path(__file__).parent / "faceid" / "images"

# Список людей и их фото
PEOPLE = [
    {
        "id_person": "almas",
        "name": "Almas",
        "photo": "almas.jpg"
    },
    {
        "id_person": "beknur",
        "name": "Beknur",
        "photo": "beknur.jpg"
    },
    {
        "id_person": "sultan",
        "name": "Sultan",
        "photo": "sultan.jpg"
    },
    {
        "id_person": "turarbek",
        "name": "Turarbek",
        "photo": "turarbek.jpg"
    }
]

def register_all_faces():
    """Регистрируем все лица из папки images"""
    
    print("=" * 60)
    print("🚀 РЕГИСТРАЦИЯ ЛИЦЬ ИЗ ПАПКИ IMAGES")
    print("=" * 60)
    
    if not face_service.model_loaded:
        print("❌ Модель распознавания не загружена!")
        print("   Запустите сервер хотя бы один раз: uvicorn main:app")
        return
    
    db = SessionLocal()
    
    try:
        for person_data in PEOPLE:
            person_id = person_data["id_person"]
            name = person_data["name"]
            photo_name = person_data["photo"]
            
            photo_path = IMAGES_DIR / photo_name
            
            if not photo_path.exists():
                print(f"⚠️  Фото не найдено: {photo_path}")
                continue
            
            print(f"\n📸 Обрабатываю {name} ({photo_name})...")
            
            # Загружаем изображение
            image = cv2.imread(str(photo_path))
            if image is None:
                print(f"   ❌ Не удалось загрузить изображение")
                continue
            
            try:
                # Регистрируем человека
                result = face_service.enroll_person(
                    images=[image],
                    id_person=person_id,
                    name=name,
                    db_session=db,
                    metadata={
                        "source": "images_folder",
                        "photo_name": photo_name
                    }
                )
                
                print(f"   ✅ {name} успешно зарегистрирован!")
                print(f"   📊 Создан эмбеддинг (вектор 512 чисел)")
                print(f"   💾 Сохранено в базу данных")
                
            except ValueError as e:
                if "already exists" in str(e):
                    print(f"   ℹ️  {name} уже зарегистрирован")
                else:
                    print(f"   ❌ Ошибка: {e}")
            except Exception as e:
                print(f"   ❌ Ошибка при регистрации: {e}")
        
        print("\n" + "=" * 60)
        print("✅ РЕГИСТРАЦИЯ ЗАВЕРШЕНА!")
        print("=" * 60)
        
        # Показываем статистику
        from faceid.models import Person
        total_persons = db.query(Person).filter(Person.is_active == True).count()
        print(f"\n📊 Всего зарегистрировано людей: {total_persons}")
        print("\n🎯 Теперь можно использовать веб-интерфейс:")
        print("   http://localhost:8000")
        
    finally:
        db.close()

if __name__ == "__main__":
    register_all_faces()

