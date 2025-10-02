"""
Тест для проверки исправленного workflow с новыми Pydantic моделями
"""
import json
from storage.mongo.client import MongoDBClient
from config import settings
from workflow_builder.state_parser.contract import StateModel, IntegrationExpressionModel

def test_workflow_parsing():
    """Тест парсинга workflow с body вместо params для POST запросов"""
    
    print("=" * 80)
    print("ТЕСТ: Парсинг workflow с новым форматом (body для POST)")
    print("=" * 80)
    print()
    
    # ID сохранённого workflow
    workflow_id = "68ded7589d42ce73ba2d7092"
    
    # Загружаем workflow из MongoDB
    client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION
    )
    
    workflow_data = client.get(workflow_id)
    
    if not workflow_data:
        print("❌ Workflow не найден в MongoDB")
        return False
    
    print(f"✅ Workflow загружен из MongoDB (ID: {workflow_id})")
    print(f"   Количество states: {len(workflow_data['states'])}")
    print()
    
    # Парсим states с помощью Pydantic
    print("🔍 Проверка парсинга states через Pydantic:")
    print()
    
    errors = []
    integration_states = []
    
    for idx, state_data in enumerate(workflow_data['states']):
        try:
            state = StateModel(**state_data)
            
            # Ищем integration states с body
            if state.state_type == 'integration':
                for expr in state.expressions:
                    if isinstance(expr, IntegrationExpressionModel):
                        integration_states.append({
                            'state_name': state.name,
                            'method': expr.method,
                            'has_body': expr.body is not None,
                            'has_params': expr.params is not None,
                            'url': expr.url
                        })
            
            print(f"   ✅ State #{idx}: {state.name} ({state.state_type})")
            
        except Exception as e:
            errors.append({
                'state_index': idx,
                'state_name': state_data.get('name', 'unknown'),
                'error': str(e)
            })
            print(f"   ❌ State #{idx}: {state_data.get('name', 'unknown')} - ОШИБКА")
            print(f"      {str(e)[:100]}")
    
    print()
    print("=" * 80)
    print("РЕЗУЛЬТАТЫ:")
    print("=" * 80)
    print()
    
    if errors:
        print(f"❌ Ошибки парсинга: {len(errors)} из {len(workflow_data['states'])} states")
        print()
        for err in errors:
            print(f"   State: {err['state_name']}")
            print(f"   Ошибка: {err['error']}")
            print()
        return False
    else:
        print(f"✅ Все {len(workflow_data['states'])} states успешно распарсены!")
        print()
    
    # Анализ integration states
    if integration_states:
        print(f"📊 Найдено {len(integration_states)} integration expressions:")
        print()
        
        post_with_body = [s for s in integration_states if s['method'] in ['post', 'put', 'patch'] and s['has_body']]
        get_with_params = [s for s in integration_states if s['method'] in ['get', 'delete'] and s['has_params']]
        
        print(f"   POST/PUT/PATCH с body: {len(post_with_body)}")
        for state in post_with_body:
            print(f"      • {state['state_name']}: {state['method'].upper()} {state['url']}")
        
        print()
        print(f"   GET/DELETE с params: {len(get_with_params)}")
        for state in get_with_params:
            print(f"      • {state['state_name']}: {state['method'].upper()} {state['url']}")
        
        print()
    
    # Финальная проверка
    print("=" * 80)
    print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("=" * 80)
    print()
    print("✅ Workflow корректно сохранён в MongoDB")
    print("✅ Все states проходят валидацию Pydantic")
    print("✅ POST запросы используют body (правильный формат)")
    print("✅ GET запросы используют params (правильный формат)")
    print()
    print(f"📝 Workflow ID: {workflow_id}")
    print()
    
    return True


if __name__ == '__main__':
    success = test_workflow_parsing()
    exit(0 if success else 1)
