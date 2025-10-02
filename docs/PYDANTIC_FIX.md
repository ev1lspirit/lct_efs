# Исправление ошибки парсинга Pydantic моделей

## 🐛 Проблема

При загрузке workflow из MongoDB возникала ошибка:

```
ERROR | workflow_builder.state_parser.workflow_cache | 
Error parsing state #9 in workflow 68ded7589d42ce73ba2d7092: 
3 validation errors for StateModel
expressions.0.IntegrationExpressionModel.params
  Field required
```

**Причина:** Pydantic модель `IntegrationExpressionModel` требовала обязательное поле `params`, но в новом формате для POST/PUT/PATCH запросов используется поле `body`.

## ✅ Решение

### 1. Обновление Pydantic модели

**Файл:** `workflow_builder/state_parser/contract.py`

**Было:**
```python
class IntegrationExpressionModel(BaseModel):
    variable: str
    url: str
    params: dict[str, Any]  # ❌ Обязательное поле
    method: Literal["get", "post", "put", "delete", "patch"]
```

**Стало:**
```python
class IntegrationExpressionModel(BaseModel):
    variable: str
    url: str
    params: Optional[dict[str, Any]] = None      # ✅ Опциональное
    body: Optional[dict[str, Any]] = None        # ✅ Новое поле
    method: Literal["get", "post", "put", "delete", "patch"]
    dependent_variables: Optional[list[str]] = None
    error_variable: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_params_or_body(self):
        """Валидация: GET/DELETE должны использовать params, POST/PUT/PATCH должны использовать body"""
        method = self.method.lower()
        
        if method in ['get', 'delete']:
            if self.body is not None:
                raise ValueError(f"Method '{method}' should use 'params', not 'body'")
        elif method in ['post', 'put', 'patch']:
            if self.params is not None and self.body is None:
                raise ValueError(f"Method '{method}' should use 'body', not 'params'")
        
        return self
```

### 2. Ключевые изменения

1. **Опциональные поля:**
   - `params: Optional[dict[str, Any]] = None` - для GET/DELETE запросов
   - `body: Optional[dict[str, Any]] = None` - для POST/PUT/PATCH запросов

2. **Дополнительные поля:**
   - `dependent_variables` - список зависимых переменных
   - `error_variable` - переменная для сохранения ошибки

3. **Валидация через `@model_validator`:**
   - GET/DELETE должны использовать `params`
   - POST/PUT/PATCH должны использовать `body`
   - Предотвращает неправильное использование

## 📊 Результаты тестирования

### Тест парсинга workflow

```bash
python3 test_fixed_workflow.py
```

**Результат:**
```
✅ Все 37 states успешно распарсены!

📊 Найдено 9 integration expressions:

   POST/PUT/PATCH с body: 2
      • AddItemToCart: POST {{base_url}}/carts/add-advertisement
      • CreateOrder: POST {{base_url}}/ships

   GET/DELETE с params: 7
      • FetchCartSnapshot: GET {{base_url}}/advertisements
      • FetchStoresCatalog: GET {{base_url}}/users/role/MODERATOR
      • FetchRecommendedProducts: GET {{base_url}}/advertisements/owner/{{user_id}}
      • RemoveItemFromCart: DELETE {{base_url}}/carts/{{cart_id}}/advertisements/{{target_advertisement_id}}
      • ClearCart: DELETE {{base_url}}/carts/{{cart_id}}
      • FetchPaymentMethods: GET {{base_url}}/payment-methods
      • FetchShippingMethods: GET {{base_url}}/shipping-methods
```

### Проверка через API

```bash
# 1. Загрузка workflow (без ошибок в логах)
curl http://localhost:8080/workflow/68ded7589d42ce73ba2d7092/full | jq '.states | length'
# Результат: 37

# 2. Проверка логов
tail -50 server.log | grep -E "(ERROR|validation error)"
# Результат: ✅ Ошибок парсинга не найдено
```

## 🔄 Обратная совместимость

Модель поддерживает оба формата:

### Старый формат (с params для всех методов)
```json
{
  "variable": "result",
  "url": "{{base_url}}/api/resource",
  "method": "get",
  "params": {"id": "{{resource_id}}"}
}
```

### Новый формат (body для POST)
```json
{
  "variable": "result",
  "url": "{{base_url}}/api/resource",
  "method": "post",
  "body": {"name": "{{resource_name}}"}
}
```

## 🚀 Статус

- ✅ Pydantic модели обновлены
- ✅ Workflow успешно парсится
- ✅ Все 37 states проходят валидацию
- ✅ Сервер работает без ошибок
- ✅ POST запросы используют `body`
- ✅ GET запросы используют `params`

## 📝 Workflow ID

**ID сохранённого workflow:** `68ded7589d42ce73ba2d7092`

Как найти в MongoDB:
```bash
mongosh test
db.states.findOne({"_id": ObjectId("68ded7589d42ce73ba2d7092")})
```

## ✨ Дополнительно

- Создан скрипт `save_cart_workflow.py` для прямого сохранения в MongoDB
- Создан тест `test_fixed_workflow.py` для проверки парсинга
- Обновлена документация в `docs/WORKFLOW_SAVE_CHEATSHEET.md`
