#!/usr/bin/env python3
"""
Быстрая проверка структуры тестового workflow
Без запуска сервера - просто выводит JSON
"""

import json
from api.tests.test_integration_workflow import test_integration_states_complete

def main():
    print("=" * 80)
    print("ПРОВЕРКА ТЕСТОВОГО WORKFLOW")
    print("=" * 80)

    workflow = test_integration_states_complete()

    print(f"\n✅ Workflow создан успешно")
    print(f"   Количество states: {len(workflow['states'])}")

    # Проверяем типы states
    state_types = {}
    for state in workflow["states"]:
        st = state.get("state_type")
        state_types[st] = state_types.get(st, 0) + 1

    print(f"\n📊 Типы состояний:")
    for st, count in state_types.items():
        print(f"   • {st}: {count}")

    # Находим Integration States
    integration_states = [s for s in workflow["states"] if s.get("state_type") == "integration"]

    print(f"\n🔗 Integration States ({len(integration_states)}):")
    for state in integration_states:
        expr = state["expressions"][0]
        print(f"\n   {state['name']}:")
        print(f"      URL: {expr['url']}")
        print(f"      Method: {expr['method']}")
        print(f"      Params: {json.dumps(expr['params'], indent=10)[:100]}...")
        if 'dependent_variables' in expr:
            print(f"      Dependent Variables: {expr['dependent_variables']}")
        if 'error_variable' in expr:
            print(f"      Error Variable: {expr['error_variable']}")

    # Проверяем структуру для API
    print(f"\n📤 Формат для POST /workflow/save:")
    print(f"   Отправлять напрямую массив states")
    print(f"   Content-Type: application/json")
    print(f"   Body: {json.dumps(workflow['states'][:1], indent=2)}...")

    # Сохраняем в файл для проверки
    with open('test_workflow.json', 'w', encoding='utf-8') as f:
        json.dump(workflow['states'], f, indent=2, ensure_ascii=False)

    print(f"\n💾 Workflow сохранен в test_workflow.json")
    print(f"   Можно использовать для ручного тестирования")

    print("\n" + "=" * 80)
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 80)

    print("\n📝 Следующие шаги:")
    print("   1. Запустите сервер:")
    print("      uvicorn api.app:app --host 127.0.0.1 --port 8080 --reload")
    print()
    print("   2. Отправьте workflow:")
    print("      curl -X POST http://localhost:8080/workflow/save \\")
    print("           -H 'Content-Type: application/json' \\")
    print("           -d @test_workflow.json")
    print()
    print("   3. Или запустите автоматический тест:")
    print("      python run_integration_test.py")

if __name__ == "__main__":
    main()
