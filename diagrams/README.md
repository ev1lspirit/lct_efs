# Диаграммы Workflow Management System

Этот каталог содержит PlantUML диаграммы для системы управления workflow.

## Файлы диаграмм

### 1. `use_case_diagram.puml`
**Use Case диаграмма** - описывает функциональные требования системы и взаимодействие акторов с системой.

**Акторы:**
- Client Application - клиентское веб-приложение
- Mobile App - мобильное приложение
- Admin Panel - административная панель
- External API - внешние API сервисы

**Основные Use Cases:**
- Инициализация workflow
- Отправка событий
- Получение экранов
- Обновление контекста
- Создание и развертывание workflow
- Обработка различных типов состояний
- Управление переходами

### 2. `sysml_diagram.puml`
**SysML Block Definition Diagram** - описывает структуру системы, основные компоненты и их взаимосвязи.

**Основные блоки:**
- **API Layer**: FastAPI приложение с эндпоинтами
- **Workflow Engine**: Automaton, WorkflowState и типы состояний
- **State Components**: Expression, Transition, обработчики
- **Expression Handlers**: BaseHandler и специализированные обработчики
- **Storage Layer**: MongoDB, Redis, SessionContext
- **External Adapters**: CommonAdapter для API вызовов
- **Workflow Parser**: GlobalStateParser, BaseHandlersCreator

**Типы состояний:**
- ScreenState - экранные состояния с UI
- TechnicalState - логические вычисления
- IntegrationState - вызовы внешних API
- ServiceState - внутренние сервисные операции

### 3. `sysml_sequence_diagram.puml`
**SysML Sequence Diagram** - описывает последовательность взаимодействий при обработке события от клиента.

**Фазы:**
1. **Инициализация Workflow**: создание сессии и загрузка workflow
2. **Отправка События**: клиент отправляет событие с параметрами
3. **Обработка События**: выполнение handlers и оценка выражений
4. **Поиск Перехода**: поиск подходящего перехода по событию или условиям
5. **Сохранение Состояния**: checkpoint и сохранение контекста в Redis
6. **Проверка Типа**: определение следующего действия по типу состояния

### 4. `sysml_state_machine.puml`
**SysML State Machine Diagram** - описывает жизненный цикл workflow и переходы между состояниями.

**Основные состояния:**
- Workflow Initialized - инициализация workflow
- State Ready - состояние готово к обработке
- Screen/Technical/Integration/Service State Processing - обработка состояний
- Transition Evaluation - оценка и выбор перехода
- State Transition - выполнение перехода
- Workflow Complete - завершение workflow

## Как использовать

### Просмотр диаграмм

#### Онлайн:
1. Откройте [PlantUML Online Editor](http://www.plantuml.com/plantuml/uml/)
2. Скопируйте содержимое `.puml` файла
3. Вставьте в редактор

#### VS Code:
1. Установите расширение [PlantUML](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml)
2. Откройте `.puml` файл
3. Нажмите `Alt+D` для предварительного просмотра

#### IntelliJ IDEA / PyCharm:
1. Установите плагин [PlantUML integration](https://plugins.jetbrains.com/plugin/7017-plantuml-integration)
2. Откройте `.puml` файл
3. Диаграмма отобразится справа

### Генерация изображений

#### Используя PlantUML CLI:
```bash
# Установка PlantUML (требуется Java)
brew install plantuml

# Генерация PNG
plantuml diagrams/use_case_diagram.puml
plantuml diagrams/sysml_diagram.puml
plantuml diagrams/sysml_sequence_diagram.puml
plantuml diagrams/sysml_state_machine.puml

# Генерация SVG (масштабируемый формат)
plantuml -tsvg diagrams/use_case_diagram.puml
plantuml -tsvg diagrams/sysml_diagram.puml
plantuml -tsvg diagrams/sysml_sequence_diagram.puml
plantuml -tsvg diagrams/sysml_state_machine.puml

# Генерация всех диаграмм
plantuml diagrams/*.puml
```

#### Используя Docker:
```bash
# Генерация PNG
docker run --rm -v $(pwd):/data plantuml/plantuml:latest -tpng /data/diagrams/*.puml

# Генерация SVG
docker run --rm -v $(pwd):/data plantuml/plantuml:latest -tsvg /data/diagrams/*.puml
```

## Обновление диаграмм

При изменении архитектуры системы обновите соответствующие диаграммы:

1. **Use Case**: добавляйте новые use cases при добавлении функциональности
2. **Block Definition**: обновляйте при изменении структуры классов
3. **Sequence**: обновляйте при изменении flow обработки запросов
4. **State Machine**: обновляйте при изменении жизненного цикла состояний

## Соглашения

- Используйте theme `blueprint` для единообразия
- Добавляйте notes для пояснения сложной логики
- Используйте правильные стереотипы SysML (`<<block>>`, `<<subsystem>>`, и т.д.)
- Группируйте связанные элементы в packages
- Документируйте constraints в notes

## Полезные ссылки

- [PlantUML Официальная документация](https://plantuml.com/)
- [PlantUML Use Case Diagram](https://plantuml.com/use-case-diagram)
- [PlantUML Class Diagram (для SysML Block)](https://plantuml.com/class-diagram)
- [PlantUML Sequence Diagram](https://plantuml.com/sequence-diagram)
- [PlantUML State Diagram](https://plantuml.com/state-diagram)
- [SysML Notation Guide](https://sysml.org/.res/docs/specs/OMGSysML-v1.4-15-06-03.pdf)
