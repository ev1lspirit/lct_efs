# 🚀 LCT EFS - Workflow Management System

## 📋 Описание проекта

LCT EFS (Workflow Management System) - это современная платформа для управления бизнес-процессами и пользовательскими workflow. Система поддерживает декларативное описание процессов в формате JSON, автоматическое управление состояниями, интеграцию с внешними API и динамическое создание пользовательских интерфейсов.

## ✨ Ключевые возможности

- 🎯 **Декларативные Workflow** - описание процессов в JSON формате
- 🔄 **Автомат состояний** - автоматическое управление переходами между состояниями
- 🖥️ **Динамические экраны** - автоматическая генерация UI на основе конфигурации
- 🌐 **Интеграции с API** - поддержка внешних HTTP-интеграций с интерполяцией переменных
- 💾 **Управление контекстом** - хранение состояния сессии в Redis
- 📱 **Multi-platform** - поддержка веб и мобильных клиентов
- 🔧 **Extensible** - легко расширяемая архитектура

## 🏗️ Архитектура системы

### Основные компоненты

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Layer  │    │   API           │    │  Core Engine    │
│                 │    │                 │    │                 │
│ • React/Vue     │───▶│ • FastAPI       │───▶│ • Automaton     │
│ • Mobile App    │    │ • CORS          │    │ • State Parser  │
│ • Demo HTML     │    │ • Routes        │    │ • Context Mgr   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  State Types    │    │  Data Storage   │    │  Integrations   │
│                 │    │                 │    │                 │
│ • Screen        │◀───│ • Redis Cache   │    │ • HTTP Adapters │
│ • Technical     │    │ • MongoDB       │    │ • External APIs │
│ • Integration   │    │ • PostgreSQL    │    │ • JSON Placeholder│
│ • Service       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Типы состояний

1. **Screen** - Состояния пользовательского интерфейса
2. **Technical** - Бизнес-логика и вычисления
3. **Integration** - Интеграция с внешними API
4. **Service** - Системные операции

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Установка зависимостей
pip install -r deployments/requirements.txt
```

### 2. Запуск инфраструктуры

```bash
# Запуск Redis и MongoDB через Docker
docker-compose up -d
```

### 3. Запуск API сервера

```bash
# Развертывание в режиме разработки
uvicorn api.app:app --reload --port 8080

# Сервер будет доступен по адресу http://localhost:8080
```

### 4. Проверка работоспособности

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
  "context": {},
  "screen": {
    "id": "screen-id",
    "type": "Screen",
    "sections": {...}
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
        "transitions": [...],
        "screen": {...}
      }
    ]
  },
  "predefined_context": {}
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
  "expressions": [
    {
      "event_name": "event_name"
    }
  ]
}
```

### Пример Screen состояния

```json
{
  "state_type": "screen",
  "name": "UserInputScreen",
  "screen": {
    "id": "screen-user-input",
    "type": "Screen",
    "name": "Поиск пользователя",
    "sections": {
      "header": {...},
      "body": {...},
      "footer": {...}
    }
  }
}
```

### Пример Integration состояния

```json
{
  "state_type": "integration",
  "name": "CallExternalAPI",
  "integration": {
    "method": "GET",
    "url": "https://api.example.com/users/{{context.user_id}}",
    "headers": {
      "Authorization": "Bearer {{context.token}}"
    }
  }
}
```

## 📂 Структура проекта

```
lct_efs/
├── api/                    # FastAPI приложение
│   ├── app.py             # Основное приложение
│   ├── routes.py          # API маршруты
│   ├── schema.py          # Pydantic схемы
│   └── test_*.py          # Интеграционные тесты
├── adapters/              # Адаптеры для внешних API
├── docs/                  # Документация
├── diagrams/              # Диаграммы архитектуры
├── storage/               # Слой работы с БД
│   ├── mongo/            # MongoDB клиент
│   ├── redis/            # Redis клиент
│   └── postgres/         # PostgreSQL клиент
├── fsm/                   # Finite State Machine
├── workflow_builder/      # Ядро workflow engine
├── tests/                 # Тесты
├── deployments/          # Docker и деплой
└── examples/             # Примеры использования
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Интеграционные тесты
pytest api/test_integration_workflow.py -v

# Тесты интерполяции
pytest tests/test_integration_interpolation.py -v
```

### Ручное тестирование

```bash
# Пример запроса
curl -X POST http://localhost:8080/client/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "client_session_id": "test-session-123",
    "client_workflow_id": "68de6c82acbc353520543bd1",
    "context": {},
    "event_name": null
  }'
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
```

### Использование

```javascript
const client = new WorkflowClient();

// Инициализация workflow
const result = await client.executeWorkflow('workflow-id-123');

// Обработка события
const nextResult = await client.executeWorkflow('workflow-id-123', 'submit_form', {
  username: 'john_doe',
  email: 'john@example.com'
});
```

## 🔄 Жизненный цикл обработки

1. **Получение запроса** - API получает запрос от клиента
2. **Проверка сессии** - Проверка/создание сессии в Redis
3. **Загрузка workflow** - Получение конфигурации из MongoDB
4. **Инициализация автомата** - Создание экземпляра Automaton
5. **Выполнение состояния** - Обработка текущего состояния
6. **Обновление контекста** - Сохранение изменений в Redis
7. **Возврат результата** - Отправка ответа клиенту

## 📊 Мониторинг и логирование

Система использует структурированное логирование с цветовой схемой:

- 🔍 **DEBUG** - Детальная отладочная информация
- ✅ **INFO** - Общая информация о выполнении
- ⚠️ **WARNING** - Предупреждения
- ❌ **ERROR** - Ошибки выполнения
- 🚨 **CRITICAL** - Критические ошибки

## 🛠️ Разработка

### Добавление нового типа состояния

1. Определите новый enum в `workflow_builder/models.py`
2. Добавьте обработчик в `Automaton`
3. Создайте соответствующую схему валидации
4. Обновите документацию

### Создание нового адаптера

1. Наследуйтесь от базового класса в `adapters/`
2. Реализуйте необходимые методы
3. Добавьте конфигурацию
4. Создайте тесты

## 🐳 Развертывание

### Docker

```bash
# Сборка образа
docker build -f deployments/Dockerfile -t lct-efs:latest .

# Запуск контейнера
docker run -p 8080:8080 lct-efs:latest
```

### Docker Compose

```bash
# Полное развертывание с БД
docker-compose -f deployments/docker-compose.yaml up -d
```

### Kubernetes

```bash
# Применение манифестов
kubectl apply -f deployments/middle_back_deployment.yaml
```

## 📈 Производительность

- **Redis** используется для быстрого доступа к контексту сессий
- **MongoDB** оптимизирован для хранения JSON-конфигураций
- **Асинхронная обработка** через FastAPI
- **Кэширование** workflow конфигураций

## 🔒 Безопасность

- CORS middleware для веб-безопасности
- Валидация входных данных через Pydantic
- Изоляция сессий через уникальные идентификаторы
- Контроль доступа к внешним API

**Версия:** 1.0.0  
**Последнее обновление:** 02.10.2025
