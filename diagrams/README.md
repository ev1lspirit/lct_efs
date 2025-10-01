# 📊 Документация и диаграммы LCT EFS

Добро пожаловать в полную документацию проекта **LCT EFS** (Execution Finite State) - движка выполнения workflow на основе конечного автомата.

---

## 📁 Структура документации

### 🎯 [Quick Guide](./quick_guide.md)
**Быстрое руководство для начала работы**

Содержит:
- 🚀 Быстрый старт и установка
- 📚 Описание всех типов состояний с примерами
- 🔀 Работа с переходами и выражениями
- 💾 Конфигурация хранилищ
- 🐛 Отладка и решение проблем
- 📈 Best practices и антипаттерны

**Читать первым!** Если вы новичок в проекте.

---

### 🏗️ [Architecture Overview](./architecture_overview.md)
**Полный обзор архитектуры системы**

Содержит:
- Высокоуровневая архитектура с диаграммами
- Описание всех компонентов системы
- Детальный workflow execution flow
- Session lifecycle
- Expression system и композиция
- Паттерны проектирования
- Примеры использования

**Для понимания внутреннего устройства системы.**

---

### 🔄 [Sequence Diagrams](./sequence_diagrams.md)
**Диаграммы последовательности (UML Sequence Diagrams)**

10 детальных диаграмм:
1. **Создание и сохранение Workflow** - как сохраняется workflow в MongoDB
2. **Запуск Workflow (новая сессия)** - инициализация и первый запуск
3. **Workflow Execution (Iteration Loop)** - основной цикл FSM
4. **Context Management Lifecycle** - работа с SessionContext
5. **Expression Evaluation Flow** - вычисление выражений
6. **Transition Selection Process** - выбор перехода
7. **State Creation and Graph Building** - построение графа состояний
8. **Dependency (Service) State Initialization** - загрузка контекста
9. **Handler Creation Pattern** - паттерн создания handlers
10. **Screen State Event Handling** - обработка UI событий

**Для понимания временных последовательностей взаимодействий.**

---

### 🧩 [Class Diagrams](./class_diagrams.md)
**Диаграммы классов (UML Class Diagrams)**

10 подробных диаграмм:
1. **Class Diagram - Core Components** - основные классы системы
2. **Expression Type Hierarchy** - иерархия типов выражений
3. **Handler Creator Pattern** - паттерн фабрики handlers
4. **Data Models** - модели данных (StateModel, etc.)
5. **API Request/Response Models** - API контракты
6. **Storage Layer Structure** - структура хранилищ
7. **State Lifecycle Diagram** - жизненный цикл состояний
8. **Context Data Flow** - поток данных контекста
9. **Expression Binding Mechanism** - механизм связывания
10. **Complete System Architecture** - полная архитектура

**Для понимания структуры классов и их взаимоотношений.**

---

### 📈 [Data Flow Diagrams](./data_flow_diagrams.md)
**Диаграммы потоков данных (DFD)**

10 визуальных диаграмм:
1. **Общий поток данных в системе** - end-to-end поток
2. **Детальный поток выполнения Automaton** - внутренняя логика FSM
3. **Поток управления контекстом** - управление SessionContext
4. **Поток обработки выражений** - вычисление expressions
5. **Поток выбора перехода** - алгоритм выбора transitions
6. **Поток сохранения и загрузки workflow** - persistence
7. **Поток обработки Screen State** - UI взаимодействие
8. **Поток интеграции с внешним API** - Integration state
9. **Поток обработки Technical State** - вычисления
10. **Полный цикл: от запроса до ответа** - complete flow с эмодзи

**Для визуального понимания движения данных в системе.**

---

### 📋 [Contract](./contract.json)
**JSON Schema контракта данных**

Полная спецификация структуры workflow definition:
- State models schema
- Expression models schema  
- Transition models schema
- Validation rules

**Для валидации и генерации workflow определений.**

---

## 🎓 Как использовать эту документацию

### Для новичков в проекте:
```
1. Quick Guide → основы и примеры
2. Architecture Overview → общее понимание
3. Data Flow Diagrams → визуальное представление
4. Sequence Diagrams → детали взаимодействий
```

### Для разработчиков:
```
1. Class Diagrams → структура кода
2. Sequence Diagrams → логика взаимодействий
3. Architecture Overview → паттерны и конвенции
4. Contract.json → валидация данных
```

### Для DevOps/SRE:
```
1. Quick Guide → конфигурация и запуск
2. Architecture Overview → компоненты и зависимости
3. Data Flow Diagrams → мониторинг потоков
```

### Для бизнес-аналитиков:
```
1. Quick Guide → возможности системы
2. Architecture Overview → примеры workflow
3. Data Flow Diagrams → визуализация процессов
```

---

## 🔍 Быстрый поиск

### По типам состояний:
- **Technical State**: [Quick Guide](./quick_guide.md#1-technical-state---вычисления), [Architecture](./architecture_overview.md#states-состояния)
- **Integration State**: [Quick Guide](./quick_guide.md#2-integration-state---api-вызовы), [Data Flow](./data_flow_diagrams.md#8-поток-интеграции-с-внешним-api)
- **Screen State**: [Quick Guide](./quick_guide.md#3-screen-state---ui-взаимодействие), [Sequence](./sequence_diagrams.md#10-screen-state-event-handling)
- **Service State**: [Quick Guide](./quick_guide.md#4-service-state---системные-состояния), [Sequence](./sequence_diagrams.md#8-dependency-service-state-initialization)

### По компонентам:
- **Automaton**: [Class Diagram](./class_diagrams.md#1-class-diagram---core-components), [Data Flow](./data_flow_diagrams.md#2-детальный-поток-выполнения-automaton)
- **SessionContext**: [Architecture](./architecture_overview.md#3-context-management-contextpy), [Sequence](./sequence_diagrams.md#4-context-management-lifecycle)
- **Handlers**: [Class Diagram](./class_diagrams.md#1-class-diagram---core-components), [Sequence](./sequence_diagrams.md#9-handler-creation-pattern)
- **Expressions**: [Architecture](./architecture_overview.md#expression-system), [Class Diagram](./class_diagrams.md#2-expression-type-hierarchy)
- **Transitions**: [Quick Guide](./quick_guide.md#🔀-переходы-transitions), [Data Flow](./data_flow_diagrams.md#5-поток-выбора-перехода)

### По операциям:
- **Создание workflow**: [Sequence](./sequence_diagrams.md#1-создание-и-сохранение-workflow), [Data Flow](./data_flow_diagrams.md#6-поток-сохранения-и-загрузки-workflow)
- **Запуск workflow**: [Sequence](./sequence_diagrams.md#2-запуск-workflow-новая-сессия), [Data Flow](./data_flow_diagrams.md#10-полный-цикл-от-запроса-до-ответа)
- **Обработка событий**: [Sequence](./sequence_diagrams.md#10-screen-state-event-handling), [Data Flow](./data_flow_diagrams.md#7-поток-обработки-screen-state)
- **API интеграция**: [Data Flow](./data_flow_diagrams.md#8-поток-интеграции-с-внешним-api)

---

## 🔗 Связанные ресурсы

### Код проекта:
- **API Layer**: `/api/routes.py`, `/api/app.py`
- **Core FSM**: `/workflow_builder/automaton/automaton.py`
- **States**: `/workflow_builder/states.py`
- **Handlers**: `/workflow_builder/handlers.py`
- **Context**: `/context.py`
- **Storage**: `/storage/redis/service.py`, `/storage/mongo/client.py`

### Конфигурация:
- **Settings**: `/config.py`
- **Docker**: `/docker-compose.yml`, `/deployments/`
- **Environment**: `.env` (создайте на основе Quick Guide)

---

## 📊 Визуальная карта документации

```
📚 LCT EFS Documentation
│
├── 🎯 Quick Guide                    ← Начните здесь!
│   ├── Быстрый старт
│   ├── Типы состояний с примерами
│   ├── Конфигурация
│   └── Troubleshooting
│
├── 🏗️ Architecture Overview          ← Общая картина
│   ├── Компоненты системы
│   ├── Workflow execution flow
│   ├── Паттерны проектирования
│   └── Примеры использования
│
├── 🔄 Sequence Diagrams             ← Временные последовательности
│   ├── Workflow lifecycle
│   ├── State execution
│   ├── Context management
│   └── Event handling
│
├── 🧩 Class Diagrams                ← Структура классов
│   ├── Core components
│   ├── Type hierarchies
│   ├── Design patterns
│   └── Data models
│
├── 📈 Data Flow Diagrams            ← Потоки данных
│   ├── End-to-end flows
│   ├── State execution flows
│   ├── Storage interactions
│   └── Complete cycles
│
└── 📋 Contract (JSON)               ← Спецификация данных
    ├── State schema
    ├── Expression schema
    └── Validation rules
```

---

## 🎨 Условные обозначения в диаграммах

### Цвета:
- 🔵 **Синий** - API/Client layer
- 🟣 **Фиолетовый** - MongoDB operations
- 🔴 **Красный** - Redis operations
- 🟢 **Зеленый** - Core FSM Engine
- 🟡 **Желтый** - Context Management

### Формы (Mermaid):
- `[Прямоугольник]` - Процесс/действие
- `{Ромб}` - Условие/решение
- `[(База данных)]` - Хранилище
- `([Закругленный])` - Начало/конец
- `[[Двойной]]` - Подпроцесс

### Стрелки:
- `-->` - Прямой поток данных
- `-.->` - Косвенная связь/ссылка
- `==>` - Важный/основной поток
- `<-->` - Двусторонний обмен

---

## 🛠️ Инструменты для работы с диаграммами

### Просмотр Mermaid диаграмм:
1. **VS Code**: установите расширение "Markdown Preview Mermaid Support"
2. **Online**: https://mermaid.live/
3. **GitHub**: автоматический рендеринг в .md файлах

### Редактирование:
1. **Mermaid Live Editor**: https://mermaid.live/
2. **Draw.io**: для экспорта в другие форматы
3. **PlantUML**: альтернатива для sequence diagrams

---

## 📝 Обновление документации

При изменении кода обновляйте соответствующие диаграммы:

| Изменение | Обновить документ |
|-----------|------------------|
| Новый тип состояния | Quick Guide, Architecture, Class Diagrams |
| Новый handler | Class Diagrams, Sequence Diagrams |
| Изменение API | Architecture, Sequence Diagrams |
| Новый storage | Architecture, Class Diagrams, Data Flow |
| Изменение логики FSM | Sequence Diagrams, Data Flow |
| Новое поле в State | Contract.json, Class Diagrams |

---

## 🤝 Вклад в документацию

### Принципы:
1. **Clarity** - ясность важнее полноты
2. **Visual** - диаграмма лучше тысячи слов
3. **Examples** - всегда приводите примеры
4. **Updates** - держите в синхронности с кодом

### Шаблон для новой диаграммы:
```markdown
## N. Название диаграммы

Краткое описание того, что показывает диаграмма.

\`\`\`mermaid
graph TD
    Start([Начало]) --> End([Конец])
\`\`\`

**Ключевые моменты:**
- Пункт 1
- Пункт 2

**Связанные диаграммы:**
- [Другая диаграмма](#ссылка)
```

---

## ❓ FAQ

### Где начать изучение проекта?
Начните с [Quick Guide](./quick_guide.md), затем переходите к [Architecture Overview](./architecture_overview.md).

### Как понять, как работает конкретное состояние?
Смотрите соответствующий раздел в [Quick Guide](./quick_guide.md) и детальный flow в [Data Flow Diagrams](./data_flow_diagrams.md).

### Как добавить новый тип состояния?
Следуйте инструкции в [Quick Guide - Расширение системы](./quick_guide.md#🔧-расширение-системы).

### Как отладить проблему с переходами?
Используйте диаграммы в [Data Flow Diagrams - Поток выбора перехода](./data_flow_diagrams.md#5-поток-выбора-перехода).

### Где найти примеры workflow?
В [Quick Guide - Примеры использования](./quick_guide.md#📊-примеры-использования) и [Architecture Overview - Пример workflow](./architecture_overview.md#📊-пример-workflow).

---

## 📞 Поддержка

Если у вас возникли вопросы:
1. Проверьте [Quick Guide - Частые проблемы](./quick_guide.md#🆘-частые-проблемы)
2. Изучите соответствующие диаграммы
3. Проверьте логи (см. [Quick Guide - Отладка](./quick_guide.md#🐛-отладка))

---

## 📄 Лицензия

Эта документация является частью проекта LCT EFS.

---

**Приятного изучения! 🚀**

*Последнее обновление: 1 октября 2025 г.*
