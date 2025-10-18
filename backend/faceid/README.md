# Face Recognition System

Система распознавания лиц с проверкой живости для безопасной биометрической аутентификации.

## Возможности

- 🔍 **Распознавание лиц** - Детекция и извлечение эмбеддингов с помощью InsightFace
- 🛡️ **Проверка живости** - Защита от спуфинг-атак (фото/видео)
- 💾 **База данных** - Хранение эмбеддингов лиц в SQLite/PostgreSQL
- 🌐 **REST API** - Полноценный API для регистрации и верификации
- 📱 **Веб-интерфейс** - Простой интерфейс для тестирования

## Быстрый старт

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Тестирование

Откройте http://localhost:8000 в браузере для веб-интерфейса.

Или запустите тестовый скрипт:

```bash
python test_face_recognition.py
```

## API Endpoints

### Основные

- `GET /api/faceid/health` - Проверка состояния системы
- `POST /api/faceid/enroll` - Регистрация нового человека
- `POST /api/faceid/verify` - Верификация лица
- `POST /api/faceid/verify-multi-frame` - Многокадровая верификация
- `GET /api/faceid/persons` - Список зарегистрированных людей

### Тестовые

- `GET /api/faceid/test-image` - Получить тестовое изображение
- `POST /api/faceid/enroll-test-image` - Зарегистрировать тестовое изображение
- `GET /api/faceid/test-verification` - Тестовая верификация

## Использование

### Регистрация человека

```bash
curl -X POST "http://localhost:8000/api/faceid/enroll" \
  -F "id_person=john_doe" \
  -F "name=John Doe" \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg"
```

### Верификация лица

```bash
curl -X POST "http://localhost:8000/api/faceid/verify" \
  -F "image=@test_photo.jpg" \
  -F "check_liveness=true"
```

## Конфигурация

Основные настройки в `config.py`:

- `THRESHOLD_HIGH_CONFIDENCE = 0.55` - Порог высокой уверенности
- `THRESHOLD_MEDIUM_CONFIDENCE = 0.45` - Порог средней уверенности
- `DETECTION_MODEL = "buffalo_l"` - Модель детекции InsightFace
- `EMBEDDING_SIZE = 512` - Размерность эмбеддинга

## Структура ответа

```json
{
  "verdict": "match|possible_match|not_found|spoof|no_face_detected",
  "id_candidate": "person_id",
  "name_candidate": "Person Name",
  "similarity": 0.85,
  "threshold_used": 0.55,
  "explain": "Научное объяснение решения",
  "evidence": {
    "probe_face_box": [x, y, w, h],
    "probe_embedding_norm": 1.0,
    "candidate_stats": {...},
    "liveness": "live|spoof|unknown"
  },
  "diagnostics": {
    "detector_confidence": 0.95,
    "lighting_score": 0.8,
    "motion_blur_score": 0.2
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Безопасность

- ✅ Эмбеддинги нормализованы L2
- ✅ Проверка живости для предотвращения спуфинга
- ✅ Логирование попыток верификации
- ✅ Валидация размера и формата изображений
- ⚠️ Настройте шифрование эмбеддингов для продакшена

## Требования

- Python 3.8+
- InsightFace
- OpenCV
- FastAPI
- SQLAlchemy
- NumPy

## Лицензия

MIT License
