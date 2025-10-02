"""
Тестовый workflow для Integration States с правильным форматом экранов
Использует реальный формат экранов с sections (header/body/footer) и компонентной структурой
"""


def get_integration_workflow_with_correct_screens():
    """
    Полный workflow с Integration States и правильно оформленными экранами
    """
    return {
        "states": [
            # ========================================
            # 1. НАЧАЛЬНЫЙ ЭКРАН - Ввод данных пользователя
            # ========================================
            {
                "state_type": "screen",
                "name": "UserInputScreen",
                "transitions": [
                    {"case": "search", "state_id": "ValidateInput"}
                ],
                "expressions": [
                    {"event_name": "search"}
                ],
                "initial_state": True,
                "final_state": False,
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
                                "padding": 16,
                                "spacing": 0,
                                "background": "#ffffff"
                            },
                            "style": {
                                "width": "100%",
                                "borderBottom": "1px solid #E5E5E5"
                            },
                            "children": [
                                {
                                    "id": "text-header-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "🔍 Поиск информации о пользователе",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "20px",
                                        "fontWeight": 600,
                                        "color": "#000000",
                                        "textAlign": "center"
                                    }
                                }
                            ]
                        },
                        "body": {
                            "id": "section-input-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 20,
                                "spacing": 16,
                                "alignItems": "stretch"
                            },
                            "style": {
                                "flex": "1 1 auto"
                            },
                            "children": [
                                {
                                    "id": "column-form",
                                    "type": "column",
                                    "properties": {
                                        "spacing": 16,
                                        "padding": 20,
                                        "background": "#ffffff"
                                    },
                                    "style": {
                                        "borderRadius": "12px",
                                        "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.1)"
                                    },
                                    "children": [
                                        {
                                            "id": "text-description",
                                            "type": "text",
                                            "properties": {
                                                "content": "Введите данные для получения профиля и заказов",
                                                "variant": "body"
                                            },
                                            "style": {
                                                "fontSize": "14px",
                                                "color": "#666666",
                                                "marginBottom": "12px"
                                            }
                                        },
                                        {
                                            "id": "column-user-id",
                                            "type": "column",
                                            "properties": {
                                                "spacing": 8
                                            },
                                            "children": [
                                                {
                                                    "id": "text-label-user-id",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "ID пользователя *",
                                                        "variant": "label"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "fontWeight": 500,
                                                        "color": "#000000"
                                                    }
                                                },
                                                {
                                                    "id": "input-user-id",
                                                    "type": "input",
                                                    "properties": {
                                                        "placeholder": "Введите ID (1-10)",
                                                        "type": "text",
                                                        "name": "user_id",
                                                        "required": True
                                                    },
                                                    "style": {
                                                        "padding": "12px",
                                                        "fontSize": "16px",
                                                        "border": "1px solid #D1D1D6",
                                                        "borderRadius": "8px",
                                                        "width": "100%"
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "id": "column-api-key",
                                            "type": "column",
                                            "properties": {
                                                "spacing": 8
                                            },
                                            "children": [
                                                {
                                                    "id": "text-label-api-key",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "API ключ *",
                                                        "variant": "label"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "fontWeight": 500,
                                                        "color": "#000000"
                                                    }
                                                },
                                                {
                                                    "id": "input-api-key",
                                                    "type": "input",
                                                    "properties": {
                                                        "placeholder": "Введите API ключ",
                                                        "type": "text",
                                                        "name": "api_key",
                                                        "required": True,
                                                        "value": "test-api-key-123"
                                                    },
                                                    "style": {
                                                        "padding": "12px",
                                                        "fontSize": "16px",
                                                        "border": "1px solid #D1D1D6",
                                                        "borderRadius": "8px",
                                                        "width": "100%"
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "id": "button-search",
                                            "type": "button",
                                            "properties": {
                                                "text": "Найти",
                                                "variant": "primary",
                                                "event": "search"
                                            },
                                            "style": {
                                                "marginTop": "16px",
                                                "padding": "14px 24px",
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "borderRadius": "8px",
                                                "background": "#007AFF",
                                                "color": "#ffffff",
                                                "border": "none",
                                                "width": "100%",
                                                "cursor": "pointer"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            },
            
            # ========================================
            # 2. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ - Валидация
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
            # 3. INTEGRATION STATE - Получение профиля
            # ========================================
            {
                "state_type": "integration",
                "name": "FetchUserProfile",
                "transitions": [
                    {"variable": "user_profile", "case": None, "state_id": "DisplayProfileScreen"},
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
            # 4. ЭКРАН - Отображение профиля
            # ========================================
            {
                "state_type": "screen",
                "name": "DisplayProfileScreen",
                "transitions": [
                    {"case": "load_orders", "state_id": "FetchUserOrders"},
                    {"case": "back", "state_id": "UserInputScreen"}
                ],
                "expressions": [
                    {"event_name": "load_orders"},
                    {"event_name": "back"}
                ],
                "initial_state": False,
                "final_state": False,
                "screen": {
                    "id": "screen-profile",
                    "type": "Screen",
                    "name": "Профиль пользователя",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "header": {
                            "id": "section-profile-header",
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
                            "children": [
                                {
                                    "id": "row-header",
                                    "type": "row",
                                    "properties": {
                                        "spacing": 12,
                                        "alignItems": "center",
                                        "justifyContent": "space-between"
                                    },
                                    "children": [
                                        {
                                            "id": "button-back-profile",
                                            "type": "button",
                                            "properties": {
                                                "text": "←",
                                                "variant": "secondary",
                                                "event": "back"
                                            },
                                            "style": {
                                                "width": "40px",
                                                "height": "40px",
                                                "border": "none",
                                                "background": "transparent",
                                                "fontSize": "24px",
                                                "color": "#007AFF"
                                            }
                                        },
                                        {
                                            "id": "text-profile-title",
                                            "type": "text",
                                            "properties": {
                                                "content": "👤 Профиль пользователя",
                                                "variant": "heading"
                                            },
                                            "style": {
                                                "fontSize": "18px",
                                                "fontWeight": 600,
                                                "color": "#000000",
                                                "flex": 1,
                                                "textAlign": "center"
                                            }
                                        },
                                        {
                                            "id": "spacer",
                                            "type": "text",
                                            "properties": {
                                                "content": ""
                                            },
                                            "style": {
                                                "width": "40px"
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "body": {
                            "id": "section-profile-body",
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
                            "children": [
                                {
                                    "id": "column-profile-info",
                                    "type": "column",
                                    "properties": {
                                        "spacing": 16,
                                        "padding": 16,
                                        "background": "#ffffff"
                                    },
                                    "style": {
                                        "borderRadius": "12px",
                                        "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.1)"
                                    },
                                    "children": [
                                        {
                                            "id": "text-section-main",
                                            "type": "text",
                                            "properties": {
                                                "content": "Основная информация",
                                                "variant": "subtitle"
                                            },
                                            "style": {
                                                "fontSize": "16px",
                                                "fontWeight": 600,
                                                "color": "#000000",
                                                "marginBottom": "8px"
                                            }
                                        },
                                        {
                                            "id": "row-profile-id",
                                            "type": "row",
                                            "properties": {
                                                "spacing": 8,
                                                "justifyContent": "space-between"
                                            },
                                            "style": {
                                                "paddingTop": "8px",
                                                "paddingBottom": "8px",
                                                "borderBottom": "1px solid #F0F0F0"
                                            },
                                            "children": [
                                                {
                                                    "id": "text-id-label",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "ID",
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "color": "#666666"
                                                    }
                                                },
                                                {
                                                    "id": "text-id-value",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": {
                                                            "reference": "${user_profile.id}",
                                                            "value": "1"
                                                        },
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "fontWeight": 500,
                                                        "color": "#000000"
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "id": "row-profile-name",
                                            "type": "row",
                                            "properties": {
                                                "spacing": 8,
                                                "justifyContent": "space-between"
                                            },
                                            "style": {
                                                "paddingTop": "8px",
                                                "paddingBottom": "8px",
                                                "borderBottom": "1px solid #F0F0F0"
                                            },
                                            "children": [
                                                {
                                                    "id": "text-name-label",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "Имя",
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "color": "#666666"
                                                    }
                                                },
                                                {
                                                    "id": "text-name-value",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": {
                                                            "reference": "${user_profile.name}",
                                                            "value": "Loading..."
                                                        },
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "fontWeight": 500,
                                                        "color": "#000000"
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "id": "row-profile-email",
                                            "type": "row",
                                            "properties": {
                                                "spacing": 8,
                                                "justifyContent": "space-between"
                                            },
                                            "style": {
                                                "paddingTop": "8px",
                                                "paddingBottom": "8px",
                                                "borderBottom": "1px solid #F0F0F0"
                                            },
                                            "children": [
                                                {
                                                    "id": "text-email-label",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "Email",
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "color": "#666666"
                                                    }
                                                },
                                                {
                                                    "id": "text-email-value",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": {
                                                            "reference": "${user_profile.email}",
                                                            "value": "Loading..."
                                                        },
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "fontWeight": 500,
                                                        "color": "#007AFF"
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "id": "row-profile-phone",
                                            "type": "row",
                                            "properties": {
                                                "spacing": 8,
                                                "justifyContent": "space-between"
                                            },
                                            "style": {
                                                "paddingTop": "8px",
                                                "paddingBottom": "8px"
                                            },
                                            "children": [
                                                {
                                                    "id": "text-phone-label",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "Телефон",
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "color": "#666666"
                                                    }
                                                },
                                                {
                                                    "id": "text-phone-value",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": {
                                                            "reference": "${user_profile.phone}",
                                                            "value": "Loading..."
                                                        },
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "fontWeight": 500,
                                                        "color": "#000000"
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-profile-footer",
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
                            "children": [
                                {
                                    "id": "button-load-orders",
                                    "type": "button",
                                    "properties": {
                                        "text": "Загрузить заказы",
                                        "variant": "primary",
                                        "event": "load_orders"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "padding": "14px",
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
                }
            },
            
            # ========================================
            # 5. INTEGRATION STATE - Получение заказов
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
            # 6. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ - Обработка заказов
            # ========================================
            {
                "state_type": "technical",
                "name": "ProcessOrdersData",
                "transitions": [
                    {"variable": "has_orders", "case": "True", "state_id": "DisplayOrdersScreen"},
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
            # 7. ЭКРАН - Список заказов
            # ========================================
            {
                "state_type": "screen",
                "name": "DisplayOrdersScreen",
                "transitions": [
                    {"case": "create_summary", "state_id": "CreateOrderSummary"},
                    {"case": "back", "state_id": "DisplayProfileScreen"}
                ],
                "expressions": [
                    {"event_name": "create_summary"},
                    {"event_name": "back"}
                ],
                "initial_state": False,
                "final_state": False,
                "screen": {
                    "id": "screen-orders",
                    "type": "Screen",
                    "name": "Заказы пользователя",
                    "style": {
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "100vh",
                        "backgroundColor": "#F5F5F5"
                    },
                    "sections": {
                        "header": {
                            "id": "section-orders-header",
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
                            "children": [
                                {
                                    "id": "row-orders-header",
                                    "type": "row",
                                    "properties": {
                                        "spacing": 12,
                                        "alignItems": "center",
                                        "justifyContent": "space-between"
                                    },
                                    "children": [
                                        {
                                            "id": "button-back-orders",
                                            "type": "button",
                                            "properties": {
                                                "text": "←",
                                                "variant": "secondary",
                                                "event": "back"
                                            },
                                            "style": {
                                                "width": "40px",
                                                "height": "40px",
                                                "border": "none",
                                                "background": "transparent",
                                                "fontSize": "24px",
                                                "color": "#007AFF"
                                            }
                                        },
                                        {
                                            "id": "text-orders-title",
                                            "type": "text",
                                            "properties": {
                                                "content": "📦 Заказы пользователя",
                                                "variant": "heading"
                                            },
                                            "style": {
                                                "fontSize": "18px",
                                                "fontWeight": 600,
                                                "color": "#000000",
                                                "flex": 1,
                                                "textAlign": "center"
                                            }
                                        },
                                        {
                                            "id": "spacer-orders",
                                            "type": "text",
                                            "properties": {
                                                "content": ""
                                            },
                                            "style": {
                                                "width": "40px"
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "body": {
                            "id": "section-orders-body",
                            "type": "Section",
                            "properties": {
                                "slot": "body",
                                "padding": 16,
                                "spacing": 12
                            },
                            "style": {
                                "flex": "1 1 auto",
                                "overflowY": "auto"
                            },
                            "children": [
                                {
                                    "id": "list-orders",
                                    "type": "list",
                                    "properties": {
                                        "variant": "unordered",
                                        "spacing": 12,
                                        "items": {
                                            "reference": "${orders}",
                                            "value": []
                                        },
                                        "itemAlias": "order"
                                    },
                                    "style": {
                                        "listStyleType": "none",
                                        "padding": 0,
                                        "margin": 0,
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "gap": "12px"
                                    },
                                    "children": [
                                        {
                                            "id": "column-order-item",
                                            "type": "column",
                                            "properties": {
                                                "spacing": 12,
                                                "padding": 16,
                                                "background": "#ffffff"
                                            },
                                            "style": {
                                                "borderRadius": "12px",
                                                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.08)"
                                            },
                                            "children": [
                                                {
                                                    "id": "row-order-header",
                                                    "type": "row",
                                                    "properties": {
                                                        "spacing": 8,
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between"
                                                    },
                                                    "children": [
                                                        {
                                                            "id": "text-order-title",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": {
                                                                    "reference": "${order.title}",
                                                                    "value": "Заказ"
                                                                },
                                                                "variant": "subtitle"
                                                            },
                                                            "style": {
                                                                "fontSize": "16px",
                                                                "fontWeight": 600,
                                                                "color": "#000000",
                                                                "flex": 1
                                                            }
                                                        },
                                                        {
                                                            "id": "text-order-id-badge",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": {
                                                                    "reference": "${order.id}",
                                                                    "value": "#1"
                                                                },
                                                                "variant": "badge"
                                                            },
                                                            "style": {
                                                                "fontSize": "12px",
                                                                "fontWeight": 500,
                                                                "padding": "4px 8px",
                                                                "borderRadius": "12px",
                                                                "background": "#007AFF",
                                                                "color": "#ffffff"
                                                            }
                                                        }
                                                    ]
                                                },
                                                {
                                                    "id": "text-order-body",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": {
                                                            "reference": "${order.body}",
                                                            "value": "Описание заказа..."
                                                        },
                                                        "variant": "body"
                                                    },
                                                    "style": {
                                                        "fontSize": "14px",
                                                        "color": "#666666",
                                                        "lineHeight": "1.5"
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "id": "section-orders-footer",
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
                            "children": [
                                {
                                    "id": "button-create-summary",
                                    "type": "button",
                                    "properties": {
                                        "text": "Создать отчет",
                                        "variant": "primary",
                                        "event": "create_summary"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "padding": "14px",
                                        "fontSize": "16px",
                                        "fontWeight": 600,
                                        "borderRadius": "8px",
                                        "background": "#34C759",
                                        "color": "#ffffff",
                                        "border": "none"
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            
            # ========================================
            # 8. INTEGRATION STATE - Создание отчета
            # ========================================
            {
                "state_type": "integration",
                "name": "CreateOrderSummary",
                "transitions": [
                    {"variable": "summary", "case": None, "state_id": "DisplayResultsScreen"},
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
            # 9. ЭКРАН - Итоговые результаты (продолжение в следующем комментарии из-за ограничения)
            # ========================================
            {
                "state_type": "screen",
                "name": "DisplayResultsScreen",
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
                "screen": {
                    "id": "screen-results",
                    "type": "Screen",
                    "name": "Результаты",
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
                                "spacing": 0,
                                "background": "#34C759"
                            },
                            "style": {
                                "width": "100%"
                            },
                            "children": [
                                {
                                    "id": "text-success-icon",
                                    "type": "text",
                                    "properties": {
                                        "content": "✅",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "48px",
                                        "textAlign": "center",
                                        "marginBottom": "8px"
                                    }
                                },
                                {
                                    "id": "text-success-title",
                                    "type": "text",
                                    "properties": {
                                        "content": "Операция завершена успешно!",
                                        "variant": "heading"
                                    },
                                    "style": {
                                        "fontSize": "20px",
                                        "fontWeight": 600,
                                        "color": "#ffffff",
                                        "textAlign": "center"
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
                            "style": {
                                "flex": "1 1 auto"
                            },
                            "children": [
                                {
                                    "id": "column-summary",
                                    "type": "column",
                                    "properties": {
                                        "spacing": 16,
                                        "padding": 16,
                                        "background": "#ffffff"
                                    },
                                    "style": {
                                        "borderRadius": "12px",
                                        "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.1)"
                                    },
                                    "children": [
                                        {
                                            "id": "text-summary-title",
                                            "type": "text",
                                            "properties": {
                                                "content": "Сводка",
                                                "variant": "subtitle"
                                            },
                                            "style": {
                                                "fontSize": "18px",
                                                "fontWeight": 600,
                                                "color": "#000000",
                                                "marginBottom": "12px"
                                            }
                                        },
                                        {
                                            "id": "row-user-info",
                                            "type": "row",
                                            "properties": {
                                                "spacing": 8,
                                                "alignItems": "center"
                                            },
                                            "style": {
                                                "paddingTop": "8px",
                                                "paddingBottom": "8px"
                                            },
                                            "children": [
                                                {
                                                    "id": "text-user-icon",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "👤",
                                                        "variant": "icon"
                                                    },
                                                    "style": {
                                                        "fontSize": "24px"
                                                    }
                                                },
                                                {
                                                    "id": "column-user-details",
                                                    "type": "column",
                                                    "properties": {
                                                        "spacing": 2,
                                                        "flex": 1
                                                    },
                                                    "children": [
                                                        {
                                                            "id": "text-user-label",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": "Пользователь",
                                                                "variant": "caption"
                                                            },
                                                            "style": {
                                                                "fontSize": "12px",
                                                                "color": "#666666"
                                                            }
                                                        },
                                                        {
                                                            "id": "text-user-value",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": {
                                                                    "reference": "${user_profile.name}",
                                                                    "value": "Загрузка..."
                                                                },
                                                                "variant": "body"
                                                            },
                                                            "style": {
                                                                "fontSize": "16px",
                                                                "fontWeight": 500,
                                                                "color": "#000000"
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "id": "row-orders-count",
                                            "type": "row",
                                            "properties": {
                                                "spacing": 8,
                                                "alignItems": "center"
                                            },
                                            "style": {
                                                "paddingTop": "8px",
                                                "paddingBottom": "8px"
                                            },
                                            "children": [
                                                {
                                                    "id": "text-orders-icon",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "📦",
                                                        "variant": "icon"
                                                    },
                                                    "style": {
                                                        "fontSize": "24px"
                                                    }
                                                },
                                                {
                                                    "id": "column-orders-details",
                                                    "type": "column",
                                                    "properties": {
                                                        "spacing": 2,
                                                        "flex": 1
                                                    },
                                                    "children": [
                                                        {
                                                            "id": "text-orders-label",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": "Заказов получено",
                                                                "variant": "caption"
                                                            },
                                                            "style": {
                                                                "fontSize": "12px",
                                                                "color": "#666666"
                                                            }
                                                        },
                                                        {
                                                            "id": "text-orders-value",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": "5",
                                                                "variant": "body"
                                                            },
                                                            "style": {
                                                                "fontSize": "16px",
                                                                "fontWeight": 500,
                                                                "color": "#000000"
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "id": "row-summary-id",
                                            "type": "row",
                                            "properties": {
                                                "spacing": 8,
                                                "alignItems": "center"
                                            },
                                            "style": {
                                                "paddingTop": "8px",
                                                "paddingBottom": "8px"
                                            },
                                            "children": [
                                                {
                                                    "id": "text-summary-icon",
                                                    "type": "text",
                                                    "properties": {
                                                        "content": "📄",
                                                        "variant": "icon"
                                                    },
                                                    "style": {
                                                        "fontSize": "24px"
                                                    }
                                                },
                                                {
                                                    "id": "column-summary-details",
                                                    "type": "column",
                                                    "properties": {
                                                        "spacing": 2,
                                                        "flex": 1
                                                    },
                                                    "children": [
                                                        {
                                                            "id": "text-summary-label",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": "Отчет создан",
                                                                "variant": "caption"
                                                            },
                                                            "style": {
                                                                "fontSize": "12px",
                                                                "color": "#666666"
                                                            }
                                                        },
                                                        {
                                                            "id": "text-summary-value",
                                                            "type": "text",
                                                            "properties": {
                                                                "content": {
                                                                    "reference": "${summary.id}",
                                                                    "value": "ID: 101"
                                                                },
                                                                "variant": "body"
                                                            },
                                                            "style": {
                                                                "fontSize": "16px",
                                                                "fontWeight": 500,
                                                                "color": "#000000"
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
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
                                "spacing": 12,
                                "background": "#ffffff"
                            },
                            "style": {
                                "borderTop": "1px solid #E5E5E5"
                            },
                            "children": [
                                {
                                    "id": "button-new-search",
                                    "type": "button",
                                    "properties": {
                                        "text": "Новый поиск",
                                        "variant": "primary",
                                        "event": "new_search"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "padding": "14px",
                                        "fontSize": "16px",
                                        "fontWeight": 600,
                                        "borderRadius": "8px",
                                        "background": "#007AFF",
                                        "color": "#ffffff",
                                        "border": "none"
                                    }
                                },
                                {
                                    "id": "button-exit",
                                    "type": "button",
                                    "properties": {
                                        "text": "Выход",
                                        "variant": "secondary",
                                        "event": "exit"
                                    },
                                    "style": {
                                        "width": "100%",
                                        "padding": "14px",
                                        "fontSize": "16px",
                                        "fontWeight": 500,
                                        "borderRadius": "8px",
                                        "background": "transparent",
                                        "color": "#007AFF",
                                        "border": "1px solid #007AFF"
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            
            # ========================================
            # ERROR SCREENS (упрощенные версии)
            # ========================================
            {
                "state_type": "screen",
                "name": "ValidationErrorScreen",
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
                "transitions": [
                    {"case": "continue", "state_id": "DisplayOrdersScreen"},
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
                "transitions": [],
                "expressions": [],
                "initial_state": False,
                "final_state": True,
            }
        ]
    }


if __name__ == "__main__":
    import json
    workflow = get_integration_workflow_with_correct_screens()
    
    # Статистика
    stats = {
        "total": len(workflow["states"]),
        "screen": len([s for s in workflow["states"] if s["state_type"] == "screen"]),
        "integration": len([s for s in workflow["states"] if s["state_type"] == "integration"]),
        "technical": len([s for s in workflow["states"] if s["state_type"] == "technical"]),
        "with_full_screens": len([s for s in workflow["states"] if s.get("state_type") == "screen" and "screen" in s and "sections" in s.get("screen", {})])
    }
    
    print(f"Создан workflow с {stats['total']} states:")
    print(f"  • Screen: {stats['screen']} (полных экранов: {stats['with_full_screens']})")
    print(f"  • Integration: {stats['integration']}")
    print(f"  • Technical: {stats['technical']}")
    
    # Сохраняем
    with open("integration_workflow_correct_format.json", "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    
    print(f"\nWorkflow сохранен в integration_workflow_correct_format.json")
