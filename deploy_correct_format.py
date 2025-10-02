"""
Скрипт деплоя workflow с правильным форматом экранов (sections: header/body/footer)
"""
import requests
import json
import sys
from typing import Dict, Any


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")


def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")


def check_server(base_url: str) -> bool:
    """Проверка доступности сервера"""
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        # Сервер работает, если отвечает (даже если 404)
        if response.status_code in [200, 404]:
            print_success(f"Сервер доступен: {base_url}")
            return True
        else:
            print_error(f"Сервер вернул статус {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Не удалось подключиться к серверу: {e}")
        return False


def load_workflow() -> Dict[str, Any]:
    """Загрузка workflow из модуля"""
    try:
        from api.integration_workflow_correct_format import get_integration_workflow_with_correct_screens
        workflow = get_integration_workflow_with_correct_screens()
        
        # Статистика
        stats = {
            "total": len(workflow["states"]),
            "screen": len([s for s in workflow["states"] if s["state_type"] == "screen"]),
            "integration": len([s for s in workflow["states"] if s["state_type"] == "integration"]),
            "technical": len([s for s in workflow["states"] if s["state_type"] == "technical"]),
            "with_sections": len([
                s for s in workflow["states"] 
                if s.get("state_type") == "screen" 
                and "screen" in s 
                and "sections" in s.get("screen", {})
            ])
        }
        
        print_success(f"Workflow загружен: {stats['total']} states")
        print(f"  • Screen states: {stats['screen']}")
        print(f"    - С sections (header/body/footer): {stats['with_sections']}")
        print(f"  • Integration states: {stats['integration']}")
        print(f"  • Technical states: {stats['technical']}")
        
        return workflow
    except Exception as e:
        print_error(f"Ошибка при загрузке workflow: {e}")
        sys.exit(1)


def save_workflow_locally(workflow: Dict[str, Any], filename: str = "workflow_correct_format.json"):
    """Сохранение workflow в файл"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print_success(f"Workflow сохранен локально: {filename}")
    except Exception as e:
        print_warning(f"Не удалось сохранить workflow локально: {e}")


def deploy_workflow(base_url: str, workflow: Dict[str, Any]) -> str:
    """Деплой workflow на сервер"""
    try:
        print_info("Отправка workflow на сервер...")
        
        # Подготовка данных
        states = workflow["states"]
        
        # Отправка на сервер
        response = requests.post(
            f"{base_url}/workflow/save",
            json={"states": states},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            workflow_id = result.get("wf_description_id")  # Правильный ключ!
            screens_saved = result.get("screens_saved", 0)
            
            print_success(f"Workflow успешно сохранен!")
            print(f"  • Workflow ID: {Colors.CYAN}{workflow_id}{Colors.ENDC}")
            print(f"  • Screens сохранено: {Colors.CYAN}{screens_saved}{Colors.ENDC}")
            
            return workflow_id
        else:
            print_error(f"Ошибка при сохранении workflow: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Ошибка при деплое workflow: {e}")
        sys.exit(1)


def create_test_session(base_url: str, workflow_id: str) -> str:
    """Создание тестовой сессии"""
    try:
        session_id = f"test-session-{workflow_id}"
        
        print_info(f"Создание тестовой сессии: {session_id}")
        
        # Сессия создается через /client/workflow без event_name (инициализация)
        response = requests.post(
            f"{base_url}/client/workflow",
            json={
                "client_workflow_id": workflow_id,
                "client_session_id": session_id,
                "context": {}
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            current_state = result.get("current_state")
            
            print_success(f"Сессия создана!")
            print(f"  • Session ID: {Colors.CYAN}{session_id}{Colors.ENDC}")
            print(f"  • Начальное состояние: {Colors.CYAN}{current_state}{Colors.ENDC}")
            
            # Показываем информацию о первом экране
            if "screen" in result:
                display_screen_preview(result["screen"])
            
            return session_id
        else:
            print_error(f"Ошибка при создании сессии: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Ошибка при создании сессии: {e}")
        sys.exit(1)


def display_screen_preview(screen: Dict[str, Any]):
    """Отображение превью экрана"""
    print(f"\n{Colors.BOLD}📱 Первый экран:{Colors.ENDC}")
    print(f"  • ID: {screen.get('id', 'N/A')}")
    print(f"  • Тип: {screen.get('type', 'N/A')}")
    print(f"  • Название: {screen.get('name', 'N/A')}")
    
    sections = screen.get("sections", {})
    if sections:
        print(f"  • Секции:")
        for section_name in ["header", "body", "footer"]:
            if section_name in sections:
                section = sections[section_name]
                children_count = len(section.get("children", []))
                print(f"    - {section_name}: {children_count} компонентов")


def generate_test_commands(base_url: str, session_id: str):
    """Генерация команд для тестирования"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}🧪 Команды для тестирования:{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    # 1. Отправка события search
    print(f"{Colors.BOLD}1. Отправить search event (ввод user_id и api_key):{Colors.ENDC}")
    cmd1 = f"""curl -X POST {base_url}/client/workflow \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "client_session_id": "{session_id}",
    "event_name": "search",
    "context": {{
      "user_id": "1",
      "api_key": "test-api-key-123"
    }}
  }}'"""
    print(f"{Colors.CYAN}{cmd1}{Colors.ENDC}\n")
    
    # 2. Отправка события load_orders
    print(f"{Colors.BOLD}2. Загрузить заказы:{Colors.ENDC}")
    cmd2 = f"""curl -X POST {base_url}/client/workflow \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "client_session_id": "{session_id}",
    "event_name": "load_orders",
    "context": {{}}
  }}'"""
    print(f"{Colors.CYAN}{cmd2}{Colors.ENDC}\n")
    
    # 3. Создание отчета
    print(f"{Colors.BOLD}3. Создать отчет:{Colors.ENDC}")
    cmd3 = f"""curl -X POST {base_url}/client/workflow \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "client_session_id": "{session_id}",
    "event_name": "create_summary",
    "context": {{}}
  }}'"""
    print(f"{Colors.CYAN}{cmd3}{Colors.ENDC}\n")
    
    # 4. Новый поиск
    print(f"{Colors.BOLD}4. Начать новый поиск:{Colors.ENDC}")
    cmd4 = f"""curl -X POST {base_url}/client/workflow \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "client_session_id": "{session_id}",
    "event_name": "new_search",
    "context": {{}}
  }}'"""
    print(f"{Colors.CYAN}{cmd4}{Colors.ENDC}\n")
    
    # 5. Проверка текущего состояния
    print(f"{Colors.BOLD}5. Проверить текущее состояние:{Colors.ENDC}")
    cmd5 = f"""curl -X GET {base_url}/client/workflow/{session_id}"""
    print(f"{Colors.CYAN}{cmd5}{Colors.ENDC}\n")
    
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")


def main():
    BASE_URL = "http://localhost:8080"
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}🚀 Деплой Workflow с правильным форматом экранов{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    # 1. Проверка сервера
    print_info("Шаг 1: Проверка доступности сервера...")
    if not check_server(BASE_URL):
        sys.exit(1)
    print()
    
    # 2. Загрузка workflow
    print_info("Шаг 2: Загрузка workflow...")
    workflow = load_workflow()
    print()
    
    # 3. Сохранение локально
    print_info("Шаг 3: Сохранение workflow локально...")
    save_workflow_locally(workflow)
    print()
    
    # 4. Деплой на сервер
    print_info("Шаг 4: Деплой workflow на сервер...")
    workflow_id = deploy_workflow(BASE_URL, workflow)
    print()
    
    # 5. Создание тестовой сессии
    print_info("Шаг 5: Создание тестовой сессии...")
    session_id = create_test_session(BASE_URL, workflow_id)
    print()
    
    # 6. Генерация команд для тестирования
    generate_test_commands(BASE_URL, session_id)
    
    print_success("Деплой завершен успешно! ✨")
    print(f"\n{Colors.BOLD}Workflow ID:{Colors.ENDC} {Colors.CYAN}{workflow_id}{Colors.ENDC}")
    print(f"{Colors.BOLD}Session ID:{Colors.ENDC} {Colors.CYAN}{session_id}{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
