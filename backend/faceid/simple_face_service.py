"""
Простой сервис распознавания лиц используя OpenCV
Работает без InsightFace - только с Haar Cascades + гистограммы
"""
import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import logging

from .config import (
    THRESHOLD_HIGH_CONFIDENCE, THRESHOLD_MEDIUM_CONFIDENCE,
    MIN_FACE_SIZE, MAX_FACES_PER_IMAGE
)
from .schemas import VerdictEnum, LivenessEnum
from .utils import (
    normalize_embedding, cosine_similarity, assess_lighting_quality,
    assess_motion_blur, embedding_to_binary, binary_to_embedding
)
from .liveness_detection import liveness_detector
from .models import Person, FaceEmbedding

logger = logging.getLogger(__name__)


class SimpleFaceRecognitionService:
    """Простой сервис распознавания с OpenCV"""
    
    def __init__(self):
        self.face_cascade = None
        self.model_loaded = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Инициализация OpenCV"""
        try:
            logger.info("🚀 Загружаем OpenCV Haar Cascade...")
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.error("❌ Не удалось загрузить Haar cascade")
                return
            
            self.model_loaded = True
            logger.info("✅ OpenCV готов к работе!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            self.model_loaded = False
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Детекция лиц"""
        if not self.model_loaded:
            raise RuntimeError("Модель не загружена")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE)
        )
        
        detected_faces = []
        for (x, y, w, h) in faces[:MAX_FACES_PER_IMAGE]:
            if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
                continue
            
            face_region = image[y:y+h, x:x+w]
            embedding = self._create_embedding(face_region)
            
            detected_faces.append({
                'bbox': [int(x), int(y), int(w), int(h)],
                'confidence': 0.85,
                'embedding': embedding
            })
        
        return detected_faces
    
    def _create_embedding(self, face_region: np.ndarray) -> np.ndarray:
        """
        Создаем эмбеддинг (векторное представление) лица
        512-мерный вектор на основе гистограмм и HOG
        """
        # Resize к стандартному размеру
        face_resized = cv2.resize(face_region, (128, 128))
        gray_face = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        
        # 1. Гистограмма яркости (256 значений)
        hist = cv2.calcHist([gray_face], [0], None, [256], [0, 256])
        hist = hist.flatten()
        hist = hist / (np.sum(hist) + 1e-6)
        
        # 2. LBP (Local Binary Patterns) - текстурные признаки
        lbp = self._compute_lbp(gray_face)
        lbp_hist = cv2.calcHist([lbp], [0], None, [256], [0, 256])
        lbp_hist = lbp_hist.flatten()
        lbp_hist = lbp_hist / (np.sum(lbp_hist) + 1e-6)
        
        # Объединяем признаки
        features = np.concatenate([hist, lbp_hist])
        
        # Дополняем до 512
        if len(features) < 512:
            features = np.pad(features, (0, 512 - len(features)), 'constant')
        else:
            features = features[:512]
        
        return features.astype(np.float32)
    
    def _compute_lbp(self, gray_image: np.ndarray) -> np.ndarray:
        """Вычисление Local Binary Pattern"""
        rows, cols = gray_image.shape
        lbp = np.zeros((rows - 2, cols - 2), dtype=np.uint8)
        
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center = gray_image[i, j]
                code = 0
                
                if gray_image[i-1, j-1] >= center: code |= 1 << 0
                if gray_image[i-1, j] >= center: code |= 1 << 1
                if gray_image[i-1, j+1] >= center: code |= 1 << 2
                if gray_image[i, j+1] >= center: code |= 1 << 3
                if gray_image[i+1, j+1] >= center: code |= 1 << 4
                if gray_image[i+1, j] >= center: code |= 1 << 5
                if gray_image[i+1, j-1] >= center: code |= 1 << 6
                if gray_image[i, j-1] >= center: code |= 1 << 7
                
                lbp[i - 1, j - 1] = code
        
        return lbp
    
    def extract_embedding(self, image: np.ndarray) -> Optional[Tuple[np.ndarray, Dict]]:
        """Извлечение эмбеддинга"""
        faces = self.detect_faces(image)
        
        if not faces:
            return None
        
        best_face = max(faces, key=lambda f: f['confidence'])
        embedding = normalize_embedding(best_face['embedding'])
        
        x, y, w, h = best_face['bbox']
        face_region = image[y:y+h, x:x+w]
        
        lighting_score = assess_lighting_quality(face_region)
        blur_score = assess_motion_blur(face_region)
        
        metadata = {
            'bbox': [int(x) for x in best_face['bbox']],
            'confidence': float(best_face['confidence']),
            'lighting_score': float(lighting_score),
            'blur_score': float(blur_score),
            'embedding_norm': float(np.linalg.norm(embedding))
        }
        
        return embedding, metadata
    
    def verify_face(
        self,
        image: np.ndarray,
        db_session,
        check_liveness: bool = True,
        frames: Optional[List[np.ndarray]] = None
    ) -> Dict[str, Any]:
        """Верификация лица"""
        timestamp = datetime.utcnow()
        
        # Проверка живости
        liveness_result = LivenessEnum.UNKNOWN
        liveness_details = {}
        
        if check_liveness:
            if frames and len(frames) > 1:
                liveness_result, liveness_details = liveness_detector.check_liveness(frames)
            else:
                liveness_result, liveness_details = liveness_detector.check_liveness([image])
            
            logger.info(f"🔍 Liveness: {liveness_result}")
            
            if liveness_result == LivenessEnum.SPOOF:
                return self._create_response(
                    verdict=VerdictEnum.SPOOF,
                    liveness=liveness_result,
                    explain="🚫 Обнаружена подделка! Это фото или видео.",
                    timestamp=timestamp,
                    liveness_details=liveness_details
                )
        
        # Извлекаем эмбеддинг
        extraction_result = self.extract_embedding(image)
        
        if extraction_result is None:
            return self._create_response(
                verdict=VerdictEnum.NO_FACE_DETECTED,
                liveness=liveness_result,
                explain="❌ Лицо не обнаружено",
                timestamp=timestamp,
                liveness_details=liveness_details
            )
        
        probe_embedding, probe_metadata = extraction_result
        
        # Ищем в базе
        match_result = self._search_database(probe_embedding, db_session)
        
        if match_result is None:
            return self._create_response(
                verdict=VerdictEnum.NOT_FOUND,
                liveness=liveness_result,
                explain="❓ Этого человека нет в базе!",
                timestamp=timestamp,
                probe_metadata=probe_metadata,
                liveness_details=liveness_details
            )
        
        person, best_similarity, best_photo_id = match_result
        
        if best_similarity >= THRESHOLD_HIGH_CONFIDENCE:
            verdict = VerdictEnum.MATCH
            explain = f"✅ Это {person.name}! ({best_similarity*100:.1f}%)"
        elif best_similarity >= THRESHOLD_MEDIUM_CONFIDENCE:
            verdict = VerdictEnum.POSSIBLE_MATCH
            explain = f"🤔 Возможно {person.name} ({best_similarity*100:.1f}%)"
        else:
            verdict = VerdictEnum.NOT_FOUND
            explain = f"❌ Не найден (лучшее: {best_similarity*100:.1f}%)"
        
        return self._create_response(
            verdict=verdict,
            liveness=liveness_result,
            explain=explain,
            timestamp=timestamp,
            probe_metadata=probe_metadata,
            candidate_info={
                'id': person.id_person,
                'name': person.name,
                'similarity': best_similarity,
                'photo_id': best_photo_id
            },
            threshold_used=THRESHOLD_HIGH_CONFIDENCE if verdict == VerdictEnum.MATCH else THRESHOLD_MEDIUM_CONFIDENCE,
            liveness_details=liveness_details
        )
    
    def _search_database(
        self,
        probe_embedding: np.ndarray,
        db_session
    ) -> Optional[Tuple[Person, float, str]]:
        """Поиск по векторам в базе"""
        persons = db_session.query(Person).filter(Person.is_active == True).all()
        
        if not persons:
            logger.info("📭 База пуста")
            return None
        
        best_match = None
        best_similarity = -1.0
        best_photo_id = None
        
        for person in persons:
            for embedding_record in person.embeddings:
                ref_embedding = binary_to_embedding(
                    embedding_record.embedding,
                    dtype=np.float32
                )
                
                if len(ref_embedding) != len(probe_embedding):
                    if len(ref_embedding) > len(probe_embedding):
                        ref_embedding = ref_embedding[:len(probe_embedding)]
                    else:
                        ref_embedding = np.pad(
                            ref_embedding,
                            (0, len(probe_embedding) - len(ref_embedding)),
                            'constant'
                        )
                
                similarity = cosine_similarity(probe_embedding, ref_embedding)
                
                logger.info(f"   📊 {person.name}: {similarity*100:.1f}%")
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = person
                    best_photo_id = embedding_record.photo_id
        
        if best_match:
            logger.info(f"🎯 Лучший: {best_match.name} ({best_similarity*100:.1f}%)")
        
        return (best_match, best_similarity, best_photo_id) if best_match else None
    
    def enroll_person(
        self,
        images: List[np.ndarray],
        id_person: str,
        name: str,
        db_session,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Регистрация человека"""
        if not images:
            raise ValueError("Нужно хотя бы одно изображение")
        
        existing = db_session.query(Person).filter(
            Person.id_person == id_person
        ).first()
        
        if existing:
            raise ValueError(f"Человек {id_person} уже зарегистрирован")
        
        embeddings = []
        for idx, image in enumerate(images):
            extraction_result = self.extract_embedding(image)
            
            if extraction_result is None:
                logger.warning(f"⚠️ Лицо не найдено на фото {idx}")
                continue
            
            embedding, img_metadata = extraction_result
            embeddings.append({
                'embedding': embedding,
                'metadata': img_metadata,
                'photo_id': f"{id_person}_photo_{idx}"
            })
        
        if not embeddings:
            raise ValueError("Не найдено лиц")
        
        person = Person(
            id_person=id_person,
            name=name,
            photo_count=len(embeddings),
            person_metadata=metadata or {},
            is_active=True
        )
        db_session.add(person)
        db_session.flush()
        
        for emb_data in embeddings:
            embedding_record = FaceEmbedding(
                person_id=person.id,
                embedding=embedding_to_binary(emb_data['embedding']),
                embedding_norm=float(np.linalg.norm(emb_data['embedding'])),
                photo_id=emb_data['photo_id'],
                quality_metrics=emb_data['metadata']
            )
            db_session.add(embedding_record)
        
        db_session.commit()
        
        logger.info(f"✅ {name} зарегистрирован ({len(embeddings)} фото)")
        
        return {
            'success': True,
            'id_person': id_person,
            'name': name,
            'photo_count': len(embeddings),
            'message': f"✅ {name} добавлен!",
            'enrolled_at': person.enrolled_at
        }
    
    def _create_response(
        self,
        verdict: VerdictEnum,
        liveness: LivenessEnum,
        explain: str,
        timestamp: datetime,
        probe_metadata: Optional[Dict] = None,
        candidate_info: Optional[Dict] = None,
        threshold_used: Optional[float] = None,
        liveness_details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Создание ответа"""
        response = {
            'verdict': verdict.value,
            'id_candidate': candidate_info['id'] if candidate_info else None,
            'name_candidate': candidate_info['name'] if candidate_info else None,
            'similarity': candidate_info['similarity'] if candidate_info else None,
            'threshold_used': threshold_used,
            'explain': explain,
            'evidence': {
                'probe_face_box': probe_metadata['bbox'] if probe_metadata else [0, 0, 0, 0],
                'probe_embedding_norm': probe_metadata['embedding_norm'] if probe_metadata else 0.0,
                'candidate_stats': {
                    'id': candidate_info['id'],
                    'name': candidate_info['name'],
                    'best_similarity': candidate_info['similarity'],
                    'matched_reference_photo_id': candidate_info['photo_id'],
                    'reference_photo_similarity': candidate_info['similarity']
                } if candidate_info else None,
                'liveness': liveness.value
            },
            'diagnostics': {
                'detector_confidence': probe_metadata['confidence'] if probe_metadata else 0.0,
                'lighting_score': probe_metadata['lighting_score'] if probe_metadata else 0.0,
                'motion_blur_score': probe_metadata['blur_score'] if probe_metadata else 0.0
            },
            'timestamp': timestamp.isoformat() + 'Z'
        }
        
        if liveness_details:
            response['liveness_details'] = liveness_details
        
        return response


# Глобальный сервис
face_service = SimpleFaceRecognitionService()

