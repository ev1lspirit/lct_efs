# Формат экранов для Workflow Engine

## Обзор

Экраны в workflow engine имеют структурированный формат с секциями (header, body, footer) и вложенными компонентами. Это позволяет создавать сложные пользовательские интерфейсы с полным контролем над layout и стилями.

## Структура экрана

### Базовая структура

```json
{
  "state_type": "screen",
  "name": "MyScreen",
  "transitions": [...],
  "expressions": [...],
  "screen": {
    "id": "screen-id",
    "type": "Screen",
    "name": "Название экрана",
    "style": {
      "display": "flex",
      "flexDirection": "column",
      "minHeight": "100vh",
      "backgroundColor": "#F5F5F5"
    },
    "sections": {
      "header": {...},
      "body": {...},
      "footer": {...}
    }
  }
}
```

### Секции (Sections)

Экран разделен на три основные секции:

#### 1. **Header** - Верхняя часть экрана

Обычно содержит:
- Заголовок
- Кнопку назад
- Действия в заголовке

```json
"header": {
  "id": "section-header",
  "type": "Section",
  "properties": {
    "slot": "header",
    "padding": 16,
    "spacing": 0,
    "background": "#ffffff"
  },
  "style": {
    "width": "100%",
    "borderBottom": "1px solid #E5E5E5"
  },
  "children": [...]
}
```

#### 2. **Body** - Основное содержимое

Содержит основной контент экрана:
- Формы
- Списки
- Карточки
- Текст

```json
"body": {
  "id": "section-body",
  "type": "Section",
  "properties": {
    "slot": "body",
    "padding": 16,
    "spacing": 16
  },
  "style": {
    "flex": "1 1 auto",
    "overflowY": "auto"
  },
  "children": [...]
}
```

#### 3. **Footer** - Нижняя часть экрана

Обычно содержит:
- Основные действия (кнопки)
- Сводная информация
- Навигация

```json
"footer": {
  "id": "section-footer",
  "type": "Section",
  "properties": {
    "slot": "footer",
    "padding": 16,
    "spacing": 0,
    "background": "#ffffff"
  },
  "style": {
    "borderTop": "1px solid #E5E5E5",
    "boxShadow": "0 -2px 8px rgba(0, 0, 0, 0.05)"
  },
  "children": [...]
}
```

## Компоненты

### Layout компоненты

#### **column** - Вертикальный layout

```json
{
  "id": "column-id",
  "type": "column",
  "properties": {
    "spacing": 16,
    "padding": 16,
    "background": "#ffffff"
  },
  "style": {
    "borderRadius": "12px"
  },
  "children": [...]
}
```

#### **row** - Горизонтальный layout

```json
{
  "id": "row-id",
  "type": "row",
  "properties": {
    "spacing": 8,
    "alignItems": "center",
    "justifyContent": "space-between"
  },
  "style": {
    "width": "100%"
  },
  "children": [...]
}
```

### UI компоненты

#### **text** - Текстовый элемент

```json
{
  "id": "text-id",
  "type": "text",
  "properties": {
    "content": "Текст или ${variable}",
    "variant": "heading|body|subtitle|caption"
  },
  "style": {
    "fontSize": "16px",
    "fontWeight": 600,
    "color": "#000000"
  }
}
```

#### **button** - Кнопка

```json
{
  "id": "button-id",
  "type": "button",
  "properties": {
    "text": "Нажми меня",
    "variant": "primary|secondary|link|icon",
    "event": "event_name",
    "eventParams": {
      "param1": "value1"
    }
  },
  "style": {
    "padding": "14px",
    "fontSize": "16px",
    "borderRadius": "8px",
    "background": "#007AFF",
    "color": "#ffffff"
  }
}
```

#### **input** - Поле ввода

```json
{
  "id": "input-id",
  "type": "input",
  "properties": {
    "placeholder": "Введите значение",
    "type": "text|number|email|password",
    "name": "field_name",
    "required": true,
    "value": "default_value"
  },
  "style": {
    "padding": "12px",
    "fontSize": "16px",
    "border": "1px solid #D1D1D6",
    "borderRadius": "8px"
  }
}
```

#### **image** - Изображение

```json
{
  "id": "image-id",
  "type": "image",
  "properties": {
    "src": "https://example.com/image.png",
    "alt": "Описание",
    "width": 80,
    "height": 80
  },
  "style": {
    "borderRadius": "12px",
    "objectFit": "cover"
  }
}
```

#### **checkbox** - Чекбокс

```json
{
  "id": "checkbox-id",
  "type": "checkbox",
  "properties": {
    "checked": true,
    "event": "toggle_event"
  },
  "style": {
    "width": "20px",
    "height": "20px"
  }
}
```

### Динамические компоненты

#### **list** - Список с итерацией

```json
{
  "id": "list-id",
  "type": "list",
  "properties": {
    "variant": "ordered|unordered",
    "spacing": 12,
    "items": {
      "reference": "${orders}",
      "value": []
    },
    "itemAlias": "order"
  },
  "style": {
    "listStyleType": "none",
    "padding": 0
  },
  "children": [
    {
      "id": "list-item-template",
      "type": "column",
      "children": [
        {
          "id": "text-item",
          "type": "text",
          "properties": {
            "content": {
              "reference": "${order.title}",
              "value": "Default"
            }
          }
        }
      ]
    }
  ]
}
```

## Динамические данные

### Использование переменных

Данные из контекста можно отобразить через `reference`:

```json
{
  "properties": {
    "content": {
      "reference": "${user_profile.name}",
      "value": "Loading..."
    }
  }
}
```

- `reference` - путь к переменной в контексте (используется если данные есть)
- `value` - значение по умолчанию (если данных нет)

### Передача параметров в события

```json
{
  "properties": {
    "event": "incrementItem",
    "eventParams": {
      "itemId": {
        "reference": "${cartItem.id}",
        "value": "item-1"
      }
    }
  }
}
```

## Примеры экранов

### 1. Форма ввода

```python
{
    "screen": {
        "id": "screen-input",
        "type": "Screen",
        "name": "Форма",
        "sections": {
            "header": {
                "children": [{
                    "type": "text",
                    "properties": {
                        "content": "Введите данные"
                    }
                }]
            },
            "body": {
                "children": [{
                    "type": "column",
                    "children": [
                        {
                            "type": "input",
                            "properties": {
                                "name": "username",
                                "placeholder": "Имя пользователя"
                            }
                        },
                        {
                            "type": "button",
                            "properties": {
                                "text": "Отправить",
                                "event": "submit"
                            }
                        }
                    ]
                }]
            }
        }
    }
}
```

### 2. Список с данными

```python
{
    "screen": {
        "id": "screen-list",
        "type": "Screen",
        "name": "Список заказов",
        "sections": {
            "body": {
                "children": [{
                    "type": "list",
                    "properties": {
                        "items": {
                            "reference": "${orders}",
                            "value": []
                        },
                        "itemAlias": "order"
                    },
                    "children": [{
                        "type": "column",
                        "children": [
                            {
                                "type": "text",
                                "properties": {
                                    "content": {
                                        "reference": "${order.title}",
                                        "value": "Заказ"
                                    }
                                }
                            }
                        ]
                    }]
                }]
            }
        }
    }
}
```

### 3. Информационный экран

```python
{
    "screen": {
        "id": "screen-info",
        "type": "Screen",
        "name": "Информация",
        "sections": {
            "header": {
                "children": [{
                    "type": "row",
                    "children": [
                        {
                            "type": "button",
                            "properties": {
                                "text": "←",
                                "event": "back"
                            }
                        },
                        {
                            "type": "text",
                            "properties": {
                                "content": "Профиль"
                            }
                        }
                    ]
                }]
            },
            "body": {
                "children": [{
                    "type": "column",
                    "children": [
                        {
                            "type": "row",
                            "children": [
                                {
                                    "type": "text",
                                    "properties": {"content": "Имя"}
                                },
                                {
                                    "type": "text",
                                    "properties": {
                                        "content": {
                                            "reference": "${user.name}",
                                            "value": "N/A"
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }]
            },
            "footer": {
                "children": [{
                    "type": "button",
                    "properties": {
                        "text": "Продолжить",
                        "event": "continue"
                    }
                }]
            }
        }
    }
}
```

## Best Practices

### 1. Именование ID

- Используйте префиксы по типу: `screen-`, `section-`, `button-`, `text-`
- Делайте ID описательными: `button-submit-order` вместо `btn1`

### 2. Стили

- Используйте единую цветовую палитру
- Стандартные отступы: 8px, 12px, 16px, 24px
- Стандартные радиусы: 8px, 12px для карточек

### 3. Layout

- Header: фиксированная высота, белый фон
- Body: flex: 1, overflow-y: auto
- Footer: фиксированная позиция снизу

### 4. Интерактивность

- Все кнопки должны иметь `event`
- Используйте `eventParams` для передачи данных
- Проверяйте required поля в формах

### 5. Доступность

- Всегда указывайте `alt` для изображений
- Используйте семантические `variant` для текста
- Добавляйте placeholder для input полей

## Развертывание

### Сохранение workflow с экранами

```python
from api.integration_workflow_correct_format import get_integration_workflow_with_correct_screens

workflow = get_integration_workflow_with_correct_screens()

# Отправка на сервер
import requests
response = requests.post(
    "http://localhost:8080/workflow/save",
    json={"states": workflow["states"]}
)

workflow_id = response.json()["wf_description_id"]
```

### Создание сессии

```python
response = requests.post(
    "http://localhost:8080/client/workflow",
    json={
        "client_workflow_id": workflow_id,
        "client_session_id": "my-session",
        "context": {}
    }
)

screen = response.json()["screen"]
```

## Тестирование

Используйте `deploy_correct_format.py` для автоматического деплоя и генерации тестовых команд:

```bash
python deploy_correct_format.py
```

Скрипт:
1. Проверит доступность сервера
2. Загрузит workflow
3. Сохранит локально в JSON
4. Задеплоит на сервер
5. Создаст тестовую сессию
6. Выдаст curl команды для тестирования

## Примеры из production

Полные рабочие примеры:
- `api/integration_workflow_correct_format.py` - workflow с Integration States
- `diagrams/contract.json` - пример корзины со сложной структурой

## Troubleshooting

### Экраны не отображаются

- Проверьте, что `state_type: "screen"`
- Убедитесь, что есть ключ `screen` в state
- Проверьте наличие всех секций (header, body, footer)

### Динамические данные не подставляются

- Используйте формат `${variable.path}`
- Проверьте, что данные есть в контексте сессии
- Добавьте `value` как fallback

### События не срабатывают

- Проверьте, что событие указано в `transitions`
- Убедитесь, что `event_name` указан в `expressions`
- Проверьте формат `eventParams`

## Ссылки

- [Пример workflow](../api/integration_workflow_correct_format.py)
- [Скрипт деплоя](../deploy_correct_format.py)
- [Пример корзины](../diagrams/contract.json)
