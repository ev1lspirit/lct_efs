# 🧪 Тестирование Integration States с интерполяцией

## 🎯 Что тестируется

✅ Интерполяция переменных `{{variable}}` → реальные значения из контекста  
✅ Валидация `dependent_variables` перед выполнением запроса  
✅ Обработка ошибок API через `error_variable`  
✅ Работа с реальным API (jsonplaceholder.typicode.com)  
✅ POST/GET запросы с вложенными структурами  

---

## 🚀 Быстрый старт

### 1. Запустите сервер (если еще не запущен)

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8080 --reload
```

### 2. Запустите автоматический тест

```bash
python run_integration_test.py
```

### 3. Проверьте результат

Тест автоматически:
- ✅ Сохранит тестовый workflow в MongoDB
- ✅ Запустит 2 сценария (успешный + валидация)
- ✅ Проверит интерполяцию переменных
- ✅ Выведет результаты

---

## 📋 Ручное тестирование

### Шаг 1: Получить JSON workflow

```bash
python api/test_integration_workflow.py
```

Скопируйте выведенный JSON.

### Шаг 2: Сохранить workflow

```bash
POST http://localhost:8080/workflow/save
Content-Type: application/json

{
    "states": <скопированный JSON>,
    "predefined_context": {}
}
```

**Ответ:** `{"wf_description_id": "abc123..."}`

### Шаг 3: Запустить workflow

```bash
POST http://localhost:8080/client/workflow
Content-Type: application/json

{
    "client_session_id": "test-session-001",
    "client_workflow_id": "abc123...",
    "context": {
        "user_id": "1",
        "api_key": "test-key-123"
    }
}
```

**Ответ:** `{"state": "UserInputScreen", "screen": {...}}`

### Шаг 4: Отправить событие

```bash
POST http://localhost:8080/client/event
Content-Type: application/json

{
    "client_session_id": "test-session-001",
    "event_name": "search",
    "context": {}
}
```

Workflow автоматически выполнит:
1. `ValidateInput` - проверка user_id и api_key
2. `FetchUserProfile` - GET запрос с интерполяцией `{{user_id}}`
3. `FetchUserOrders` - GET запрос с params `{"userId": "{{user_id}}"}`
4. `CreateOrderSummary` - POST запрос с интерполяцией в title
5. `DisplayResults` - показ результатов

---

## 🔍 Проверка интерполяции в логах

После запуска смотрите логи сервера:

```log
INFO: Integration request: GET https://jsonplaceholder.typicode.com/users/1
DEBUG: Original params: {}
DEBUG: Interpolated params: {}

INFO: Integration request: GET https://jsonplaceholder.typicode.com/posts
DEBUG: Original params: {'userId': '{{user_id}}', '_limit': '5'}
DEBUG: Interpolated params: {'userId': '1', '_limit': '5'}

INFO: Integration request: POST https://jsonplaceholder.typicode.com/posts
DEBUG: Original params: {'title': 'Order Summary for User {{user_id}}', ...}
DEBUG: Interpolated params: {'title': 'Order Summary for User 1', ...}
```

✅ **Если видите `Interpolated params` с реальными значениями - интерполяция работает!**

---

## 📊 Структура тестового workflow

```
UserInputScreen (начало)
    ↓ event: "search"
ValidateInput (технический state)
    ↓ валидация user_id и api_key
FetchUserProfile (Integration State)
    • GET https://jsonplaceholder.typicode.com/users/{{user_id}}
    • dependent_variables: ["user_id"]
    • error_variable: "profile_error"
    ↓
FetchUserOrders (Integration State)
    • GET https://jsonplaceholder.typicode.com/posts
    • params: {"userId": "{{user_id}}", "_limit": "5"}
    • dependent_variables: ["user_id"]
    ↓
ProcessOrdersData (технический state)
    • Проверка len(orders) > 0
    ↓
CreateOrderSummary (Integration State)
    • POST https://jsonplaceholder.typicode.com/posts
    • params: {"title": "Order Summary for User {{user_id}}", ...}
    • dependent_variables: ["user_id"]
    ↓
DisplayResults
    ↓ event: "exit"
ExitFlow (финал)
```

---

## 🧪 Тестовые сценарии

### Сценарий 1: Успешный путь ✅

**Контекст:**
```json
{
    "user_id": "1",
    "api_key": "test-key"
}
```

**События:**
1. `search` → выполняются все Integration States
2. `exit` → завершение

**Ожидаемый результат:**
- Все Integration States выполнены
- В контексте появились: `user_profile`, `orders`, `summary`
- Финальный state: `ExitFlow`

### Сценарий 2: Ошибка валидации ❌

**Контекст:**
```json
{
    "user_id": "",  // Пустой!
    "api_key": "test-key"
}
```

**События:**
1. `search` → ошибка валидации
2. Переход в `ValidationErrorScreen`
3. `retry` с исправленным user_id
4. `search` → успешно

**Ожидаемый результат:**
- Валидация отклоняет пустой user_id
- После исправления workflow проходит успешно

### Сценарий 3: Ошибка API 🔴

**Контекст:**
```json
{
    "user_id": "99999",  // Несуществующий
    "api_key": "test-key"
}
```

**Ожидаемый результат:**
- API возвращает ошибку
- Ошибка сохраняется в `context["profile_error"]`
- Переход в `ProfileErrorScreen`
- Возможность retry или возврата назад

---

## 📁 Файлы

| Файл | Описание |
|------|----------|
| `api/test_integration_workflow.py` | Тестовые workflows и сценарии |
| `run_integration_test.py` | Автоматический запуск тестов |
| `workflow_builder/handlers.py` | Реализация IntegrationHandler с интерполяцией |
| `workflow_builder/expressions.py` | Модели IntegrationStateExpression |
| `tests/test_integration_interpolation.py` | 16 unit тестов |
| `docs/INTEGRATION_STATES_FIXES.md` | Полная документация (500+ строк) |
| `docs/INTEGRATION_STATES_SUMMARY.md` | Краткий summary |

---

## ✅ Чек-лист проверки

После запуска теста проверьте:

- [ ] Автоматический тест показал "ВСЕ ТЕСТЫ ПРОЙДЕНЫ"
- [ ] В логах есть `DEBUG: Interpolated params: ...`
- [ ] Интерполяция заменила `{{user_id}}` на `"1"`
- [ ] API запросы выполнились успешно
- [ ] В контексте появились переменные: `user_profile`, `orders`, `summary`
- [ ] Валидация отклонила пустой `user_id`
- [ ] Error handling сработал (если протестировали)

---

## 🐛 Troubleshooting

**Проблема:** Сервер недоступен

**Решение:**
```bash
uvicorn api.app:app --host 127.0.0.1 --port 8080
```

---

**Проблема:** Ошибка "Variable not found in context"

**Решение:** Убедитесь, что переменная передана в начальном контексте:
```json
{
    "context": {
        "user_id": "1",  // ← Обязательно!
        "api_key": "test-key"
    }
}
```

---

**Проблема:** API не отвечает

**Решение:** Проверьте доступность jsonplaceholder.typicode.com:
```bash
curl https://jsonplaceholder.typicode.com/users/1
```

---

**Проблема:** Интерполяция не работает

**Решение:**
1. Проверьте, что используете обновленную версию кода
2. Смотрите логи: должны быть `DEBUG: Interpolated params`
3. Убедитесь, что переменные есть в контексте

---

## 📞 Поддержка

**Документация:**
- `docs/INTEGRATION_STATES_FIXES.md` - полное руководство
- `docs/INTEGRATION_STATES_SUMMARY.md` - краткий summary

**Тесты:**
- `tests/test_integration_interpolation.py` - 16 unit тестов
- `run_integration_test.py` - автоматический интеграционный тест

---

## 🎉 Готово!

Integration States с интерполяцией полностью функциональны и протестированы! 🚀

**Дата:** 2 октября 2025  
**Версия:** 1.0
