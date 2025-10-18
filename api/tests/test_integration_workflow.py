"""
Тестовый workflow для проверки исправленных Integration States
Демонстрирует:
1. Интерполяцию переменных {{variable}}
2. Валидацию dependent_variables
3. Обработку ошибок через error_variable
4. Работу с вложенными структурами и массивами
"""


def test_integration_states_complete():
    """
    Полный workflow для проверки Integration States с:
    - Интерполяцией простых переменных
    - Интерполяцией вложенных структур
    - Валидацией dependent_variables
    - Обработкой ошибок API
    - Множественными API вызовами
    """
    return {
        "states": [
            # ========================================
            # 1. НАЧАЛЬНЫЙ ЭКРАН - Ввод данных пользователя
            # ========================================
            {
                "state_type": "screen",
                "name": "UserInputScreen",
                "screen": {
                    "id": "screen-user-input",
                    "type": "Screen",
                    "name": "Поиск пользователя",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "header": {
                            "id": "section-input-header",
                            "type": "Section",
                            "properties": {
                                "slot": "header",
                                "padding": 16
                            },
                            "children": [
                                {
                                    "id": "text-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "🔍 Поиск информации о пользователе",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000"
                                    }
                                }
                            ]
                        },
                        "body": {
                            "id": "section-input-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16
                            },
                            "children": [
                                {
                                    "id": "text-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "Введите ID пользователя и API ключ для поиска",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "marginBottom": "16px"
                                    }
                                },
                                {
                                    "id": "input-user-id",
                                    "type": "input",
                                    "properties": {
                                        "name": "user_id",
                                        "label": "User ID",
                                        "placeholder": "Например: 1",
                                        "required": True,
                                        "inputType": "text"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "padding": "12px",
                                        "fontSize": "16px",
                                        "borderRadius": "8px",
                                        "border": "1px solid #E5E5E5"
                                    }
                                },
                                {
                                    "id": "input-api-key",
                                    "type": "input",
                                    "properties": {
                                        "name": "api_key",
                                        "label": "API Key",
                                        "placeholder": "Ваш API ключ",
                                        "required": True,
                                        "inputType": "text"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "padding": "12px",
                                        "fontSize": "16px",
                                        "borderRadius": "8px",
                                        "border": "1px solid #E5E5E5"
                                    }
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-input-footer",
                            "type": "Section",
                            "properties": {
                                "slot": "footer",
                                "padding": 16
                            },
                            "children": [
                                {
                                    "id": "button-search",
                                    "type": "button",
                                    "properties": {
                                        "text": "Найти",
                                        "variant": "primary",
                                        "event": "search"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "height": "48px",
                                        "fontSize": "16px",
                                        "fontWeight": 600,
                                        "borderRadius": "8px",
                                        "background": "#007AFF",
                                        "color": "#ffffff",
                                        "border": "none"
                                    }
                                }
                            ]
                        }
                    }
                },
                "transitions": [
                    {"case": "search", "state_id": "ValidateInput"}
                ],
                "expressions": [
                    {"event_name": "search"}
                ],
                "initial_state": True,
                "final_state": False,
            },
            
            # ========================================
            # 2. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ - Валидация ввода
            # ========================================
            {
                "state_type": "technical",
                "name": "ValidateInput",
                "transitions": [
                    {"variable": "input_valid", "case": "True", "state_id": "FetchUserProfile"},
                    {"variable": "input_valid", "case": "False", "state_id": "ValidationErrorScreen"}
                ],
                "expressions": [
                    {
                        "variable": "input_valid",
                        "dependent_variables": ["user_id", "api_key"],
                        "expression": "len(user_id) > 0 and len(api_key) > 0"
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # ========================================
            # 3. INTEGRATION STATE - Получение профиля пользователя
            # Демонстрирует:
            # - Интерполяцию простых переменных {{user_id}}
            # - dependent_variables валидацию
            # - error_variable для обработки ошибок
            # ========================================
            {
                "state_type": "integration",
                "name": "FetchUserProfile",
                "transitions": [
                    {"variable": "user_profile", "case": None, "state_id": "FetchUserOrders"},
                    {"variable": "profile_error", "case": "True", "state_id": "ProfileErrorScreen"}
                ],
                "expressions": [
                    {
                        "variable": "user_profile",
                        "url": "https://jsonplaceholder.typicode.com/users/{{user_id}}",
                        "params": {},
                        "method": "get",
                        "dependent_variables": ["user_id"],
                        "error_variable": "profile_error"
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # ========================================
            # 4. INTEGRATION STATE - Получение заказов пользователя
            # Демонстрирует:
            # - Интерполяцию в URL и params
            # - Множественные параметры
            # - Обработку ошибок
            # ========================================
            {
                "state_type": "integration",
                "name": "FetchUserOrders",
                "transitions": [
                    {"variable": "orders", "case": None, "state_id": "ProcessOrdersData"},
                    {"variable": "orders_error", "case": "True", "state_id": "OrdersErrorScreen"}
                ],
                "expressions": [
                    {
                        "variable": "orders",
                        "url": "https://jsonplaceholder.typicode.com/posts",
                        "params": {
                            "userId": "{{user_id}}",
                            "_limit": "5"
                        },
                        "method": "get",
                        "dependent_variables": ["user_id"],
                        "error_variable": "orders_error"
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # ========================================
            # 5. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ - Обработка данных заказов
            # ========================================
            {
                "state_type": "technical",
                "name": "ProcessOrdersData",
                "transitions": [
                    {"variable": "has_orders", "case": "True", "state_id": "CreateOrderSummary"},
                    {"variable": "has_orders", "case": "False", "state_id": "NoOrdersScreen"}
                ],
                "expressions": [
                    {
                        "variable": "has_orders",
                        "dependent_variables": ["orders"],
                        "expression": "len(orders) > 0"
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # ========================================
            # 6. INTEGRATION STATE - Создание отчета (POST запрос)
            # Демонстрирует:
            # - POST запрос с body
            # - Интерполяцию вложенных структур
            # - Множественные переменные в params
            # ========================================
            {
                "state_type": "integration",
                "name": "CreateOrderSummary",
                "transitions": [
                    {"variable": "summary", "case": None, "state_id": "DisplayResults"},
                    {"variable": "summary_error", "case": "True", "state_id": "SummaryErrorScreen"}
                ],
                "expressions": [
                    {
                        "variable": "summary",
                        "url": "https://jsonplaceholder.typicode.com/posts",
                        "params": {
                            "title": "Order Summary for User {{user_id}}",
                            "body": "Summary of orders",
                            "userId": "{{user_id}}"
                        },
                        "method": "post",
                        "dependent_variables": ["user_id"],
                        "error_variable": "summary_error"
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # ========================================
            # 7. ЭКРАН - Отображение результатов
            # ========================================
            {
                "state_type": "screen",
                "name": "DisplayResults",
                "screen": {
                    "id": "screen-display-results",
                    "type": "Screen",
                    "name": "Результаты поиска",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "header": {
                            "id": "section-results-header",
                            "type": "Section",
                            "properties": {
                                "slot": "header",
                                "padding": 16,
                                "background": "#ffffff"
                            },
                            "children": [
                                {
                                    "id": "text-results-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "✅ Результаты поиска",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000"
                                    }
                                },
                                {
                                    "id": "text-results-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "Информация о пользователе успешно получена",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "marginTop": "8px"
                                    }
                                }
                            ]
                        },
                        "body": {
                            "id": "section-results-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16
                            },
                            "children": [
                                {
                                    "id": "column-user-profile",
                                    "type": "column",
                                    "properties": {
                                        "spacing": 8,
                                        "padding": 16,
                                        "background": "#ffffff"
                                    },
                                    "style": {
                                        "borderRadius": "8px"
                                    },
                                    "children": [
                                        {
                                            "id": "text-profile-label",
                                            "type": "text",
                                            "properties": {
                                                "content": "👤 Профиль пользователя",
                                                "variant": "subtitle"
                                            },
                                            "style": {
                                                "fontSize": "17px",
                                                "fontWeight": 600
                                            }
                                        },
                                        {
                                            "id": "text-profile-data",
                                            "type": "text",
                                            "properties": {
                                                "content": {
                                                    "reference": "${user_profile}",
                                                    "value": "Загрузка..."
                                                },
                                                "variant": "body"
                                            },
                                            "style": {
                                                "fontSize": "14px",
                                                "color": "#000000",
                                                "whiteSpace": "pre-wrap"
                                            }
                                        }
                                    ]
                                },
                                {
                                    "id": "column-orders",
                                    "type": "column",
                                    "properties": {
                                        "spacing": 8,
                                        "padding": 16,
                                        "background": "#ffffff"
                                    },
                                    "style": {
                                        "borderRadius": "8px"
                                    },
                                    "children": [
                                        {
                                            "id": "text-orders-label",
                                            "type": "text",
                                            "properties": {
                                                "content": "📦 Заказы",
                                                "variant": "subtitle"
                                            },
                                            "style": {
                                                "fontSize": "17px",
                                                "fontWeight": 600
                                            }
                                        },
                                        {
                                            "id": "text-orders-data",
                                            "type": "text",
                                            "properties": {
                                                "content": {
                                                    "reference": "${orders}",
                                                    "value": "Загрузка..."
                                                },
                                                "variant": "body"
                                            },
                                            "style": {
                                                "fontSize": "14px",
                                                "color": "#000000",
                                                "whiteSpace": "pre-wrap"
                                            }
                                        }
                                    ]
                                },
                                {
                                    "id": "column-summary",
                                    "type": "column",
                                    "properties": {
                                        "spacing": 8,
                                        "padding": 16,
                                        "background": "#ffffff"
                                    },
                                    "style": {
                                        "borderRadius": "8px"
                                    },
                                    "children": [
                                        {
                                            "id": "text-summary-label",
                                            "type": "text",
                                            "properties": {
                                                "content": "📊 Отчет",
                                                "variant": "subtitle"
                                            },
                                            "style": {
                                                "fontSize": "17px",
                                                "fontWeight": 600
                                            }
                                        },
                                        {
                                            "id": "text-summary-data",
                                            "type": "text",
                                            "properties": {
                                                "content": {
                                                    "reference": "${summary}",
                                                    "value": "Загрузка..."
                                                },
                                                "variant": "body"
                                            },
                                            "style": {
                                                "fontSize": "14px",
                                                "color": "#000000",
                                                "whiteSpace": "pre-wrap"
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-results-footer",
                            "type": "Section",
                            "properties": {
                                "slot": "footer",
                                "padding": 16,
                                "background": "#ffffff"
                            },
                            "children": [
                                {
                                    "id": "row-footer-buttons",
                                    "type": "row",
                                    "properties": {
                                        "spacing": 12,
                                        "justifyContent": "space-between"
                                    },
                                    "children": [
                                        {
                                            "id": "button-new-search",
                                            "type": "button",
                                            "properties": {
                                                "text": "Новый поиск",
                                                "variant": "secondary",
                                                "event": "new_search"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#F2F2F7",
                                                "color": "#000000",
                                                "border": "none"
                                            }
                                        },
                                        {
                                            "id": "button-exit",
                                            "type": "button",
                                            "properties": {
                                                "text": "Выход",
                                                "variant": "primary",
                                                "event": "exit"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#007AFF",
                                                "color": "#ffffff",
                                                "border": "none"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                "transitions": [
                    {"case": "new_search", "state_id": "UserInputScreen"},
                    {"case": "exit", "state_id": "ExitFlow"}
                ],
                "expressions": [
                    {"event_name": "new_search"},
                    {"event_name": "exit"}
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # ========================================
            # ERROR SCREENS - Обработка различных ошибок
            # ========================================
            {
                "state_type": "screen",
                "name": "ValidationErrorScreen",
                "screen": {
                    "id": "screen-validation-error",
                    "type": "Screen",
                    "name": "Ошибка валидации",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "body": {
                            "id": "section-validation-error-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16,
                                "alignItems": "center",
                                "justifyContent": "center"
                            },
                            "children": [
                                {
                                    "id": "text-error-icon",
                                    "type": "text",
                                    "properties": {
                                        "content": "❌",
                                        "variant": "icon"
                                    },
                                    "style": {
                                        "fontSize": "64px",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "Ошибка валидации",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "Пожалуйста, заполните все обязательные поля",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-message",
                                    "type": "text",
                                    "properties": {
                                        "content": "User ID и API Key не могут быть пустыми",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "14px",
                                        "color": "#FF3B30",
                                        "textAlign": "center",
                                        "padding": "12px",
                                        "background": "#FFE5E5",
                                        "borderRadius": "8px"
                                    }
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-validation-error-footer",
                            "type": "Section",
                            "properties": {
                                "slot": "footer",
                                "padding": 16
                            },
                            "children": [
                                {
                                    "id": "button-retry",
                                    "type": "button",
                                    "properties": {
                                        "text": "Попробовать снова",
                                        "variant": "primary",
                                        "event": "retry"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "height": "48px",
                                        "fontSize": "16px",
                                        "fontWeight": 600,
                                        "borderRadius": "8px",
                                        "background": "#007AFF",
                                        "color": "#ffffff",
                                        "border": "none"
                                    }
                                }
                            ]
                        }
                    }
                },
                "transitions": [
                    {"case": "retry", "state_id": "UserInputScreen"}
                ],
                "expressions": [
                    {"event_name": "retry"}
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "ProfileErrorScreen",
                "screen": {
                    "id": "screen-profile-error",
                    "type": "Screen",
                    "name": "Ошибка профиля",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "body": {
                            "id": "section-profile-error-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16,
                                "alignItems": "center",
                                "justifyContent": "center"
                            },
                            "children": [
                                {
                                    "id": "text-error-icon",
                                    "type": "text",
                                    "properties": {
                                        "content": "⚠️",
                                        "variant": "icon"
                                    },
                                    "style": {
                                        "fontSize": "64px",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "Ошибка загрузки профиля",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "Не удалось получить данные пользователя",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-message",
                                    "type": "text",
                                    "properties": {
                                        "content": {
                                            "reference": "${profile_error}",
                                            "value": "Ошибка сети"
                                        },
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "14px",
                                        "color": "#FF9500",
                                        "textAlign": "center",
                                        "padding": "12px",
                                        "background": "#FFF4E5",
                                        "borderRadius": "8px"
                                    }
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-profile-error-footer",
                            "type": "Section",
                            "properties": {
                                "slot": "footer",
                                "padding": 16
                            },
                            "children": [
                                {
                                    "id": "row-error-buttons",
                                    "type": "row",
                                    "properties": {
                                        "spacing": 12
                                    },
                                    "children": [
                                        {
                                            "id": "button-back",
                                            "type": "button",
                                            "properties": {
                                                "text": "Назад",
                                                "variant": "secondary",
                                                "event": "back"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#F2F2F7",
                                                "color": "#000000",
                                                "border": "none"
                                            }
                                        },
                                        {
                                            "id": "button-retry",
                                            "type": "button",
                                            "properties": {
                                                "text": "Повторить",
                                                "variant": "primary",
                                                "event": "retry"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#007AFF",
                                                "color": "#ffffff",
                                                "border": "none"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                "transitions": [
                    {"case": "retry", "state_id": "FetchUserProfile"},
                    {"case": "back", "state_id": "UserInputScreen"}
                ],
                "expressions": [
                    {"event_name": "retry"},
                    {"event_name": "back"}
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "OrdersErrorScreen",
                "screen": {
                    "id": "screen-orders-error",
                    "type": "Screen",
                    "name": "Ошибка заказов",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "body": {
                            "id": "section-orders-error-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16,
                                "alignItems": "center",
                                "justifyContent": "center"
                            },
                            "children": [
                                {
                                    "id": "text-error-icon",
                                    "type": "text",
                                    "properties": {
                                        "content": "⚠️",
                                        "variant": "icon"
                                    },
                                    "style": {
                                        "fontSize": "64px",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "Ошибка загрузки заказов",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "Не удалось получить список заказов",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-message",
                                    "type": "text",
                                    "properties": {
                                        "content": {
                                            "reference": "${orders_error}",
                                            "value": "Ошибка сети"
                                        },
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "14px",
                                        "color": "#FF9500",
                                        "textAlign": "center",
                                        "padding": "12px",
                                        "background": "#FFF4E5",
                                        "borderRadius": "8px"
                                    }
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-orders-error-footer",
                            "type": "Section",
                            "properties": {
                                "slot": "footer",
                                "padding": 16
                            },
                            "children": [
                                {
                                    "id": "row-error-buttons",
                                    "type": "row",
                                    "properties": {
                                        "spacing": 12
                                    },
                                    "children": [
                                        {
                                            "id": "button-back",
                                            "type": "button",
                                            "properties": {
                                                "text": "Назад",
                                                "variant": "secondary",
                                                "event": "back"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#F2F2F7",
                                                "color": "#000000",
                                                "border": "none"
                                            }
                                        },
                                        {
                                            "id": "button-retry",
                                            "type": "button",
                                            "properties": {
                                                "text": "Повторить",
                                                "variant": "primary",
                                                "event": "retry"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#007AFF",
                                                "color": "#ffffff",
                                                "border": "none"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                "transitions": [
                    {"case": "retry", "state_id": "FetchUserOrders"},
                    {"case": "back", "state_id": "UserInputScreen"}
                ],
                "expressions": [
                    {"event_name": "retry"},
                    {"event_name": "back"}
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "SummaryErrorScreen",
                "screen": {
                    "id": "screen-summary-error",
                    "type": "Screen",
                    "name": "Ошибка отчета",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "body": {
                            "id": "section-summary-error-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16,
                                "alignItems": "center",
                                "justifyContent": "center"
                            },
                            "children": [
                                {
                                    "id": "text-error-icon",
                                    "type": "text",
                                    "properties": {
                                        "content": "⚠️",
                                        "variant": "icon"
                                    },
                                    "style": {
                                        "fontSize": "64px",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "Ошибка создания отчета",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "Не удалось создать итоговый отчет",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-error-message",
                                    "type": "text",
                                    "properties": {
                                        "content": {
                                            "reference": "${summary_error}",
                                            "value": "Ошибка сети"
                                        },
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "14px",
                                        "color": "#FF9500",
                                        "textAlign": "center",
                                        "padding": "12px",
                                        "background": "#FFF4E5",
                                        "borderRadius": "8px"
                                    }
                                },
                                {
                                    "id": "text-success-note",
                                    "type": "text",
                                    "properties": {
                                        "content": "Но данные пользователя и заказов получены успешно",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "14px",
                                        "color": "#34C759",
                                        "textAlign": "center",
                                        "padding": "12px",
                                        "background": "#E5F8EC",
                                        "borderRadius": "8px"
                                    }
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-summary-error-footer",
                            "type": "Section",
                            "properties": {
                                "slot": "footer",
                                "padding": 16
                            },
                            "children": [
                                {
                                    "id": "row-error-buttons",
                                    "type": "row",
                                    "properties": {
                                        "spacing": 12
                                    },
                                    "children": [
                                        {
                                            "id": "button-back",
                                            "type": "button",
                                            "properties": {
                                                "text": "Назад",
                                                "variant": "secondary",
                                                "event": "back"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#F2F2F7",
                                                "color": "#000000",
                                                "border": "none"
                                            }
                                        },
                                        {
                                            "id": "button-continue",
                                            "type": "button",
                                            "properties": {
                                                "text": "Продолжить",
                                                "variant": "primary",
                                                "event": "continue"
                                            },
                                            "style": {
                                                "flex": 1,
                                                "height": "48px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#007AFF",
                                                "color": "#ffffff",
                                                "border": "none"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                "transitions": [
                    {"case": "continue", "state_id": "DisplayResults"},
                    {"case": "back", "state_id": "UserInputScreen"}
                ],
                "expressions": [
                    {"event_name": "continue"},
                    {"event_name": "back"}
                ],
                "initial_state": False,
                "final_state": False,
            },
            {
                "state_type": "screen",
                "name": "NoOrdersScreen",
                "screen": {
                    "id": "screen-no-orders",
                    "type": "Screen",
                    "name": "Заказы не найдены",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "body": {
                            "id": "section-no-orders-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16,
                                "alignItems": "center",
                                "justifyContent": "center"
                            },
                            "children": [
                                {
                                    "id": "text-icon",
                                    "type": "text",
                                    "properties": {
                                        "content": "📭",
                                        "variant": "icon"
                                    },
                                    "style": {
                                        "fontSize": "64px",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "Заказы не найдены",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "У этого пользователя пока нет заказов",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "column-user-info",
                                    "type": "column",
                                    "properties": {
                                        "spacing": 8,
                                        "padding": 16,
                                        "background": "#ffffff"
                                    },
                                    "style": {
                                        "borderRadius": "8px",
                                        "marginTop": "16px",
                                        "width": "100%"
                                    },
                                    "children": [
                                        {
                                            "id": "text-profile-label",
                                            "type": "text",
                                            "properties": {
                                                "content": "👤 Профиль",
                                                "variant": "subtitle"
                                            },
                                            "style": {
                                                "fontSize": "17px",
                                                "fontWeight": 600
                                            }
                                        },
                                        {
                                            "id": "text-profile-data",
                                            "type": "text",
                                            "properties": {
                                                "content": {
                                                    "reference": "${user_profile}",
                                                    "value": "Загрузка..."
                                                },
                                                "variant": "body"
                                            },
                                            "style": {
                                                "fontSize": "14px",
                                                "color": "#000000",
                                                "whiteSpace": "pre-wrap"
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-no-orders-footer",
                            "type": "Section",
                            "properties": {
                                "slot": "footer",
                                "padding": 16
                            },
                            "children": [
                                {
                                    "id": "button-back",
                                    "type": "button",
                                    "properties": {
                                        "text": "Назад к поиску",
                                        "variant": "primary",
                                        "event": "back"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "height": "48px",
                                        "fontSize": "16px",
                                        "fontWeight": 600,
                                        "borderRadius": "8px",
                                        "background": "#007AFF",
                                        "color": "#ffffff",
                                        "border": "none"
                                    }
                                }
                            ]
                        }
                    }
                },
                "transitions": [
                    {"case": "back", "state_id": "UserInputScreen"}
                ],
                "expressions": [
                    {"event_name": "back"}
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # ========================================
            # ФИНАЛЬНОЕ СОСТОЯНИЕ
            # ========================================
            {
                "state_type": "screen",
                "name": "ExitFlow",
                "screen": {
                    "id": "screen-exit",
                    "type": "Screen",
                    "name": "Завершение",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "body": {
                            "id": "section-exit-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 16,
                                "alignItems": "center",
                                "justifyContent": "center"
                            },
                            "children": [
                                {
                                    "id": "text-icon",
                                    "type": "text",
                                    "properties": {
                                        "content": "👋",
                                        "variant": "icon"
                                    },
                                    "style": {
                                        "fontSize": "64px",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "До свидания!",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "24px",
                                        "fontWeight": 700,
                                        "color": "#000000",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-description",
                                    "type": "text",
                                    "properties": {
                                        "content": "Спасибо за использование сервиса поиска",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "15px",
                                        "color": "#8E8E93",
                                        "textAlign": "center"
                                    }
                                },
                                {
                                    "id": "text-success",
                                    "type": "text",
                                    "properties": {
                                        "content": "Workflow завершён успешно",
                                        "variant": "body"
                                    },
                                    "style": {
                                        "fontSize": "14px",
                                        "color": "#34C759",
                                        "textAlign": "center",
                                        "padding": "12px",
                                        "background": "#E5F8EC",
                                        "borderRadius": "8px",
                                        "marginTop": "16px"
                                    }
                                }
                            ]
                        }
                    }
                },
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            },
        ]
    }


def test_integration_interpolation_advanced():
    """
    Продвинутый тест интерполяции с:
    - Множественными переменными в одной строке
    - Вложенными структурами
    - Массивами с интерполяцией
    """
    return {
        "states": [
            {
                "state_type": "screen",
                "name": "InputForm",
                "transitions": [
                    {"case": "submit", "state_id": "SetupData"}
                ],
                "expressions": [
                    {"event_name": "submit"}
                ],
                "initial_state": True,
                "final_state": False,
            },
            
            # Техническое состояние для подготовки данных
            {
                "state_type": "technical",
                "name": "SetupData",
                "transitions": [
                    {"variable": "data_ready", "case": "True", "state_id": "SendComplexRequest"}
                ],
                "expressions": [
                    {
                        "variable": "data_ready",
                        "dependent_variables": ["first_name", "last_name", "email", "city"],
                        "expression": "True"
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            # Integration state с вложенными структурами
            {
                "state_type": "integration",
                "name": "SendComplexRequest",
                "transitions": [
                    {"variable": "response", "case": None, "state_id": "ShowResult"}
                ],
                "expressions": [
                    {
                        "variable": "response",
                        "url": "https://jsonplaceholder.typicode.com/posts",
                        "params": {
                            "title": "{{first_name}} {{last_name}}",
                            "body": "User from {{city}}",
                            "email": "{{email}}",
                            "tags": ["user_{{first_name}}", "city_{{city}}"]
                        },
                        "method": "post",
                        "dependent_variables": ["first_name", "last_name", "email", "city"],
                        "error_variable": "api_error"
                    }
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            {
                "state_type": "screen",
                "name": "ShowResult",
                "transitions": [
                    {"case": "done", "state_id": "Complete"}
                ],
                "expressions": [
                    {"event_name": "done"}
                ],
                "initial_state": False,
                "final_state": False,
            },
            
            {
                "state_type": "screen",
                "name": "Complete",
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            }
        ]
    }


def get_test_scenarios():
    """
    Тестовые сценарии для проверки различных случаев
    """
    return {
        # ========================================
        # Сценарий 1: Успешный путь
        # ========================================
        "success_path": {
            "description": "Успешное получение профиля и заказов",
            "events": [
                {
                    "event_name": None,  # Первый вход
                    "context": {
                        "user_id": "1",
                        "api_key": "test-api-key-123"
                    }
                },
                {
                    "event_name": "search",
                    "context": {}
                },
                # После FetchUserProfile автоматически перейдет к FetchUserOrders
                # После FetchUserOrders -> ProcessOrdersData -> CreateOrderSummary -> DisplayResults
                {
                    "event_name": "exit",
                    "context": {}
                }
            ],
            "expected_context_variables": [
                "user_id",
                "api_key",
                "user_profile",  # От FetchUserProfile
                "orders",  # От FetchUserOrders
                "summary"  # От CreateOrderSummary
            ],
            "expected_final_state": "ExitFlow"
        },
        
        # ========================================
        # Сценарий 2: Ошибка валидации
        # ========================================
        "validation_error": {
            "description": "Пустой user_id - ошибка валидации",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "user_id": "",  # Пустой!
                        "api_key": "test-key"
                    }
                },
                {
                    "event_name": "search",
                    "context": {}
                },
                {
                    "event_name": "retry",
                    "context": {
                        "user_id": "1",  # Исправили
                        "api_key": "test-key"
                    }
                },
                {
                    "event_name": "search",
                    "context": {}
                },
                {
                    "event_name": "exit",
                    "context": {}
                }
            ],
            "expected_final_state": "ExitFlow"
        },
        
        # ========================================
        # Сценарий 3: Несуществующий пользователь
        # ========================================
        "user_not_found": {
            "description": "API вернет ошибку для несуществующего ID",
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "user_id": "99999",  # Несуществующий
                        "api_key": "test-key"
                    }
                },
                {
                    "event_name": "search",
                    "context": {}
                },
                # API может вернуть ошибку, используем error_variable
                {
                    "event_name": "back",
                    "context": {}
                }
            ],
            "expected_context_variables": [
                "user_id",
                "profile_error"  # Ошибка должна быть сохранена
            ]
        },
        
        # ========================================
        # Сценарий 4: Продвинутая интерполяция
        # ========================================
        "advanced_interpolation": {
            "description": "Проверка интерполяции множественных переменных",
            "workflow": test_integration_interpolation_advanced(),
            "events": [
                {
                    "event_name": None,
                    "context": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "city": "Moscow"
                    }
                },
                {
                    "event_name": "submit",
                    "context": {}
                },
                {
                    "event_name": "done",
                    "context": {}
                }
            ],
            "expected_interpolated_params": {
                "title": "John Doe",  # {{first_name}} {{last_name}}
                "body": "User from Moscow",  # {{city}}
                "email": "john.doe@example.com",  # {{email}}
                "tags": ["user_John", "city_Moscow"]  # Массив с интерполяцией
            },
            "expected_final_state": "Complete"
        }
    }


# ========================================
# ИНСТРУКЦИИ ПО ЗАПУСКУ ТЕСТА
# ========================================
"""
ШАГИ ДЛЯ ТЕСТИРОВАНИЯ:

1. Сохраните workflow в MongoDB:
   
   POST http://localhost:8080/workflow/save
   Content-Type: application/json
   
   {
       "states": <результат test_integration_states_complete()>,
       "predefined_context": {}
   }
   
   Ответ: {"wf_description_id": "abc123..."}

2. Запустите workflow с начальным контекстом:
   
   POST http://localhost:8080/client/workflow
   Content-Type: application/json
   
   {
       "client_session_id": "test-session-001",
       "client_workflow_id": "abc123...",
       "context": {
           "user_id": "1",
           "api_key": "test-api-key-123"
       }
   }
   
   Ответ: {"screen": {...}, "state": "UserInputScreen"}

3. Отправьте событие "search":
   
   POST http://localhost:8080/client/event
   Content-Type: application/json
   
   {
       "client_session_id": "test-session-001",
       "event_name": "search",
       "context": {}
   }
   
   Workflow автоматически выполнит:
   - ValidateInput (технический state)
   - FetchUserProfile (integration state с интерполяцией {{user_id}})
   - FetchUserOrders (integration state)
   - ProcessOrdersData (технический state)
   - CreateOrderSummary (POST запрос с интерполяцией)
   - Вернет экран DisplayResults

4. Проверьте логи для интерполяции:
   
   В логах сервера должны быть:
   
   INFO: Integration request: GET https://jsonplaceholder.typicode.com/users/1
   DEBUG: Original params: {}
   DEBUG: Interpolated params: {}
   
   INFO: Integration request: GET https://jsonplaceholder.typicode.com/posts
   DEBUG: Original params: {'userId': '{{user_id}}', '_limit': '5'}
   DEBUG: Interpolated params: {'userId': '1', '_limit': '5'}
   
   INFO: Integration request: POST https://jsonplaceholder.typicode.com/posts
   DEBUG: Original params: {'title': 'Order Summary for User {{user_id}}', ...}
   DEBUG: Interpolated params: {'title': 'Order Summary for User 1', ...}

5. Проверьте контекст сессии:
   
   GET http://localhost:8080/session/test-session-001
   
   Должен содержать:
   {
       "user_id": "1",
       "api_key": "test-api-key-123",
       "user_profile": {...},  // Результат от API
       "orders": [...],        // Массив заказов
       "summary": {...}        // Созданный отчет
   }

6. Тест обработки ошибок (опционально):
   
   Используйте несуществующий user_id:
   
   {
       "context": {
           "user_id": "99999",
           "api_key": "test-key"
       }
   }
   
   Если API вернет ошибку, проверьте:
   - context["profile_error"] должен содержать информацию об ошибке
   - Workflow перейдет в ProfileErrorScreen

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:

✅ Интерполяция работает: {{user_id}} заменяется на "1"
✅ Dependent variables проверяются перед запросом
✅ API запросы выполняются успешно
✅ Результаты сохраняются в контекст
✅ Error handling работает через error_variable
✅ Логи показывают Original и Interpolated params
✅ Workflow проходит через все Integration States
"""


if __name__ == "__main__":
    import json
    
    print("=" * 80)
    print("ТЕСТОВЫЙ WORKFLOW ДЛЯ INTEGRATION STATES")
    print("=" * 80)
    
    workflow = test_integration_states_complete()
    print("\n1. Основной workflow (JSON для POST /workflow/save):")
    print(json.dumps(workflow, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("2. Тестовые сценарии:")
    print("=" * 80)
    
    scenarios = get_test_scenarios()
    for name, scenario in scenarios.items():
        print(f"\n{name}:")
        print(f"  Описание: {scenario['description']}")
        print(f"  События: {len(scenario['events'])}")
        if 'expected_final_state' in scenario:
            print(f"  Ожидаемое финальное состояние: {scenario['expected_final_state']}")
    
    print("\n" + "=" * 80)
    print("3. Продвинутый workflow (интерполяция массивов и вложенных структур):")
    print("=" * 80)
    
    advanced = test_integration_interpolation_advanced()
    print(json.dumps(advanced, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("📚 Инструкции по запуску - см. docstring выше")
    print("=" * 80)
