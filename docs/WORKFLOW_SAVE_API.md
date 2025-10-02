# Документация API эндпоинта /workflow/save

## Описание
Эндпоинт для сохранения описания workflow (конечного автомата) в MongoDB.

**URL:** `POST /workflow/save`

**Content-Type:** `application/json`

---

## Структура запроса

### Основной объект `SaveWorkflowRequest`

```json
{
  "states": StateSet,           // Набор состояний workflow (обязательно)
  "predefined_context": {}      // Предопределенный контекст (опционально)
}
```

### Объект `StateSet`

```json
{
  "states": [StateModel, ...]   // Массив состояний
}
```

**Правила валидации:**
- ✅ Должен быть **ровно один** state с `initial_state: true`
- ✅ Должен быть **хотя бы один** state с `final_state: true`
- ✅ Массив states не должен быть пустым

---

## Объект `StateModel`

### Общая структура

```json
{
  "state_type": "technical" | "integration" | "screen" | "service",
  "name": "string",                    // Уникальное имя состояния
  "screen": {},                        // Опционально, для state_type="screen"
  "transitions": [TransitionModel],    // Переходы в другие состояния
  "expressions": [Expression],         // Выражения для обработки данных
  "initial_state": false,              // true только для начального состояния
  "events": [EventModel],              // События, которые может генерировать состояние
  "final_state": false                 // true для финальных состояний
}
```

---

## Типы состояний (state_type)

### 1. **service** - Служебное состояние
Используется для инициализации и обработки ошибок системы.

```json
{
  "state_type": "service",
  "name": "__service_init",
  "screen": {},
  "transitions": [
    {
      "case": null,
      "state_id": "next_state",
      "variable": null
    }
  ],
  "expressions": [],
  "initial_state": true,
  "events": [],
  "final_state": false
}
```

**Специальные имена:**
- `__service_init` - начальное состояние системы
- `__service_error` - состояние ошибки системы

---

### 2. **screen** - Экран с UI
Представляет пользовательский интерфейс.

```json
{
  "state_type": "screen",
  "name": "login_screen",
  "screen": {
    "title": "Вход в систему",
    "description": "Введите учетные данные",
    "fields": [
      {
        "name": "username",
        "type": "text",
        "label": "Логин",
        "required": true,
        "placeholder": "Введите логин"
      }
    ],
    "buttons": [
      {
        "label": "Войти",
        "action": "submit",
        "event": "login_submit"
      }
    ]
  },
  "transitions": [
    {
      "case": null,
      "state_id": "validation_state",
      "variable": null
    }
  ],
  "expressions": [],
  "initial_state": false,
  "events": [
    {
      "event_name": "login_submit"
    }
  ],
  "final_state": false
}
```

**Структура screen:**
- `title` - заголовок экрана
- `description` - описание
- `fields` - поля формы
- `buttons` - кнопки действий

---

### 3. **technical** - Техническая обработка
Выполняет вычисления и проверки на основе данных контекста.

```json
{
  "state_type": "technical",
  "name": "validate_input",
  "screen": {},
  "transitions": [
    {
      "case": "is_valid == True",
      "state_id": "success_state",
      "variable": "is_valid"
    },
    {
      "case": "is_valid == False",
      "state_id": "error_state",
      "variable": "is_valid"
    }
  ],
  "expressions": [
    {
      "variable": "is_valid",
      "dependent_variables": ["username", "password"],
      "expression": "len(username) > 3 and len(password) >= 6"
    }
  ],
  "initial_state": false,
  "events": [],
  "final_state": false
}
```

**TechnicalExpressionModel:**
- `variable` - имя переменной для сохранения результата
- `dependent_variables` - список переменных из контекста
- `expression` - Python выражение (lambda-подобное)

---

### 4. **integration** - Интеграция с внешними API
Выполняет HTTP запросы к внешним сервисам.

```json
{
  "state_type": "integration",
  "name": "call_api",
  "screen": {},
  "transitions": [
    {
      "case": "response.status == 200",
      "state_id": "success_state",
      "variable": "response"
    },
    {
      "case": "response.status != 200",
      "state_id": "error_state",
      "variable": "response"
    }
  ],
  "expressions": [
    {
      "variable": "response",
      "url": "https://api.example.com/endpoint",
      "params": {
        "user_id": "{{user_id}}",
        "action": "login"
      },
      "method": "post"
    }
  ],
  "initial_state": false,
  "events": [],
  "final_state": false
}
```

**IntegrationExpressionModel:**
- `variable` - имя переменной для сохранения ответа
- `url` - URL эндпоинта
- `params` - параметры запроса (поддерживает шаблоны `{{variable}}`)
- `method` - HTTP метод: `"get"`, `"post"`, `"put"`, `"delete"`, `"patch"`

---

## Объект `TransitionModel`

Описывает переход между состояниями.

```json
{
  "case": "username != ''",      // Условие перехода (Python выражение) или null
  "state_id": "next_state",      // Имя целевого состояния
  "variable": "username"         // Переменная для проверки условия (или null)
}
```

**Правила:**
- Если `case` = `null`, переход происходит безусловно
- Если `case` задано, выполняется проверка условия
- `variable` указывает на переменную в контексте для evaluation

---

## Объект `EventModel`

```json
{
  "event_name": "button_click"   // Имя события
}
```

События используются для реакции на пользовательские действия.

---

## Объект `predefined_context`

Предопределенные переменные контекста workflow.

```json
{
  "user_id": "12345",
  "app_version": "1.0.0",
  "locale": "ru",
  "theme": "dark",
  "max_retries": 3
}
```

Может содержать любые пары ключ-значение (строки, числа, массивы, объекты).

---

## Примеры запросов

### Минимальный пример

```json
{
  "states": {
    "states": [
      {
        "state_type": "service",
        "name": "__service_init",
        "screen": {},
        "transitions": [{"case": null, "state_id": "welcome", "variable": null}],
        "expressions": [],
        "initial_state": true,
        "events": [],
        "final_state": false
      },
      {
        "state_type": "screen",
        "name": "welcome",
        "screen": {"title": "Добро пожаловать"},
        "transitions": [],
        "expressions": [],
        "initial_state": false,
        "events": [],
        "final_state": true
      }
    ]
  },
  "predefined_context": {}
}
```

### Полный пример
См. файл `workflow_save_example.json`

---

## Ответ сервера

### Успешный ответ (200 OK)

```json
{
  "status": "success",
  "wf_description_id": "68dd1234567890abcdef1234",
  "wf_context_id": "68dd1234567890abcdef1234",
  "screens_saved": 2
}
```

**Поля:**
- `status` - статус операции
- `wf_description_id` - MongoDB ObjectId сохраненного workflow
- `wf_context_id` - MongoDB ObjectId сохраненного контекста
- `screens_saved` - количество сохраненных экранов

### Ошибка валидации (422 Unprocessable Entity)

```json
{
  "detail": [
    {
      "loc": ["body", "states", "states"],
      "msg": "There must be exactly one state with 'initial_state' set to True.",
      "type": "value_error"
    }
  ]
}
```

### Ошибка сервера (500 Internal Server Error)

```json
{
  "detail": "Database error while saving workflow states: ..."
}
```

---

## Тестирование

### cURL

```bash
curl -X POST http://127.0.0.1:8080/workflow/save \
  -H "Content-Type: application/json" \
  -d @docs/workflow_save_minimal.json
```

### Python

```python
import requests

with open('docs/workflow_save_minimal.json', 'r') as f:
    data = json.load(f)

response = requests.post(
    'http://127.0.0.1:8080/workflow/save',
    json=data
)
print(response.json())
```

### Swagger UI

Откройте http://127.0.0.1:8080/docs и найдите эндпоинт `/workflow/save` для интерактивного тестирования.

---

## Коллекции MongoDB

После сохранения создаются записи в следующих коллекциях:

1. **states** - описание состояний workflow
   ```json
   {
     "_id": ObjectId("..."),
     "states": [...]
   }
   ```

2. **workflow_context** - предопределенный контекст
   ```json
   {
     "_id": ObjectId("..."),
     "user_id": "12345",
     "app_version": "1.0.0"
   }
   ```

3. **screens** - данные экранов (если есть screen states)
   ```json
   {
     "_id": ObjectId("..."),
     "workflow_id": "...",
     "state_name": "login_screen",
     "screen": {...}
   }
   ```

---

## Лучшие практики

1. ✅ **Всегда начинайте с `__service_init`**
   ```json
   {
     "state_type": "service",
     "name": "__service_init",
     "initial_state": true
   }
   ```

2. ✅ **Всегда добавляйте `__service_error`**
   ```json
   {
     "state_type": "service",
     "name": "__service_error",
     "final_state": true
   }
   ```

3. ✅ **Используйте осмысленные имена состояний**
   - ❌ `state1`, `state2`
   - ✅ `login_screen`, `validate_input`, `call_auth_api`

4. ✅ **Проверяйте условия переходов**
   - Убедитесь, что все возможные значения переменных покрыты
   - Добавляйте fallback переходы

5. ✅ **Структурируйте контекст**
   ```json
   {
     "predefined_context": {
       "app": {
         "name": "MyApp",
         "version": "1.0.0"
       },
       "user": {
         "role": "admin"
       }
     }
   }
   ```

---

## Диаграмма workflow

```
[__service_init] 
      ↓
[login_screen] 
      ↓
[validate_credentials]
      ↓              ↓
[call_auth_api]  [error_screen]
      ↓              ↓
[success_screen] → END
```

---

## См. также

- `docs/workflow_save_example.json` - Полный пример с авторизацией
- `docs/workflow_save_minimal.json` - Минимальный рабочий пример
- `docs/MONGODB_FIXES.md` - Документация по MongoDB
- Swagger UI: http://127.0.0.1:8080/docs
