#!/usr/bin/env python3
"""
Скрипт для просмотра эмбеддингов в базе данных
"""
import sys
import os
import numpy as np

# Добавляем путь к модулю faceid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from faceid.models import Person, FaceEmbedding
from faceid.utils import binary_to_embedding

def view_embeddings():
    """Показать все эмбеддинги"""
    
    print("=" * 80)
    print("🧠 ПРОСМОТР ЭМБЕДДИНГОВ (ВЕКТОРОВ) В БАЗЕ ДАННЫХ")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Получаем всех людей
        persons = db.query(Person).filter(Person.is_active == True).all()
        
        if not persons:
            print("❌ В базе нет зарегистрированных людей!")
            print("   Сначала запустите: curl -X POST http://localhost:8000/api/faceid/enroll-all-from-images")
            return
        
        print(f"📊 Найдено людей: {len(persons)}")
        print()
        
        for person in persons:
            print(f"👤 {person.name} (ID: {person.id_person})")
            print(f"   📸 Фото: {person.photo_count}")
            print(f"   📅 Зарегистрирован: {person.enrolled_at}")
            print()
            
            for i, embedding_record in enumerate(person.embeddings):
                print(f"   📷 Фото {i+1} ({embedding_record.photo_id}):")
                
                # Конвертируем из binary в numpy array
                embedding_vector = binary_to_embedding(
                    embedding_record.embedding,
                    dtype=np.float32
                )
                
                print(f"      🔢 Размерность: {len(embedding_vector)} чисел")
                print(f"      📏 Норма вектора: {embedding_record.embedding_norm:.4f}")
                print(f"      📊 Min: {np.min(embedding_vector):.4f}, Max: {np.max(embedding_vector):.4f}")
                print(f"      📈 Среднее: {np.mean(embedding_vector):.4f}")
                print(f"      🔢 Первые 10 чисел: {embedding_vector[:10]}")
                print(f"      🔢 Последние 10 чисел: {embedding_vector[-10:]}")
                print(f"      ⚙️  Качество: {embedding_record.quality_metrics}")
                print()
        
        print("=" * 80)
        print("✅ ЭМБЕДДИНГИ ПОКАЗАНЫ!")
        print("=" * 80)
        
        # Показываем как получить через API
        print("\n🌐 Или через API:")
        print("   Все эмбеддинги: http://localhost:8000/api/faceid/embeddings")
        print("   Конкретный человек: http://localhost:8000/api/faceid/embeddings/almas")
        
    finally:
        db.close()

if __name__ == "__main__":
    view_embeddings()
