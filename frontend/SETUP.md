# 🚀 Быстрая настройка Frontend

## Проблема: Кнопка Connect не работает

### ✅ Исправлено:
1. Ошибка типов в `use-live-api-with-rag.ts` - **ИСПРАВЛЕНА**
2. Конфигурация Gemini API ключа

## 🔑 Настройка Gemini API Key

### Вариант 1: app.json (Рекомендуется)

Откройте `app.json` и добавьте ваш API ключ:

```json
{
  "expo": {
    "extra": {
      "BACKEND_URL": "http://46.101.175.118:8000",
      "GEMINI_API_KEY": "ВАШ-GEMINI-API-КЛЮЧ-СЮДА"
    }
  }
}
```

### Вариант 2: Переменные окружения

Создайте файл `.env` в корне frontend:

```bash
EXPO_PUBLIC_GEMINI_API_KEY=ВАШ-GEMINI-API-КЛЮЧ-СЮДА
EXPO_PUBLIC_BACKEND_URL=http://46.101.175.118:8000
```

## 📝 Где получить Gemini API Key

1. Перейдите на: https://makersuite.google.com/app/apikey
2. Создайте новый API ключ
3. Скопируйте и вставьте в конфигурацию

## 🧪 Проверка

После настройки ключа:

```bash
# Перезапустите приложение
npm start

# Откройте Live Chat
# Нажмите кнопку "Connect"
# Должно подключиться к Gemini Live
```

## 🐛 Отладка

### Проверьте консоль браузера на наличие ошибок:

```javascript
// Должны увидеть:
[Config] Backend URL: http://46.101.175.118:8000
[RAG Tools Client] Initialized with URL: http://46.101.175.118:8000
[RAG] Connecting with RAG tools: ["vector_search", "web_search"]
Connected to Gemini Live API! 🚀
```

### Типичные ошибки:

1. **"API key not found"**
   - Решение: Добавьте GEMINI_API_KEY в app.json

2. **"Network error"**
   - Решение: Проверьте, что backend работает
   - Тест: `curl http://46.101.175.118:8000/api/health`

3. **"RAG tools not loading"**
   - Решение: Убедитесь что vector store инициализирован
   - Тест: `curl http://46.101.175.118:8000/api/rag/live/health`

## ✨ Что исправлено

### 1. Ошибка типов (TypeScript)
**Было:**
```typescript
finalConfig.tools = tools.map(tool => ({
  functionDeclarations: [{
    parameters: tool.parameters,  // ❌ Неправильный тип
  }]
}));
```

**Стало:**
```typescript
finalConfig.tools = tools.map(tool => ({
  functionDeclarations: [{
    parameters: {
      type: tool.parameters.type as any,  // ✅ Правильный тип
      properties: tool.parameters.properties,
      required: tool.parameters.required,
    } as any,
  }]
})) as any;
```

### 2. Конфигурация backend URL
- Все localhost URL заменены на `http://46.101.175.118:8000`
- Создан централизованный `lib/config.ts`
- Автоматическое определение URL из нескольких источников

### 3. RAG интеграция
- Tools правильно регистрируются с Gemini
- Индикатор 🧠 RAG показывает статус
- Автоматическая загрузка function declarations

## 📱 Тестирование

1. **Подключение:**
   - Откройте Live Chat
   - Нажмите "Connect"
   - Статус должен стать "● LIVE" (красная кнопка)

2. **RAG Tools:**
   - Индикатор должен быть зеленым: 🧠 RAG
   - Проверьте консоль: "Tools registered with Gemini"

3. **Тестовые запросы:**
   - "What is our remote work policy?" - должен использовать vector_search
   - "What are latest AI trends?" - должен использовать web_search

## 🎯 Итоговый чеклист

- [ ] Добавлен GEMINI_API_KEY в app.json
- [ ] Backend работает на http://46.101.175.118:8000
- [ ] Vector store инициализирован
- [ ] Frontend запущен (npm start)
- [ ] Кнопка Connect работает
- [ ] RAG индикатор зеленый
- [ ] Голосовое взаимодействие работает

## 💡 Полезные команды

```bash
# Перезапуск с чистым кешем
npm start -- --clear

# Проверка backend
curl http://46.101.175.118:8000/api/health

# Проверка RAG
curl http://46.101.175.118:8000/api/rag/live/health

# Логи backend
docker compose logs -f backend
```

## 🆘 Если всё еще не работает

1. Проверьте GEMINI_API_KEY правильный
2. Перезапустите frontend полностью
3. Откройте DevTools консоль (F12)
4. Скопируйте и пришлите все ошибки
5. Проверьте Network вкладку на failed requests

