# Исправление Integration State: "Загрузка милых картинок"

## 🔴 Текущая проблема

```json
{
  "state_type": "integration",
  "name": "Загрузка милых картинок",
  "expressions": [
    {
      "variable": "cute_images",  // ✅ Expression определён
      "url": "https://nekos.best/api/v2/hug?amount=4",
      "method": "get"
    }
  ],
  "transitions": [
    {
      "state_id": "Экран с милыми картинками",
      "variable": null  // ❌ ПРОБЛЕМА! Переход не связан с переменной
    }
  ]
}
```

## ✅ Решение

### Вариант 1: Исправить через MongoDB

```javascript
// Подключитесь к MongoDB
docker exec -it lct_efs-mongo-1 mongosh test

// Обновите переход
db.states.updateOne(
  { "states.name": "Загрузка милых картинок" },
  { 
    $set: { 
      "states.$[state].transitions.$[trans].variable": "cute_images"
    } 
  },
  {
    arrayFilters: [
      { "state.name": "Загрузка милых картинок" },
      { "trans.state_id": "Экран с милыми картинками" }
    ]
  }
)
```

### Вариант 2: Пересохранить workflow через API

Исправьте JSON файл:

```json
{
  "states": [
    {
      "state_type": "integration",
      "name": "Загрузка милых картинок",
      "expressions": [
        {
          "variable": "cute_images",
          "url": "https://nekos.best/api/v2/hug?amount=4",
          "method": "get"
        }
      ],
      "transitions": [
        {
          "state_id": "Экран с милыми картинками",
          "variable": "cute_images"  // ✅ Добавлено!
        }
      ],
      "initial_state": true
    },
    {
      "state_type": "screen",
      "name": "Экран с милыми картинками",
      "screen": { /* ... */ },
      "transitions": []
    }
  ]
}
```

Затем:
```bash
curl -X POST http://localhost:8080/workflow/save \
  -H "Content-Type: application/json" \
  -d @fixed_workflow.json
```

## 🔍 Почему это важно

### Как работает биндинг в Integration State:

1. **Expression** объявляет переменную: `"variable": "cute_images"`
2. **Transition** должен **ссылаться** на эту переменную: `"variable": "cute_images"`
3. Система связывает их автоматически

### Код биндинга (states.py):
```python
# Для integration state
binding_expression_key = "variable"  # Ключ в expression
binding_key = "variables"             # Ключ в transition

# Находит transition, где:
expr.variable in transition.variables
# "cute_images" in {"cute_images"} ✅
# "cute_images" in {None} ❌
```

## 📊 Правила для Integration State

### ✅ Правильная структура:
```json
{
  "state_type": "integration",
  "name": "API запрос",
  "expressions": [
    { "variable": "result", "url": "..." }
  ],
  "transitions": [
    { 
      "state_id": "Следующий экран",
      "variable": "result"  // ⚠️ ОБЯЗАТЕЛЬНО!
    }
  ]
}
```

### ❌ Типичные ошибки:

#### Ошибка 1: `variable: null`
```json
{ "state_id": "Next", "variable": null }  // ❌ Не свяжется!
```

#### Ошибка 2: Несовпадение имён
```json
{
  "expressions": [
    { "variable": "result" }  // ✅
  ],
  "transitions": [
    { "variable": "data" }    // ❌ Разные имена!
  ]
}
```

#### Ошибка 3: Множественные переходы
```json
{
  "expressions": [
    { "variable": "result" }
  ],
  "transitions": [
    { "variable": "result", "state_id": "Success" },
    { "variable": "result", "state_id": "Error" }  // ❌ Два перехода!
  ]
}
```

#### Ошибка 4: Условие в переходе
```json
{
  "transitions": [
    { 
      "variable": "result",
      "case": "result.status == 200"  // ❌ Integration не поддерживает условия!
    }
  ]
}
```

## 🧪 Проверка

После исправления проверьте:

```bash
# 1. Запустите сервер
./.venv/bin/python -m uvicorn api.app:app --reload --port 8080

# 2. Попробуйте выполнить workflow
curl -X POST http://localhost:8080/client/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "client_session_id": "test-cute-images",
    "workflow_id": "YOUR_WORKFLOW_ID",
    "input_event": "START"
  }'

# 3. Не должно быть ошибки про transitions!
```

## 🎯 Результат

После исправления биндинг пройдёт успешно:
```
DEBUG | Binding transitions for state 'Загрузка милых картинок' (type=integration)
DEBUG |   Expression [0] variable='cute_images'
DEBUG |     Bound to 1 transition(s): ['Экран с милыми картинками'] ✅
```
