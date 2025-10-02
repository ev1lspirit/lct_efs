# Шпаргалка: JSON для /workflow/save

## 📋 Быстрый старт

### Минимальный рабочий пример
```bash
curl -X POST http://127.0.0.1:8080/workflow/save \
  -H "Content-Type: application/json" \
  -d @docs/workflow_save_minimal.json
```

---

## 🏗️ Структура запроса

```json
{
  "states": {
    "states": [
      /* массив StateModel */
    ]
  },
  "predefined_context": {
    /* любые пары ключ-значение */
  }
}
```

---

## 🎯 Типы состояний (state_type)

### 1️⃣ service - Служебное
```json
{
  "state_type": "service",
  "name": "__service_init",
  "transitions": [{"case": null, "state_id": "next", "variable": null}],
  "initial_state": true
}
```

### 2️⃣ screen - Экран UI
```json
{
  "state_type": "screen",
  "name": "login_screen",
  "screen": {
    "title": "Вход",
    "fields": [{"name": "username", "type": "text"}]
  },
  "events": [{"event_name": "submit"}]
}
```

### 3️⃣ technical - Вычисления
```json
{
  "state_type": "technical",
  "name": "validate",
  "expressions": [{
    "variable": "is_valid",
    "dependent_variables": ["username"],
    "expression": "len(username) > 3"
  }],
  "transitions": [
    {"case": "is_valid == True", "state_id": "success", "variable": "is_valid"}
  ]
}
```

### 4️⃣ integration - API вызов
```json
{
  "state_type": "integration",
  "name": "call_api",
  "expressions": [{
    "variable": "response",
    "url": "https://api.example.com/login",
    "params": {"user": "{{username}}"},
    "method": "post"
  }],
  "transitions": [
    {"case": "response.status == 200", "state_id": "success", "variable": "response"}
  ]
}
```

---

## ✅ Обязательные правила

1. **Ровно 1** состояние с `"initial_state": true`
2. **Минимум 1** состояние с `"final_state": true`
3. Все `state_id` в transitions должны существовать

---

## 📦 Готовые примеры

| Файл | Описание |
|------|----------|
| `workflow_save_minimal.json` | Минимальный (2 состояния) |
| `workflow_save_example.json` | Полный пример с авторизацией |

---

## 🔧 Тестирование

### Swagger UI
http://127.0.0.1:8080/docs

### Python
```python
import requests, json

with open('docs/workflow_save_minimal.json') as f:
    response = requests.post(
        'http://127.0.0.1:8080/workflow/save',
        json=json.load(f)
    )
print(response.json())
```

---

## 📤 Ответ сервера

### Успех
```json
{
  "status": "success",
  "wf_description_id": "68dd...",
  "wf_context_id": "68dd...",
  "screens_saved": 2
}
```

### Ошибка
```json
{
  "detail": "There must be exactly one state with 'initial_state' set to True."
}
```

---

## 💡 Шаблон workflow

```json
{
  "states": {
    "states": [
      {
        "state_type": "service",
        "name": "__service_init",
        "screen": {},
        "transitions": [{"case": null, "state_id": "FIRST_STATE", "variable": null}],
        "expressions": [],
        "initial_state": true,
        "events": [],
        "final_state": false
      },
      
      /* ВАШ КОД ЗДЕСЬ */
      
      {
        "state_type": "service",
        "name": "__service_error",
        "screen": {},
        "transitions": [],
        "expressions": [],
        "initial_state": false,
        "events": [],
        "final_state": true
      }
    ]
  },
  "predefined_context": {
    /* ваши переменные */
  }
}
```

---

📚 **Полная документация:** `docs/WORKFLOW_SAVE_API.md`
