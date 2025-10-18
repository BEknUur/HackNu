# 🚀 SETUP - Быстрый старт

## 1️⃣ Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

**Если получаете ошибку "externally-managed-environment":**

Используйте системный Python с флагом:
```bash
pip3 install --break-system-packages -r requirements.txt
```

Или создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

## 2️⃣ Запуск сервера

```bash
cd backend
uvicorn main:app --reload
```

Сервер запустится на http://localhost:8000

## 3️⃣ Регистрация всех лиц

Откройте в браузере или через curl:

```bash
curl -X POST "http://localhost:8000/api/faceid/enroll-all-from-images"
```

Это зарегистрирует всех 4 человек:
- Almas
- Beknur  
- Sultan
- Turarbek

## 4️⃣ Использование

1. Откройте http://localhost:8000
2. Нажмите "📹 Включить камеру"
3. Система автоматически распознает лица!

## ✅ Готово!

Теперь камера будет распознавать зарегистрированных людей по их векторным эмбеддингам!

