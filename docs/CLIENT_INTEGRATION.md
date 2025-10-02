# Интеграция клиента с Workflow Engine

## Обзор

Клиентское приложение (фронтенд) взаимодействует с Workflow Engine через REST API. При каждом запросе сервер возвращает текущий экран со всеми необходимыми данными для отображения.

## API Endpoint

**URL:** `POST /client/workflow`

**Base URL:** `http://localhost:8080` (или ваш production URL)

## Схема работы

```
┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│   Client    │────────▶│  API Server │────────▶│   Workflow   │
│  (Frontend) │         │             │         │    Engine    │
└─────────────┘         └─────────────┘         └──────────────┘
       │                       │                        │
       │                       │                        │
       │  1. POST /client/     │                        │
       │     workflow          │   2. Process state     │
       │  ────────────────────▶│  ────────────────────▶ │
       │                       │                        │
       │                       │   3. Return screen     │
       │  4. Render screen     │  ◀──────────────────── │
       │  ◀────────────────────│                        │
       │                       │                        │
       │  5. User action       │                        │
       │  ────────────────────▶│                        │
       │                       │                        │
       └───────────────────────┴────────────────────────┘
```

## 1. Инициализация сессии

### Первый запрос (создание сессии)

```javascript
const response = await fetch('http://localhost:8080/client/workflow', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    client_workflow_id: '68de6c82acbc353520543bd1', // ID workflow
    client_session_id: 'user-123-session-456',      // Уникальный ID сессии
    context: {}                                      // Начальный контекст (пустой)
  })
});

const data = await response.json();
```

### Ответ сервера

```json
{
  "session_id": "user-123-session-456",
  "context": {
    "__workflow_id": "68de6c82acbc353520543bd1",
    "__created_at": "2025-10-02 15:13:54.472296",
    "_id": "68de6c82acbc353520543bd1"
  },
  "current_state": "UserInputScreen",
  "state_type": "screen",
  "screen": {
    "id": "screen-user-input",
    "type": "Screen",
    "name": "Поиск пользователя",
    "style": {
      "display": "flex",
      "flexDirection": "column",
      "minHeight": "100vh",
      "backgroundColor": "#F5F5F5"
    },
    "sections": {
      "header": {
        "id": "section-input-header",
        "type": "Section",
        "properties": { /* ... */ },
        "style": { /* ... */ },
        "children": [ /* компоненты header */ ]
      },
      "body": {
        "id": "section-input-body",
        "type": "Section",
        "properties": { /* ... */ },
        "style": { /* ... */ },
        "children": [ /* компоненты body */ ]
      },
      "footer": {
        "id": "section-footer",
        "type": "Section",
        "properties": { /* ... */ },
        "style": { /* ... */ },
        "children": [ /* компоненты footer */ ]
      }
    }
  }
}
```

## 2. Отправка событий

Когда пользователь взаимодействует с UI (нажимает кнопку, отправляет форму), клиент отправляет событие:

```javascript
const response = await fetch('http://localhost:8080/client/workflow', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    client_session_id: 'user-123-session-456',  // Существующая сессия
    event_name: 'search',                        // Название события
    context: {                                   // Данные из формы
      user_id: '1',
      api_key: 'test-api-key-123'
    }
  })
});

const data = await response.json();
```

### Ответ с новым экраном

```json
{
  "session_id": "user-123-session-456",
  "context": {
    "__workflow_id": "68de6c82acbc353520543bd1",
    "__created_at": "2025-10-02 15:13:54.472296",
    "_id": "68de6c82acbc353520543bd1",
    "user_id": "1",
    "api_key": "test-api-key-123",
    "input_valid": "True",
    "user_profile": "{'id': 1, 'name': 'Leanne Graham', ...}"
  },
  "current_state": "DisplayProfileScreen",
  "state_type": "screen",
  "screen": {
    "id": "screen-profile",
    "type": "Screen",
    "name": "Профиль пользователя",
    "sections": { /* ... */ }
  }
}
```

## 3. Рендеринг экранов на клиенте

### React пример

```typescript
import React, { useState, useEffect } from 'react';

interface WorkflowResponse {
  session_id: string;
  context: Record<string, any>;
  current_state: string;
  state_type: string;
  screen?: ScreenDefinition;
}

interface ScreenDefinition {
  id: string;
  type: string;
  name: string;
  style: React.CSSProperties;
  sections: {
    header?: Section;
    body?: Section;
    footer?: Section;
  };
}

interface Section {
  id: string;
  type: string;
  properties: any;
  style: React.CSSProperties;
  children: Component[];
}

const WorkflowClient: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('');
  const [screen, setScreen] = useState<ScreenDefinition | null>(null);
  const [context, setContext] = useState<Record<string, any>>({});

  // Инициализация сессии
  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    const response = await fetch('http://localhost:8080/client/workflow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_workflow_id: '68de6c82acbc353520543bd1',
        client_session_id: `session-${Date.now()}`,
        context: {}
      })
    });

    const data: WorkflowResponse = await response.json();
    setSessionId(data.session_id);
    setScreen(data.screen || null);
    setContext(data.context);
  };

  // Отправка события
  const sendEvent = async (eventName: string, eventContext: Record<string, any> = {}) => {
    const response = await fetch('http://localhost:8080/client/workflow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_session_id: sessionId,
        event_name: eventName,
        context: eventContext
      })
    });

    const data: WorkflowResponse = await response.json();
    setScreen(data.screen || null);
    setContext(data.context);
  };

  if (!screen) return <div>Загрузка...</div>;

  return (
    <div style={screen.style}>
      {screen.sections.header && (
        <ScreenSection
          section={screen.sections.header}
          context={context}
          onEvent={sendEvent}
        />
      )}
      {screen.sections.body && (
        <ScreenSection
          section={screen.sections.body}
          context={context}
          onEvent={sendEvent}
        />
      )}
      {screen.sections.footer && (
        <ScreenSection
          section={screen.sections.footer}
          context={context}
          onEvent={sendEvent}
        />
      )}
    </div>
  );
};

// Компонент для рендеринга секции
const ScreenSection: React.FC<{
  section: Section;
  context: Record<string, any>;
  onEvent: (eventName: string, context: Record<string, any>) => void;
}> = ({ section, context, onEvent }) => {
  return (
    <div style={section.style}>
      {section.children.map((child, index) => (
        <ComponentRenderer
          key={child.id || index}
          component={child}
          context={context}
          onEvent={onEvent}
        />
      ))}
    </div>
  );
};

// Универсальный рендерер компонентов
const ComponentRenderer: React.FC<{
  component: any;
  context: Record<string, any>;
  onEvent: (eventName: string, context: Record<string, any>) => void;
}> = ({ component, context, onEvent }) => {
  const { type, properties, style, children } = component;

  // Интерполяция значений
  const resolveValue = (value: any): any => {
    if (typeof value === 'object' && value.reference) {
      // Подставляем значение из контекста
      const path = value.reference.replace('${', '').replace('}', '');
      return getNestedValue(context, path) || value.value;
    }
    return value;
  };

  switch (type) {
    case 'text':
      return (
        <span style={style}>
          {resolveValue(properties.content)}
        </span>
      );

    case 'button':
      return (
        <button
          style={style}
          onClick={() => {
            if (properties.event) {
              onEvent(properties.event, properties.eventParams || {});
            }
          }}
        >
          {properties.text}
        </button>
      );

    case 'input':
      return (
        <input
          type={properties.type || 'text'}
          name={properties.name}
          placeholder={properties.placeholder}
          required={properties.required}
          defaultValue={resolveValue(properties.value)}
          style={style}
        />
      );

    case 'image':
      return (
        <img
          src={resolveValue(properties.src)}
          alt={resolveValue(properties.alt)}
          width={properties.width}
          height={properties.height}
          style={style}
        />
      );

    case 'column':
      return (
        <div style={{ ...style, display: 'flex', flexDirection: 'column' }}>
          {children?.map((child: any, index: number) => (
            <ComponentRenderer
              key={child.id || index}
              component={child}
              context={context}
              onEvent={onEvent}
            />
          ))}
        </div>
      );

    case 'row':
      return (
        <div style={{ ...style, display: 'flex', flexDirection: 'row' }}>
          {children?.map((child: any, index: number) => (
            <ComponentRenderer
              key={child.id || index}
              component={child}
              context={context}
              onEvent={onEvent}
            />
          ))}
        </div>
      );

    case 'list':
      const items = resolveValue(properties.items) || [];
      const itemAlias = properties.itemAlias || 'item';
      
      return (
        <ul style={style}>
          {items.map((item: any, index: number) => {
            // Создаем контекст для каждого элемента списка
            const itemContext = { ...context, [itemAlias]: item };
            
            return (
              <li key={index}>
                {children?.map((child: any, childIndex: number) => (
                  <ComponentRenderer
                    key={child.id || childIndex}
                    component={child}
                    context={itemContext}
                    onEvent={onEvent}
                  />
                ))}
              </li>
            );
          })}
        </ul>
      );

    case 'checkbox':
      return (
        <input
          type="checkbox"
          checked={properties.checked}
          onChange={() => {
            if (properties.event) {
              onEvent(properties.event, {});
            }
          }}
          style={style}
        />
      );

    default:
      console.warn(`Unknown component type: ${type}`);
      return null;
  }
};

// Вспомогательная функция для получения вложенных значений
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((acc, part) => acc?.[part], obj);
};

export default WorkflowClient;
```

## 4. Обработка событий от пользователя

### Форма с input полями

```typescript
const handleFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  const formData = new FormData(e.currentTarget);
  
  const context = {
    user_id: formData.get('user_id') as string,
    api_key: formData.get('api_key') as string,
  };

  await sendEvent('search', context);
};
```

### Кнопка с событием

```typescript
<button
  onClick={() => sendEvent('load_orders', {})}
>
  Загрузить заказы
</button>
```

### Кнопка с параметрами

```typescript
<button
  onClick={() => sendEvent('incrementItem', {
    itemId: cartItem.id
  })}
>
  +
</button>
```

## 5. Полный пример использования

```typescript
import React, { useState } from 'react';

const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('');
  const [screen, setScreen] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = 'http://localhost:8080';
  const WORKFLOW_ID = '68de6c82acbc353520543bd1';

  // 1. Инициализация при загрузке
  React.useEffect(() => {
    initWorkflow();
  }, []);

  const initWorkflow = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/client/workflow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_workflow_id: WORKFLOW_ID,
          client_session_id: `session-${Date.now()}`,
          context: {}
        })
      });

      const data = await response.json();
      setSessionId(data.session_id);
      setScreen(data.screen);
    } catch (error) {
      console.error('Failed to initialize workflow:', error);
    } finally {
      setLoading(false);
    }
  };

  // 2. Отправка событий
  const sendEvent = async (eventName: string, eventContext = {}) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/client/workflow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_session_id: sessionId,
          event_name: eventName,
          context: eventContext
        })
      });

      const data = await response.json();
      setScreen(data.screen);
    } catch (error) {
      console.error('Failed to send event:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Загрузка...</div>;
  if (!screen) return <div>Нет экрана для отображения</div>;

  // 3. Рендеринг экрана
  return <ScreenRenderer screen={screen} onEvent={sendEvent} />;
};

export default App;
```

## 6. JavaScript (Vanilla) пример

```javascript
class WorkflowClient {
  constructor(apiBase, workflowId) {
    this.apiBase = apiBase;
    this.workflowId = workflowId;
    this.sessionId = null;
    this.screen = null;
    this.context = {};
  }

  async init() {
    const response = await fetch(`${this.apiBase}/client/workflow`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_workflow_id: this.workflowId,
        client_session_id: `session-${Date.now()}`,
        context: {}
      })
    });

    const data = await response.json();
    this.sessionId = data.session_id;
    this.screen = data.screen;
    this.context = data.context;
    
    return data;
  }

  async sendEvent(eventName, eventContext = {}) {
    const response = await fetch(`${this.apiBase}/client/workflow`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_session_id: this.sessionId,
        event_name: eventName,
        context: eventContext
      })
    });

    const data = await response.json();
    this.screen = data.screen;
    this.context = data.context;
    
    return data;
  }

  renderScreen() {
    // Реализация рендеринга экрана
    const container = document.getElementById('screen-container');
    container.innerHTML = '';
    
    if (!this.screen) return;

    // Рендерим header, body, footer
    if (this.screen.sections.header) {
      container.appendChild(this.renderSection(this.screen.sections.header));
    }
    if (this.screen.sections.body) {
      container.appendChild(this.renderSection(this.screen.sections.body));
    }
    if (this.screen.sections.footer) {
      container.appendChild(this.renderSection(this.screen.sections.footer));
    }
  }

  renderSection(section) {
    const div = document.createElement('div');
    Object.assign(div.style, section.style);
    
    section.children.forEach(child => {
      div.appendChild(this.renderComponent(child));
    });
    
    return div;
  }

  renderComponent(component) {
    const { type, properties, style, children } = component;
    
    switch (type) {
      case 'text':
        const span = document.createElement('span');
        span.textContent = this.resolveValue(properties.content);
        Object.assign(span.style, style);
        return span;
        
      case 'button':
        const button = document.createElement('button');
        button.textContent = properties.text;
        Object.assign(button.style, style);
        button.onclick = () => {
          this.sendEvent(properties.event, properties.eventParams || {})
            .then(() => this.renderScreen());
        };
        return button;
        
      // ... другие типы компонентов
      
      default:
        return document.createElement('div');
    }
  }

  resolveValue(value) {
    if (typeof value === 'object' && value.reference) {
      const path = value.reference.replace('${', '').replace('}', '');
      return this.getNestedValue(this.context, path) || value.value;
    }
    return value;
  }

  getNestedValue(obj, path) {
    return path.split('.').reduce((acc, part) => acc?.[part], obj);
  }
}

// Использование
const client = new WorkflowClient(
  'http://localhost:8080',
  '68de6c82acbc353520543bd1'
);

client.init().then(() => {
  client.renderScreen();
});
```

## 7. Обработка ошибок

```typescript
const sendEvent = async (eventName: string, context = {}) => {
  try {
    const response = await fetch('http://localhost:8080/client/workflow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_session_id: sessionId,
        event_name: eventName,
        context
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Проверяем тип состояния
    if (data.state_type === 'screen') {
      setScreen(data.screen);
    } else {
      console.log('Non-screen state:', data.current_state);
    }
    
    return data;
  } catch (error) {
    console.error('Failed to send event:', error);
    // Показываем пользователю ошибку
    setError('Не удалось выполнить действие. Попробуйте еще раз.');
  }
};
```

## 8. Тестирование с curl

```bash
# 1. Инициализация сессии
curl -X POST http://localhost:8080/client/workflow \
  -H 'Content-Type: application/json' \
  -d '{
    "client_workflow_id": "68de6c82acbc353520543bd1",
    "client_session_id": "test-session-123",
    "context": {}
  }'

# 2. Отправка события
curl -X POST http://localhost:8080/client/workflow \
  -H 'Content-Type: application/json' \
  -d '{
    "client_session_id": "test-session-123",
    "event_name": "search",
    "context": {
      "user_id": "1",
      "api_key": "test-key"
    }
  }'
```

## Важные моменты

### Session ID
- Должен быть уникальным для каждого пользователя
- Храните его в localStorage/sessionStorage
- Используйте один session_id для всего workflow

### Workflow ID
- Получите от бэкенд команды после деплоя workflow
- Жестко закодируйте в конфиге фронтенда
- Или получайте динамически через отдельный endpoint

### Context
- Сервер автоматически сохраняет контекст между запросами
- Не нужно отправлять весь контекст каждый раз
- Отправляйте только новые/измененные данные

### Динамические данные
- Используйте формат `${variable.path}` для reference
- Сервер автоматически подставит значения из контекста
- Fallback на `value` если данных нет

## Готовый workflow для тестирования

**Workflow ID:** `68de6c82acbc353520543bd1`

**Сценарий:**
1. UserInputScreen - ввод user_id и api_key
2. DisplayProfileScreen - отображение профиля
3. DisplayOrdersScreen - список заказов
4. DisplayResultsScreen - итоговый экран

**События:**
- `search` - начать поиск
- `load_orders` - загрузить заказы
- `create_summary` - создать отчет
- `new_search` - новый поиск
- `back` - назад
- `exit` - выход

## Ссылки

- [Формат экранов](./SCREEN_FORMAT.md)
- [Примеры workflow](../api/integration_workflow_correct_format.py)
- [Скрипт деплоя](../deploy_correct_format.py)
