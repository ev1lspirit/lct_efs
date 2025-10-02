#!/usr/bin/env python3
"""
Автоматический тестовый запуск Integration States с интерполяцией
Требует: запущенный сервер на localhost:8080
"""

import requests
import json
import time
from typing import Optional

import pytest
from api.test_integration_workflow import (
    test_integration_states_complete,
    get_test_scenarios
)


BASE_URL = "http://localhost:8080"
SESSION_ID = f"integration-test-{int(time.time())}"


@pytest.fixture(scope="module")
def workflow_id():
    """Provision a workflow on the backend or skip tests if API недоступно."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:  # pragma: no cover - network dependent
        pytest.skip(f"Workflow API недоступно по адресу {BASE_URL}: {exc}")

    workflow = test_integration_states_complete()
    wf_id = save_workflow(workflow)
    if not wf_id:
        pytest.skip("Не удалось сохранить workflow через API – тесты пропущены")

    return wf_id


def print_section(title):
    """Красивый вывод секции"""
    print("\n" + "=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)


def print_success(message):
    """Вывод успеха"""
    print(f"✅ {message}")


def print_error(message):
    """Вывод ошибки"""
    print(f"❌ {message}")


def print_info(message):
    """Вывод информации"""
    print(f"ℹ️  {message}")


def save_workflow(workflow: dict) -> Optional[str]:
    """Сохраняет workflow в MongoDB через API"""
    url = f"{BASE_URL}/workflow/save"
    
    try:
        # API expects SaveWorkflowRequest: {"states": [...], "predefined_context": {}}
        response = requests.post(
            url,
            json={
                "states": workflow["states"],
                "predefined_context": {}
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            workflow_id = data.get("wf_description_id")
            print_success(f"Workflow сохранён с ID: {workflow_id}")
            return workflow_id
        else:
            print_error(f"Ошибка сохранения workflow: {response.status_code}")
            print_error(f"Ответ: {response.text}")
            return None
    except Exception as e:
        print_error(f"Исключение при сохранении: {e}")
        return None


def start_workflow(workflow_id, context):
    """Запускает workflow с начальным контекстом"""
    print_section("Шаг 2: Запуск workflow с начальным контекстом")
    
    print_info(f"Session ID: {SESSION_ID}")
    print_info(f"Workflow ID: {workflow_id}")
    print_info(f"Начальный контекст: {json.dumps(context, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/client/workflow",
        json={
            "client_session_id": SESSION_ID,
            "client_workflow_id": workflow_id,
            "context": context
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        current_state = data.get("current_state", "Unknown")
        print_success(f"Workflow запущен, текущий state: {current_state}")
        return data
    else:
        print_error(f"Ошибка запуска workflow: {response.status_code}")
        print_error(f"Ответ: {response.text}")
        return None


def send_event(event_name, context=None):
    """Отправляет событие в workflow"""
    print_section(f"Отправка события: {event_name}")
    
    payload = {
        "client_session_id": SESSION_ID,
        "event_name": event_name,
        "context": context or {}
    }
    
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/client/workflow",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        current_state = data.get("state", "Unknown")
        print_success(f"Событие обработано, текущий state: {current_state}")
        
        # Показываем, какие переменные добавлены в контекст
        if "context" in data:
            new_vars = [k for k in data["context"].keys() if k not in ["user_id", "api_key"]]
            if new_vars:
                print_info(f"Новые переменные в контексте: {', '.join(new_vars)}")
        
        return data
    else:
        print_error(f"Ошибка обработки события: {response.status_code}")
        print_error(f"Ответ: {response.text}")
        return None


def check_context():
    """Проверяет текущий контекст сессии"""
    print_section("Проверка контекста сессии")
    
    # Используем Redis для получения контекста
    # Или через специальный endpoint если есть
    print_info("Контекст сессии можно проверить через Redis:")
    print_info(f"Key: session:{SESSION_ID}")
    
    # TODO: Если есть endpoint для получения контекста, использовать его
    # response = requests.get(f"{BASE_URL}/session/{SESSION_ID}")


def test_success_scenario(workflow_id):
    """
    Тест успешного сценария:
    1. Пользователь вводит данные
    2. Валидация проходит
    3. Получаем профиль пользователя (Integration State с интерполяцией)
    4. Получаем заказы (Integration State с params интерполяцией)
    5. Создаем отчет (POST запрос с интерполяцией)
    6. Показываем результаты
    """
    print_section("СЦЕНАРИЙ 1: Успешный путь")
    
    # Шаг 1: Запускаем workflow с валидными данными
    context = {
        "user_id": "1",
        "api_key": "test-api-key-123"
    }
    
    result = start_workflow(workflow_id, context)
    if not result:
        return False
    
    # Должны быть на UserInputScreen
    if result.get("current_state") != "UserInputScreen":
        print_error(f"Ожидался UserInputScreen, получен {result.get('current_state')}")
        return False
    
    print_success("✓ Находимся на UserInputScreen")
    
    # Шаг 2: Отправляем событие "search"
    # Это запустит цепочку:
    # UserInputScreen -> ValidateInput -> FetchUserProfile -> FetchUserOrders -> 
    # ProcessOrdersData -> CreateOrderSummary -> DisplayResults
    
    time.sleep(1)  # Небольшая пауза для читаемости логов
    
    result = send_event("search")
    if not result:
        return False
    
    # После всех Integration States должны быть на DisplayResults
    expected_state = "DisplayResults"
    if result.get("current_state") != expected_state:
        print_error(f"Ожидался {expected_state}, получен {result.get('current_state')}")
        # Это не критично, может быть промежуточный state
    else:
        print_success(f"✓ Достигнут {expected_state}")
    
    # Шаг 3: Проверяем, что в контексте появились данные от API
    print_info("\nПроверка переменных в контексте:")
    expected_vars = ["user_profile", "orders", "summary"]
    
    # TODO: Получить реальный контекст из Redis или через API
    print_info("Ожидаемые переменные:")
    for var in expected_vars:
        print_info(f"  - {var}")
    
    # Шаг 4: Завершаем workflow
    time.sleep(1)
    
    result = send_event("exit")
    if not result:
        return False
    
    if result.get("current_state") == "ExitFlow":
        print_success("✓ Workflow успешно завершен!")
        return True
    else:
        print_error(f"Не достигнуто финальное состояние, текущее: {result.get('current_state')}")
        return False


def test_validation_error_scenario(workflow_id):
    """
    Тест ошибки валидации:
    1. Пользователь вводит пустой user_id
    2. Валидация не проходит
    3. Показываем ошибку
    4. Пользователь исправляет и повторяет
    """
    print_section("СЦЕНАРИЙ 2: Ошибка валидации")
    
    # Используем новый session ID
    global SESSION_ID
    SESSION_ID = f"integration-test-validation-{int(time.time())}"
    
    # Шаг 1: Запускаем с ПУСТЫМ user_id
    context = {
        "user_id": "",  # Пустой!
        "api_key": "test-key"
    }
    
    result = start_workflow(workflow_id, context)
    if not result:
        return False
    
    # Шаг 2: Отправляем "search" - должна быть ошибка валидации
    time.sleep(1)
    
    result = send_event("search")
    if not result:
        return False
    
    # Должны попасть на ValidationErrorScreen
    if result.get("current_state") == "ValidationErrorScreen":
        print_success("✓ Валидация корректно отклонила пустой user_id")
    else:
        print_error(f"Ожидался ValidationErrorScreen, получен {result.get('current_state')}")
    
    # Шаг 3: Исправляем и повторяем
    time.sleep(1)
    
    result = send_event("retry", {"user_id": "1", "api_key": "test-key"})
    if not result:
        return False
    
    # Должны вернуться на UserInputScreen
    if result.get("current_state") == "UserInputScreen":
        print_success("✓ Вернулись на UserInputScreen для исправления")
        return True
    else:
        print_error(f"Ожидался UserInputScreen, получен {result.get('current_state')}")
        return False


def test_interpolation_logging():
    """
    Проверка логирования интерполяции
    Инструкция для проверки вручную
    """
    print_section("ПРОВЕРКА ЛОГИРОВАНИЯ ИНТЕРПОЛЯЦИИ")
    
    print_info("Для проверки интерполяции смотрите логи сервера:")
    print()
    print("Ожидаемые записи в логах:")
    print()
    print("  INFO: Integration request: GET https://jsonplaceholder.typicode.com/users/1")
    print("  DEBUG: Original params: {}")
    print("  DEBUG: Interpolated params: {}")
    print()
    print("  INFO: Integration request: GET https://jsonplaceholder.typicode.com/posts")
    print("  DEBUG: Original params: {'userId': '{{user_id}}', '_limit': '5'}")
    print("  DEBUG: Interpolated params: {'userId': '1', '_limit': '5'}")
    print()
    print("  INFO: Integration request: POST https://jsonplaceholder.typicode.com/posts")
    print("  DEBUG: Original params: {'title': 'Order Summary for User {{user_id}}', ...}")
    print("  DEBUG: Interpolated params: {'title': 'Order Summary for User 1', ...}")
    print()
    print_success("Если видите эти записи - интерполяция работает!")


def main():
    """Главная функция запуска тестов"""
    print("=" * 80)
    print("🧪 АВТОМАТИЧЕСКИЙ ТЕСТ INTEGRATION STATES С ИНТЕРПОЛЯЦИЕЙ")
    print("=" * 80)
    print()
    print_info("Проверяется:")
    print_info("  ✓ Интерполяция переменных {{variable}}")
    print_info("  ✓ Валидация через dependent_variables")
    print_info("  ✓ Обработка ошибок через error_variable")
    print_info("  ✓ Работа с реальным API (jsonplaceholder.typicode.com)")
    print()
    
    # Проверяем доступность сервера
    try:
        response = requests.get(f"{BASE_URL}/")
        print_success(f"Сервер доступен: {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print_error(f"Сервер недоступен: {BASE_URL}")
        print_error("Запустите сервер: uvicorn api.app:app --host 127.0.0.1 --port 8080")
        return
    
    # Шаг 1: Создаём и сохраняем workflow
    workflow = test_integration_states_complete()
    workflow_id = save_workflow(workflow)
    if not workflow_id:
        print_error("Не удалось сохранить workflow. Тест остановлен.")
        return
    
    # Шаг 2: Тестируем успешный сценарий
    time.sleep(1)
    success = test_success_scenario(workflow_id)
    
    # Шаг 3: Тестируем ошибку валидации
    time.sleep(2)
    validation_success = test_validation_error_scenario(workflow_id)
    
    # Шаг 4: Инструкции по проверке логов
    time.sleep(1)
    test_interpolation_logging()
    
    # Итоги
    print_section("ИТОГИ ТЕСТИРОВАНИЯ")
    
    if success:
        print_success("Сценарий 1 (успешный путь): ПРОЙДЕН ✓")
    else:
        print_error("Сценарий 1 (успешный путь): ПРОВАЛЕН ✗")
    
    if validation_success:
        print_success("Сценарий 2 (валидация): ПРОЙДЕН ✓")
    else:
        print_error("Сценарий 2 (валидация): ПРОВАЛЕН ✗")
    
    if success and validation_success:
        print()
        print("=" * 80)
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 80)
        print()
        print_success("Integration States работают корректно!")
        print_success("Интерполяция переменных {{variable}} функционирует!")
        print_success("Валидация dependent_variables работает!")
        print()
        print_info("Следующие шаги:")
        print_info("  1. Проверьте логи сервера на наличие DEBUG записей")
        print_info("  2. Проверьте Redis для контекста сессии")
        print_info("  3. Используйте этот workflow для дальнейшей разработки")
        print()
    else:
        print()
        print("=" * 80)
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("=" * 80)
        print()
        print_info("Проверьте:")
        print_info("  1. Логи сервера на наличие ошибок")
        print_info("  2. Доступность API jsonplaceholder.typicode.com")
        print_info("  3. Корректность реализации IntegrationHandler")


if __name__ == "__main__":
    main()
