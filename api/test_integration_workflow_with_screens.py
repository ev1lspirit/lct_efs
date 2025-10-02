"""
Тестовый workflow для проверки Integration States с полными экранами
Готов для запуска на тестовом стенде с UI
Демонстрирует:
1. Интерполяцию переменных {{variable}}
2. Валидацию dependent_variables
3. Обработку ошибок через error_variable
4. Полные экраны с отображением информации
"""


def test_integration_workflow_with_ui():
    """
    Полный workflow с UI для тестового стенда
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
                    "type": "form",
                    "title": "🔍 Поиск информации о пользователе",
                    "description": "Введите данные для получения профиля и заказов пользователя",
                    "fields": [
                        {
                            "id": "user_id",
                            "label": "ID пользователя",
                            "type": "text",
                            "placeholder": "Введите ID (1-10)",
                            "required": True,
                            "validation": {
                                "pattern": "^[1-9][0-9]*$",
                                "message": "ID должен быть числом от 1 до 10"
                            }
                        },
                        {
                            "id": "api_key",
                            "label": "API ключ",
                            "type": "text",
                            "placeholder": "Введите API ключ",
                            "required": True,
                            "default": "test-api-key-123"
                        }
                    ],
                    "actions": [
                        {
                            "id": "search",
                            "label": "Найти",
                            "type": "primary",
                            "event": "search"
                        }
                    ]
                }
            },
            
            # ========================================
            # 2. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ - Валидация ввода
            # ========================================
            {
                "state_type": "technical",
                "name": "ValidateInput",
                "transitions": [
                    {"variable": "input_valid", "case": "True", "state_id": "LoadingScreen"},
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
            # 3. ЭКРАН ЗАГРУЗКИ
            # ========================================
            {
                "state_type": "screen",
                "name": "LoadingScreen",
                "transitions": [
                    {"case": "continue", "state_id": "FetchUserProfile"}
                ],
                "expressions": [
                    {"event_name": "continue"}
                ],
                "initial_state": False,
                "final_state": False,
                "screen": {
                    "type": "loading",
                    "title": "⏳ Загрузка данных...",
                    "description": "Получаем профиль пользователя {{user_id}}",
                    "spinner": True,
                    "auto_continue": True,
                    "auto_continue_delay": 1000
                }
            },
            
            # ========================================
            # 4. INTEGRATION STATE - Получение профиля пользователя
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
            # 5. ЭКРАН - Отображение профиля
            # ========================================
            {
                "state_type": "screen",
                "name": "DisplayProfileScreen",
                "transitions": [
                    {"case": "load_orders", "state_id": "FetchUserOrders"}
                ],
                "expressions": [
                    {"event_name": "load_orders"}
                ],
                "initial_state": False,
                "final_state": False,
                "screen": {
                    "type": "info",
                    "title": "👤 Профиль пользователя",
                    "sections": [
                        {
                            "title": "Основная информация",
                            "fields": [
                                {
                                    "label": "ID",
                                    "value": "{{user_profile.id}}",
                                    "type": "text"
                                },
                                {
                                    "label": "Имя",
                                    "value": "{{user_profile.name}}",
                                    "type": "text"
                                },
                                {
                                    "label": "Email",
                                    "value": "{{user_profile.email}}",
                                    "type": "text"
                                },
                                {
                                    "label": "Телефон",
                                    "value": "{{user_profile.phone}}",
                                    "type": "text"
                                },
                                {
                                    "label": "Веб-сайт",
                                    "value": "{{user_profile.website}}",
                                    "type": "link"
                                }
                            ]
                        },
                        {
                            "title": "Адрес",
                            "fields": [
                                {
                                    "label": "Улица",
                                    "value": "{{user_profile.address.street}}",
                                    "type": "text"
                                },
                                {
                                    "label": "Город",
                                    "value": "{{user_profile.address.city}}",
                                    "type": "text"
                                },
                                {
                                    "label": "Индекс",
                                    "value": "{{user_profile.address.zipcode}}",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "title": "Компания",
                            "fields": [
                                {
                                    "label": "Название",
                                    "value": "{{user_profile.company.name}}",
                                    "type": "text"
                                },
                                {
                                    "label": "Слоган",
                                    "value": "{{user_profile.company.catchPhrase}}",
                                    "type": "text"
                                }
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "id": "load_orders",
                            "label": "Загрузить заказы",
                            "type": "primary",
                            "event": "load_orders"
                        }
                    ]
                }
            },
            
            # ========================================
            # 6. INTEGRATION STATE - Получение заказов пользователя
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
            # 7. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ - Обработка данных заказов
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
            # 8. ЭКРАН - Отображение заказов
            # ========================================
            {
                "state_type": "screen",
                "name": "DisplayOrdersScreen",
                "transitions": [
                    {"case": "create_summary", "state_id": "CreateOrderSummary"}
                ],
                "expressions": [
                    {"event_name": "create_summary"}
                ],
                "initial_state": False,
                "final_state": False,
                "screen": {
                    "type": "list",
                    "title": "📦 Заказы пользователя #{{user_id}}",
                    "description": "Найдено заказов: {{orders.length}}",
                    "items": {
                        "source": "orders",
                        "template": {
                            "title": "{{item.title}}",
                            "subtitle": "ID: {{item.id}}",
                            "description": "{{item.body}}",
                            "badge": {
                                "text": "Заказ #{{item.id}}",
                                "color": "blue"
                            }
                        }
                    },
                    "actions": [
                        {
                            "id": "create_summary",
                            "label": "Создать отчет",
                            "type": "primary",
                            "event": "create_summary"
                        },
                        {
                            "id": "back",
                            "label": "Назад",
                            "type": "secondary",
                            "event": "back"
                        }
                    ]
                }
            },
            
            # ========================================
            # 9. INTEGRATION STATE - Создание отчета (POST запрос)
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
            # 10. ЭКРАН - Итоговые результаты
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
                    "type": "success",
                    "title": "✅ Операция завершена успешно!",
                    "icon": "checkmark-circle",
                    "sections": [
                        {
                            "title": "Сводка",
                            "type": "summary",
                            "items": [
                                {
                                    "icon": "👤",
                                    "label": "Пользователь",
                                    "value": "{{user_profile.name}}"
                                },
                                {
                                    "icon": "📧",
                                    "label": "Email",
                                    "value": "{{user_profile.email}}"
                                },
                                {
                                    "icon": "📦",
                                    "label": "Заказов получено",
                                    "value": "{{orders.length}}"
                                },
                                {
                                    "icon": "📄",
                                    "label": "Отчет создан",
                                    "value": "ID: {{summary.id}}"
                                }
                            ]
                        },
                        {
                            "title": "Детали отчета",
                            "type": "card",
                            "content": {
                                "title": "Order Summary for User {{user_id}}",
                                "status": "created",
                                "timestamp": "{{__created_at}}"
                            }
                        }
                    ],
                    "actions": [
                        {
                            "id": "new_search",
                            "label": "Новый поиск",
                            "type": "primary",
                            "event": "new_search"
                        },
                        {
                            "id": "exit",
                            "label": "Выход",
                            "type": "secondary",
                            "event": "exit"
                        }
                    ]
                }
            },
            
            # ========================================
            # ERROR SCREENS - Обработка различных ошибок
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
                "screen": {
                    "type": "error",
                    "title": "⚠️ Ошибка валидации",
                    "icon": "alert-circle",
                    "message": "Введенные данные некорректны",
                    "details": [
                        "ID пользователя должен быть заполнен",
                        "API ключ должен быть заполнен"
                    ],
                    "actions": [
                        {
                            "id": "retry",
                            "label": "Попробовать снова",
                            "type": "primary",
                            "event": "retry"
                        }
                    ]
                }
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
                "screen": {
                    "type": "error",
                    "title": "❌ Ошибка загрузки профиля",
                    "icon": "close-circle",
                    "message": "Не удалось получить профиль пользователя {{user_id}}",
                    "details": [
                        "Возможные причины:",
                        "• Пользователь с таким ID не существует",
                        "• Проблемы с подключением к API",
                        "• Некорректный API ключ"
                    ],
                    "error_info": {
                        "message": "{{profile_error}}",
                        "code": "PROFILE_FETCH_ERROR"
                    },
                    "actions": [
                        {
                            "id": "retry",
                            "label": "Повторить",
                            "type": "primary",
                            "event": "retry"
                        },
                        {
                            "id": "back",
                            "label": "Изменить данные",
                            "type": "secondary",
                            "event": "back"
                        }
                    ]
                }
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
                "screen": {
                    "type": "error",
                    "title": "❌ Ошибка загрузки заказов",
                    "icon": "close-circle",
                    "message": "Не удалось получить заказы пользователя {{user_id}}",
                    "details": [
                        "Возможные причины:",
                        "• Проблемы с подключением к API",
                        "• Таймаут запроса",
                        "• Некорректный формат данных"
                    ],
                    "error_info": {
                        "message": "{{orders_error}}",
                        "code": "ORDERS_FETCH_ERROR"
                    },
                    "actions": [
                        {
                            "id": "retry",
                            "label": "Повторить",
                            "type": "primary",
                            "event": "retry"
                        },
                        {
                            "id": "back",
                            "label": "Вернуться",
                            "type": "secondary",
                            "event": "back"
                        }
                    ]
                }
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
                "screen": {
                    "type": "warning",
                    "title": "⚠️ Ошибка создания отчета",
                    "icon": "alert-triangle",
                    "message": "Не удалось создать отчет, но данные успешно получены",
                    "details": [
                        "Профиль пользователя загружен",
                        "Заказы получены",
                        "Создание отчета не выполнено"
                    ],
                    "error_info": {
                        "message": "{{summary_error}}",
                        "code": "SUMMARY_CREATE_ERROR"
                    },
                    "actions": [
                        {
                            "id": "continue",
                            "label": "Продолжить без отчета",
                            "type": "primary",
                            "event": "continue"
                        },
                        {
                            "id": "back",
                            "label": "Начать заново",
                            "type": "secondary",
                            "event": "back"
                        }
                    ]
                }
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
                "screen": {
                    "type": "info",
                    "title": "ℹ️ Заказы не найдены",
                    "icon": "information-circle",
                    "message": "У пользователя {{user_profile.name}} пока нет заказов",
                    "illustration": "empty-box",
                    "actions": [
                        {
                            "id": "back",
                            "label": "Искать другого пользователя",
                            "type": "primary",
                            "event": "back"
                        }
                    ]
                }
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
                "screen": {
                    "type": "complete",
                    "title": "👋 До свидания!",
                    "message": "Спасибо за использование системы",
                    "icon": "hand-wave"
                }
            }
        ]
    }


# Вспомогательная функция для сохранения в файл
def save_workflow_to_file(filename="integration_workflow_with_screens.json"):
    """Сохраняет workflow в JSON файл"""
    import json
    workflow = test_integration_workflow_with_ui()
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"Workflow сохранен в {filename}")


if __name__ == "__main__":
    # Для тестирования - выводим количество states
    workflow = test_integration_workflow_with_ui()
    print(f"Создан workflow с {len(workflow['states'])} states:")
    
    screen_states = [s for s in workflow['states'] if s['state_type'] == 'screen']
    integration_states = [s for s in workflow['states'] if s['state_type'] == 'integration']
    technical_states = [s for s in workflow['states'] if s['state_type'] == 'technical']
    
    print(f"  • Screen states: {len(screen_states)}")
    print(f"  • Integration states: {len(integration_states)}")
    print(f"  • Technical states: {len(technical_states)}")
    
    # Сохраняем в файл
    save_workflow_to_file()
