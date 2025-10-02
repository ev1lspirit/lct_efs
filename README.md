# LCT EFS Project

Система управления workflow с поддержкой state machine, integration states, и динамических экранов.

## 🚀 Новое: Формат Workflow 2.0

**✅ Добавлена поддержка нового формата workflow с улучшенной структурой!**

### Ключевые улучшения:
- ✅ Правильное использование `body` для POST/PUT/PATCH запросов
- ✅ Модульное хранение в MongoDB (states, context, screens)
- ✅ Автоматическая валидация формата
- ✅ Новый API endpoint для получения полного workflow

### Быстрый старт:
```bash
# Тестирование нового формата
python test_new_format.py

# Получить полный workflow
curl http://localhost:8080/workflow/{workflow_id}/full
```

📚 **Документация:**
- [Полная документация нового формата](docs/NEW_WORKFLOW_FORMAT.md)
- [Быстрый старт](docs/QUICK_START_NEW_FORMAT.md)
- [Changelog](docs/NEW_FORMAT_CHANGELOG.md)
- [Summary](docs/SUMMARY.md)

## 📋 Основные возможности

- **State Machine Engine** - FSM для управления workflow
- **Integration States** - HTTP запросы к внешним API
- **Technical States** - Вычисления и трансформации данных
- **Screen States** - Динамические UI компоненты
- **MongoDB Storage** - Модульное хранение workflow
- **Redis Cache** - Кэширование сессий пользователей

## 🏗️ Архитектура

### Структура MongoDB:
```
lct_efs_db/
├── states/            # Определения состояний workflow
├── workflow_context/  # Предопределённые переменные
└── screens/          # JSON описания экранов
```

### API Endpoints:
- `POST /workflow/save` - Сохранение workflow
- `GET /workflow/{id}/full` - Получение полного workflow ✨ NEW
- `POST /client/workflow` - Выполнение workflow

## 🔧 Установка и запуск

```bash
# Установка зависимостей
pip install -r deployments/requirements.txt

# Запуск сервера
uvicorn api.app:app --host 127.0.0.1 --port 8080

# В другом терминале - тестирование
python test_new_format.py
```

## 📝 Пример workflow

См. [cart_workflow.json](cart_workflow.json) - полный пример корзины покупок с:
- 37 states (technical, integration, screen)
- 10 screens (UI компоненты)
- 35 предопределённых переменных
- Интеграция с бэкенд API

## 🧪 Тестирование

```bash
# Тест нового формата
python test_new_format.py

# Интеграционные тесты
python run_integration_test.py

# Проверка workflow
python check_workflows.py
```

## 📖 Документация

- [Новый формат workflow](docs/NEW_WORKFLOW_FORMAT.md) ✨
- [Быстрый старт](docs/QUICK_START_NEW_FORMAT.md) ✨
- [Интеграция с мобильным приложением](docs/MOBILE_APP_INTEGRATION_GUIDE.md)
- [Формат экранов](docs/SCREEN_FORMAT.md)
- [Руководство по тестированию](docs/TEST_INTEGRATION_README.md)

## 🛠️ Разработка

### Структура проекта:
```
lct_efs/
├── api/                    # REST API endpoints
├── storage/               
│   ├── mongo/             # MongoDB клиент ✨ Обновлён
│   └── redis/             # Redis кэш
├── workflow_builder/      # FSM движок
│   ├── automaton/         # State machine
│   └── builders/          # Обработчики состояний
├── docs/                  # Документация ✨ Новые файлы
├── test_new_format.py     # Тесты нового формата ✨
└── cart_workflow.json     # Пример workflow ✨ Обновлён
```

## 🔄 Миграция на новый формат

### Изменения в integration states:

**Старый формат (deprecated):**
```json
{
  "url": "{{base_url}}/carts/add-advertisement",
  "params": { "cart_id": "{{cart_id}}" },
  "method": "post"
}
```

**Новый формат (рекомендуется):**
```json
{
  "url": "{{base_url}}/carts/add-advertisement",
  "body": { "cart_id": "{{cart_id}}" },
  "method": "post"
}
```

Система автоматически валидирует формат и выводит предупреждения.

## 📊 Статус проекта

- ✅ FSM движок - Production ready
- ✅ MongoDB storage - Production ready ✨ Обновлён
- ✅ Redis cache - Production ready
- ✅ API endpoints - Production ready ✨ Расширен
- ✅ Формат workflow 2.0 - Production ready ✨ NEW
- ✅ Документация - Полная ✨ Обновлена

## 🤝 Вклад

См. документацию в `docs/` для подробностей по разработке и интеграции.

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f server.log`
2. Запустите тесты: `python test_new_format.py`
3. Изучите документацию в `docs/`
4. Проверьте примеры в `cart_workflow.json`

---

**Версия:** 2.0  
**Дата обновления:** 2 октября 2025 г.  
**Status:** ✅ Production Ready
