# 🔐 Face Auth - Система распознавания лиц

Система авторизации по распознаванию лиц с автоматической детекцией и проверкой живости.

## ✨ Возможности

- 📹 **Автоматическое распознавание** через веб-камеру
- 🔍 **Детекция лиц** с высокой точностью
- 🛡️ **Проверка живости** - защита от фото/видео
- ✅ **Быстрая авторизация** - 2 секунды на проверку
- 💾 **База данных** людей с их эмбеддингами

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
cd backend
uvicorn main:app --reload
```

Сервер запустится на http://localhost:8000

### 3. Открыть веб-интерфейс

Откройте в браузере: **http://localhost:8000**

## 🎯 Как использовать

1. **Откройте http://localhost:8000**
2. **Нажмите "📹 Включить камеру"**
3. **Система автоматически распознает лицо**
4. **Результат:**
   - ✅ **Найден** - показывает имя и авторизует
   - ❌ **Не найден** - человек не в базе
   - 🚫 **Подделка** - обнаружено фото/видео

## 📝 Регистрация новых людей

### Через API:

```bash
curl -X POST "http://localhost:8000/api/faceid/enroll" \
  -F "id_person=user123" \
  -F "name=Иван Иванов" \
  -F "images=@photo.jpg"
```

### Через тестовые изображения:

```bash
curl -X POST "http://localhost:8000/api/faceid/enroll-test-image"
```

Это зарегистрирует тестовое изображение из `backend/faceid/images/almas.jpg`

## 🔧 API Endpoints

- `GET /` - Веб-интерфейс
- `GET /health` - Статус системы
- `GET /api/faceid/health` - Статус Face ID
- `POST /api/faceid/enroll` - Регистрация человека
- `POST /api/faceid/verify` - Проверка лица
- `GET /api/faceid/persons` - Список зарегистрированных
- `GET /api/faceid/test-image/{name}` - Получить тестовое изображение

## 📁 Структура проекта

```
HackNu/
├── backend/
│   ├── faceid/              # Модуль распознавания лиц
│   │   ├── images/          # Тестовые изображения
│   │   ├── models.py        # Модели БД
│   │   ├── routes.py        # API endpoints
│   │   ├── advanced_face_service.py  # Сервис распознавания
│   │   └── ...
│   ├── main.py             # Главный файл приложения
│   ├── database.py         # Настройка БД
│   └── requirements.txt    # Зависимости
└── frontend/
    └── index.html          # Веб-интерфейс

```

## 🧪 Тестирование

### Зарегистрировать тестовое лицо:

```bash
curl -X POST "http://localhost:8000/api/faceid/enroll-test-image"
```

### Проверить распознавание:

```bash
curl -X GET "http://localhost:8000/api/faceid/test-verification"
```

## ⚙️ Настройки

Настройки в `backend/faceid/config.py`:

- `THRESHOLD_HIGH_CONFIDENCE = 0.40` - Порог высокой уверенности
- `THRESHOLD_MEDIUM_CONFIDENCE = 0.30` - Порог средней уверенности
- `MIN_FACE_SIZE = 80` - Минимальный размер лица в пикселях

## 🔒 Безопасность

- ✅ Проверка живости для защиты от спуфинга
- ✅ Эмбеддинги нормализованы L2
- ✅ Логирование всех попыток авторизации
- ✅ CORS настроен для безопасности

## 📊 База данных

SQLite база данных (`hacknu.db`) хранит:
- **Persons** - зарегистрированные люди
- **FaceEmbeddings** - эмбеддинги лиц (512-мерные векторы)
- **VerificationAttempts** - журнал попыток распознавания

## 🎓 Технологии

- **Backend:** FastAPI, SQLAlchemy
- **Computer Vision:** OpenCV, InsightFace (опционально)
- **Frontend:** Vanilla HTML/CSS/JS
- **Database:** SQLite

## 📞 Поддержка

Если нужна помощь - проверьте логи сервера в терминале.

## 📄 Лицензия

MIT License

---

**Сделано для HackNu 2024** 🚀

