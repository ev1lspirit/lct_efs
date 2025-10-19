# 🚀 LCT EFS - Workflow Management System

> **🔧 Последнее обновление (17.10.2025)**: Исправлена критическая ошибка IntegrationHandler (POST/PUT/PATCH теперь используют body вместо params), добавлен TTL для Redis сессий, проведена очистка документации.

## 📋 Описание проекта

LCT EFS (Workflow Management System) - это современная платформа для управления бизнес-процессами и пользовательскими workflow. Система поддерживает декларативное описание процессов в формате JSON, автоматическое управление состояниями, интеграцию с внешними API и динамическое создание пользовательских интерфейсов.

## ✨ Ключевые возможности

- 🎯 **Декларативные Workflow** - описание процессов в JSON формате
- 🔄 **Автомат состояний** - автоматическое управление переходами между состояниями
- 🖥️ **Динамические экраны** - автоматическая генерация UI на основе конфигурации
- 🌐 **Интеграции с API** - поддержка внешних HTTP-интеграций с интерполяцией переменных
- 💾 **Управление контекстом** - хранение состояния сессии в Redis с автоматическим TTL
- 📱 **Multi-platform** - поддержка веб и мобильных клиентов
- 🔧 **Extensible** - легко расширяемая архитектура
- 🔐 **Безопасность** - валидация session_id, защита от инъекций, автоматическое продление TTL

## 🏗️ Архитектура системы

### Основные компоненты

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Layer  │    │   API Layer     │    │  Core Engine    │
│                 │    │                 │    │                 │
│ • React/Vue     │───▶│ • FastAPI       │───▶│ • Automaton     │
│ • Mobile App    │    │ • CORS          │    │ • State Parser  │
│ • Demo HTML     │    │ • Routes        │    │ • Expressions   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  State Types    │    │  Data Storage   │    │  Integrations   │
│                 │    │                 │    │                 │
│ • Screen        │◀───│ • Redis Cache   │    │ • HTTP Adapters │
│ • Technical     │    │ • MongoDB       │    │ • External APIs │
│ • Integration   │    │ • PostgreSQL    │    │ • RESTful       │
│ • Service       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Типы состояний

1. **Screen** - Состояния пользовательского интерфейса с секциями (header, body, footer)
2. **Technical** - Бизнес-логика и вычисления на основе выражений
3. **Integration** - Интеграция с внешними API (GET/POST/PUT/DELETE/PATCH)
4. **Service** - Системные операции (`__service_init`, `__service_error`)

## 🚀 Быстрый старт

### 1. Предварительные требования

- Python 3.10+
- Docker и Docker Compose
- Redis 6.0+
- MongoDB 4.4+

### 2. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Установка зависимостей
python -m pip install -r deployments\requirements.txt
```


### 3. Запуск инфраструктуры

```bash
# Запуск Redis и MongoDB через Docker
docker-compose -f deployments\docker-compose.yaml up -d

# Проверка статуса контейнеров
docker-compose -f deployments\docker-compose.yaml ps
```

### 4. Запуск API сервера

```bash
# Запуск с auto-reload
python -m uvicorn api.app:app --reload --port 8080

# Сервер будет доступен по адресу http://localhost:8080
# Документация API: http://localhost:8080/docs
```

### 5. Проверка работоспособности

```bash
# Проверка health check
curl http://localhost:8080/healthcheck
# Ответ: {"status": "ok"}
```

## 📋 API Reference

### POST /client/workflow

Основной endpoint для взаимодействия с workflow.

**Запрос:**
```json
{
  "client_session_id": "unique-session-id",
  "client_workflow_id": "workflow-id-from-mongo",
  "context": {},
  "event_name": "event_name_or_null"
}
```

**Ответ:**
```json
{
  "current_state": "state_name",
  "context": {
    "variable1": "value1"
  },
  "screen": {
    "id": "screen-id",
    "type": "Screen",
    "sections": {
      "header": {},
      "body": {},
      "footer": {}
    }
  },
  "status": "success"
}
```

### POST /workflow/save

Сохранение конфигурации workflow в MongoDB.

**Запрос:**
```json
{
  "states": {
    "states": [
      {
        "state_type": "screen",
        "name": "login_screen",
        "initial_state": true,
        "transitions": [
          {
            "case": "submit",
            "state_id": "next_state"
          }
        ],
        "screen": {
          "id": "screen-1",
          "type": "Screen",
          "sections": {}
        }
      }
    ]
  },
  "predefined_context": {
    "app_version": "1.0.0"
  }
}
```

**Ответ:**
```json
{
  "workflow_id": "507f1f77bcf86cd799439011",
  "screens_saved": 1,
  "context_saved": true
}
```

## 📝 Формат Workflow

### Структура состояния

```json
{
  "state_type": "screen|technical|integration|service",
  "name": "unique_state_name",
  "initial_state": true,
  "final_state": false,
  "transitions": [
    {
      "case": "event_name",
      "state_id": "next_state_name"
    }
  ],
  "expressions": []
}
```

### Пример Screen состояния

```json
{
  "state_type": "screen",
  "name": "UserInputScreen",
  "initial_state": false,
  "final_state": false,
  "transitions": [
    {"case": "submit", "state_id": "ProcessData"}
  ],
  "screen": {
    "id": "screen-user-input",
    "type": "Screen",
    "name": "Ввод данных",
    "sections": {
      "header": {
        "title": "Введите ваши данные"
      },
      "body": {
        "fields": [
          {
            "id": "username",
            "type": "text",
            "label": "Имя пользователя"
          }
        ]
      },
      "footer": {
        "buttons": [
          {
            "id": "submit_btn",
            "label": "Отправить",
            "event": "submit"
          }
        ]
      }
    }
  }
}
```

### Пример Integration состояния

```json
{
  "state_type": "integration",
  "name": "FetchUserData",
  "initial_state": false,
  "final_state": false,
  "transitions": [
    {"case": "default", "state_id": "ShowResults"}
  ],
  "expressions": [
    {
      "variable": "user_data",
      "method": "get",
      "url": "https://jsonplaceholder.typicode.com/users/{{context.user_id}}",
      "dependent_variables": ["user_id"],
      "error_variable": "api_error"
    }
  ]
}
```

**⚠️ Важно:** 
- Методы `GET`, `DELETE` используют `params` для параметров
- Методы `POST`, `PUT`, `PATCH` используют `body` для данных

### Пример Technical состояния

```json
{
  "state_type": "technical",
  "name": "CalculateTotal",
  "transitions": [
    {"case": "default", "state_id": "ShowTotal"}
  ],
  "expressions": [
    {
      "variable": "total",
      "dependent_variables": ["price", "quantity"],
      "expression": "context['price'] * context['quantity']"
    }
  ]
}
```

## 📂 Структура проекта

```
lct_efs/
├── api/                      # FastAPI приложение
│   ├── app.py               # Основное приложение с CORS
│   ├── routes.py            # API endpoints
│   ├── schema.py            # Pydantic схемы
│   └── tests/               # Интеграционные тесты
├── workflow_builder/        # Ядро workflow engine
│   ├── automaton/          # Реализация автомата
│   ├── state_parser/       # Парсинг JSON в StateModel
│   ├── expressions.py      # Обработка выражений
│   ├── models.py           # Базовые модели
│   └── states.py           # Типы состояний
├── storage/                 # Слой работы с БД
│   ├── mongo/              # MongoDB клиент
│   ├── redis/              # Redis клиент с TTL
│   └── postgres/           # PostgreSQL клиент
├── adapters/               # HTTP адаптеры для интеграций
├── docs/                   # Документация
│   └── FIX_CUTE_IMAGES_TRANSITION.md
├── deployments/            # Docker и зависимости
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   └── requirements.txt
├── tests/                  # End-to-end тесты
├── config.py              # Настройки проекта
└── utils.py               # Утилиты и логирование
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
python -m pytest

# Конкретный тест
python -m pytest test_new_format.py -v

# Интеграционные тесты
python -m pytest tests/test_automaton_end_to_end.py -v

# Тесты с выводом логов
python -m pytest -v -s
```

### Примеры тестов

Проект содержит различные типы тестов:
- `test_new_format.py` - тесты сохранения workflow в MongoDB
- `tests/test_automaton_end_to_end.py` - end-to-end тесты автомата
- `tests/test_integration_interpolation.py` - тесты интерполяции переменных
- `tests/test_session_error_handling.py` - тесты обработки ошибок сессий

### Ручное тестирование через curl

```bash
# Инициализация workflow
curl -X POST http://localhost:8080/client/workflow ^
  -H "Content-Type: application/json" ^
  -d "{\"client_session_id\":\"test-123\",\"client_workflow_id\":\"507f1f77bcf86cd799439011\",\"context\":{},\"event_name\":null}"

# Отправка события
curl -X POST http://localhost:8080/client/workflow ^
  -H "Content-Type: application/json" ^
  -d "{\"client_session_id\":\"test-123\",\"client_workflow_id\":\"507f1f77bcf86cd799439011\",\"context\":{},\"event_name\":\"submit\"}"
```

## 🌐 Интеграция с клиентами

### JavaScript/React пример

```javascript
class WorkflowClient {
  constructor(baseUrl = 'http://localhost:8080') {
    this.baseUrl = baseUrl;
    this.sessionId = this.generateSessionId();
  }

  async executeWorkflow(workflowId, eventName = null, context = {}) {
    const response = await fetch(`${this.baseUrl}/client/workflow`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_session_id: this.sessionId,
        client_workflow_id: workflowId,
        context: context,
        event_name: eventName
      })
    });
    return response.json();
  }

  generateSessionId() {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Использование
const client = new WorkflowClient();
const result = await client.executeWorkflow('workflow-id-123');
console.log('Current state:', result.current_state);
```

## 🔄 Жизненный цикл обработки

1. **Получение запроса** - FastAPI принимает POST запрос на `/client/workflow`
2. **Проверка сессии** - Redis проверяет существующую сессию или создает новую с TTL
3. **Загрузка workflow** - MongoDB возвращает конфигурацию состояний
4. **Парсинг workflow** - `StateParser` преобразует JSON в `StateModel`
5. **Инициализация автомата** - Создается экземпляр `Automaton`
6. **Выполнение состояния** - Обработка текущего состояния (screen/technical/integration)
7. **Обработка выражений** - Интерполяция переменных и вычисления
8. **Переход по транзициям** - Определение следующего состояния
9. **Обновление контекста** - Сохранение в Redis с продлением TTL
10. **Возврат результата** - JSON ответ клиенту

## 📊 Последние изменения (17.10.2025)

### ✅ Исправления

1. **Critical Fix: IntegrationHandler**
   - `POST/PUT/PATCH` теперь отправляют данные в `body` (не в query string)
   - `GET/DELETE` используют `params` для query параметров
   - Добавлена валидация на уровне `IntegrationExpressionModel`

2. **Redis TTL для сессий**
   - `create_session()` устанавливает TTL (по умолчанию 3600s)
   - `update_session()` автоматически продлевает TTL
   - `get_session()` проверяет истечение и возвращает `None` для истекших сессий

3. **Улучшенное логирование**
   - Интерполированные переменные в URL
   - Разделение base_url и endpoint
   - Детальные логи request kwargs (json vs params)
   - Логирование ошибок с status_code и content

## 🛠️ Разработка

### Добавление нового типа состояния

1. Добавьте enum в `workflow_builder/models.py`:
```python
class StateTypeEnum(str, Enum):
    SCREEN = "screen"
    TECHNICAL = "technical"
    INTEGRATION = "integration"
    SERVICE = "service"
    YOUR_NEW_TYPE = "your_new_type"  # новый тип
```

2. Создайте класс состояния в `workflow_builder/states.py`
3. Добавьте обработчик в `workflow_builder/automaton/`
4. Обновите `STATE_CLASSES` в `state_parser/contract.py`
5. Создайте тесты

### Создание нового HTTP адаптера

1. Наследуйтесь от `commonAdapter.py`
2. Реализуйте методы `get()`, `post()`, `put()`, `delete()`
3. Добавьте интерполяцию через `{{context.variable}}`
4. Добавьте error handling с `error_variable`

## 🐳 Развертывание

### Docker

```bash
# Сборка образа
docker build -f deployments\Dockerfile -t lct-efs:latest .

# Запуск контейнера
docker run -p 8080:8080 --env-file .env lct-efs:latest
```

### Docker Compose (рекомендуется)

```bash
# Полное развертывание с инфраструктурой
docker-compose -f deployments\docker-compose.yaml up -d

# Просмотр логов
docker-compose -f deployments\docker-compose.yaml logs -f

# Остановка
docker-compose -f deployments\docker-compose.yaml down
```



## 📈 Производительность

- **Redis** - кэширование сессий и контекста с автоматическим TTL
- **MongoDB** - хранение JSON workflow с индексами
- **FastAPI** - асинхронная обработка запросов
- **Пулинг соединений** - для MongoDB и Redis

## 🔒 Безопасность

- ✅ CORS middleware для веб-безопасности
- ✅ Валидация входных данных через Pydantic
- ✅ Изоляция сессий через UUID
- ✅ URL-encoding паролей в connection strings
- ✅ Автоматическое истечение сессий (TTL)
- ✅ Защита от SQL/NoSQL инъекций

## 📚 Документация

- `docs/FIX_CUTE_IMAGES_TRANSITION.md` - примеры интеграционных состояний
- `.github/copilot-instructions.md` - руководство для разработчиков
- `CHANGELOG_2025_10_17.md` - последние изменения
- API документация доступна по `/docs` после запуска сервера

