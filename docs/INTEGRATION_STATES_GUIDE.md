# Руководство: Integration States - Загрузка данных из API в контекст

## 📋 Обзор

**Integration States** (состояния интеграции) - это специальный тип состояний в workflow, который позволяет:

✅ **Получать данные из внешних API**  
✅ **Автоматически сохранять результат в контекст сессии**  
✅ **Использовать данные на следующих экранах**  
✅ **Поддерживать все HTTP методы** (GET, POST, PUT, DELETE, PATCH)

---

## 🏗️ Текущая архитектура

### Существующая реализация

**Файл:** `workflow_builder/expressions.py`

```python
@define(slots=True)
class IntegrationStateExpression(BaseStateExpression):
    variable: str              # Имя переменной для сохранения результата
    url: str                   # Полный URL эндпоинта
    params: dict[str, Any]     # Параметры запроса (query/body)
    method: str                # HTTP метод: get, post, put, delete, patch
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.integration
```

**Файл:** `workflow_builder/handlers.py`

```python
@define(slots=True)
class IntegrationHandler(BaseHandler):
    adapter: Any               # CommonAdapter для HTTP запросов
    metadata: "IntegrationStateExpression"
    context: "SessionContext"
    
    @check_context_consistency
    def result(self):
        base_url, endpoint = self._split_url()
        adapter = self.adapter(base_url=base_url)
        method_attr = self._get_method(adapter)
        response = method_attr(endpoint=endpoint, params=self.metadata.params)
        return response  # Результат автоматически сохраняется в context[variable]
```

---

## 📝 Базовые примеры использования

### Пример 1: Получение профиля пользователя (GET)

```json
{
  "state_type": "integration",
  "name": "FetchUserProfile",
  "transitions": [
    {
      "variable": "user_profile",
      "case": null,
      "state_id": "ProfileScreen"
    }
  ],
  "expressions": [
    {
      "variable": "user_profile",
      "url": "https://api.example.com/users/123",
      "params": {},
      "method": "get"
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

**Что происходит:**
1. Отправляется `GET https://api.example.com/users/123`
2. Ответ API сохраняется в `context["user_profile"]`
3. Переход к `ProfileScreen`, где данные доступны

**Использование на экране:**

```json
{
  "state_type": "screen",
  "name": "ProfileScreen",
  "screen": {
    "title": "Профиль",
    "components": [
      {
        "type": "text",
        "content": "Имя: {{user_profile.name}}"
      },
      {
        "type": "text",
        "content": "Email: {{user_profile.email}}"
      },
      {
        "type": "text",
        "content": "Баланс: {{user_profile.balance}} ₽"
      }
    ]
  }
}
```

### Пример 2: Отправка данных (POST)

```json
{
  "state_type": "integration",
  "name": "SubmitApplication",
  "transitions": [
    {
      "variable": "application_result",
      "case": null,
      "state_id": "CheckApplicationStatus"
    }
  ],
  "expressions": [
    {
      "variable": "application_result",
      "url": "https://api.example.com/applications",
      "params": {
        "user_id": "{{user_id}}",
        "loan_amount": "{{loan_amount}}",
        "employment_type": "{{employment_type}}"
      },
      "method": "post"
    }
  ],
  "initial_state": false,
  "final_state": false
}
```

**Интерполяция переменных:**
- `{{user_id}}` заменится на значение из `context["user_id"]`
- `{{loan_amount}}` → `context["loan_amount"]`
- Результат запроса → `context["application_result"]`

### Пример 3: Получение списка данных

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
      "url": "https://api.example.com/products",
      "params": {
        "category": "{{selected_category}}",
        "limit": 20,
        "offset": 0
      },
      "method": "get"
    }
  ]
}
```

**Использование списка на экране:**

```json
{
  "state_type": "screen",
  "name": "CatalogScreen",
  "screen": {
    "title": "Каталог товаров",
    "components": [
      {
        "type": "list",
        "data": "{{products}}",
        "itemTemplate": {
          "title": "{{item.name}}",
          "subtitle": "{{item.price}} ₽",
          "image": "{{item.image_url}}",
          "action": {
            "event": "select_product",
            "params": {"product_id": "{{item.id}}"}
          }
        }
      }
    ]
  }
}
```

---

## 🚀 Улучшенная версия Integration States

### Предлагаемые улучшения

#### 1. **Добавить заголовки (Headers)**

```python
@define(slots=True)
class IntegrationStateExpression(BaseStateExpression):
    variable: str
    url: str
    params: dict[str, Any] = field(factory=dict)
    method: str = field(default="get")
    headers: dict[str, str] = field(factory=dict)  # NEW: Заголовки запроса
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.integration
```

**Пример использования:**

```json
{
  "variable": "protected_data",
  "url": "https://api.example.com/secure/data",
  "params": {},
  "method": "get",
  "headers": {
    "Authorization": "Bearer {{access_token}}",
    "X-API-Key": "{{api_key}}",
    "Content-Type": "application/json"
  }
}
```

#### 2. **Добавить обработку ошибок**

```python
@define(slots=True)
class IntegrationStateExpression(BaseStateExpression):
    variable: str
    url: str
    params: dict[str, Any] = field(factory=dict)
    method: str = field(default="get")
    headers: dict[str, str] = field(factory=dict)
    timeout: int = field(default=30)                    # NEW: Таймаут в секундах
    retry_count: int = field(default=0)                 # NEW: Количество повторов
    on_error: Optional[str] = field(default=None)       # NEW: Состояние при ошибке
    error_variable: Optional[str] = field(default=None) # NEW: Переменная для ошибки
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.integration
```

**Пример с обработкой ошибок:**

```json
{
  "state_type": "integration",
  "name": "FetchCreditScore",
  "transitions": [
    {
      "variable": "credit_score",
      "case": null,
      "state_id": "ScoreLoadedScreen"
    },
    {
      "variable": "api_error",
      "case": "not_null",
      "state_id": "ErrorScreen"
    }
  ],
  "expressions": [
    {
      "variable": "credit_score",
      "url": "https://api.creditbureau.com/score/{{user_id}}",
      "params": {},
      "method": "get",
      "headers": {
        "Authorization": "Bearer {{access_token}}"
      },
      "timeout": 15,
      "retry_count": 3,
      "error_variable": "api_error"
    }
  ]
}
```

#### 3. **Добавить трансформацию ответа**

```python
@define(slots=True)
class IntegrationStateExpression(BaseStateExpression):
    variable: str
    url: str
    params: dict[str, Any] = field(factory=dict)
    method: str = field(default="get")
    headers: dict[str, str] = field(factory=dict)
    timeout: int = field(default=30)
    retry_count: int = field(default=0)
    response_path: Optional[str] = field(default=None)  # NEW: JSONPath для извлечения
    transform: Optional[dict] = field(default=None)     # NEW: Маппинг полей
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.integration
```

**Пример с трансформацией:**

```json
{
  "variable": "user_data",
  "url": "https://api.example.com/users/123",
  "method": "get",
  "response_path": "$.data.user",
  "transform": {
    "full_name": "{{firstName}} {{lastName}}",
    "age": "{{birthYear | calculate_age}}",
    "display_balance": "{{balance | format_currency}}"
  }
}
```

**API Response:**
```json
{
  "status": "success",
  "data": {
    "user": {
      "firstName": "Иван",
      "lastName": "Петров",
      "birthYear": 1990,
      "balance": 15000.50
    }
  }
}
```

**Результат в context:**
```json
{
  "user_data": {
    "full_name": "Иван Петров",
    "age": 35,
    "display_balance": "15 000,50 ₽"
  }
}
```

#### 4. **Добавить кэширование**

```python
@define(slots=True)
class IntegrationStateExpression(BaseStateExpression):
    variable: str
    url: str
    params: dict[str, Any] = field(factory=dict)
    method: str = field(default="get")
    cache_ttl: Optional[int] = field(default=None)      # NEW: TTL кэша в секундах
    cache_key: Optional[str] = field(default=None)      # NEW: Ключ кэша
    type_: ClassVar[StateTypeEnum] = StateTypeEnum.integration
```

**Пример с кэшированием:**

```json
{
  "variable": "exchange_rates",
  "url": "https://api.exchangerate.com/latest",
  "method": "get",
  "cache_ttl": 3600,
  "cache_key": "exchange_rates_{{date}}"
}
```

**Логика кэширования в IntegrationHandler:**

```python
@check_context_consistency
def result(self):
    # Проверяем кэш
    if self.metadata.cache_ttl and self.metadata.cache_key:
        cache_key = self._interpolate(self.metadata.cache_key)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for {cache_key}")
            return cached_result
    
    # Выполняем запрос
    base_url, endpoint = self._split_url()
    adapter = self.adapter(base_url=base_url)
    method_attr = self._get_method(adapter)
    
    # Интерполируем параметры
    interpolated_params = self._interpolate_params(self.metadata.params)
    
    response = method_attr(
        endpoint=endpoint,
        params=interpolated_params,
        headers=self.metadata.headers,
        timeout=self.metadata.timeout
    )
    
    # Сохраняем в кэш
    if self.metadata.cache_ttl and self.metadata.cache_key:
        cache_key = self._interpolate(self.metadata.cache_key)
        self._save_to_cache(cache_key, response, self.metadata.cache_ttl)
    
    return response
```

---

## 🎯 Продвинутые сценарии

### Сценарий 1: Цепочка запросов

```json
{
  "states": [
    {
      "state_type": "integration",
      "name": "GetUserProfile",
      "transitions": [
        {"variable": "user", "case": null, "state_id": "GetUserOrders"}
      ],
      "expressions": [
        {
          "variable": "user",
          "url": "https://api.example.com/users/{{user_id}}",
          "method": "get"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "GetUserOrders",
      "transitions": [
        {"variable": "orders", "case": null, "state_id": "GetOrderDetails"}
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
      "state_type": "integration",
      "name": "GetOrderDetails",
      "transitions": [
        {"variable": "order_details", "case": null, "state_id": "DashboardScreen"}
      ],
      "expressions": [
        {
          "variable": "order_details",
          "url": "https://api.example.com/orders/{{orders[0].id}}/details",
          "method": "get"
        }
      ]
    },
    {
      "state_type": "screen",
      "name": "DashboardScreen",
      "screen": {
        "title": "Дашборд",
        "components": [
          {"type": "text", "content": "Пользователь: {{user.name}}"},
          {"type": "text", "content": "Активных заказов: {{orders | length}}"},
          {"type": "text", "content": "Детали заказа: {{order_details.status}}"}
        ]
      }
    }
  ]
}
```

### Сценарий 2: Условный запрос на основе данных

```json
{
  "states": [
    {
      "state_type": "technical",
      "name": "CheckUserType",
      "transitions": [
        {"variable": "is_premium", "case": "True", "state_id": "FetchPremiumData"},
        {"variable": "is_premium", "case": "False", "state_id": "FetchBasicData"}
      ],
      "expressions": [
        {
          "variable": "is_premium",
          "dependent_variables": ["user_subscription"],
          "expression": "user_subscription == 'premium'"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "FetchPremiumData",
      "transitions": [
        {"variable": "premium_content", "case": null, "state_id": "ContentScreen"}
      ],
      "expressions": [
        {
          "variable": "premium_content",
          "url": "https://api.example.com/premium/content",
          "params": {"user_id": "{{user_id}}"},
          "method": "get"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "FetchBasicData",
      "transitions": [
        {"variable": "basic_content", "case": null, "state_id": "ContentScreen"}
      ],
      "expressions": [
        {
          "variable": "basic_content",
          "url": "https://api.example.com/basic/content",
          "params": {"user_id": "{{user_id}}"},
          "method": "get"
        }
      ]
    }
  ]
}
```

### Сценарий 3: Параллельные запросы (с technical state)

```json
{
  "states": [
    {
      "state_type": "integration",
      "name": "FetchUserData",
      "transitions": [
        {"variable": "user", "case": null, "state_id": "FetchNotifications"}
      ],
      "expressions": [
        {
          "variable": "user",
          "url": "https://api.example.com/users/{{user_id}}",
          "method": "get",
          "cache_ttl": 300
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "FetchNotifications",
      "transitions": [
        {"variable": "notifications", "case": null, "state_id": "FetchBalance"}
      ],
      "expressions": [
        {
          "variable": "notifications",
          "url": "https://api.example.com/notifications",
          "params": {"user_id": "{{user_id}}", "unread_only": true},
          "method": "get"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "FetchBalance",
      "transitions": [
        {"variable": "balance", "case": null, "state_id": "CheckDataLoaded"}
      ],
      "expressions": [
        {
          "variable": "balance",
          "url": "https://api.example.com/balance/{{user_id}}",
          "method": "get"
        }
      ]
    },
    {
      "state_type": "technical",
      "name": "CheckDataLoaded",
      "transitions": [
        {"variable": "all_loaded", "case": "True", "state_id": "DashboardScreen"}
      ],
      "expressions": [
        {
          "variable": "all_loaded",
          "dependent_variables": ["user", "notifications", "balance"],
          "expression": "is_not_none(user) and is_not_none(notifications) and is_not_none(balance)"
        }
      ]
    }
  ]
}
```

### Сценарий 4: Пагинация

```json
{
  "states": [
    {
      "state_type": "screen",
      "name": "ProductListScreen",
      "screen": {
        "title": "Товары",
        "components": [
          {
            "type": "list",
            "data": "{{products.items}}",
            "itemTemplate": {
              "title": "{{item.name}}",
              "price": "{{item.price}} ₽"
            }
          },
          {
            "type": "pagination",
            "current_page": "{{products.current_page}}",
            "total_pages": "{{products.total_pages}}",
            "has_next": "{{products.has_next}}"
          }
        ],
        "buttons": [
          {
            "id": "next_page",
            "label": "Следующая страница",
            "event": "load_next_page",
            "enabled": "{{products.has_next}}"
          }
        ]
      },
      "transitions": [
        {"case": "load_next_page", "state_id": "LoadNextPage"}
      ],
      "expressions": [
        {"event_name": "load_next_page"}
      ]
    },
    {
      "state_type": "technical",
      "name": "IncrementPage",
      "transitions": [
        {"variable": "next_page", "case": null, "state_id": "LoadNextPage"}
      ],
      "expressions": [
        {
          "variable": "next_page",
          "dependent_variables": ["current_page"],
          "expression": "current_page + 1"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "LoadNextPage",
      "transitions": [
        {"variable": "products", "case": null, "state_id": "ProductListScreen"}
      ],
      "expressions": [
        {
          "variable": "products",
          "url": "https://api.example.com/products",
          "params": {
            "page": "{{next_page}}",
            "limit": 20,
            "category": "{{selected_category}}"
          },
          "method": "get"
        }
      ]
    }
  ]
}
```

---

## 🔒 Безопасность и Best Practices

### 1. Защита токенов

```json
{
  "state_type": "integration",
  "name": "SecureAPICall",
  "expressions": [
    {
      "variable": "protected_data",
      "url": "https://api.example.com/secure",
      "method": "get",
      "headers": {
        "Authorization": "Bearer {{access_token}}"
      }
    }
  ]
}
```

**⚠️ Важно:** Не храните токены в `predefined_context`. Получайте их через отдельный authentication flow.

### 2. Валидация данных перед запросом

```json
{
  "states": [
    {
      "state_type": "technical",
      "name": "ValidateInput",
      "transitions": [
        {"variable": "input_valid", "case": "True", "state_id": "SendDataToAPI"},
        {"variable": "input_valid", "case": "False", "state_id": "ErrorScreen"}
      ],
      "expressions": [
        {
          "variable": "input_valid",
          "dependent_variables": ["email", "phone", "amount"],
          "expression": "len(email) > 0 and len(phone) == 11 and amount > 0"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "SendDataToAPI",
      "expressions": [
        {
          "variable": "api_response",
          "url": "https://api.example.com/submit",
          "params": {
            "email": "{{email}}",
            "phone": "{{phone}}",
            "amount": "{{amount}}"
          },
          "method": "post"
        }
      ]
    }
  ]
}
```

### 3. Обработка ошибок API

```python
# В IntegrationHandler
@check_context_consistency
def result(self):
    try:
        base_url, endpoint = self._split_url()
        adapter = self.adapter(base_url=base_url)
        method_attr = self._get_method(adapter)
        
        response = method_attr(
            endpoint=endpoint,
            params=self.metadata.params,
            headers=self.metadata.headers,
            timeout=self.metadata.timeout
        )
        
        # Сохраняем успешный результат
        return response
        
    except RequestException as e:
        logger.error(f"API request failed: {e}", exc_info=True)
        
        # Если указана переменная для ошибки
        if self.metadata.error_variable:
            error_data = {
                "error": True,
                "message": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }
            with self.context as ctx:
                ctx[self.metadata.error_variable] = error_data
        
        # Возвращаем None или default значение
        return self.metadata.get('default_value', None)
```

### 4. Rate Limiting

```python
# Добавить в IntegrationHandler
from time import sleep
from collections import defaultdict

class IntegrationHandler(BaseHandler):
    _request_timestamps = defaultdict(list)
    
    def _check_rate_limit(self, url: str, max_requests: int = 10, window: int = 60):
        """Проверка rate limit (10 запросов в минуту)"""
        now = time.time()
        timestamps = self._request_timestamps[url]
        
        # Убираем старые timestamps
        timestamps = [ts for ts in timestamps if now - ts < window]
        
        if len(timestamps) >= max_requests:
            sleep_time = window - (now - timestamps[0])
            logger.warning(f"Rate limit hit for {url}, sleeping {sleep_time}s")
            sleep(sleep_time)
        
        timestamps.append(now)
        self._request_timestamps[url] = timestamps
```

---

## 📊 Мониторинг и отладка

### Логирование API запросов

```python
class IntegrationHandler(BaseHandler):
    @check_context_consistency
    def result(self):
        start_time = time.time()
        
        logger.info(
            f"Integration API call starting",
            extra={
                "url": self.metadata.url,
                "method": self.metadata.method,
                "params": self.metadata.params,
                "variable": self.metadata.variable
            }
        )
        
        try:
            response = self._execute_request()
            
            duration = time.time() - start_time
            logger.info(
                f"Integration API call successful",
                extra={
                    "url": self.metadata.url,
                    "method": self.metadata.method,
                    "duration_ms": duration * 1000,
                    "response_size": len(str(response)),
                    "variable": self.metadata.variable
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Integration API call failed",
                extra={
                    "url": self.metadata.url,
                    "method": self.metadata.method,
                    "duration_ms": duration * 1000,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
```

### Отладочный эндпоинт

```python
# В api/routes.py
@router.post("/debug/integration-test")
async def test_integration(
    url: str,
    method: str = "get",
    params: dict = {},
    headers: dict = {}
) -> dict:
    """
    Тестирование integration запроса без создания workflow
    """
    try:
        from adapters.commonAdapter import CommonAdapter
        
        adapter = CommonAdapter(base_url=url)
        method_fn = getattr(adapter, method.lower())
        
        response = method_fn(endpoint="", params=params, headers=headers)
        
        return {
            "success": True,
            "data": response,
            "type": type(response).__name__
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

---

## 🧪 Тестирование

### Пример workflow для теста

```python
def test_integration_workflow():
    """Тест workflow с integration состояниями"""
    test_json = {
        "states": [
            {
                "state_type": "integration",
                "name": "FetchData",
                "transitions": [
                    {"variable": "api_data", "case": null, "state_id": "DisplayData"}
                ],
                "expressions": [
                    {
                        "variable": "api_data",
                        "url": "https://jsonplaceholder.typicode.com/users/1",
                        "params": {},
                        "method": "get"
                    }
                ],
                "initial_state": True,
                "final_state": False
            },
            {
                "state_type": "screen",
                "name": "DisplayData",
                "screen": {
                    "title": "User Data",
                    "components": [
                        {"type": "text", "content": "Name: {{api_data.name}}"},
                        {"type": "text", "content": "Email: {{api_data.email}}"}
                    ]
                },
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True
            }
        ]
    }
    return test_json
```

### Мок для тестирования

```python
from unittest.mock import Mock, patch

def test_integration_handler():
    # Mock adapter
    mock_adapter = Mock()
    mock_adapter.get = Mock(return_value={"id": 1, "name": "John"})
    
    # Create handler
    handler = IntegrationHandler(
        adapter=lambda base_url: mock_adapter,
        metadata=IntegrationStateExpression(
            variable="user",
            url="https://api.example.com/users/1",
            params={},
            method="get"
        ),
        context=SessionContext(session={}, workflow_id="test")
    )
    
    # Execute
    result = handler.result()
    
    # Assert
    assert result == {"id": 1, "name": "John"}
    mock_adapter.get.assert_called_once()
```

---

## 📦 Полный пример: Кредитная заявка

```json
{
  "states": [
    {
      "state_type": "screen",
      "name": "ApplicationFormScreen",
      "screen": {
        "title": "Заявка на кредит",
        "fields": [
          {"id": "amount", "type": "number", "label": "Сумма кредита"},
          {"id": "term_months", "type": "number", "label": "Срок (месяцев)"},
          {"id": "income", "type": "number", "label": "Ежемесячный доход"}
        ],
        "buttons": [
          {"id": "submit", "label": "Отправить", "event": "submit"}
        ]
      },
      "transitions": [
        {"case": "submit", "state_id": "ValidateInput"}
      ],
      "expressions": [
        {"event_name": "submit"}
      ],
      "initial_state": true,
      "final_state": false
    },
    {
      "state_type": "technical",
      "name": "ValidateInput",
      "transitions": [
        {"variable": "input_valid", "case": "True", "state_id": "FetchCreditScore"},
        {"variable": "input_valid", "case": "False", "state_id": "ApplicationFormScreen"}
      ],
      "expressions": [
        {
          "variable": "input_valid",
          "dependent_variables": ["amount", "term_months", "income"],
          "expression": "amount > 0 and amount <= 5000000 and term_months >= 6 and term_months <= 60 and income > 0"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "FetchCreditScore",
      "transitions": [
        {"variable": "credit_score", "case": null, "state_id": "CheckEligibility"}
      ],
      "expressions": [
        {
          "variable": "credit_score",
          "url": "https://api.creditbureau.com/score",
          "params": {
            "user_id": "{{user_id}}",
            "include_history": true
          },
          "method": "get",
          "headers": {
            "Authorization": "Bearer {{api_token}}"
          },
          "timeout": 15,
          "cache_ttl": 300,
          "error_variable": "credit_score_error"
        }
      ]
    },
    {
      "state_type": "technical",
      "name": "CheckEligibility",
      "transitions": [
        {"variable": "is_eligible", "case": "True", "state_id": "SubmitApplication"},
        {"variable": "is_eligible", "case": "False", "state_id": "RejectionScreen"}
      ],
      "expressions": [
        {
          "variable": "is_eligible",
          "dependent_variables": ["credit_score", "income", "amount"],
          "expression": "credit_score.score >= 600 and income >= amount / term_months * 0.3"
        }
      ]
    },
    {
      "state_type": "integration",
      "name": "SubmitApplication",
      "transitions": [
        {"variable": "application", "case": null, "state_id": "ApprovalScreen"}
      ],
      "expressions": [
        {
          "variable": "application",
          "url": "https://api.bank.com/applications",
          "params": {
            "user_id": "{{user_id}}",
            "amount": "{{amount}}",
            "term_months": "{{term_months}}",
            "income": "{{income}}",
            "credit_score": "{{credit_score.score}}"
          },
          "method": "post",
          "headers": {
            "Authorization": "Bearer {{api_token}}",
            "Content-Type": "application/json"
          }
        }
      ]
    },
    {
      "state_type": "screen",
      "name": "ApprovalScreen",
      "screen": {
        "title": "Заявка одобрена!",
        "components": [
          {"type": "text", "content": "Номер заявки: {{application.id}}"},
          {"type": "text", "content": "Сумма: {{application.amount}} ₽"},
          {"type": "text", "content": "Ставка: {{application.interest_rate}}%"},
          {"type": "text", "content": "Ежемесячный платеж: {{application.monthly_payment}} ₽"}
        ],
        "buttons": [
          {"id": "accept", "label": "Принять", "event": "accept"}
        ]
      },
      "transitions": [],
      "expressions": [],
      "initial_state": false,
      "final_state": true
    },
    {
      "state_type": "screen",
      "name": "RejectionScreen",
      "screen": {
        "title": "К сожалению, заявка отклонена",
        "components": [
          {"type": "text", "content": "Ваш кредитный рейтинг: {{credit_score.score}}"},
          {"type": "text", "content": "Причина: недостаточный доход или низкий кредитный рейтинг"}
        ]
      },
      "transitions": [],
      "expressions": [],
      "initial_state": false,
      "final_state": true
    }
  ],
  "predefined_context": {
    "api_token": "secret_token_here"
  }
}
```

---

## ✅ Чек-лист реализации улучшений

### Базовые возможности (уже реализовано)
- [x] GET запросы
- [x] POST запросы
- [x] PUT, DELETE, PATCH запросы
- [x] Параметры запроса (params)
- [x] Автоматическое сохранение в контекст

### Улучшения (предлагаемые)
- [ ] Добавить поддержку headers
- [ ] Добавить timeout для запросов
- [ ] Добавить retry_count
- [ ] Добавить error_variable
- [ ] Добавить on_error состояние
- [ ] Добавить response_path (JSONPath)
- [ ] Добавить transform (маппинг полей)
- [ ] Добавить cache_ttl и cache_key
- [ ] Добавить rate limiting
- [ ] Улучшить логирование
- [ ] Добавить отладочный эндпоинт
- [ ] Написать unit тесты

---

## 🔗 Связанные файлы

- `workflow_builder/handlers.py` - IntegrationHandler
- `workflow_builder/expressions.py` - IntegrationStateExpression
- `workflow_builder/state_parser/contract.py` - IntegrationExpressionModel
- `adapters/commonAdapter.py` - HTTP клиент
- `api/testWorkflow.py` - Примеры integration workflows

---

## 📞 Дополнительная информация

### Связанные документы
- [TECHNICAL_STATES_IMPROVEMENT_PROMPT.md](./TECHNICAL_STATES_IMPROVEMENT_PROMPT.md) - Улучшения technical states
- [MOBILE_APP_INTEGRATION_GUIDE.md](./MOBILE_APP_INTEGRATION_GUIDE.md) - Интеграция мобильного приложения

### Примеры использования
См. `api/testWorkflow.py`:
- `test_workflow_1_simple_login()` - Integration с FetchUserProfile
- `test_workflow_3_complex_loan_application()` - Множественные integration запросы
- `test_workflow()` - Базовый пример с FetchExternalData

---

_Последнее обновление: 2 октября 2025 г._
