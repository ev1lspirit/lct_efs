# Исправление ошибки Expression.integration() - body parameter

## 🐛 Проблема #2

После исправления Pydantic моделей возникла новая ошибка:

```
TypeError: Expression.integration() got an unexpected keyword argument 'body'
```

**Причина:** Метод `Expression.integration()` и класс `IntegrationStateExpression` не были обновлены для поддержки нового параметра `body`.

## ✅ Решение

### 1. Обновление метода Expression.integration()

**Файл:** `workflow_builder/expressions.py`

**Было:**
```python
@classmethod
def integration(
    cls,
    *,
    variable: str,
    url: str,
    params: dict[str, Any],  # ❌ Обязательный параметр
    method: str = "get",
    dependent_variables: list[str] = None,
    error_variable: str = None
) -> "IntegrationStateExpression":
    return IntegrationStateExpression(
        variable=variable,
        url=url,
        params=params,
        method=method,
        dependent_variables=dependent_variables or [],
        error_variable=error_variable
    )
```

**Стало:**
```python
@classmethod
def integration(
    cls,
    *,
    variable: str,
    url: str,
    params: dict[str, Any] = None,  # ✅ Опциональный
    body: dict[str, Any] = None,    # ✅ Новый параметр
    method: str = "get",
    dependent_variables: list[str] = None,
    error_variable: str = None
) -> "IntegrationStateExpression":
    return IntegrationStateExpression(
        variable=variable,
        url=url,
        params=params,
        body=body,  # ✅ Передаём body
        method=method,
        dependent_variables=dependent_variables or [],
        error_variable=error_variable
    )
```

### 2. Обновление класса IntegrationStateExpression

**Файл:** `workflow_builder/expressions.py`

**Было:**
```python
variable: str = field(validator=validators.instance_of(str))
url: str = field(validator=validators.instance_of(str))
params: dict[str, Any] = field(
    factory=dict, validator=validators.instance_of(dict)
)  # query or body params
method: str = field(...)
dependent_variables: list[str] = field(...)
error_variable: Optional[str] = field(...)
```

**Стало:**
```python
variable: str = field(validator=validators.instance_of(str))
url: str = field(validator=validators.instance_of(str))
params: Optional[dict[str, Any]] = field(
    default=None, validator=validators.optional(validators.instance_of(dict))
)  # ✅ query params для GET/DELETE
body: Optional[dict[str, Any]] = field(
    default=None, validator=validators.optional(validators.instance_of(dict))
)  # ✅ body params для POST/PUT/PATCH
method: str = field(...)
dependent_variables: list[str] = field(...)
error_variable: Optional[str] = field(...)
```

### 3. Обновление IntegrationHandler

**Файл:** `workflow_builder/handlers.py`

**Было:**
```python
base_url, endpoint = self._split_url(interpolated_url)

# Интерполируем params перед отправкой запроса
interpolated_params = self._interpolate_params(self.metadata.params)

logger.info(f"Integration request: {self.metadata.method.upper()} {interpolated_url}")
logger.debug(f"Original params: {self.metadata.params}")
logger.debug(f"Interpolated params: {interpolated_params}")

adapter = self.adapter(base_url=base_url)
method_attr = self._get_method(adapter)
response = method_attr(endpoint=endpoint, params=interpolated_params)
```

**Стало:**
```python
base_url, endpoint = self._split_url(interpolated_url)

# Интерполируем params или body в зависимости от метода
method = self.metadata.method.lower()
if method in ['post', 'put', 'patch']:
    # POST/PUT/PATCH используют body
    params_to_use = self.metadata.body or {}
    interpolated_params = self._interpolate_params(params_to_use)
    logger.info(f"Integration request: {self.metadata.method.upper()} {interpolated_url}")
    logger.debug(f"Original body: {self.metadata.body}")
    logger.debug(f"Interpolated body: {interpolated_params}")
else:
    # GET/DELETE используют params
    params_to_use = self.metadata.params or {}
    interpolated_params = self._interpolate_params(params_to_use)
    logger.info(f"Integration request: {self.metadata.method.upper()} {interpolated_url}")
    logger.debug(f"Original params: {self.metadata.params}")
    logger.debug(f"Interpolated params: {interpolated_params}")

adapter = self.adapter(base_url=base_url)
method_attr = self._get_method(adapter)
response = method_attr(endpoint=endpoint, params=interpolated_params)
```

## 📊 Результаты тестирования

### 1. Тест парсинга Pydantic моделей

```bash
python3 test_fixed_workflow.py
```

**Результат:**
```
✅ Все 37 states успешно распарсены!

📊 Найдено 9 integration expressions:
   POST/PUT/PATCH с body: 2
   GET/DELETE с params: 7
```

### 2. Тест клиентского endpoint

```bash
python3 test_client_endpoint.py
```

**Результат:**
```
✅ Workflow успешно инициализирован!
📊 Данные workflow:
   Current State: CartOverviewScreen
   Context Variables: 43 переменных
```

### 3. Проверка логов

```bash
tail -100 server.log | grep ERROR
```

**Результат:** ✅ Ошибок не найдено

## 🎯 Что исправлено

### Уровень 1: Pydantic модели (contract.py)
- ✅ `IntegrationExpressionModel` поддерживает `params` и `body`
- ✅ Добавлен валидатор `@model_validator` для проверки формата

### Уровень 2: Expression builder (expressions.py)
- ✅ Метод `Expression.integration()` принимает параметр `body`
- ✅ Класс `IntegrationStateExpression` имеет поля `params` и `body`
- ✅ Оба поля опциональные с правильными валидаторами

### Уровень 3: Runtime handler (handlers.py)
- ✅ `IntegrationHandler` различает GET/DELETE (params) и POST/PUT/PATCH (body)
- ✅ Логирование отображает правильные параметры в зависимости от метода

## 🚀 Статус

- ✅ Pydantic модели обновлены
- ✅ Expression builder обновлён
- ✅ Integration handler обновлён
- ✅ Workflow успешно парсится (37/37 states)
- ✅ Workflow успешно инициализируется через API
- ✅ POST запросы используют `body`
- ✅ GET запросы используют `params`
- ✅ Сервер работает без ошибок

## 📝 Workflow ID

**ID сохранённого workflow:** `68ded7589d42ce73ba2d7092`

## 📁 Созданные тесты

1. `test_fixed_workflow.py` - Тест парсинга Pydantic моделей
2. `test_client_endpoint.py` - Тест клиентского endpoint

## ✨ Полная цепочка исправлений

1. **Проблема #1:** Pydantic модели требовали обязательное поле `params`
   - **Решение:** Обновлена `IntegrationExpressionModel` в `contract.py`
   
2. **Проблема #2:** `Expression.integration()` не принимал параметр `body`
   - **Решение:** Обновлены `Expression.integration()` и `IntegrationStateExpression` в `expressions.py`
   
3. **Проблема #3:** `IntegrationHandler` не различал params/body
   - **Решение:** Обновлён метод `result()` в `handlers.py`

Все три уровня работают согласованно! 🎉
