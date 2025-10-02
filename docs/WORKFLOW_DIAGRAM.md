# 🔄 Тестовый Workflow - Визуализация

## Диаграмма потока выполнения

```
┌─────────────────────────────────────────────────────────────────┐
│                      ТЕСТОВЫЙ WORKFLOW                           │
│         Демонстрация Integration States с интерполяцией          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│  UserInputScreen    │ ← START
│  (screen)           │
│                     │
│  Пользователь вводит│
│  user_id и api_key  │
└──────────┬──────────┘
           │ event: "search"
           ↓
┌─────────────────────┐
│  ValidateInput      │
│  (technical)        │
│                     │
│  ✓ len(user_id) > 0 │
│  ✓ len(api_key) > 0 │
└──────────┬──────────┘
           │ input_valid = True
           ↓
┌─────────────────────────────────────────────────────────┐
│  FetchUserProfile (INTEGRATION STATE)                   │
│                                                          │
│  URL: https://jsonplaceholder.typicode.com/users/       │
│       {{user_id}} ← ИНТЕРПОЛЯЦИЯ                        │
│                                                          │
│  Method: GET                                            │
│  Params: {}                                             │
│  dependent_variables: ["user_id"]  ← ВАЛИДАЦИЯ          │
│  error_variable: "profile_error"   ← ОБРАБОТКА ОШИБОК   │
│                                                          │
│  Логи:                                                  │
│  INFO: Integration request: GET .../users/1             │
│  DEBUG: Original params: {}                             │
│  DEBUG: Interpolated params: {}                         │
└──────────┬──────────────────────────────────────────────┘
           │ user_profile = {...}
           ↓
┌─────────────────────────────────────────────────────────┐
│  FetchUserOrders (INTEGRATION STATE)                    │
│                                                          │
│  URL: https://jsonplaceholder.typicode.com/posts        │
│                                                          │
│  Method: GET                                            │
│  Params:                                                │
│    userId: "{{user_id}}"  ← ИНТЕРПОЛЯЦИЯ В PARAMS       │
│    _limit: "5"                                          │
│                                                          │
│  dependent_variables: ["user_id"]                       │
│  error_variable: "orders_error"                         │
│                                                          │
│  Логи:                                                  │
│  DEBUG: Original params:                                │
│    {'userId': '{{user_id}}', '_limit': '5'}             │
│  DEBUG: Interpolated params:                            │
│    {'userId': '1', '_limit': '5'}  ← ЗНАЧЕНИЕ ИЗ CONTEXT│
└──────────┬──────────────────────────────────────────────┘
           │ orders = [{...}, {...}, ...]
           ↓
┌─────────────────────┐
│  ProcessOrdersData  │
│  (technical)        │
│                     │
│  ✓ len(orders) > 0  │
└──────────┬──────────┘
           │ has_orders = True
           ↓
┌─────────────────────────────────────────────────────────┐
│  CreateOrderSummary (INTEGRATION STATE)                 │
│                                                          │
│  URL: https://jsonplaceholder.typicode.com/posts        │
│                                                          │
│  Method: POST                                           │
│  Params:                                                │
│    title: "Order Summary for User {{user_id}}"         │
│           ↑ МНОЖЕСТВЕННЫЕ СЛОВА + ИНТЕРПОЛЯЦИЯ          │
│    body: "Summary of orders"                            │
│    userId: "{{user_id}}"                                │
│                                                          │
│  dependent_variables: ["user_id"]                       │
│  error_variable: "summary_error"                        │
│                                                          │
│  Логи:                                                  │
│  DEBUG: Original params:                                │
│    {'title': 'Order Summary for User {{user_id}}', ...} │
│  DEBUG: Interpolated params:                            │
│    {'title': 'Order Summary for User 1', ...}           │
└──────────┬──────────────────────────────────────────────┘
           │ summary = {...}
           ↓
┌─────────────────────┐
│  DisplayResults     │
│  (screen)           │
│                     │
│  Показываем:        │
│  • user_profile     │
│  • orders           │
│  • summary          │
└──────────┬──────────┘
           │ event: "exit"
           ↓
┌─────────────────────┐
│  ExitFlow           │ ← END
│  (final state)      │
└─────────────────────┘


════════════════════════════════════════════════════════════════

ОБРАБОТКА ОШИБОК (альтернативные пути):

ValidateInput
    │ input_valid = False
    ↓
┌─────────────────────────┐
│ ValidationErrorScreen   │
│                         │
│ Сообщение:              │
│ "user_id и api_key      │
│  обязательны"           │
└──────────┬──────────────┘
           │ event: "retry"
           ↓
      UserInputScreen


FetchUserProfile
    │ profile_error = True
    ↓
┌─────────────────────────┐
│ ProfileErrorScreen      │
│                         │
│ Показываем ошибку:      │
│ context["profile_error"]│
│   {                     │
│     "error": True,      │
│     "message": "...",   │
│     "status_code": 404  │
│   }                     │
└──────────┬──────────────┘
           │ event: "retry" или "back"
           ↓
      FetchUserProfile или UserInputScreen


ProcessOrdersData
    │ has_orders = False
    ↓
┌─────────────────────────┐
│ NoOrdersScreen          │
│                         │
│ "Заказы не найдены"     │
└──────────┬──────────────┘
           │ event: "back"
           ↓
      UserInputScreen

════════════════════════════════════════════════════════════════

КОНТЕКСТ НА КАЖДОМ ЭТАПЕ:

1. Начало (UserInputScreen):
   {
     "user_id": "1",
     "api_key": "test-key-123"
   }

2. После ValidateInput:
   {
     "user_id": "1",
     "api_key": "test-key-123",
     "input_valid": "True"
   }

3. После FetchUserProfile:
   {
     "user_id": "1",
     "api_key": "test-key-123",
     "input_valid": "True",
     "user_profile": {
       "id": 1,
       "name": "Leanne Graham",
       "email": "Sincere@april.biz",
       ...
     }
   }

4. После FetchUserOrders:
   {
     ...(предыдущий контекст)...,
     "orders": [
       {"id": 1, "userId": 1, "title": "...", "body": "..."},
       {"id": 2, "userId": 1, "title": "...", "body": "..."},
       ...
     ]
   }

5. После CreateOrderSummary:
   {
     ...(предыдущий контекст)...,
     "summary": {
       "id": 101,
       "title": "Order Summary for User 1",  ← ИНТЕРПОЛИРОВАНО!
       "body": "Summary of orders",
       "userId": "1"
     }
   }

════════════════════════════════════════════════════════════════

ДЕМОНСТРИРУЕМЫЕ ВОЗМОЖНОСТИ:

✅ 1. ПРОСТАЯ ИНТЕРПОЛЯЦИЯ
   URL: .../users/{{user_id}}
   Результат: .../users/1

✅ 2. ИНТЕРПОЛЯЦИЯ В PARAMS
   Params: {"userId": "{{user_id}}"}
   Результат: {"userId": "1"}

✅ 3. МНОЖЕСТВЕННЫЕ ПЕРЕМЕННЫЕ В СТРОКЕ
   "Order Summary for User {{user_id}}"
   Результат: "Order Summary for User 1"

✅ 4. ВАЛИДАЦИЯ DEPENDENT_VARIABLES
   dependent_variables: ["user_id"]
   → Проверка наличия перед запросом

✅ 5. ОБРАБОТКА ОШИБОК
   error_variable: "profile_error"
   → Сохранение ошибки в контекст
   → Переход в error screen

✅ 6. ЛОГИРОВАНИЕ
   DEBUG: Original params: {'userId': '{{user_id}}'}
   DEBUG: Interpolated params: {'userId': '1'}

════════════════════════════════════════════════════════════════

СТАТИСТИКА WORKFLOW:

• Всего states: 11
• Screen states: 6
• Technical states: 2
• Integration states: 3
• Finalize states: 1

• Transitions: 20
• Events: 8

• API calls: 3
  - GET .../users/{{user_id}}
  - GET .../posts?userId={{user_id}}
  - POST .../posts (body с интерполяцией)

• Интерполируемых переменных: 1 (user_id)
• Использований интерполяции: 5

════════════════════════════════════════════════════════════════
```

## Легенда

```
┌────────────┐
│  Состояние │  - Прямоугольник = State
└────────────┘

     │
     ↓         - Стрелка = Transition

(screen)      - Тип state
(technical)
(integration)

{{variable}}  - Интерполируемая переменная

event: "name" - Пользовательское событие

dependent_variables  - Валидация
error_variable      - Обработка ошибок
```

---

**Версия:** 1.0  
**Дата:** 2 октября 2025
