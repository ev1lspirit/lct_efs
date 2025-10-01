# LCT EFS - Краткое руководство

## 🎯 Что это?

**LCT EFS** - это движок выполнения workflow на основе **конечного автомата (Finite State Machine)**. Система позволяет создавать и выполнять динамические бизнес-процессы через API без изменения кода.

---

## 🚀 Быстрый старт

### 1. Запуск сервисов
```bash
# Запуск MongoDB и Redis
docker-compose up -d

# Запуск API сервера
cd api && uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Создание workflow
```bash
curl -X POST http://localhost:8000/workflow/save \
  -H "Content-Type: application/json" \
  -d '{
    "states": {
      "states": [
        {
          "state_type": "service",
          "name": "__init__",
          "initial_state": true,
          "transitions": [{"state_id": "check_balance"}],
          "expressions": []
        },
        {
          "state_type": "technical",
          "name": "check_balance",
          "transitions": [
            {
              "state_id": "success_screen",
              "variables": ["has_funds"],
              "case": "has_funds == True"
            }
          ],
          "expressions": [
            {
              "variable": "has_funds",
              "dependent_variables": ["balance"],
              "expression": "balance > 100"
            }
          ]
        },
        {
          "state_type": "screen",
          "name": "success_screen",
          "final_state": true,
          "expressions": [{"event_name": "close"}]
        }
      ]
    },
    "predefined_context": {"balance": 500}
  }'
```

### 3. Запуск workflow
```bash
curl -X POST http://localhost:8000/client/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "client_session_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_workflow_id": "wf_12345"
  }'
```

---

## 📚 Типы состояний

### 1. **Technical State** - Вычисления
Выполняет Python выражения и обновляет контекст.

```json
{
  "state_type": "technical",
  "name": "calculate_total",
  "expressions": [
    {
      "variable": "total",
      "dependent_variables": ["price", "quantity"],
      "expression": "price * quantity"
    }
  ],
  "transitions": [{"state_id": "next_state"}]
}
```

**Возможности:**
- Математические операции: `+`, `-`, `*`, `/`
- Сравнения: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Логические операторы: `and`, `or`, `not`
- Функции: `len()`, `sum()`, `max()`, `min()`

---

### 2. **Integration State** - API вызовы
Делает HTTP запросы к внешним сервисам.

```json
{
  "state_type": "integration",
  "name": "fetch_user_data",
  "expressions": [
    {
      "variable": "user_data",
      "url": "https://api.example.com/users/{{user_id}}",
      "method": "get",
      "params": {"fields": "name,email"}
    }
  ],
  "transitions": [{"state_id": "process_data"}]
}
```

**Поддерживаемые методы:**
- `get`, `post`, `put`, `patch`, `delete`

**Особенности:**
- Может иметь только один переход
- Переход не может иметь условие (`case`)

---

### 3. **Screen State** - UI взаимодействие
Событийно-ориентированное состояние для работы с UI.

```json
{
  "state_type": "screen",
  "name": "confirmation_dialog",
  "expressions": [
    {"event_name": "confirm"},
    {"event_name": "cancel"}
  ],
  "transitions": [
    {
      "state_id": "process_action",
      "keys": ["confirm"]
    },
    {
      "state_id": "cancel_action",
      "keys": ["cancel"]
    }
  ]
}
```

**Поведение:**
1. **Первый визит**: возвращает экран клиенту, ждет события
2. **Второй визит**: обрабатывает событие, переходит к следующему состоянию

---

### 4. **Service State** - Системные состояния
Специальные состояния для инициализации и ошибок.

```json
{
  "state_type": "service",
  "name": "__init__",
  "initial_state": true,
  "expressions": [],
  "transitions": [{"state_id": "first_business_state"}]
}
```

**Стандартные состояния:**
- `__init__` - начальное состояние (загружает контекст из MongoDB)
- `__error__` - состояние ошибки

---

## 🔀 Переходы (Transitions)

### Простой переход
```json
{
  "state_id": "next_state"
}
```

### Условный переход (для Technical states)
```json
{
  "state_id": "approved_state",
  "variables": ["status"],
  "case": "status == 'approved'"
}
```

### Переход по событию (для Screen states)
```json
{
  "state_id": "confirmed_state",
  "keys": ["confirm_button"]
}
```

---

## 🧮 Выражения (Expressions)

### Композиция выражений
Можно комбинировать выражения через логические операторы:

```python
# AND - все условия должны быть true
expr = (
    Expression.technical(
        dependent_variables=["balance"], 
        expression="balance > 0"
    ) 
    & Expression.technical(
        dependent_variables=["age"], 
        expression="age >= 18"
    )
).bind_transition(name="approved")

# OR - хотя бы одно условие true
expr = (
    Expression.technical(
        dependent_variables=["is_vip"], 
        expression="is_vip == True"
    )
    | Expression.technical(
        dependent_variables=["total"], 
        expression="total > 10000"
    )
).bind_transition(name="special_offer")
```

---

## 💾 Хранилища данных

### MongoDB - Постоянное хранение
| Коллекция | Содержимое | Когда используется |
|-----------|------------|-------------------|
| `states` | Определения workflow | При сохранении/загрузке workflow |
| `workflows` | Предопределенный контекст | При инициализации workflow |

### Redis - Кэш и сессии
| Ключ | Содержимое | TTL |
|------|------------|-----|
| `session:{id}` | Данные сессии | Сессия |
| `state:{id}` | Текущее состояние | Сессия |
| `workflow_context:{id}` | Контекст workflow | Кэш |
| `screen:{id}` | Данные экрана | 1 секунда |

---

## 🔄 Жизненный цикл workflow

```
1. Client → POST /workflow/save
   └─> Сохранение workflow в MongoDB

2. Client → POST /client/workflow
   ├─> Проверка сессии в Redis
   ├─> Создание новой сессии (если нужно)
   └─> Инициализация автомата

3. Automaton
   ├─> Загрузка workflow из MongoDB
   ├─> Построение графа состояний
   └─> Итерация по состояниям:
       
       while not final_state:
           ├─> Вычисление выражений
           ├─> Проверка переходов
           ├─> Обновление контекста
           └─> Переход к следующему состоянию
           
       if screen_state and on_return:
           └─> Возврат экрана клиенту
           
4. Response → Client
   └─> Контекст и данные состояния
```

---

## 🛠️ Context Management

### Использование SessionContext
```python
from context import SessionContext

# Context manager - автосохранение
with SessionContext(session_id, workflow_id) as context:
    # Чтение
    balance = context.get("balance")
    
    # Обновление
    context["new_key"] = "value"
    context.update({"key1": "val1", "key2": "val2"})
    
# Автоматически сохраняется в Redis при выходе из блока
```

### Внутренние переменные
Используйте префикс `__` для системных переменных:

```python
{
    "__workflow_id": "wf_123",
    "__created_at": "2025-10-01T10:00:00",
    "__session_state": "active",
    # Пользовательские переменные
    "balance": 1000,
    "user_id": "user_456"
}
```

---

## 🔐 Безопасность

### Безопасное выполнение кода
Технические выражения выполняются через `simpleeval`:

```python
# ✅ Разрешено
"balance > 0"
"len(items) > 0"
"sum([1, 2, 3])"
"max(prices)"

# ❌ Запрещено
"import os"
"__import__('os')"
"exec('...')"
"eval('...')"
```

### Валидация зависимостей
Перед выполнением проверяются все `dependent_variables`:

```python
# Expression требует "balance" в контексте
{
    "variable": "has_funds",
    "dependent_variables": ["balance"],
    "expression": "balance > 100"
}

# Если "balance" отсутствует → ValueError
```

---

## 📊 Примеры использования

### Пример 1: Простой approval workflow
```json
{
  "states": {
    "states": [
      {
        "state_type": "service",
        "name": "__init__",
        "initial_state": true,
        "transitions": [{"state_id": "check_amount"}]
      },
      {
        "state_type": "technical",
        "name": "check_amount",
        "expressions": [
          {
            "variable": "needs_approval",
            "dependent_variables": ["amount"],
            "expression": "amount > 1000"
          }
        ],
        "transitions": [
          {
            "state_id": "approval_screen",
            "variables": ["needs_approval"],
            "case": "needs_approval == True"
          },
          {
            "state_id": "auto_approve"
          }
        ]
      },
      {
        "state_type": "screen",
        "name": "approval_screen",
        "expressions": [
          {"event_name": "approve"},
          {"event_name": "reject"}
        ],
        "transitions": [
          {"state_id": "approved", "keys": ["approve"]},
          {"state_id": "rejected", "keys": ["reject"]}
        ]
      },
      {
        "state_type": "technical",
        "name": "approved",
        "final_state": true,
        "expressions": [
          {
            "variable": "status",
            "expression": "'approved'"
          }
        ]
      }
    ]
  },
  "predefined_context": {"amount": 1500}
}
```

### Пример 2: Интеграция с внешним API
```json
{
  "states": {
    "states": [
      {
        "state_type": "service",
        "name": "__init__",
        "initial_state": true,
        "transitions": [{"state_id": "fetch_user"}]
      },
      {
        "state_type": "integration",
        "name": "fetch_user",
        "expressions": [
          {
            "variable": "user_info",
            "url": "https://jsonplaceholder.typicode.com/users/{{user_id}}",
            "method": "get",
            "params": {}
          }
        ],
        "transitions": [{"state_id": "display_user"}]
      },
      {
        "state_type": "screen",
        "name": "display_user",
        "final_state": true,
        "expressions": [{"event_name": "close"}]
      }
    ]
  },
  "predefined_context": {"user_id": 1}
}
```

---

## 🐛 Отладка

### Логирование
Система использует стандартный Python logging:

```python
import logging

# Установите уровень для детального лога
logging.basicConfig(level=logging.DEBUG)

# В коде проекта используется:
logger = logging.getLogger(__name__)
logger.debug("Detailed state transitions...")
logger.info("Session lifecycle events...")
logger.error("Failed operations...")
```

### Проверка состояния в Redis
```bash
# Получить данные сессии
redis-cli HGETALL "session:550e8400-e29b-41d4-a716-446655440000"

# Получить текущее состояние
redis-cli HGETALL "state:550e8400-e29b-41d4-a716-446655440000"

# Получить контекст workflow
redis-cli HGETALL "workflow_context:wf_12345"
```

### Проверка workflow в MongoDB
```javascript
// Подключение к MongoDB
use lct_efs

// Получить определение workflow
db.states.findOne({"_id": ObjectId("wf_12345")})

// Получить контекст workflow
db.workflows.findOne({"_id": ObjectId("wf_12345")})
```

---

## ⚙️ Конфигурация

### Переменные окружения (.env)
```bash
# MongoDB
MONGO_URL=mongodb://localhost:27017/lct_efs
STATES_MONGO_COLLECTION=states
WORKFLOW_MONGO_COLLECTION=workflows

# Redis
REDIS_URL=redis://localhost:6379

# FSM
SERVICE_INIT_STATE=__init__
SERVICE_ERROR_STATE=__error__
```

### config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB
    mongo_url: str
    STATES_MONGO_COLLECTION: str = "states"
    WORKFLOW_MONGO_COLLECTION: str = "workflows"
    
    # Redis
    redis_url: str
    
    # FSM
    SERVICE_INIT_STATE: str = "__init__"
    SERVICE_ERROR_STATE: str = "__error__"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🔧 Расширение системы

### Добавление нового типа состояния

1. **Создать класс состояния** (`workflow_builder/states.py`):
```python
class CustomState(WorkflowState):
    type_ = StateTypeEnum.custom
```

2. **Создать expression модель** (`workflow_builder/expressions.py`):
```python
@define
class CustomStateExpression(BaseExpression):
    variable: str
    custom_param: str
    
    def bindable(self) -> bool:
        return True
```

3. **Создать handler** (`workflow_builder/handlers.py`):
```python
@define(slots=True)
class CustomHandler(BaseHandler):
    metadata: CustomStateExpression
    context: SessionContext
    
    def result(self):
        # Custom logic here
        return custom_result
```

4. **Создать handler creator** (`workflow_builder/builders/custom.py`):
```python
class WorkflowCustomHandlersCreator(BaseHandlersCreator[CustomHandler]):
    def __call__(self) -> list[CustomHandler]:
        return [
            CustomHandler(metadata=expr, context=self.context)
            for expr in self.handlers
        ]
```

5. **Зарегистрировать в mapping** (`workflow_builder/models.py`):
```python
state_mapping: dict[StateTypeEnum, Type[BaseHandlersCreator]] = {
    # ...
    StateTypeEnum.custom: WorkflowCustomHandlersCreator,
}
```

---

## 📈 Best Practices

### ✅ Хорошие практики

1. **Именование состояний**: используйте понятные имена
   ```json
   "name": "validate_user_credentials"  // ✅
   "name": "state1"                     // ❌
   ```

2. **Управление контекстом**: минимизируйте объем данных
   ```json
   // ✅ Храните только необходимое
   {"user_id": 123, "role": "admin"}
   
   // ❌ Не храните большие объекты
   {"full_user_object": {...1000 полей...}}
   ```

3. **Обработка ошибок**: всегда предусматривайте переход на ошибку
   ```json
   {
     "transitions": [
       {"state_id": "success", "case": "error == None"},
       {"state_id": "__error__"}
     ]
   }
   ```

4. **Использование final_state**: явно помечайте конечные состояния
   ```json
   {
     "state_type": "screen",
     "name": "completion_screen",
     "final_state": true
   }
   ```

### ❌ Антипаттерны

1. **Циклические переходы без выхода**
   ```json
   // ❌ Бесконечный цикл
   {
     "name": "state_a",
     "transitions": [{"state_id": "state_b"}]
   },
   {
     "name": "state_b",
     "transitions": [{"state_id": "state_a"}]
   }
   ```

2. **Integration state с условным переходом**
   ```json
   // ❌ Запрещено
   {
     "state_type": "integration",
     "transitions": [
       {"state_id": "next", "case": "result == 'ok'"}
     ]
   }
   ```

3. **Отсутствие dependent_variables**
   ```json
   // ❌ Переменная используется, но не указана
   {
     "expression": "balance > 0",
     "dependent_variables": []  // Должно быть ["balance"]
   }
   ```

---

## 📚 Дополнительные материалы

- **Архитектура**: `/diagrams/architecture_overview.md`
- **Диаграммы последовательности**: `/diagrams/sequence_diagrams.md`
- **Диаграммы классов**: `/diagrams/class_diagrams.md`
- **Контракт данных**: `/diagrams/contract.json`

---

## 🆘 Частые проблемы

### Проблема: "No matching transition found"
**Причина**: Нет перехода, соответствующего результатам выражений

**Решение**: 
- Добавьте переход по умолчанию (без `case`)
- Проверьте логику условий в `case`

### Проблема: "Missing dependent variables"
**Причина**: Переменные отсутствуют в контексте

**Решение**:
- Убедитесь, что переменные были установлены в предыдущих состояниях
- Проверьте `predefined_context` при сохранении workflow

### Проблема: Session не найдена
**Причина**: Сессия истекла или не была создана

**Решение**:
- Передайте `client_workflow_id` при первом запросе
- Проверьте TTL в Redis

---

## 🎓 Заключение

LCT EFS предоставляет мощный и гибкий способ создания динамических workflow через:

- ✅ **Декларативный подход**: workflow описывается через JSON
- ✅ **Безопасное выполнение**: изолированное выполнение кода
- ✅ **Персистентность**: автоматическое сохранение состояния
- ✅ **Расширяемость**: легко добавлять новые типы состояний
- ✅ **Событийная модель**: поддержка UI-взаимодействия

Начните с простых workflow и постепенно усложняйте логику! 🚀
