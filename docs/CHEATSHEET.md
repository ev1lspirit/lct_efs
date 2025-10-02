# 🚀 Шпаргалка: Новый формат Workflow

## 📝 Основные правила

### HTTP методы и параметры

| Метод  | Используй | ❌ Не используй |
|--------|-----------|-----------------|
| GET    | `params`  | `body`          |
| POST   | `body`    | `params`        |
| PUT    | `body`    | `params`        |
| PATCH  | `body`    | `params`        |
| DELETE | `params`  | `body`          |

## 💻 Примеры кода

### ✅ Правильный POST запрос
```json
{
  "url": "{{base_url}}/carts/add-advertisement",
  "body": {
    "cart_id": "{{cart_id}}",
    "advertisement_id": "{{target_advertisement_id}}"
  },
  "method": "post"
}
```

### ❌ Неправильный POST запрос
```json
{
  "url": "{{base_url}}/carts/add-advertisement",
  "params": {  // ← Неправильно!
    "cart_id": "{{cart_id}}",
    "advertisement_id": "{{target_advertisement_id}}"
  },
  "method": "post"
}
```

## 🗂️ MongoDB коллекции

```
states              - Определения состояний (37 states)
workflow_context    - Переменные контекста (35 vars)
screens            - JSON экранов (10 screens)
```

## 🔧 Быстрые команды

```bash
# Тестирование
python test_new_format.py

# Запуск сервера
uvicorn api.app:app --host 127.0.0.1 --port 8080

# Проверка логов
tail -f server.log | grep -E "(✅|⚠️|❌)"

# Сохранить workflow
curl -X POST http://localhost:8080/workflow/save \
  -H "Content-Type: application/json" \
  -d @cart_workflow.json

# Получить полный workflow
curl http://localhost:8080/workflow/{id}/full | jq
```

## 📊 MongoDB запросы

```javascript
// Подключиться
mongosh lct_efs_db

// Посмотреть коллекции
db.getCollectionNames()

// Посчитать документы
db.states.countDocuments()
db.workflow_context.countDocuments()
db.screens.countDocuments()

// Найти workflow
db.states.findOne({"_id": ObjectId("...")})

// Найти все screens для workflow
db.screens.find({"workflow_id": "..."})

// Найти конкретный screen
db.screens.findOne({
  "workflow_id": "...",
  "state_id": "CartOverviewScreen"
})
```

## 🔍 Что проверить в логах

```bash
✅ "Using new format with 'body'"          # Правильный формат
⚠️  "should use 'body' instead of 'params'" # Старый формат
❌ "Error"                                  # Ошибки
```

## 📚 Документация

- **Полная:** [docs/NEW_WORKFLOW_FORMAT.md](NEW_WORKFLOW_FORMAT.md)
- **Быстрый старт:** [docs/QUICK_START_NEW_FORMAT.md](QUICK_START_NEW_FORMAT.md)
- **Сравнение:** [docs/VISUAL_COMPARISON.md](VISUAL_COMPARISON.md)
- **Changelog:** [docs/NEW_FORMAT_CHANGELOG.md](NEW_FORMAT_CHANGELOG.md)

## 🐛 Troubleshooting

| Проблема | Решение |
|----------|---------|
| POST не работает | Проверь, используется ли `body` вместо `params` |
| Screens не сохраняются | Проверь `state_type: "screen"` и наличие поля `screen` |
| Context не загружается | Убедись, что `predefined_context` передан при сохранении |
| Workflow не найден | Проверь `workflow_id` в MongoDB |

## 🎯 Checklist при создании workflow

- [ ] POST/PUT/PATCH используют `body`
- [ ] GET/DELETE используют `params`
- [ ] Все screen states имеют поле `screen`
- [ ] `predefined_context` содержит все переменные
- [ ] Протестировано через `test_new_format.py`

## 📱 API Endpoints

```
POST /workflow/save              - Сохранить workflow
GET  /workflow/{id}/full         - Получить полный workflow
POST /client/workflow            - Выполнить workflow
```

## 🔑 Важные ID

После сохранения workflow:
```json
{
  "wf_description_id": "abc123",  // ID в states
  "wf_context_id": "abc123",      // ID в workflow_context (тот же!)
  "screens_saved": 10             // Кол-во сохранённых screens
}
```

## ⚡ Python код

### Сохранить workflow
```python
from storage.mongo.client import MongoDBClient

client = MongoDBClient("lct_efs_db", "states")
workflow_id = client.insert_workflow_with_format_validation({
    "states": [...],
    "predefined_context": {...}
})
```

### Получить полный workflow
```python
client = MongoDBClient("lct_efs_db", "states")
full_workflow = client.get_workflow_with_context(workflow_id)
# Содержит: states, predefined_context, screens
```

## 🎨 Структура workflow файла

```json
{
  "states": [
    {
      "state_type": "technical|integration|screen",
      "name": "StateName",
      "transitions": [...],
      "expressions": [...],
      "screen": {...}  // Только для screen states
    }
  ],
  "predefined_context": {
    "base_url": "http://...",
    "user_id": 14,
    ...
  }
}
```

## ✅ Валидация перед деплоем

```bash
# 1. Запустить тесты
python test_new_format.py

# 2. Проверить формат
grep -r "\"method\": \"post\"" cart_workflow.json
# Убедись, что есть "body", а не "params"

# 3. Проверить MongoDB
mongosh lct_efs_db --eval "db.states.countDocuments()"

# 4. Проверить API
curl http://localhost:8080/docs
```

## 🚨 Критические ошибки

1. **POST с params** → Используй `body`
2. **Отсутствие predefined_context** → Добавь контекст
3. **Screen без поля screen** → Добавь `"screen": {...}`
4. **Несовпадающие ID** → workflow_id и context_id должны быть одинаковыми

---

**💡 Совет:** Держи эту шпаргалку под рукой при работе с workflows!

**📞 Помощь:** Проверь `docs/` если нужны детали
