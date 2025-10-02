# Новый формат Workflow - Changelog

## ✅ Что было добавлено

### 1. Поддержка правильного HTTP формата
- ✅ **`body`** для POST/PUT/PATCH запросов (вместо `params`)
- ✅ **`params`** остаётся для GET/DELETE запросов (query parameters)
- ✅ Автоматическая валидация формата при сохранении

### 2. Модульное хранение в MongoDB

#### Три отдельные коллекции:
1. **`states`** - Определения всех состояний workflow
2. **`workflow_context`** - Предопределённый контекст (переменные)
3. **`screens`** - JSON описания экранов

### 3. Новые методы в MongoDBClient

```python
# Сохранение с валидацией формата
workflow_id = client.insert_workflow_with_format_validation(workflow_data)

# Получение полного workflow (states + context + screens)
full_workflow = client.get_workflow_with_context(workflow_id)
```

### 4. Новый API endpoint

```bash
GET /workflow/{workflow_id}/full
```

Возвращает полный workflow со всеми связанными данными.

### 5. Исправления в cart_workflow.json

#### AddItemToCart
```diff
- "params": { "cart_id": "{{cart_id}}", ... }
+ "body": { "cart_id": "{{cart_id}}", ... }
```

#### CreateOrder
```diff
- "params": { "name": "...", "shipping_method_id": "...", ... }
+ "body": { "name": "...", "shipping_method_id": "...", ... }
```

## 📊 Результаты тестирования

```
✅ Workflow ID: 68ded36b2cd7a54315733d27
✅ Context ID: 68ded36b2cd7a54315733d27
✅ Screens сохранено: 10/10
✅ States: 37
✅ Context vars: 35
✅ Полная загрузка: Успешно
```

## 🗂️ Структура хранения

### До (старый формат):
```
states (collection)
└── {
      "_id": "...",
      "states": [...],
      "predefined_context": {...},
      "screens": {...}  // Всё в одном документе
    }
```

### После (новый формат):
```
states (collection)
└── { "_id": "abc123", "states": [...] }

workflow_context (collection)
└── { "_id": "abc123", "base_url": "...", "user_id": 14, ... }

screens (collection)
├── { "_id": "x1", "workflow_id": "abc123", "state_id": "CartOverviewScreen", "screen": {...} }
├── { "_id": "x2", "workflow_id": "abc123", "state_id": "CheckoutSummaryScreen", "screen": {...} }
└── ...
```

**Преимущества:**
- 🎯 Модульность - каждая часть хранится отдельно
- 🔄 Переиспользование - screens можно обновлять независимо
- 🚀 Эффективность - меньше дублирования данных
- 📈 Масштабируемость - легко добавлять новые коллекции

## 📝 Созданные файлы

### Код
1. **`storage/mongo/client.py`** - Обновлённый MongoDBClient
   - `insert_workflow_with_format_validation()` - Сохранение с валидацией
   - `get_workflow_with_context()` - Получение полного workflow

2. **`api/routes.py`** - Обновлённые API endpoints
   - `POST /workflow/save` - Обновлён для нового формата
   - `GET /workflow/{id}/full` - Новый endpoint

3. **`test_new_format.py`** - Тестовый скрипт
   - Валидация формата
   - Сохранение/загрузка
   - Проверка всех компонентов

### Документация
4. **`docs/NEW_WORKFLOW_FORMAT.md`** - Полная документация
5. **`docs/QUICK_START_NEW_FORMAT.md`** - Быстрый старт
6. **`docs/NEW_FORMAT_CHANGELOG.md`** - Этот файл

## 🚀 Как использовать

### 1. Проверить формат
```bash
python test_new_format.py
```

### 2. Сохранить workflow
```bash
curl -X POST http://localhost:8080/workflow/save \
  -H "Content-Type: application/json" \
  -d @cart_workflow.json
```

### 3. Получить полный workflow
```bash
curl http://localhost:8080/workflow/{workflow_id}/full
```

## 📋 Checklist миграции

- [x] Заменить `params` на `body` в POST запросах
- [x] Добавить методы валидации в MongoDBClient
- [x] Обновить API routes для нового формата
- [x] Создать endpoint для получения полного workflow
- [x] Написать тесты
- [x] Создать документацию
- [x] Протестировать на cart_workflow.json

## ⚠️ Breaking Changes

**Нет breaking changes!** Старый формат продолжает работать, но система выводит предупреждения:

```
⚠️  State 'AddItemToCart': POST should use 'body' instead of 'params'
```

## 🔄 Обратная совместимость

Система поддерживает оба формата:
- ✅ Новый формат с `body` - рекомендуется
- ⚠️ Старый формат с `params` - работает, но deprecated

## 📚 Дополнительные ресурсы

- **Полная документация:** [docs/NEW_WORKFLOW_FORMAT.md](NEW_WORKFLOW_FORMAT.md)
- **Быстрый старт:** [docs/QUICK_START_NEW_FORMAT.md](QUICK_START_NEW_FORMAT.md)
- **API документация:** http://localhost:8080/docs
- **Пример workflow:** `cart_workflow.json`

## 🎯 Следующие шаги

1. ✅ Протестировать на production данных
2. ✅ Обновить все существующие workflows
3. ✅ Добавить мониторинг использования старого формата
4. ✅ Создать скрипт автоматической миграции

## 👥 Команда

Реализовано: GitHub Copilot  
Дата: 2 октября 2025 г.  
Версия: 2.0

## 📞 Поддержка

При проблемах:
1. Проверьте логи: `tail -f server.log`
2. Запустите тесты: `python test_new_format.py`
3. Проверьте документацию: `docs/NEW_WORKFLOW_FORMAT.md`

---

**🎉 Спасибо за использование нового формата workflow!**
