"""
Скрипт для прямого сохранения cart_workflow.json в MongoDB
Обходит валидацию Pydantic API
"""
import json
from storage.mongo.client import MongoDBClient
from config import settings

def save_cart_workflow():
    # Загружаем workflow
    with open('cart_workflow.json', 'r', encoding='utf-8') as f:
        workflow_data = json.load(f)

    # Создаём клиент
    client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION
    )

    # Сохраняем workflow
    workflow_id = client.insert_workflow_with_format_validation(workflow_data)

    if workflow_id:
        print(f'✅ Workflow успешно сохранён!')
        print(f'📝 Workflow ID: {workflow_id}')
        print(f'')
        print(f'Теперь сохраняем screens и context...')
        
        # Сохраняем screens
        screens_client = MongoDBClient(
            database=settings.MONGO_DB,
            collection=settings.SCREENS_MONGO_COLLECTION
        )
        
        saved_screens = 0
        for state in workflow_data['states']:
            if state.get('state_type') == 'screen' and state.get('screen'):
                try:
                    screen_id = screens_client.upsert_screen(
                        workflow_id=workflow_id,
                        state_id=state['name'],
                        screen_json=state['screen']
                    )
                    saved_screens += 1
                except Exception as e:
                    print(f'❌ Ошибка при сохранении screen {state["name"]}: {e}')
        
        print(f'✅ Screens сохранено: {saved_screens}')
        
        # Сохраняем context
        context_client = MongoDBClient(
            database=settings.MONGO_DB,
            collection=settings.WORKFLOW_MONGO_COLLECTION
        )
        
        predefined_context = workflow_data.get('predefined_context', {})
        if predefined_context:
            context_id = context_client.insert_description(
                predefined_context,
                overriden_id=workflow_id
            )
            print(f'✅ Context сохранён (ID: {context_id})')
            print(f'✅ Context содержит {len(predefined_context)} переменных')
        
        print(f'')
        print(f'🎉 ВСЁ ГОТОВО!')
        print(f'')
        print(f'📊 Итого:')
        print(f'   - Workflow ID: {workflow_id}')
        print(f'   - States: {len(workflow_data["states"])}')
        print(f'   - Screens: {saved_screens}')
        print(f'   - Context vars: {len(predefined_context)}')
        print(f'')
        print(f'🔍 Как найти workflow в MongoDB:')
        print(f'')
        print(f'   1. Через mongosh:')
        print(f'      mongosh {settings.MONGO_DB}')
        states_collection = settings.STATES_MONGO_COLLECTION
        print(f'      db.{states_collection}.findOne({{"_id": ObjectId("{workflow_id}")}})')
        print(f'')
        print(f'   2. Через API:')
        print(f'      curl http://localhost:8080/workflow/{workflow_id}/full | jq')
        print(f'')
        print(f'   3. Через Python:')
        print(f'      client.get_workflow_with_context("{workflow_id}")')
        
        return workflow_id
    else:
        print('❌ Ошибка при сохранении workflow')
        return None

if __name__ == '__main__':
    save_cart_workflow()
