# LCT EFS - Архитектура и принципы работы

## 📋 Обзор проекта

**LCT EFS** (Execution Finite State) - это движок выполнения бизнес-процессов на основе **конечного автомата (FSM)**, который управляет динамическими, настраиваемыми workflow. Система управляет переходами между состояниями через технические выражения, внешние интеграции и UI-взаимодействия с персистентностью состояния в Redis и MongoDB.

---

## 🏗️ Высокоуровневая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                      │
│  ┌──────────────────┐         ┌───────────────────────────┐    │
│  │ POST /workflow/   │         │ POST /client/workflow     │    │
│  │      save         │         │  (session management)     │    │
│  └──────────────────┘         └───────────────────────────┘    │
└────────────────────┬────────────────────────┬────────────────────┘
                     │                        │
                     ▼                        ▼
        ┌────────────────────┐    ┌─────────────────────────┐
        │   MongoDB          │    │    Redis Cache          │
        │ ┌────────────────┐ │    │ ┌─────────────────────┐ │
        │ │ States         │ │    │ │ session:{id}        │ │
        │ │ Collection     │ │    │ │ state:{id}          │ │
        │ └────────────────┘ │    │ │ workflow_context:{} │ │
        │ ┌────────────────┐ │    │ │ screen:{id}         │ │
        │ │ Workflow       │ │    │ └─────────────────────┘ │
        │ │ Context Coll.  │ │    └─────────────────────────┘
        │ └────────────────┘ │
        └────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────────────┐
        │        Workflow Builder (FSM Engine)        │
        │  ┌─────────────────────────────────────┐   │
        │  │         Automaton (FSM)              │   │
        │  │  - State iteration                   │   │
        │  │  - Expression evaluation             │   │
        │  │  - Transition logic                  │   │
        │  └─────────────────────────────────────┘   │
        │                                             │
        │  ┌──────────────┐  ┌──────────────────┐   │
        │  │   States     │  │    Handlers      │   │
        │  │ - Technical  │  │ - Technical      │   │
        │  │ - Integration│  │ - Integration    │   │
        │  │ - Screen     │  │ - Screen         │   │
        │  │ - Service    │  │ - Dependency     │   │
        │  └──────────────┘  └──────────────────┘   │
        └─────────────────────────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────────────┐
        │          External Integrations              │
        │  - HTTP API calls via CommonAdapter         │
        │  - simpleeval для безопасного eval          │
        └─────────────────────────────────────────────┘
```

---

## 🔄 Основные компоненты

### 1. **API Layer** (`api/`)
- **FastAPI** приложение с двумя основными endpoint'ами
- Управление сессиями и workflow

#### Эндпоинты:

**POST `/workflow/save`**
```python
{
    "states": {
        "states": [
            {
                "state_type": "technical|integration|screen|service",
                "name": "state_name",
                "transitions": [...],
                "expressions": [...],
                "initial_state": true/false,
                "final_state": true/false
            }
        ]
    },
    "predefined_context": {"key": "value"}
}
```
- Сохраняет определения workflow в MongoDB
- Создает две коллекции: определения состояний и предопределенный контекст

**POST `/client/workflow`**
```python
{
    "client_session_id": "uuid",
    "client_workflow_id": "workflow_id",
    "event_name": "optional_event"
}
```
- Проверяет существование сессии в Redis
- Создает новую сессию если не найдена
- Инициализирует автомат и запускает workflow

---

### 2. **Workflow Builder** (`workflow_builder/`)

#### Automaton (FSM Engine)
Ядро системы - конечный автомат, который:
- Строит граф состояний из MongoDB
- Итерирует по состояниям через `__next__()`
- Вычисляет выражения и проверяет переходы
- Обновляет контекст сессии

**Lifecycle:**
```python
1. Parse workflow definition from MongoDB (GlobalStateParser)
2. Build automaton subgraph from SERVICE_INIT_STATE
3. Iterate states:
   - Evaluate expressions
   - Check transitions
   - Update context
4. Stop at Screen state or completion
5. Persist state to Redis via SessionContext
```

#### States (Состояния)
Четыре типа состояний:

**Technical State** - Вычисляет Python выражения
```python
expr = Expression.technical(
    dependent_variables=["balance"],
    expression="balance > 0"
)
```

**Integration State** - HTTP вызовы к внешним API
```python
expr = Expression.integration(
    variable="api_result",
    url="https://api.example.com/endpoint",
    method="get",
    params={"key": "value"}
)
```

**Screen State** - UI взаимодействие, событийно-ориентированное
```python
expr = Expression.screen(
    event_name="button_click"
)
```

**Service State** - Системные состояния (`__init__`, `__error__`)
- Ленивая загрузка контекста из MongoDB→Redis

---

### 3. **Context Management** (`context.py`)

**SessionContext** - Thread-safe обертка контекста с Redis бэкендом:

```python
# Context manager pattern
with SessionContext(session_id, workflow_id) as context:
    context.update({"key": "value"})  
    # Auto-saves on __exit__
```

**Функции:**
- `_get_session_context()` - загрузка из Redis
- `update_session()` - сохранение контекста
- `update_session_state()` - сохранение метаданных состояния
- `get_session_state()` - получение текущего состояния

---

### 4. **Handlers** (`workflow_builder/handlers.py`)

Каждый тип состояния имеет свой handler:

**TechnicalHandler**
- Использует `simpleeval.simple_eval()` для безопасного выполнения
- Допустимые функции: `len`, `sum`, `max`, `min`
- Доступ к переменным через `context.session`

**IntegrationHandler**
- HTTP вызовы через `CommonAdapter`
- Парсинг URL на base_url и endpoint
- Поддержка всех HTTP методов

**ScreenHandler**
- Проверка соответствия событий
- Возвращает `bool` при совпадении `event_name`

**DependencyHandler**
- Ленивая загрузка workflow контекста
- MongoDB → Redis при первом обращении
- Merge с session context

---

### 5. **Storage Layer**

#### Redis (`storage/redis/service.py`)
**Singleton pattern** - одно соединение на приложение

**Ключи:**
- `session:{id}` - данные сессии
- `state:{id}` - метаданные состояния
- `workflow_context:{id}` - контекст workflow
- `screen:{id}` - кэш экранов

**Операции:**
- `create_session()` - создание новой сессии
- `get_session()` / `update_session()` - CRUD сессий
- `save_state()` / `get_state()` - управление состоянием
- `set_workflow_context()` - кэширование контекста

#### MongoDB (`storage/mongo/client.py`)
**Коллекции:**
- `states` (из settings.STATES_MONGO_COLLECTION) - определения workflow
- `workflows` (из settings.WORKFLOW_MONGO_COLLECTION) - контексты workflow

---

## 🔀 Expression System

### Композиция выражений
Поддержка логических операторов:

```python
expr = (
    Expression.technical(
        dependent_variables=["balance"], 
        expression="balance>0"
    )
    & Expression.technical(
        dependent_variables=["x"], 
        expression="x>0"
    )
).bind_transition(name="next_id")
```

**Операторы:**
- `&` (AND) - все выражения должны быть true
- `|` (OR) - хотя бы одно выражение true

### Transitions (Переходы)
Переходы связывают выражения с целевыми состояниями:

```python
transition = Transition(
    state_id="target_state",
    case="balance > 100",  # опциональное условие
    variables={"balance"},
    keys={"event_name"}
)
```

**Валидация:**
- Integration states могут иметь только один переход
- Integration transitions не могут иметь условие (case)
- Все dependent_variables должны быть в контексте

---

## 🔄 Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Client Request: POST /client/workflow                    │
│    - client_session_id                                      │
│    - client_workflow_id                                     │
│    - event_name (optional)                                  │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Session Check (Redis)                                    │
│    - Exists? → Load context                                 │
│    - New? → Create session with workflow_id                 │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Automaton Initialization                                 │
│    - Load workflow from MongoDB (GlobalStateParser)         │
│    - Build state graph from SERVICE_INIT_STATE              │
│    - Resolve initial state from session                     │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. State Iteration (while not final)                        │
│                                                             │
│    ┌─────────────────────────────────────┐                │
│    │ Is Screen State?                    │                │
│    └──────┬──────────────────┬───────────┘                │
│           │ YES              │ NO                          │
│           ▼                  ▼                             │
│    ┌─────────────┐    ┌──────────────────┐               │
│    │ If on_return│    │ Evaluate handlers │               │
│    │ → Return    │    │ - Technical: eval │               │
│    │             │    │ - Integration: HTTP│               │
│    │ Match event │    │ - Service: init   │               │
│    │ → Transition│    │                   │               │
│    └─────────────┘    └──────────────────┘               │
│           │                  │                             │
│           └──────┬───────────┘                             │
│                  ▼                                         │
│    ┌─────────────────────────────────────┐               │
│    │ Find matching transition:           │               │
│    │ - Check expression results          │               │
│    │ - Evaluate transition.case          │               │
│    │ - Get next state                    │               │
│    └─────────────────────────────────────┘               │
│                  │                                         │
│                  ▼                                         │
│    ┌─────────────────────────────────────┐               │
│    │ Update current_state                │               │
│    │ Save state metadata to Redis        │               │
│    └─────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Response                                                 │
│    - Screen state → Return screen data                      │
│    - Final state → Complete workflow                        │
│    - Context updated in Redis                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Паттерны и конвенции

### State Type Mapping (Registry Pattern)
```python
# workflow_builder/models.py
state_mapping: dict[StateTypeEnum, Type[BaseHandlersCreator]] = {
    StateTypeEnum.technical: WorkflowTechnicalHandlersCreator,
    StateTypeEnum.integration: WorkflowIntegrationHandlersCreator,
    StateTypeEnum.screen: WorkflowScreenHandlersCreator,
    StateTypeEnum.service: WorkflowDependencyHandlersCreator,
}
```

### Error Handling
- Декоратор `@execute_safe()` для внешних вызовов
- Логирование перед raise
- Явная валидация переходов

### Type Safety
- `attrs @define` для data classes
- `TYPE_CHECKING` для избежания циклических импортов
- Generic параметры для handler creators

---

## 🔧 Конфигурация

### Environment Variables
```bash
# MongoDB - Workflow definitions and contexts
MONGO_URL=<mongodb_connection_string>
STATES_MONGO_COLLECTION=states
WORKFLOW_MONGO_COLLECTION=workflows

# Redis - Session and state cache
REDIS_URL=redis://localhost:6379

# FSM Configuration
SERVICE_INIT_STATE=__init__
SERVICE_ERROR_STATE=__error__
```

---

## 📊 Пример workflow

### 1. Сохранение workflow
```python
POST /workflow/save
{
    "states": {
        "states": [
            {
                "state_type": "service",
                "name": "__init__",
                "initial_state": true,
                "final_state": false,
                "transitions": [{"state_id": "check_balance"}],
                "expressions": []
            },
            {
                "state_type": "technical",
                "name": "check_balance",
                "transitions": [
                    {
                        "state_id": "api_call",
                        "variables": ["has_balance"],
                        "case": "has_balance == True"
                    },
                    {
                        "state_id": "error_screen"
                    }
                ],
                "expressions": [
                    {
                        "variable": "has_balance",
                        "dependent_variables": ["balance"],
                        "expression": "balance > 0"
                    }
                ]
            },
            {
                "state_type": "integration",
                "name": "api_call",
                "transitions": [{"state_id": "show_result"}],
                "expressions": [
                    {
                        "variable": "api_result",
                        "url": "https://api.example.com/data",
                        "method": "get",
                        "params": {"user_id": "{{user_id}}"}
                    }
                ]
            },
            {
                "state_type": "screen",
                "name": "show_result",
                "final_state": true,
                "expressions": [
                    {"event_name": "close_screen"}
                ]
            }
        ]
    },
    "predefined_context": {
        "balance": 1000,
        "user_id": "12345"
    }
}
```

### 2. Запуск workflow
```python
POST /client/workflow
{
    "client_session_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_workflow_id": "wf_12345",
    "event_name": null
}
```

### 3. Execution Flow
```
__init__ (Service) 
  → Load predefined context: {balance: 1000, user_id: "12345"}
  → Transition to "check_balance"

check_balance (Technical)
  → Evaluate: balance > 0 → has_balance = True
  → Transition case: has_balance == True → "api_call"

api_call (Integration)
  → HTTP GET https://api.example.com/data?user_id=12345
  → api_result = response
  → Transition to "show_result"

show_result (Screen)
  → Return screen state to client
  → Wait for event "close_screen"
```

---

## 🔑 Ключевые особенности

### ✅ Динамическая конфигурация
- Workflow определяется через JSON/API
- Без изменения кода приложения

### ✅ Персистентность состояния
- Redis для быстрого доступа к сессиям
- MongoDB для долгосрочного хранения

### ✅ Безопасное выполнение кода
- `simpleeval` для технических выражений
- Ограниченный набор функций
- Контекстная изоляция

### ✅ Событийно-ориентированная модель
- Screen states с event matching
- UI-driven transitions

### ✅ Расширяемость
- Registry pattern для новых типов состояний
- Handler creators для кастомной логики
- Validators для бизнес-правил

---

## 🚀 Запуск

```bash
# Start services
docker-compose up -d

# Run API server
cd api && uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

---

## 📝 Важные замечания

- **Singleton Pattern**: `RedisCache` использует `GeneralPurposeSingletonMeta`
- **Context Variables**: Префикс `__` для внутренних ключей (`__workflow_id`, `__created_at`)
- **State Graph**: Автомат строит подграф до первого Screen state
- **Expression Metadata**: Все выражения хранят `dependent_variables` для валидации
