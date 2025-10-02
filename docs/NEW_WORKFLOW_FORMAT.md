# Новый формат Workflow

## Обзор

Система теперь поддерживает улучшенный формат workflow с правильной обработкой HTTP запросов и раздельным хранением данных в MongoDB.

## Основные изменения

### 1. Использование `body` вместо `params` для POST/PUT/PATCH

**Старый формат (устаревший):**
```json
{
  "state_type": "integration",
  "name": "AddItemToCart",
  "expressions": [
    {
      "variable": "add_item_response",
      "url": "{{base_url}}/carts/add-advertisement",
      "params": {
        "cart_id": "{{cart_id}}",
        "advertisement_id": "{{target_advertisement_id}}"
      },
      "method": "post"
    }
  ]
}
```

**Новый формат (рекомендуется):**
```json
{
  "state_type": "integration",
  "name": "AddItemToCart",
  "expressions": [
    {
      "variable": "add_item_response",
      "url": "{{base_url}}/carts/add-advertisement",
      "body": {
        "cart_id": "{{cart_id}}",
        "advertisement_id": "{{target_advertisement_id}}"
      },
      "method": "post"
    }
  ]
}
```

### 2. Раздельное хранение в MongoDB

Workflow теперь хранится в трёх отдельных коллекциях:

#### a) **states** - Определения состояний
```javascript
{
  "_id": ObjectId("..."),
  "states": [
    {
      "state_type": "technical",
      "name": "InitCartWorkflow",
      "transitions": [...],
      "expressions": [...]
    },
    // ... другие состояния
  ]
}
```

#### b) **workflow_context** - Предопределённый контекст
```javascript
{
  "_id": ObjectId("..."), // Совпадает с workflow ID
  "base_url": "http://localhost:8080/backservices/api",
  "user_id": 14,
  "cart_id": 3,
  // ... другие переменные контекста
}
```

#### c) **screens** - JSON экранов
```javascript
{
  "_id": ObjectId("..."),
  "workflow_id": "...",
  "state_id": "CartOverviewScreen",
  "screen": {
    "id": "screen-cart-overview",
    "type": "Screen",
    "name": "Корзина",
    // ... полное определение экрана
  }
}
```

## API Endpoints

### Сохранение Workflow

**POST** `/workflow/save`

```json
{
  "states": {
    "states": [
      // массив состояний
    ]
  },
  "predefined_context": {
    "base_url": "http://localhost:8080/backservices/api",
    "user_id": 14,
    // ... другие переменные
  }
}
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

### Получение полного Workflow

**GET** `/workflow/{workflow_id}/full`

**Ответ:**
```json
{
  "status": "success",
  "workflow_id": "67890abc...",
  "data": {
    "_id": "67890abc...",
    "states": [...],
    "predefined_context": {...},
    "screens": {
      "CartOverviewScreen": {...},
      "CheckoutSummaryScreen": {...}
    }
  }
}
```

## Правила для Integration States

### GET запросы
```json
{
  "variable": "cart_snapshot",
  "url": "{{base_url}}/carts/{{cart_id}}/with-advertisements",
  "params": {},  // Параметры в URL (query string)
  "method": "get"
}
```

### POST/PUT/PATCH запросы
```json
{
  "variable": "order_created",
  "url": "{{base_url}}/ships",
  "body": {  // ✅ Используйте body, не params
    "name": "Заказ для {{cart_snapshot.user.first_name}}",
    "shipping_method_id": "{{selected_shipping_method}}",
    "payment_method_id": "{{selected_payment_method}}"
  },
  "method": "post"
}
```

### DELETE запросы
```json
{
  "variable": "remove_item_response",
  "url": "{{base_url}}/carts/{{cart_id}}/advertisements/{{target_advertisement_id}}",
  "params": {},  // Обычно пусто для DELETE
  "method": "delete"
}
```

## Валидация формата

Система автоматически валидирует формат при сохранении:

- ✅ **POST/PUT/PATCH с `body`** - Новый правильный формат
- ⚠️ **POST/PUT/PATCH с `params`** - Старый формат, выводится предупреждение
- ✅ **GET/DELETE с `params`** - Корректно для query parameters

## Преимущества нового формата

1. **Соответствие HTTP стандартам** - POST/PUT/PATCH отправляют данные в теле запроса
2. **Модульность** - Раздельное хранение states, context и screens
3. **Переиспользование** - Screens можно обновлять независимо
4. **Эффективность** - Контекст не дублируется с каждым состоянием
5. **Масштабируемость** - Легко добавлять новые коллекции данных

## Migration Guide

### Обновление существующих workflow

1. Найдите все integration states с методом `post`, `put` или `patch`
2. Замените `"params"` на `"body"` в expressions
3. Сохраните обновлённый workflow через `/workflow/save`

### Пример миграции

**До:**
```json
{
  "url": "{{base_url}}/carts/add-advertisement",
  "params": {"cart_id": "{{cart_id}}"},
  "method": "post"
}
```

**После:**
```json
{
  "url": "{{base_url}}/carts/add-advertisement",
  "body": {"cart_id": "{{cart_id}}"},
  "method": "post"
}
```

## MongoDB Methods

### Новые методы в `MongoDBClient`

#### `insert_workflow_with_format_validation(workflow_data)`
Сохраняет workflow с валидацией нового формата:
```python
workflow_data = {
    "states": [...],
    "predefined_context": {...}
}
inserted_id = client.insert_workflow_with_format_validation(workflow_data)
```

#### `get_workflow_with_context(workflow_id)`
Получает полный workflow со всеми связанными данными:
```python
full_workflow = client.get_workflow_with_context(workflow_id)
# Возвращает: {states, predefined_context, screens}
```

## Логирование

Система логирует:
- ✅ Успешное сохранение с новым форматом
- ⚠️ Предупреждения о старом формате
- ❌ Ошибки валидации

## Best Practices

1. **Всегда используйте `body`** для POST/PUT/PATCH запросов
2. **Используйте `params`** только для query parameters (GET/DELETE)
3. **Сохраняйте screens отдельно** для переиспользования
4. **Версионируйте workflows** через MongoDB `_id`
5. **Тестируйте миграцию** перед применением на production

## Troubleshooting

### Проблема: POST запрос не работает
**Решение:** Проверьте, используете ли `body` вместо `params`

### Проблема: Screens не сохраняются
**Решение:** Убедитесь, что `state_type: "screen"` и поле `screen` заполнено

### Проблема: Context не загружается
**Решение:** Проверьте, что `predefined_context` передан при сохранении

## Поддержка

Для вопросов и проблем:
- Проверьте логи: `tail -f server.log`
- Изучите примеры: `cart_workflow.json`
- Документация API: `/docs` (Swagger UI)
