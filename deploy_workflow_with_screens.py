#!/usr/bin/env python3
"""
Скрипт для загрузки и запуска workflow с UI на тестовом стенде
"""

import requests
import json
import sys
from typing import Optional


# Конфигурация
BASE_URL = "http://localhost:8000"
WORKFLOW_FILE = "integration_workflow_with_screens.json"


class Colors:
    """ANSI цвета для вывода"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Печать заголовка"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}")
    print(f"{text}")
    print(f"{'=' * 80}{Colors.RESET}\n")


def print_success(text: str):
    """Печать успеха"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text: str):
    """Печать ошибки"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text: str):
    """Печать информации"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def print_warning(text: str):
    """Печать предупреждения"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def check_server() -> bool:
    """Проверяет доступность сервера"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return True
    except requests.exceptions.ConnectionError:
        return False


def load_workflow_from_module() -> dict:
    """Загружает workflow из Python модуля"""
    try:
        from api.tests.test_integration_workflow_with_screens import test_integration_workflow_with_ui
        return test_integration_workflow_with_ui()
    except ImportError as e:
        print_error(f"Не удалось импортировать workflow: {e}")
        sys.exit(1)


def save_workflow_to_server(workflow: dict) -> Optional[str]:
    """Сохраняет workflow на сервер"""
    url = f"{BASE_URL}/workflow/save"

    try:
        response = requests.post(
            url,
            json={
                "states": workflow["states"],
                "predefined_context": {}
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            workflow_id = data.get("wf_description_id")
            screens_saved = data.get("screens_saved", 0)
            print_success(f"Workflow сохранён с ID: {workflow_id}")
            print_info(f"Экранов сохранено: {screens_saved}")
            return workflow_id
        else:
            print_error(f"Ошибка сохранения: {response.status_code}")
            print_error(f"Ответ: {response.text[:500]}")
            return None
    except Exception as e:
        print_error(f"Исключение при сохранении: {e}")
        return None


def create_test_session(workflow_id: str) -> Optional[dict]:
    """Создает тестовую сессию"""
    session_id = f"ui-test-session-{workflow_id}"

    try:
        response = requests.post(
            f"{BASE_URL}/client/workflow",
            json={
                "client_session_id": session_id,
                "client_workflow_id": workflow_id,
                "context": {}
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Сессия создана: {session_id}")
            print_info(f"Текущий state: {data.get('current_state')}")
            print_info(f"Тип state: {data.get('state_type')}")
            return {
                "session_id": session_id,
                "workflow_id": workflow_id,
                "data": data
            }
        else:
            print_error(f"Ошибка создания сессии: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Исключение при создании сессии: {e}")
        return None


def display_screen_info(screen_data: dict):
    """Отображает информацию об экране"""
    if not screen_data or "screen" not in screen_data:
        print_warning("Нет данных экрана для отображения")
        return

    screen = screen_data.get("screen", {})

    print(f"\n{Colors.CYAN}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}📺 ЭКРАН: {screen.get('title', 'N/A')}{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}")

    if "description" in screen:
        print(f"\n{screen['description']}")

    # Поля формы
    if "fields" in screen:
        print(f"\n{Colors.BOLD}Поля формы:{Colors.RESET}")
        for field in screen["fields"]:
            required = "🔴" if field.get("required") else "⚪"
            print(f"  {required} {field['label']} ({field['id']})")
            if "placeholder" in field:
                print(f"     └─ Подсказка: {field['placeholder']}")

    # Секции
    if "sections" in screen:
        print(f"\n{Colors.BOLD}Секции:{Colors.RESET}")
        for section in screen["sections"]:
            print(f"\n  📋 {section.get('title', 'Без названия')}")
            if "fields" in section:
                for field in section["fields"]:
                    print(f"     • {field['label']}: {field['value']}")

    # Действия
    if "actions" in screen:
        print(f"\n{Colors.BOLD}Доступные действия:{Colors.RESET}")
        for action in screen["actions"]:
            action_type = action.get("type", "default")
            icon = "🟢" if action_type == "primary" else "⚪"
            print(f"  {icon} [{action['id']}] {action['label']} → event: {action['event']}")

    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}\n")


def generate_test_instructions(session_info: dict):
    """Генерирует инструкции для тестирования"""
    print_header("📝 ИНСТРУКЦИИ ДЛЯ ТЕСТИРОВАНИЯ")

    session_id = session_info["session_id"]
    workflow_id = session_info["workflow_id"]

    print(f"{Colors.BOLD}Информация о сессии:{Colors.RESET}")
    print(f"  • Session ID: {Colors.CYAN}{session_id}{Colors.RESET}")
    print(f"  • Workflow ID: {Colors.CYAN}{workflow_id}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Как тестировать workflow:{Colors.RESET}\n")

    print("1️⃣  Отправка события (заполнение формы):")
    print(f"{Colors.YELLOW}")
    print(f"""   curl -X POST {BASE_URL}/client/workflow \\
     -H 'Content-Type: application/json' \\
     -d '{{
       "client_session_id": "{session_id}",
       "event_name": "search",
       "context": {{
         "user_id": "1",
         "api_key": "test-api-key-123"
       }}
     }}'""")
    print(f"{Colors.RESET}")

    print("2️⃣  Проверка текущего состояния:")
    print(f"{Colors.YELLOW}")
    print(f"""   curl -X POST {BASE_URL}/client/workflow \\
     -H 'Content-Type: application/json' \\
     -d '{{
       "client_session_id": "{session_id}",
       "client_workflow_id": "{workflow_id}",
       "context": {{}}
     }}'""")
    print(f"{Colors.RESET}")

    print("3️⃣  Продолжение workflow (переход дальше):")
    print(f"{Colors.YELLOW}")
    print(f"""   curl -X POST {BASE_URL}/client/workflow \\
     -H 'Content-Type: application/json' \\
     -d '{{
       "client_session_id": "{session_id}",
       "event_name": "load_orders",
       "context": {{}}
     }}'""")
    print(f"{Colors.RESET}")

    print("\n4️⃣  Полный тестовый сценарий:")
    print(f"{Colors.GREEN}")
    print(f"""   # Шаг 1: Начальный экран (UserInputScreen)
   # Шаг 2: Отправить событие 'search' с user_id и api_key
   # Шаг 3: Система загружает профиль (автоматически)
   # Шаг 4: Отобразится экран с профилем (DisplayProfileScreen)
   # Шаг 5: Отправить событие 'load_orders'
   # Шаг 6: Система загружает заказы (автоматически)
   # Шаг 7: Отобразится список заказов (DisplayOrdersScreen)
   # Шаг 8: Отправить событие 'create_summary'
   # Шаг 9: Система создает отчет (автоматически)
   # Шаг 10: Итоговый экран с результатами (DisplayResultsScreen)
   # Шаг 11: Отправить 'exit' для завершения""")
    print(f"{Colors.RESET}")

    print(f"\n{Colors.BOLD}Примеры тестов:{Colors.RESET}\n")

    print("✅ Успешный сценарий:")
    print("   user_id=1, api_key=test-api-key-123")

    print("\n❌ Тест валидации:")
    print("   user_id=\"\", api_key=\"\" (пустые значения)")

    print("\n❌ Тест ошибки API:")
    print("   user_id=999999 (несуществующий пользователь)")


def save_workflow_to_json(workflow: dict, filename: str = "workflow_deployed.json"):
    """Сохраняет workflow в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print_success(f"Workflow сохранен в файл: {filename}")


def main():
    """Основная функция"""
    print_header("🚀 ЗАГРУЗКА WORKFLOW С UI НА ТЕСТОВЫЙ СТЕНД")

    # Проверяем сервер
    print_info("Проверка доступности сервера...")
    if not check_server():
        print_error(f"Сервер недоступен: {BASE_URL}")
        print_info("Запустите сервер: uvicorn api.app:app --host 127.0.0.1 --port 8080")
        sys.exit(1)
    print_success(f"Сервер доступен: {BASE_URL}")

    # Загружаем workflow
    print_info("Загрузка workflow из модуля...")
    workflow = load_workflow_from_module()

    stats = {
        "total": len(workflow["states"]),
        "screen": len([s for s in workflow["states"] if s["state_type"] == "screen"]),
        "integration": len([s for s in workflow["states"] if s["state_type"] == "integration"]),
        "technical": len([s for s in workflow["states"] if s["state_type"] == "technical"])
    }

    print_success(f"Workflow загружен: {stats['total']} states")
    print_info(f"  • Screen: {stats['screen']}, Integration: {stats['integration']}, Technical: {stats['technical']}")

    # Сохраняем локально
    save_workflow_to_json(workflow)

    # Отправляем на сервер
    print_header("📤 СОХРАНЕНИЕ WORKFLOW НА СЕРВЕР")
    workflow_id = save_workflow_to_server(workflow)

    if not workflow_id:
        print_error("Не удалось сохранить workflow")
        sys.exit(1)

    # Создаем тестовую сессию
    print_header("🔧 СОЗДАНИЕ ТЕСТОВОЙ СЕССИИ")
    session_info = create_test_session(workflow_id)

    if not session_info:
        print_error("Не удалось создать сессию")
        sys.exit(1)

    # Отображаем информацию о первом экране
    display_screen_info(session_info["data"])

    # Генерируем инструкции
    generate_test_instructions(session_info)

    # Итоги
    print_header("🎉 ГОТОВО!")
    print_success("Workflow успешно развернут и готов к тестированию")
    print_info(f"Workflow ID: {workflow_id}")
    print_info(f"Session ID: {session_info['session_id']}")

    print(f"\n{Colors.BOLD}Следующие шаги:{Colors.RESET}")
    print("  1. Используйте curl команды выше для тестирования")
    print("  2. Или подключите frontend приложение к этому workflow")
    print("  3. Проверьте логи сервера для отладки")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\nПрервано пользователем")
        sys.exit(0)
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
