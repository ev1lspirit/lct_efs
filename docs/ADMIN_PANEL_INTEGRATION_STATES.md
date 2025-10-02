# Промпт для админ-панели: Интеграционные состояния (Integration States)

## 📋 Введение

Этот документ предназначен для команды, разрабатывающей админ-панель для создания workflow. Здесь описано, как реализовать UI для создания **интеграционных состояний** (Integration States) - специальных состояний, которые загружают данные из внешних API и сохраняют их в контекст сессии.

---

## 🎯 Что такое Integration State?

**Integration State** - это состояние workflow, которое:

1. 🌐 **Выполняет HTTP запрос** к внешнему API
2. 💾 **Сохраняет результат** в контекст сессии
3. ➡️ **Автоматически переходит** к следующему состоянию
4. 🔄 **Делает данные доступными** для всех последующих состояний

### Типичные сценарии использования

- ✅ Получение профиля пользователя из CRM
- ✅ Загрузка каталога товаров из внешней системы
- ✅ Проверка кредитного рейтинга в бюро
- ✅ Отправка данных формы на backend
- ✅ Получение курсов валют
- ✅ Загрузка списка филиалов/отделений
- ✅ Проверка наличия товара на складе

---

## 🏗️ Структура данных

### JSON Schema для Integration State

```json
{
  "state_type": "integration",
  "name": "UniqueStateName",
  "transitions": [
    {
      "variable": "result_variable_name",
      "case": null,
      "state_id": "NextStateName"
    }
  ],
  "expressions": [
    {
      "variable": "result_variable_name",
      "url": "https://api.example.com/endpoint",
      "params": {
        "key1": "value1",
        "key2": "{{context_variable}}"
      },
      "method": "get"
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

### Обязательные поля

| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `state_type` | string | Тип состояния (всегда `"integration"`) | `"integration"` |
| `name` | string | Уникальное имя состояния | `"FetchUserProfile"` |
| `transitions` | array | Список переходов к следующим состояниям | См. ниже |
| `expressions` | array | Список API запросов (обычно один) | См. ниже |
| `initial_state` | boolean | Начальное ли это состояние workflow | `false` |
| `final_state` | boolean | Конечное ли это состояние workflow | `false` |

### Поля Expression

| Поле | Тип | Обязательное | Описание | Пример |
|------|-----|--------------|----------|--------|
| `variable` | string | ✅ Да | Имя переменной для сохранения результата | `"user_profile"` |
| `url` | string | ✅ Да | Полный URL эндпоинта (с протоколом) | `"https://api.example.com/users/123"` |
| `params` | object | ❌ Нет | Параметры запроса (query для GET, body для POST) | `{"user_id": "123"}` |
| `method` | string | ❌ Нет | HTTP метод (по умолчанию `"get"`) | `"get"`, `"post"`, `"put"`, `"delete"`, `"patch"` |

### Поля Transition

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `variable` | string | ✅ Да | Имя переменной из expression |
| `case` | null | ✅ Да | Всегда `null` для integration states |
| `state_id` | string | ✅ Да | Имя следующего состояния |

---

## 🎨 UI/UX для админ-панели

### 1. Форма создания Integration State

#### Базовые поля

```
┌─────────────────────────────────────────────────────────────┐
│ Тип состояния: [Integration State ▼]                        │
├─────────────────────────────────────────────────────────────┤
│ Название состояния *                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ FetchUserProfile                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ 💡 Используйте CamelCase, например: FetchData, GetOrders  │
├─────────────────────────────────────────────────────────────┤
│ Название переменной результата *                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ user_profile                                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│ 💡 Результат API будет сохранен в context[user_profile]   │
├─────────────────────────────────────────────────────────────┤
│ URL эндпоинта *                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ https://api.example.com/users/{{user_id}}              │ │
│ └─────────────────────────────────────────────────────────┘ │
│ 💡 Используйте {{variable}} для подстановки из контекста  │
├─────────────────────────────────────────────────────────────┤
│ HTTP метод                                                  │
│ ⦿ GET  ○ POST  ○ PUT  ○ DELETE  ○ PATCH                   │
├─────────────────────────────────────────────────────────────┤
│ Параметры запроса                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Key             │ Value                    │ [x] [+]    │ │
│ │ user_id         │ {{user_id}}             │             │ │
│ │ include_profile │ true                     │             │ │
│ │ format          │ json                     │             │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [+ Добавить параметр]                                       │
├─────────────────────────────────────────────────────────────┤
│ Следующее состояние *                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ProfileScreen                              ▼            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Продвинутые настройки (опционально, в будущем)

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Дополнительные настройки                                 │
├─────────────────────────────────────────────────────────────┤
│ ☐ Добавить заголовки (Headers)                             │
│   └── Authorization: Bearer {{access_token}}               │
│       Content-Type: application/json                        │
│       [+ Добавить заголовок]                               │
├─────────────────────────────────────────────────────────────┤
│ ☐ Настроить таймаут                                        │
│   └── [30] секунд                                          │
├─────────────────────────────────────────────────────────────┤
│ ☐ Обработка ошибок                                         │
│   └── Переменная для ошибки: [api_error]                  │
│       Состояние при ошибке: [ErrorScreen ▼]               │
├─────────────────────────────────────────────────────────────┤
│ ☐ Кэширование результата                                   │
│   └── Время жизни кэша: [300] секунд (5 минут)           │
└─────────────────────────────────────────────────────────────┘
```

### 2. Визуализация в дереве workflow

```
┌──────────────────────────────────────────────────────┐
│ Workflow: Loan Application                           │
├──────────────────────────────────────────────────────┤
│                                                       │
│  [Screen] LoginScreen                                │
│     ↓ (event: submit)                                │
│  [Technical] ValidateCredentials                     │
│     ↓ (is_valid = True)                              │
│  🌐 [Integration] FetchUserProfile ← ВОТ ОН!         │
│     │ 📡 GET api.example.com/users/{{user_id}}       │
│     │ 💾 Сохраняет в: user_profile                   │
│     ↓ (автоматически)                                │
│  [Screen] DashboardScreen                            │
│     │ 🔍 Использует: {{user_profile.name}}           │
│     ↓ (event: logout)                                │
│  [Technical] Logout                                  │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 3. Подсказки и валидация

#### Валидация URL

```javascript
function validateURL(url) {
  // Проверка формата URL
  const urlPattern = /^https?:\/\/.+/;
  if (!urlPattern.test(url)) {
    return {
      valid: false,
      error: "URL должен начинаться с http:// или https://"
    };
  }
  
  // Предупреждение о небезопасном http
  if (url.startsWith('http://')) {
    return {
      valid: true,
      warning: "⚠️ Используется незащищенный HTTP. Рекомендуется HTTPS"
    };
  }
  
  return { valid: true };
}
```

#### Валидация переменной

```javascript
function validateVariableName(name) {
  // Только буквы, цифры и подчеркивания
  const pattern = /^[a-z_][a-z0-9_]*$/;
  if (!pattern.test(name)) {
    return {
      valid: false,
      error: "Используйте только строчные буквы, цифры и '_'. Начинайте с буквы."
    };
  }
  
  // Проверка зарезервированных имен
  const reserved = ['__workflow_id', '__created_at', 'context', 'session'];
  if (reserved.includes(name)) {
    return {
      valid: false,
      error: `"${name}" - зарезервированное имя. Выберите другое.`
    };
  }
  
  return { valid: true };
}
```

#### Автодополнение для параметров

```javascript
// Подсказка доступных переменных из контекста
function getAvailableVariables(currentState, workflow) {
  const variables = new Set();
  
  // Переменные из predefined_context
  Object.keys(workflow.predefined_context).forEach(v => variables.add(v));
  
  // Переменные из предыдущих состояний
  const previousStates = getStatesBefore(currentState, workflow);
  previousStates.forEach(state => {
    if (state.state_type === 'integration') {
      state.expressions.forEach(expr => variables.add(expr.variable));
    }
    if (state.state_type === 'technical') {
      state.expressions.forEach(expr => variables.add(expr.variable));
    }
  });
  
  return Array.from(variables);
}

// Использование в UI
<input
  type="text"
  value={paramValue}
  onChange={handleChange}
  placeholder="Введите значение или {{переменная}}"
  list="available-variables"
/>
<datalist id="available-variables">
  {availableVariables.map(v => (
    <option key={v} value={`{{${v}}}`}>{v}</option>
  ))}
</datalist>
```

---

## 📝 Примеры для админ-панели

### Пример 1: Простой GET запрос

**Сценарий:** Получить профиль пользователя после логина

```json
{
  "state_type": "integration",
  "name": "FetchUserProfile",
  "transitions": [
    {
      "variable": "user_profile",
      "case": null,
      "state_id": "DashboardScreen"
    }
  ],
  "expressions": [
    {
      "variable": "user_profile",
      "url": "https://api.example.com/users/{{user_id}}",
      "params": {},
      "method": "get"
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

**Инструкция для администратора:**

1. Выберите тип состояния: **Integration State**
2. Название: `FetchUserProfile`
3. Переменная результата: `user_profile`
4. URL: `https://api.example.com/users/{{user_id}}`
5. Метод: **GET**
6. Параметры: оставьте пустыми
7. Следующее состояние: `DashboardScreen`

**Результат:** На экране `DashboardScreen` можно использовать `{{user_profile.name}}`, `{{user_profile.email}}`, и т.д.

---

### Пример 2: POST запрос с параметрами

**Сценарий:** Отправить заявку на кредит

```json
{
  "state_type": "integration",
  "name": "SubmitLoanApplication",
  "transitions": [
    {
      "variable": "application_result",
      "case": null,
      "state_id": "ApplicationStatusScreen"
    }
  ],
  "expressions": [
    {
      "variable": "application_result",
      "url": "https://api.bank.com/applications",
      "params": {
        "user_id": "{{user_id}}",
        "loan_amount": "{{loan_amount}}",
        "term_months": "{{term_months}}",
        "employment_type": "{{employment_type}}",
        "monthly_income": "{{monthly_income}}"
      },
      "method": "post"
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

**Инструкция для администратора:**

1. Выберите тип состояния: **Integration State**
2. Название: `SubmitLoanApplication`
3. Переменная результата: `application_result`
4. URL: `https://api.bank.com/applications`
5. Метод: **POST**
6. Параметры:
   - `user_id` = `{{user_id}}`
   - `loan_amount` = `{{loan_amount}}`
   - `term_months` = `{{term_months}}`
   - `employment_type` = `{{employment_type}}`
   - `monthly_income` = `{{monthly_income}}`
7. Следующее состояние: `ApplicationStatusScreen`

**Результат:** Ответ API сохраняется в `context["application_result"]`, например:
```json
{
  "application_id": "APP-12345",
  "status": "pending",
  "created_at": "2025-10-02T10:00:00Z"
}
```

---

### Пример 3: Получение списка данных

**Сценарий:** Загрузить каталог товаров по категории

```json
{
  "state_type": "integration",
  "name": "FetchProductCatalog",
  "transitions": [
    {
      "variable": "products",
      "case": null,
      "state_id": "CatalogScreen"
    }
  ],
  "expressions": [
    {
      "variable": "products",
      "url": "https://api.shop.com/products",
      "params": {
        "category": "{{selected_category}}",
        "limit": "20",
        "offset": "0",
        "sort": "price_asc"
      },
      "method": "get"
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

**Инструкция для администратора:**

1. Выберите тип состояния: **Integration State**
2. Название: `FetchProductCatalog`
3. Переменная результата: `products`
4. URL: `https://api.shop.com/products`
5. Метод: **GET**
6. Параметры:
   - `category` = `{{selected_category}}` (из предыдущего экрана)
   - `limit` = `20` (константа)
   - `offset` = `0` (константа)
   - `sort` = `price_asc` (константа)
7. Следующее состояние: `CatalogScreen`

**Использование на экране:**
```json
{
  "state_type": "screen",
  "name": "CatalogScreen",
  "screen": {
    "title": "Каталог",
    "components": [
      {
        "type": "list",
        "data": "{{products}}",
        "itemTemplate": {
          "title": "{{item.name}}",
          "price": "{{item.price}} ₽",
          "image": "{{item.image_url}}"
        }
      }
    ]
  }
}
```

---

### Пример 4: Цепочка запросов

**Сценарий:** Сначала получить профиль, потом заказы пользователя

```json
{
  "states": [
    {
      "state_type": "integration",
      "name": "FetchUserProfile",
      "transitions": [
        {
          "variable": "user",
          "case": null,
          "state_id": "FetchUserOrders"
        }
      ],
      "expressions": [
        {
          "variable": "user",
          "url": "https://api.example.com/users/{{user_id}}",
          "params": {},
          "method": "get"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "FetchUserOrders",
      "transitions": [
        {
          "variable": "orders",
          "case": null,
          "state_id": "DashboardScreen"
        }
      ],
      "expressions": [
        {
          "variable": "orders",
          "url": "https://api.example.com/orders",
          "params": {
            "user_id": "{{user.id}}",
            "status": "active"
          },
          "method": "get"
        }
      ]
    },
    {
      "state_type": "screen",
      "name": "DashboardScreen",
      "screen": {
        "title": "Личный кабинет",
        "components": [
          {"type": "text", "content": "Привет, {{user.name}}!"},
          {"type": "text", "content": "У вас {{orders.length}} активных заказов"}
        ]
      }
    }
  ]
}
```

**Инструкция для администратора:**

**Шаг 1: Создать первое integration состояние**
- Название: `FetchUserProfile`
- Переменная: `user`
- URL: `https://api.example.com/users/{{user_id}}`
- Метод: GET
- Следующее состояние: `FetchUserOrders`

**Шаг 2: Создать второе integration состояние**
- Название: `FetchUserOrders`
- Переменная: `orders`
- URL: `https://api.example.com/orders`
- Метод: GET
- Параметры:
  - `user_id` = `{{user.id}}` ⚠️ Обратите внимание: используем данные из первого запроса!
  - `status` = `active`
- Следующее состояние: `DashboardScreen`

**Шаг 3: Создать screen состояние**
- На экране можно использовать и `{{user.*}}`, и `{{orders.*}}`

---

## 🎓 Обучающие материалы для админ-панели

### Встроенная документация

#### 1. Tooltip подсказки

```html
<!-- Поле URL -->
<label>
  URL эндпоинта
  <InfoIcon tooltip="
    Полный URL API эндпоинта с протоколом (https://).
    Можно использовать переменные из контекста: {{user_id}}
    Пример: https://api.example.com/users/{{user_id}}
  " />
</label>

<!-- Поле переменной -->
<label>
  Переменная результата
  <InfoIcon tooltip="
    Имя переменной, в которую будет сохранен результат API.
    Используйте snake_case: user_profile, order_list, credit_score
    Эту переменную можно использовать на следующих экранах через {{variable_name}}
  " />
</label>

<!-- Поле параметров -->
<label>
  Параметры
  <InfoIcon tooltip="
    Для GET - query параметры (?key=value)
    Для POST/PUT/PATCH - тело запроса (JSON)
    Используйте {{}} для подстановки значений из контекста
  " />
</label>
```

#### 2. Примеры в виде шаблонов

```javascript
const integrationTemplates = [
  {
    name: "Получить профиль пользователя",
    description: "Загружает данные пользователя из API",
    template: {
      state_type: "integration",
      name: "FetchUserProfile",
      expressions: [{
        variable: "user_profile",
        url: "https://api.example.com/users/{{user_id}}",
        params: {},
        method: "get"
      }],
      transitions: [{
        variable: "user_profile",
        case: null,
        state_id: ""  // Администратор заполнит
      }]
    }
  },
  {
    name: "Отправить данные формы",
    description: "Отправляет данные на сервер методом POST",
    template: {
      state_type: "integration",
      name: "SubmitForm",
      expressions: [{
        variable: "submit_result",
        url: "https://api.example.com/submit",
        params: {
          // Администратор заполнит
        },
        method: "post"
      }],
      transitions: [{
        variable: "submit_result",
        case: null,
        state_id: ""
      }]
    }
  },
  {
    name: "Загрузить список элементов",
    description: "Получает массив данных (товары, заказы, etc)",
    template: {
      state_type: "integration",
      name: "FetchList",
      expressions: [{
        variable: "items_list",
        url: "https://api.example.com/items",
        params: {
          "limit": "20",
          "offset": "0"
        },
        method: "get"
      }],
      transitions: [{
        variable: "items_list",
        case: null,
        state_id: ""
      }]
    }
  }
];
```

#### 3. Интерактивный туториал

```
┌──────────────────────────────────────────────────────────┐
│ 🎓 Обучение: Создание Integration State                 │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Шаг 1/5: Выберите тип состояния                         │
│ ┌───────────────────────────────────────────────────┐   │
│ │ [Integration State ▼] ✓                           │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ 💡 Integration State загружает данные из внешнего API   │
│    и сохраняет результат в контекст сессии.             │
│                                                           │
│              [Назад]  [Далее →]  [Пропустить]           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 🎓 Обучение: Создание Integration State                 │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Шаг 2/5: Введите название                               │
│ ┌───────────────────────────────────────────────────┐   │
│ │ FetchUserProfile                                   │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ 💡 Используйте понятное имя с глаголом действия:        │
│    • FetchUserProfile - получить профиль                │
│    • SubmitApplication - отправить заявку               │
│    • LoadProductList - загрузить список товаров         │
│                                                           │
│              [← Назад]  [Далее →]  [Пропустить]         │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ 🎓 Обучение: Создание Integration State                 │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Шаг 3/5: Настройте API запрос                           │
│                                                           │
│ URL: ┌────────────────────────────────────────────┐     │
│      │ https://api.example.com/users/{{user_id}} │     │
│      └────────────────────────────────────────────┘     │
│                                                           │
│ Метод: ⦿ GET  ○ POST  ○ PUT  ○ DELETE                  │
│                                                           │
│ 💡 Подсказка:                                            │
│    • Используйте {{переменная}} для подстановки         │
│    • Доступные переменные: user_id, session_id          │
│                                                           │
│              [← Назад]  [Далее →]  [Пропустить]         │
└──────────────────────────────────────────────────────────┘
```

---

## 🔍 Отладка и тестирование в админ-панели

### Функция "Тест API запроса"

```
┌──────────────────────────────────────────────────────────┐
│ 🧪 Тест API запроса                                      │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ URL: https://api.example.com/users/123                   │
│ Метод: GET                                                │
│                                                           │
│ Параметры:                                                │
│ • user_id = 123                                          │
│ • include_profile = true                                 │
│                                                           │
│                    [Выполнить тест]                       │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ Результат:                                                │
│                                                           │
│ ✅ Успешно (200 OK) - 245ms                              │
│                                                           │
│ {                                                         │
│   "id": 123,                                             │
│   "name": "Иван Петров",                                 │
│   "email": "ivan@example.com",                           │
│   "balance": 15000.50                                    │
│ }                                                         │
│                                                           │
│ 💾 Данные будут доступны в следующих состояниях как:    │
│    {{user_profile.id}}                                   │
│    {{user_profile.name}}                                 │
│    {{user_profile.email}}                                │
│    {{user_profile.balance}}                              │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Предпросмотр контекста

```
┌──────────────────────────────────────────────────────────┐
│ 📊 Контекст после выполнения состояния                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Текущее состояние: FetchUserProfile                      │
│                                                           │
│ Доступные переменные:                                    │
│                                                           │
│ ├─ user_id: "123"           (из predefined_context)     │
│ ├─ session_id: "sess_abc"   (из predefined_context)     │
│ └─ user_profile: {           (из Integration State)      │
│      "id": 123,                                          │
│      "name": "Иван Петров",                              │
│      "email": "ivan@example.com",                        │
│      "balance": 15000.50                                 │
│    }                                                      │
│                                                           │
│ 🔍 Эти переменные можно использовать в следующих        │
│    состояниях через синтаксис {{variable_name}}         │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## ⚠️ Частые ошибки и их решения

### Ошибка 1: Неправильный формат URL

```
❌ Неправильно:
   api.example.com/users/123
   www.example.com/api/users
   
✅ Правильно:
   https://api.example.com/users/123
   https://www.example.com/api/users
```

**Решение в UI:**
```javascript
if (!url.match(/^https?:\/\//)) {
  showError("URL должен начинаться с http:// или https://");
}
```

### Ошибка 2: Несуществующая переменная в параметрах

```
❌ Неправильно:
   URL: https://api.example.com/users/{{usr_id}}
   (переменной usr_id нет в контексте)
   
✅ Правильно:
   URL: https://api.example.com/users/{{user_id}}
   (переменная user_id есть в predefined_context)
```

**Решение в UI:**
```javascript
// Подсветка несуществующих переменных
function highlightUndefinedVariables(text, availableVars) {
  const variables = text.match(/\{\{([^}]+)\}\}/g) || [];
  return variables.map(v => {
    const varName = v.replace(/[{}]/g, '');
    if (!availableVars.includes(varName)) {
      return {
        variable: varName,
        error: `Переменная "${varName}" не найдена в контексте`
      };
    }
  }).filter(Boolean);
}
```

### Ошибка 3: Забыли указать transition

```
❌ Неправильно:
   transitions: []  // Пусто!
   
✅ Правильно:
   transitions: [
     {
       "variable": "user_profile",
       "case": null,
       "state_id": "NextScreen"
     }
   ]
```

**Решение в UI:**
```javascript
if (state.transitions.length === 0 && !state.final_state) {
  showError("Необходимо указать хотя бы один переход к следующему состоянию");
}
```

### Ошибка 4: Неправильное использование результата на экране

```
❌ Неправильно (на экране):
   "content": "{{user_profile}}"  // Выведет [object Object]
   
✅ Правильно:
   "content": "{{user_profile.name}}"  // Выведет "Иван Петров"
```

**Решение в UI:**
```javascript
// Предупреждение при попытке вывести объект целиком
if (text.match(/\{\{[^.]+\}\}/)) {
  showWarning(
    "Возможно, вы пытаетесь вывести объект целиком. " +
    "Используйте {{variable.field}} для доступа к полям."
  );
}
```

---

## 🚀 Продвинутые возможности (Roadmap)

### Планируемые улучшения в будущем

#### 1. Заголовки (Headers)

```json
{
  "variable": "protected_data",
  "url": "https://api.example.com/secure",
  "method": "get",
  "headers": {
    "Authorization": "Bearer {{access_token}}",
    "X-API-Key": "{{api_key}}",
    "Content-Type": "application/json"
  }
}
```

**UI:**
```
┌─────────────────────────────────────────────────────────┐
│ 🔐 Заголовки (Headers)                                  │
│ ┌───────────────────────────────────────────────────┐   │
│ │ Заголовок         │ Значение           │ [x] [+]  │   │
│ │ Authorization     │ Bearer {{token}}   │          │   │
│ │ Content-Type      │ application/json   │          │   │
│ └───────────────────────────────────────────────────┘   │
│ [+ Добавить заголовок]                                  │
└─────────────────────────────────────────────────────────┘
```

#### 2. Обработка ошибок

```json
{
  "variable": "api_result",
  "url": "https://api.example.com/data",
  "method": "get",
  "timeout": 30,
  "retry_count": 3,
  "error_variable": "api_error",
  "on_error_state": "ErrorScreen"
}
```

**UI:**
```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Обработка ошибок                                     │
│                                                          │
│ ☑ Сохранить ошибку в переменную                        │
│   Переменная: [api_error___________]                   │
│                                                          │
│ ☑ Перейти к состоянию при ошибке                       │
│   Состояние: [ErrorScreen ▼]                           │
│                                                          │
│ Таймаут: [30] секунд                                    │
│ Повторных попыток: [3]                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 3. Трансформация ответа

```json
{
  "variable": "user_data",
  "url": "https://api.example.com/users/123",
  "method": "get",
  "response_path": "$.data.user",
  "transform": {
    "full_name": "{{firstName}} {{lastName}}",
    "display_balance": "{{balance | format_currency}}"
  }
}
```

**UI:**
```
┌─────────────────────────────────────────────────────────┐
│ 🔄 Трансформация ответа                                 │
│                                                          │
│ JSONPath для извлечения:                                │
│ [$.data.user___________________________________]         │
│ 💡 Пример: $.data.user извлечет только объект user     │
│                                                          │
│ Маппинг полей:                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Новое поле    │ Выражение           │ [x] [+]     │  │
│ │ full_name     │ {{firstName}} {{..  │             │  │
│ │ display_bal.. │ {{balance | forma.. │             │  │
│ └────────────────────────────────────────────────────┘  │
│ [+ Добавить маппинг]                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 4. Кэширование

```json
{
  "variable": "exchange_rates",
  "url": "https://api.exchange.com/rates",
  "method": "get",
  "cache_ttl": 3600,
  "cache_key": "rates_{{date}}"
}
```

**UI:**
```
┌─────────────────────────────────────────────────────────┐
│ 💾 Кэширование                                          │
│                                                          │
│ ☑ Кэшировать результат                                 │
│                                                          │
│   Время жизни: [3600] секунд (1 час)                   │
│                                                          │
│   Ключ кэша: [rates_{{date}}_______________]           │
│   💡 Используйте переменные для уникального ключа      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Чек-лист для разработчиков админ-панели

### Обязательные функции (MVP)

- [ ] Форма создания Integration State
  - [ ] Поле "Название состояния" (валидация: непустое, уникальное)
  - [ ] Поле "Переменная результата" (валидация: snake_case, не зарезервированное)
  - [ ] Поле "URL" (валидация: http/https, формат URL)
  - [ ] Выбор HTTP метода (radio buttons: GET, POST, PUT, DELETE, PATCH)
  - [ ] Таблица параметров (key-value pairs)
  - [ ] Выбор следующего состояния (dropdown)

- [ ] Валидация
  - [ ] Проверка формата URL
  - [ ] Проверка имени переменной
  - [ ] Проверка существования переменных в `{{}}` синтаксисе
  - [ ] Предупреждение о HTTP вместо HTTPS

- [ ] Визуализация
  - [ ] Отображение Integration State в дереве workflow
  - [ ] Иконка для Integration State (🌐 или 📡)
  - [ ] Показ URL и метода в превью

- [ ] Подсказки
  - [ ] Tooltip для каждого поля
  - [ ] Автодополнение для параметров (список доступных переменных)
  - [ ] Примеры в placeholder'ах

### Желательные функции

- [ ] Шаблоны (templates) для быстрого создания
  - [ ] "Получить профиль пользователя"
  - [ ] "Отправить данные формы"
  - [ ] "Загрузить список элементов"

- [ ] Тестирование
  - [ ] Кнопка "Тест API запроса"
  - [ ] Показ результата в JSON формате
  - [ ] Показ времени выполнения
  - [ ] Показ ошибок с деталями

- [ ] Отладка
  - [ ] Предпросмотр контекста после выполнения
  - [ ] Подсветка несуществующих переменных
  - [ ] Показ доступных полей из результата API

- [ ] UX улучшения
  - [ ] Drag & drop для изменения порядка параметров
  - [ ] Копирование состояния
  - [ ] История изменений
  - [ ] Поиск состояний

### Продвинутые функции (будущее)

- [ ] Поддержка заголовков (Headers)
- [ ] Настройка таймаута
- [ ] Настройка retry
- [ ] Обработка ошибок (error_variable, on_error_state)
- [ ] Трансформация ответа (response_path, transform)
- [ ] Кэширование (cache_ttl, cache_key)

---

## 🔗 API Reference для backend

### Эндпоинт сохранения workflow

```
POST /workflow/save
Content-Type: application/json
```

**Request Body:**
```json
{
  "states": [
    {
      "state_type": "integration",
      "name": "FetchUserProfile",
      "transitions": [
        {
          "variable": "user_profile",
          "case": null,
          "state_id": "NextState"
        }
      ],
      "expressions": [
        {
          "variable": "user_profile",
          "url": "https://api.example.com/users/{{user_id}}",
          "params": {},
          "method": "get"
        }
      ],
      "initial_state": false,
      "final_state": false
    }
  ],
  "predefined_context": {
    "user_id": "123"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "wf_description_id": "507f1f77bcf86cd799439011",
  "wf_context_id": "507f1f77bcf86cd799439011",
  "screens_saved": 0
}
```

### Валидация на backend

Backend автоматически валидирует:
- ✅ Формат URL
- ✅ Допустимые HTTP методы
- ✅ Структуру transitions
- ✅ Уникальность имен состояний

---

## 📚 Дополнительные ресурсы

### Связанные документы

- [INTEGRATION_STATES_GUIDE.md](./INTEGRATION_STATES_GUIDE.md) - Техническое руководство для разработчиков backend
- [MOBILE_APP_INTEGRATION_GUIDE.md](./MOBILE_APP_INTEGRATION_GUIDE.md) - Гайд для мобильных разработчиков
- [TECHNICAL_STATES_IMPROVEMENT_PROMPT.md](./TECHNICAL_STATES_IMPROVEMENT_PROMPT.md) - Улучшения technical states

### Примеры workflow

См. `api/testWorkflow.py`:
- `test_workflow_1_simple_login()` - Пример с FetchUserProfile
- `test_workflow_3_complex_loan_application()` - Множественные integration запросы
- `test_workflow()` - Базовый пример

---

## ❓ FAQ для администраторов

**Q: Сколько Integration States можно использовать в одном workflow?**
A: Неограниченное количество. Можно создавать цепочки запросов.

**Q: Можно ли использовать данные из одного Integration State в другом?**
A: Да! Данные накапливаются в контексте. Пример: `{{user.id}}` из первого запроса можно использовать во втором.

**Q: Что делать, если API возвращает ошибку?**
A: Сейчас workflow остановится с ошибкой. В будущих версиях будет обработка ошибок через `error_variable` и `on_error_state`.

**Q: Можно ли отправить файл через Integration State?**
A: Пока нет. Сначала загрузите файл на CDN/S3, затем отправьте URL через Integration State.

**Q: Как передать токен авторизации?**
A: В будущей версии через headers: `"Authorization": "Bearer {{token}}"`. Сейчас можно добавить в params или в URL.

**Q: Поддерживается ли GraphQL?**
A: Нет, только REST API. Для GraphQL используйте POST запрос с query в параметрах.

---

_Последнее обновление: 2 октября 2025 г._

---

## 🎯 Резюме для Product Manager

### Что такое Integration States в двух словах

**Integration States** - это "умные" состояния workflow, которые автоматически загружают данные из внешних API и делают их доступными для всех последующих экранов. Это позволяет создавать динамические workflow без программирования.

### Ключевые преимущества

1. **Zero code** - администратор создает интеграцию через UI
2. **Переиспользование данных** - один запрос, данные доступны везде
3. **Гибкость** - любые REST API поддерживаются
4. **Безопасность** - данные хранятся в защищенной сессии

### Что нужно для запуска MVP

1. Форма создания Integration State (3-5 полей)
2. Базовая валидация (URL, имя переменной)
3. Отображение в дереве workflow
4. Документация для администраторов

**Оценка:** 2-3 недели разработки для MVP

### Roadmap улучшений

- **Q1 2026:** Headers, Error handling
- **Q2 2026:** Caching, Response transformation
- **Q3 2026:** GraphQL support, File uploads
