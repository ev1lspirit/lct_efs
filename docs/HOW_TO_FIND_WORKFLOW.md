# 🔍 Как найти новый workflow в MongoDB

## 📋 Быстрая справка

### Вариант 1: Через MongoDB Shell (mongosh)

```bash
# Подключиться к базе данных
mongosh lct_efs_db

# Или с указанием параметров подключения
mongosh mongodb://localhost:27017/lct_efs_db
```

#### Найти все workflows
```javascript
// Показать все workflows
db.states.find().pretty()

// Посчитать количество workflows
db.states.countDocuments()

// Найти последний созданный workflow
db.states.find().sort({_id: -1}).limit(1).pretty()
```

#### Найти конкретный workflow по ID
```javascript
// По ID
db.states.findOne({_id: ObjectId("68ded36b2cd7a54315733d27")})

// Получить только список состояний
db.states.findOne(
  {_id: ObjectId("68ded36b2cd7a54315733d27")},
  {states: 1}
)
```

#### Найти workflow с его контекстом
```javascript
// Найти states
var workflow = db.states.findOne({_id: ObjectId("68ded36b2cd7a54315733d27")})

// Найти context (с тем же ID)
var context = db.workflow_context.findOne({_id: ObjectId("68ded36b2cd7a54315733d27")})

// Найти все screens для этого workflow
var screens = db.screens.find({workflow_id: "68ded36b2cd7a54315733d27"}).toArray()

// Показать всё вместе
printjson({
  workflow_id: workflow._id,
  states_count: workflow.states.length,
  context_vars: Object.keys(context).length,
  screens_count: screens.length
})
```

#### Поиск по содержимому
```javascript
// Найти workflow, содержащий определённое состояние
db.states.find({"states.name": "CartOverviewScreen"}).pretty()

// Найти workflow с определённым state_type
db.states.find({"states.state_type": "screen"}).pretty()

// Найти workflow с POST запросами использующими body
db.states.find({
  "states.expressions.method": "post",
  "states.expressions.body": {$exists: true}
}).pretty()
```

---

### Вариант 2: Через Python (test_new_format.py)

```bash
# Запустить тестовый скрипт (он покажет ID)
python test_new_format.py
```

Вывод покажет:
```
✅ Workflow ID: 68ded36b2cd7a54315733d27
✅ Context ID: 68ded36b2cd7a54315733d27
✅ Screens сохранено: 10
```

---

### Вариант 3: Через Python код

```python
from storage.mongo.client import MongoDBClient
from config import settings

# Создать клиент
client = MongoDBClient(
    database=settings.MONGO_DB,
    collection=settings.STATES_MONGO_COLLECTION
)

# Получить все workflows
all_workflows = client.get_all()
print(f"Всего workflows: {len(all_workflows)}")

# Получить последний workflow
if all_workflows:
    last_workflow = all_workflows[-1]
    workflow_id = str(last_workflow['_id'])
    print(f"Последний workflow ID: {workflow_id}")
    
    # Получить полный workflow с контекстом и screens
    full_workflow = client.get_workflow_with_context(workflow_id)
    print(f"States: {len(full_workflow['states'])}")
    print(f"Context vars: {len(full_workflow['predefined_context'])}")
    print(f"Screens: {len(full_workflow['screens'])}")
```

---

### Вариант 4: Через API

```bash
# Получить список всех workflows (если есть endpoint)
curl http://localhost:8080/workflows

# Получить конкретный workflow по ID
curl http://localhost:8080/workflow/68ded36b2cd7a54315733d27/full | jq

# Красиво отформатировать JSON
curl http://localhost:8080/workflow/68ded36b2cd7a54315733d27/full | jq '.data.states[] | select(.state_type == "screen") | .name'
```

---

### Вариант 5: Через MongoDB Compass (GUI)

1. Открыть MongoDB Compass
2. Подключиться к `mongodb://localhost:27017`
3. Выбрать базу данных `lct_efs_db`
4. Открыть коллекцию `states`
5. Найти документ с нужным `_id`

---

## 🔎 Полезные запросы

### Найти самый новый workflow
```bash
mongosh lct_efs_db --eval "db.states.find().sort({_id: -1}).limit(1).pretty()"
```

### Найти все workflows созданные сегодня
```javascript
var today = new Date()
today.setHours(0,0,0,0)
var todayObjectId = ObjectId(Math.floor(today.getTime()/1000).toString(16) + "0000000000000000")

db.states.find({_id: {$gte: todayObjectId}}).pretty()
```

### Найти workflow по названию состояния
```javascript
db.states.find({"states.name": "CartOverviewScreen"}).pretty()
```

### Посчитать screens для workflow
```javascript
db.screens.countDocuments({workflow_id: "68ded36b2cd7a54315733d27"})
```

### Получить список всех screens workflow
```javascript
db.screens.find(
  {workflow_id: "68ded36b2cd7a54315733d27"},
  {state_id: 1, _id: 0}
)
```

---

## 📊 Структура данных

### states коллекция
```javascript
{
  _id: ObjectId("68ded36b2cd7a54315733d27"),
  states: [
    {
      state_type: "technical",
      name: "InitCartWorkflow",
      transitions: [...],
      expressions: [...]
    },
    // ... 37 states
  ]
}
```

### workflow_context коллекция
```javascript
{
  _id: ObjectId("68ded36b2cd7a54315733d27"),  // Тот же ID!
  base_url: "http://localhost:8080/backservices/api",
  user_id: 14,
  cart_id: 3,
  // ... 35 переменных
}
```

### screens коллекция
```javascript
{
  _id: ObjectId("..."),
  workflow_id: "68ded36b2cd7a54315733d27",
  state_id: "CartOverviewScreen",
  screen: {
    id: "screen-cart-overview",
    type: "Screen",
    name: "Корзина",
    // ... полное определение экрана
  }
}
```

---

## 🎯 Практические примеры

### Пример 1: Найти workflow и показать его структуру
```bash
mongosh lct_efs_db << 'EOF'
var wf = db.states.findOne()
if (wf) {
  print("Workflow ID: " + wf._id)
  print("States count: " + wf.states.length)
  
  var ctx = db.workflow_context.findOne({_id: wf._id})
  print("Context vars: " + Object.keys(ctx).length)
  
  var screens = db.screens.countDocuments({workflow_id: wf._id.toString()})
  print("Screens count: " + screens)
}
EOF
```

### Пример 2: Экспортировать workflow в JSON
```bash
# Экспортировать states
mongoexport --db=lct_efs_db --collection=states \
  --query='{"_id": ObjectId("68ded36b2cd7a54315733d27")}' \
  --out=workflow_export.json --pretty

# Экспортировать context
mongoexport --db=lct_efs_db --collection=workflow_context \
  --query='{"_id": ObjectId("68ded36b2cd7a54315733d27")}' \
  --out=context_export.json --pretty

# Экспортировать screens
mongoexport --db=lct_efs_db --collection=screens \
  --query='{"workflow_id": "68ded36b2cd7a54315733d27"}' \
  --out=screens_export.json --jsonArray --pretty
```

### Пример 3: Python скрипт для поиска
```python
#!/usr/bin/env python3
"""Найти все workflows в MongoDB"""

from storage.mongo.client import MongoDBClient
from config import settings
from datetime import datetime

def find_all_workflows():
    client = MongoDBClient(settings.MONGO_DB, settings.STATES_MONGO_COLLECTION)
    workflows = client.get_all()
    
    print(f"\n{'='*60}")
    print(f"Найдено workflows: {len(workflows)}")
    print(f"{'='*60}\n")
    
    for i, wf in enumerate(workflows, 1):
        wf_id = str(wf['_id'])
        states_count = len(wf.get('states', []))
        
        print(f"{i}. Workflow ID: {wf_id}")
        print(f"   States: {states_count}")
        
        # Получить context
        ctx_client = MongoDBClient(settings.MONGO_DB, settings.WORKFLOW_MONGO_COLLECTION)
        context = ctx_client.get(wf_id)
        if context:
            print(f"   Context vars: {len(context)}")
        
        # Получить screens
        scr_client = MongoDBClient(settings.MONGO_DB, settings.SCREENS_MONGO_COLLECTION)
        screens = list(scr_client.collection.find({"workflow_id": wf_id}))
        print(f"   Screens: {len(screens)}")
        print()

if __name__ == "__main__":
    find_all_workflows()
```

Сохрани как `find_workflows.py` и запусти:
```bash
python find_workflows.py
```

---

## 🚀 Быстрые команды

```bash
# Подключиться и показать последний workflow
mongosh lct_efs_db --eval "db.states.find().sort({_id:-1}).limit(1).pretty()"

# Посчитать все workflows
mongosh lct_efs_db --eval "db.states.countDocuments()"

# Показать все screens
mongosh lct_efs_db --eval "db.screens.find({}, {state_id:1, workflow_id:1}).pretty()"

# Найти workflow через API
curl http://localhost:8080/workflow/68ded36b2cd7a54315733d27/full | jq '.data | {states: .states | length, context: .predefined_context | length, screens: .screens | length}'
```

---

## 💡 Советы

1. **Используй ObjectId** для точного поиска по `_id`
2. **workflow_id и _id совпадают** между states и workflow_context
3. **screens** ссылаются на workflow через строку `workflow_id`
4. **Последний созданный** workflow имеет самый большой `_id`
5. **Используй .pretty()** для красивого вывода в mongosh
6. **Используй jq** для красивого форматирования JSON из API

---

## 📞 Нужна помощь?

- **Тестовый скрипт:** `python test_new_format.py`
- **Документация:** `docs/CHEATSHEET.md`
- **Примеры:** Смотри выше! ⬆️

---

**Готово!** Теперь ты знаешь все способы найти workflow в MongoDB! 🎉
