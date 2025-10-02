# Краткое руководство: Новый формат Workflow

## Быстрый старт

### 1. Проверка формата workflow

```bash
python test_new_format.py
```

Этот скрипт:
- ✅ Проверит правильность использования `body` vs `params`
- ✅ Сохранит workflow в MongoDB с валидацией
- ✅ Сохранит screens отдельно
- ✅ Сохранит predefined_context
- ✅ Получит и проверит полный workflow

### 2. Исправление формата в cart_workflow.json

**Найдите все integration states с POST/PUT/PATCH:**

```json
// ❌ НЕПРАВИЛЬНО
{
  "state_type": "integration",
  "name": "AddItemToCart",
  "expressions": [{
    "url": "{{base_url}}/carts/add-advertisement",
    "params": {           // ← Неправильно для POST
      "cart_id": "{{cart_id}}",
      "advertisement_id": "{{target_advertisement_id}}"
    },
    "method": "post"
  }]
}

// ✅ ПРАВИЛЬНО
{
  "state_type": "integration",
  "name": "AddItemToCart",
  "expressions": [{
    "url": "{{base_url}}/carts/add-advertisement",
    "body": {             // ← Правильно для POST
      "cart_id": "{{cart_id}}",
      "advertisement_id": "{{target_advertisement_id}}"
    },
    "method": "post"
  }]
}
```

### 3. Сохранение через API

```bash
curl -X POST http://localhost:8080/workflow/save \
  -H "Content-Type: application/json" \
  -d @cart_workflow.json
```

**Ответ:**
```json
{
  "status": "success",
  "wf_description_id": "67890abc...",
  "wf_context_id": "67890abc...",
  "screens_saved": 5
}
```

### 4. Получение полного workflow

```bash
curl http://localhost:8080/workflow/67890abc.../full
```

## Ключевые правила

| Метод HTTP | Используйте | Пример |
|------------|-------------|--------|
| GET        | `params`    | Query parameters в URL |
| POST       | `body`      | ✅ Данные в теле запроса |
| PUT        | `body`      | ✅ Данные в теле запроса |
| PATCH      | `body`      | ✅ Данные в теле запроса |
| DELETE     | `params`    | Обычно пустой |

## Структура MongoDB

```
lct_efs_db
├── states            # Определения состояний
│   └── { "_id": "...", "states": [...] }
│
├── workflow_context  # Предопределённый контекст
│   └── { "_id": "...", "base_url": "...", "user_id": 14, ... }
│
└── screens          # JSON экранов
    └── { "_id": "...", "workflow_id": "...", "state_id": "...", "screen": {...} }
```

## Что было исправлено в cart_workflow.json

### AddItemToCart
```diff
- "params": { "cart_id": "...", "advertisement_id": "..." }
+ "body": { "cart_id": "...", "advertisement_id": "..." }
```

### CreateOrder
```diff
- "params": { "name": "...", "shipping_method_id": "...", ... }
+ "body": { "name": "...", "shipping_method_id": "...", ... }
```

## Проверка логов

```bash
tail -f server.log | grep -E "(✅|⚠️|❌)"
```

Ищите:
- ✅ `Using new format with 'body'` - Правильный формат
- ⚠️ `should use 'body' instead of 'params'` - Старый формат
- ❌ Ошибки валидации

## Troubleshooting

### Ошибка: "Failed to save workflow"
```bash
# Проверьте MongoDB
mongosh
> use lct_efs_db
> db.states.find().limit(1)
```

### Ошибка: "POST запрос не работает"
1. Проверьте, используется ли `body` вместо `params`
2. Проверьте логи: `tail -50 server.log`
3. Проверьте формат: `python test_new_format.py`

### Screens не сохраняются
```python
# Проверьте наличие поля screen в state
state = {
    "state_type": "screen",  # ✅ Обязательно
    "name": "CartOverviewScreen",
    "screen": { ... }        # ✅ Обязательно
}
```

## Полезные команды

```bash
# Запуск сервера
uvicorn api.app:app --host 127.0.0.1 --port 8080

# Тестирование формата
python test_new_format.py

# Проверка workflow
curl http://localhost:8080/workflow/{id}/full | jq

# Проверка MongoDB
mongosh lct_efs_db --eval "db.states.countDocuments()"
mongosh lct_efs_db --eval "db.screens.countDocuments()"
mongosh lct_efs_db --eval "db.workflow_context.countDocuments()"
```

## Документация

- Полная документация: [docs/NEW_WORKFLOW_FORMAT.md](NEW_WORKFLOW_FORMAT.md)
- API документация: http://localhost:8080/docs
- Примеры: `cart_workflow.json`

## Миграция существующих workflows

```python
# Скрипт миграции (пример)
from storage.mongo.client import MongoDBClient

client = MongoDBClient("lct_efs_db", "states")

# Получить старый workflow
old_workflow = client.get("old_workflow_id")

# Исправить формат (заменить params на body для POST)
for state in old_workflow['states']:
    if state.get('state_type') == 'integration':
        for expr in state.get('expressions', []):
            if expr.get('method', '').lower() in ['post', 'put', 'patch']:
                if 'params' in expr and 'body' not in expr:
                    expr['body'] = expr.pop('params')

# Сохранить с новым форматом
new_id = client.insert_workflow_with_format_validation(old_workflow)
print(f"Migrated: {new_id}")
```

---

**Готово!** Теперь ваш workflow использует правильный HTTP формат и эффективное хранение в MongoDB. 🎉
