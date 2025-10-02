# Диагностика ошибки "Workflow not found"

## Проблема

Клиент получает ошибку:
```
ValueError: Workflow 68dd6796aef18bd8b52ba7fd not found
```

## Причина

Workflow с ID `68dd6796aef18bd8b52ba7fd` **не существует в MongoDB**.

## Что было сделано

1. ✅ Улучшена обработка ошибок в `workflow_cache.py`:
   - Добавлена валидация формата ObjectId
   - Добавлено детальное логирование
   - Добавлены информативные сообщения об ошибках

2. ✅ Улучшена обработка ошибок в `parser.py`:
   - Добавлено подробное сообщение с 4 возможными причинами
   - Добавлены рекомендации по устранению проблемы

3. ✅ Создана утилита `check_workflows.py` для диагностики workflows

## Текущее состояние MongoDB

В базе данных `test`, коллекции `states` найдено **14 workflows**:

1. `68dd1f14a46a018f75576701` - 9 состояний ✅
2. `68dd1f1d03e007e8b66676c3` - 9 состояний ✅
3. `68dd20f742a45c0581e22210` - 9 состояний ✅
4. `68dd0a8cf8730654b4ec3708` - 9 состояний ✅
5. `68dd0a8cf8730654b4ec3707` - 9 состояний ✅
6. `68dd0a8cf8730654b4ec3706` - 9 состояний ✅
7. `68dd5af68341ae5cb6c60002` - 9 состояний ✅
8. `68dd5b558341ae5cb6c60008` - 9 состояний ✅
9. `68dd68fe8341ae5cb6c60024` - 9 состояний ✅ **(последний сохраненный)**
10. ... и еще 5 workflows

**Важно**: Workflow ID `68dd6796aef18bd8b52ba7fd` отсутствует в списке!

## Решение

### Вариант 1: Использовать существующий workflow

Используйте один из существующих workflow ID, например последний:

```bash
# POST /client/workflow
{
  "client_session_id": "a3a7e755-6e9b-4ddf-a0b8-a685aafeed30",
  "client_workflow_id": "68dd68fe8341ae5cb6c60024"
}
```

### Вариант 2: Создать новый workflow

Создайте новый workflow через `POST /workflow/save`:

```bash
curl -X POST http://127.0.0.1:8080/workflow/save \
  -H "Content-Type: application/json" \
  -d @docs/workflow_save_minimal.json
```

Ответ вернет новый `workflow_id`, который можно использовать.

### Вариант 3: Проверить все workflows

Используйте утилиту для просмотра всех workflows:

```bash
# Показать все workflows
python check_workflows.py

# Проверить конкретный workflow
python check_workflows.py 68dd68fe8341ae5cb6c60024
```

## Команды для диагностики

### 1. Просмотр всех workflows
```bash
python check_workflows.py
```

### 2. Проверка конкретного workflow
```bash
python check_workflows.py <workflow_id>
```

### 3. Проверка через MongoDB Shell
```bash
mongosh
use test
db.states.find({}, {_id: 1})
```

### 4. Подсчет workflows
```bash
mongosh
use test
db.states.countDocuments()
```

## Логи ошибки

Теперь при попытке использовать несуществующий workflow вы увидите подробное сообщение:

```
ERROR | workflow_builder.state_parser.workflow_cache | Workflow 68dd6796aef18bd8b52ba7fd not found in MongoDB

ValueError: Workflow 68dd6796aef18bd8b52ba7fd not found

Возможные причины:
1. Workflow с таким ID не был сохранен в MongoDB
   → Убедитесь, что workflow был создан через POST /workflow/save
2. Workflow был удален из базы данных
   → Проверьте коллекцию: states (база данных: test)
3. Неправильный формат ID
   → ID должен быть валидным ObjectId (24 hex символа)
4. Workflow сохранен в другую базу/коллекцию
   → Проверьте настройки MONGO_DB и STATES_MONGO_COLLECTION
```

## Рекомендации

1. **Всегда сохраняйте workflow ID** после создания workflow через `/workflow/save`
2. **Используйте `check_workflows.py`** для проверки существующих workflows перед использованием
3. **Проверяйте логи** - теперь они содержат подробную информацию о причине ошибки
4. **Используйте валидацию** - система теперь проверяет формат ObjectId перед запросом к БД

## Итог

✅ Обработка ошибок улучшена
✅ Диагностика проблемы завершена
✅ Созданы инструменты для проверки workflows
⚠️ Клиент должен использовать существующий workflow ID
