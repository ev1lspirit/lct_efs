# LCT EFS - Execution Finite State Machine

**LCT EFS** (Execution Finite State) - это мощный движок выполнения бизнес-процессов на основе конечного автомата (FSM). Система позволяет создавать и выполнять динамические, настраиваемые workflow через API без изменения кода приложения.

## 🚀 Быстрый старт

### Запуск сервисов
```bash
# Запустить MongoDB и Redis
docker-compose up -d

# Запустить API сервер
cd api && uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### Создание первого workflow
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
          "transitions": [{"state_id": "hello"}]
        },
        {
          "state_type": "screen",
          "name": "hello",
          "final_state": true,
          "expressions": [{"event_name": "close"}]
        }
      ]
    },
    "predefined_context": {"message": "Hello, World!"}
  }'
```

## 📚 Документация

Полная документация доступна в папке [`/diagrams`](./diagrams/README.md):

### 📖 Основные документы:
- **[Quick Guide](./diagrams/quick_guide.md)** - быстрое руководство для начала работы
- **[Architecture Overview](./diagrams/architecture_overview.md)** - полный обзор архитектуры
- **[Sequence Diagrams](./diagrams/sequence_diagrams.md)** - диаграммы последовательности (10 диаграмм)
- **[Class Diagrams](./diagrams/class_diagrams.md)** - диаграммы классов (10 диаграмм)
- **[Data Flow Diagrams](./diagrams/data_flow_diagrams.md)** - диаграммы потоков данных (10 диаграмм)

### 🎯 Для новичков:
1. [Quick Guide](./diagrams/quick_guide.md) - начните здесь!
2. [Architecture Overview](./diagrams/architecture_overview.md) - общее понимание
3. [Data Flow Diagrams](./diagrams/data_flow_diagrams.md) - визуальное представление

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────┐
│           API Layer (FastAPI)               │
│  /workflow/save  |  /client/workflow        │
└────────────┬────────────────┬───────────────┘
             │                │
        ┌────▼─────┐    ┌─────▼──────┐
        │ MongoDB  │    │   Redis    │
        │ (States) │    │ (Sessions) │
        └──────────┘    └────────────┘
             │                │
        ┌────▼────────────────▼───────────┐
        │   Workflow Builder (FSM)        │
        │ - Automaton (конечный автомат)  │
        │ - States (состояния)            │
        │ - Handlers (обработчики)        │
        │ - Expressions (выражения)       │
        └─────────────────────────────────┘
```

## ✨ Основные возможности

### 4 типа состояний:

#### 1. **Technical State** - Вычисления
```json
{
  "state_type": "technical",
  "name": "calculate",
  "expressions": [{
    "variable": "total",
    "dependent_variables": ["price", "qty"],
    "expression": "price * qty"
  }]
}
```

#### 2. **Integration State** - HTTP API вызовы
```json
{
  "state_type": "integration",
  "name": "fetch_data",
  "expressions": [{
    "variable": "result",
    "url": "https://api.example.com/data",
    "method": "get"
  }]
}
```

#### 3. **Screen State** - UI взаимодействие
```json
{
  "state_type": "screen",
  "name": "confirmation",
  "expressions": [
    {"event_name": "confirm"},
    {"event_name": "cancel"}
  ]
}
```

#### 4. **Service State** - Системные состояния
```json
{
  "state_type": "service",
  "name": "__init__",
  "initial_state": true
}
```

## 🔄 Как это работает

1. **Сохранение workflow** → MongoDB (определения состояний)
2. **Запрос клиента** → Создание/загрузка сессии (Redis)
3. **Инициализация автомата** → Построение графа состояний
4. **Выполнение FSM** → Итерация по состояниям:
   - Вычисление выражений
   - Проверка переходов
   - Обновление контекста
5. **Возврат результата** → Screen state или финальное состояние

## 🛠️ Технологический стек

- **FastAPI** - API framework
- **MongoDB** - хранение workflow определений
- **Redis** - кэширование сессий и состояний
- **simpleeval** - безопасное выполнение Python выражений
- **attrs** - data classes
- **Pydantic** - валидация данных

## 📊 Примеры использования

### Approval Workflow
```python
# 1. Проверка суммы → Technical State
# 2. Если > 1000 → Screen State (ожидание одобрения)
# 3. Event "approve" → Final State
```

### API Integration Workflow
```python
# 1. Service State → загрузка контекста
# 2. Integration State → вызов внешнего API
# 3. Technical State → обработка результата
# 4. Screen State → отображение данных
```

Полные примеры см. в [Quick Guide](./diagrams/quick_guide.md#📊-примеры-использования)

## ⚙️ Конфигурация

Создайте `.env` файл:

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

## 🔐 Безопасность

- **simpleeval** для безопасного выполнения кода
- Ограниченный набор функций: `len`, `sum`, `max`, `min`
- Валидация зависимостей перед выполнением
- Изоляция контекста между сессиями

## 🐛 Отладка

### Логи
```bash
# Включить DEBUG логирование
export LOG_LEVEL=DEBUG
python -m api.app
```

### Redis проверка
```bash
redis-cli HGETALL "session:your-session-id"
redis-cli HGETALL "state:your-session-id"
```

### MongoDB проверка
```javascript
db.states.find({})
db.workflows.find({})
```

## 📈 Best Practices

✅ **Хорошо:**
- Понятные имена состояний: `validate_user_credentials`
- Минимизация данных в контексте
- Явное указание `final_state`
- Переход по умолчанию для обработки ошибок

❌ **Плохо:**
- Циклические переходы без выхода
- Integration state с условным переходом
- Отсутствие `dependent_variables`

Подробнее: [Quick Guide - Best Practices](./diagrams/quick_guide.md#📈-best-practices)

## 🔧 Расширение системы

Добавление нового типа состояния:
1. Создать класс в `workflow_builder/states.py`
2. Создать expression в `workflow_builder/expressions.py`
3. Создать handler в `workflow_builder/handlers.py`
4. Зарегистрировать в `state_mapping`

Подробная инструкция: [Quick Guide - Расширение](./diagrams/quick_guide.md#🔧-расширение-системы)

## 📁 Структура проекта

```
lct_efs/
├── api/                    # FastAPI endpoints
│   ├── app.py
│   └── routes.py
├── workflow_builder/       # Core FSM engine
│   ├── automaton/         # Automaton implementation
│   ├── states.py          # State types
│   ├── handlers.py        # State handlers
│   ├── expressions.py     # Expression models
│   └── transitions.py     # Transition logic
├── storage/               # Storage layer
│   ├── mongo/            # MongoDB client
│   └── redis/            # Redis cache
├── context.py            # SessionContext manager
├── config.py             # Settings
└── diagrams/             # 📚 Full documentation
    ├── README.md
    ├── quick_guide.md
    ├── architecture_overview.md
    ├── sequence_diagrams.md
    ├── class_diagrams.md
    └── data_flow_diagrams.md
```

## 🤝 Вклад в проект

1. Изучите [Architecture Overview](./diagrams/architecture_overview.md)
2. Следуйте паттернам проектирования из документации
3. Обновляйте диаграммы при изменении кода
4. Добавляйте тесты для новых компонентов

## 📄 Лицензия

[Укажите вашу лицензию]

## 🆘 Поддержка

- 📚 [Документация](./diagrams/README.md)
- 🐛 [FAQ - Частые проблемы](./diagrams/quick_guide.md#🆘-частые-проблемы)
- 📧 [Контакты для связи]

---

**Начните с [Quick Guide](./diagrams/quick_guide.md) и создайте свой первый workflow уже сегодня! 🚀**

