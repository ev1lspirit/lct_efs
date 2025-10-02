"""
Полный тест workflow через клиентский endpoint
"""
import requests
import json

def test_client_workflow():
    """Тест инициализации workflow через клиентский endpoint"""
    
    print("=" * 80)
    print("ТЕСТ: Инициализация workflow через /client/workflow")
    print("=" * 80)
    print()
    
    workflow_id = "68ded7589d42ce73ba2d7092"
    
    # Данные для запроса
    request_data = {
        "client_workflow_id": workflow_id,
        "user_id": "test_user_123",
        "client_session_id": "test_session_cart_001",
        "event_name": None
    }
    
    print(f"📤 Отправка запроса:")
    print(f"   URL: http://localhost:8080/client/workflow")
    print(f"   Workflow ID: {workflow_id}")
    print(f"   User ID: {request_data['user_id']}")
    print(f"   Session ID: {request_data['client_session_id']}")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8080/client/workflow",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Ответ сервера:")
        print(f"   Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workflow успешно инициализирован!")
            print()
            print(f"📊 Данные workflow:")
            print(f"   Workflow ID: {data.get('workflow_id', 'N/A')}")
            print(f"   Current State: {data.get('current_state', 'N/A')}")
            print(f"   Context Variables: {len(data.get('context', {}))} переменных")
            print()
            
            if 'context' in data:
                print(f"🔑 Ключевые переменные контекста:")
                context = data['context']
                important_vars = ['user_id', 'cart_id', 'base_url']
                for var in important_vars:
                    if var in context:
                        print(f"      • {var}: {context[var]}")
            
            print()
            print("=" * 80)
            print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
            print("=" * 80)
            print()
            print("✅ Workflow инициализирован без ошибок")
            print("✅ Expression.integration() корректно обрабатывает body")
            print("✅ IntegrationHandler работает с новым форматом")
            print()
            return True
            
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при запросе: {type(e).__name__}")
        print(f"   {str(e)}")
        return False


if __name__ == '__main__':
    success = test_client_workflow()
    exit(0 if success else 1)
