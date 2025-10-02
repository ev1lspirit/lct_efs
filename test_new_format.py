#!/usr/bin/env python3
"""
Скрипт для тестирования нового формата workflow в MongoDB.
Проверяет:
1. Сохранение workflow с валидацией формата
2. Получение полного workflow с context и screens
3. Правильное использование body вместо params в POST запросах
"""

import json
import logging
from storage.mongo.client import MongoDBClient
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_cart_workflow():
    """Загрузить cart_workflow.json"""
    with open('cart_workflow.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def test_format_validation():
    """Тест валидации формата"""
    logger.info("="*60)
    logger.info("Тест 1: Валидация формата workflow")
    logger.info("="*60)
    
    # Загружаем workflow
    workflow_data = load_cart_workflow()
    
    # Создаём клиент
    client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION
    )
    
    # Проверяем формат integration states
    integration_states = [
        s for s in workflow_data['states'] 
        if s.get('state_type') == 'integration'
    ]
    
    logger.info(f"Найдено {len(integration_states)} integration states")
    
    for state in integration_states:
        state_name = state.get('name', 'Unknown')
        for expr in state.get('expressions', []):
            method = expr.get('method', '').upper()
            has_body = 'body' in expr
            has_params = 'params' in expr
            
            if method in ['POST', 'PUT', 'PATCH']:
                if has_body:
                    logger.info(f"✅ {state_name}: {method} использует 'body' (новый формат)")
                elif has_params:
                    logger.warning(f"⚠️  {state_name}: {method} использует 'params' (старый формат)")
            else:
                logger.debug(f"   {state_name}: {method} - OK")
    
    return workflow_data


def test_save_workflow(workflow_data):
    """Тест сохранения workflow"""
    logger.info("\n" + "="*60)
    logger.info("Тест 2: Сохранение workflow с новым форматом")
    logger.info("="*60)
    
    client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION
    )
    
    # Сохраняем с валидацией
    workflow_id = client.insert_workflow_with_format_validation(workflow_data)
    
    if workflow_id:
        logger.info(f"✅ Workflow успешно сохранён с ID: {workflow_id}")
        return workflow_id
    else:
        logger.error("❌ Ошибка при сохранении workflow")
        return None


def test_save_screens(workflow_data, workflow_id):
    """Тест сохранения screens"""
    logger.info("\n" + "="*60)
    logger.info("Тест 3: Сохранение screens отдельно")
    logger.info("="*60)
    
    screens_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.SCREENS_MONGO_COLLECTION
    )
    
    saved_count = 0
    screen_states = [
        s for s in workflow_data['states']
        if s.get('state_type') == 'screen' and s.get('screen')
    ]
    
    logger.info(f"Найдено {len(screen_states)} screen states")
    
    for state in screen_states:
        state_name = state['name']
        screen_data = state['screen']
        
        try:
            screen_id = screens_client.upsert_screen(
                workflow_id=workflow_id,
                state_id=state_name,
                screen_json=screen_data
            )
            logger.info(f"✅ Screen '{state_name}' сохранён с ID: {screen_id}")
            saved_count += 1
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении screen '{state_name}': {e}")
    
    logger.info(f"\nСохранено {saved_count}/{len(screen_states)} screens")
    return saved_count


def test_save_context(workflow_data, workflow_id):
    """Тест сохранения predefined context"""
    logger.info("\n" + "="*60)
    logger.info("Тест 4: Сохранение predefined context")
    logger.info("="*60)
    
    context_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.WORKFLOW_MONGO_COLLECTION
    )
    
    predefined_context = workflow_data.get('predefined_context', {})
    logger.info(f"Context содержит {len(predefined_context)} переменных")
    
    if not predefined_context:
        logger.warning("⚠️  Predefined context пуст")
        return None
    
    # Сохраняем с тем же ID что и workflow
    context_id = context_client.insert_description(
        predefined_context,
        overriden_id=workflow_id
    )
    
    if context_id:
        logger.info(f"✅ Context сохранён с ID: {context_id}")
        # Показываем первые несколько переменных
        sample_vars = list(predefined_context.keys())[:5]
        logger.info(f"Примеры переменных: {', '.join(sample_vars)}")
        return context_id
    else:
        logger.error("❌ Ошибка при сохранении context")
        return None


def test_retrieve_full_workflow(workflow_id):
    """Тест получения полного workflow"""
    logger.info("\n" + "="*60)
    logger.info("Тест 5: Получение полного workflow")
    logger.info("="*60)
    
    client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION
    )
    
    full_workflow = client.get_workflow_with_context(workflow_id)
    
    if not full_workflow:
        logger.error("❌ Не удалось получить workflow")
        return False
    
    logger.info("✅ Workflow успешно получен")
    logger.info(f"   - States: {len(full_workflow.get('states', []))}")
    logger.info(f"   - Context vars: {len(full_workflow.get('predefined_context', {}))}")
    logger.info(f"   - Screens: {len(full_workflow.get('screens', {}))}")
    
    # Проверяем структуру
    assert '_id' in full_workflow, "Отсутствует _id"
    assert 'states' in full_workflow, "Отсутствуют states"
    assert 'predefined_context' in full_workflow, "Отсутствует predefined_context"
    assert 'screens' in full_workflow, "Отсутствуют screens"
    
    logger.info("✅ Все компоненты workflow на месте")
    return True


def test_screen_retrieval(workflow_id, state_name="CartOverviewScreen"):
    """Тест получения конкретного screen"""
    logger.info("\n" + "="*60)
    logger.info(f"Тест 6: Получение screen '{state_name}'")
    logger.info("="*60)
    
    screens_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.SCREENS_MONGO_COLLECTION
    )
    
    screen = screens_client.get_screen_by_keys(workflow_id, state_name)
    
    if screen:
        logger.info(f"✅ Screen '{state_name}' найден")
        logger.info(f"   - ID: {screen['_id']}")
        logger.info(f"   - Workflow ID: {screen['workflow_id']}")
        logger.info(f"   - State ID: {screen['state_id']}")
        screen_data = screen.get('screen', {})
        logger.info(f"   - Screen name: {screen_data.get('name', 'N/A')}")
        logger.info(f"   - Screen type: {screen_data.get('type', 'N/A')}")
        return True
    else:
        logger.warning(f"⚠️  Screen '{state_name}' не найден")
        return False


def main():
    """Основная функция запуска тестов"""
    logger.info("\n" + "="*60)
    logger.info("ТЕСТИРОВАНИЕ НОВОГО ФОРМАТА WORKFLOW")
    logger.info("="*60)
    
    try:
        # Тест 1: Валидация формата
        workflow_data = test_format_validation()
        
        # Тест 2: Сохранение workflow
        workflow_id = test_save_workflow(workflow_data)
        if not workflow_id:
            logger.error("Не удалось сохранить workflow. Тесты прерваны.")
            return
        
        # Тест 3: Сохранение screens
        screens_saved = test_save_screens(workflow_data, workflow_id)
        
        # Тест 4: Сохранение context
        context_id = test_save_context(workflow_data, workflow_id)
        
        # Тест 5: Получение полного workflow
        success = test_retrieve_full_workflow(workflow_id)
        
        # Тест 6: Получение конкретного screen
        if screens_saved > 0:
            test_screen_retrieval(workflow_id)
        
        # Итоговый отчёт
        logger.info("\n" + "="*60)
        logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("="*60)
        logger.info(f"✅ Workflow ID: {workflow_id}")
        logger.info(f"✅ Context ID: {context_id}")
        logger.info(f"✅ Screens сохранено: {screens_saved}")
        logger.info(f"✅ Полная загрузка: {'Успешно' if success else 'Ошибка'}")
        
        logger.info("\n🎉 Все тесты завершены!")
        logger.info(f"\nДля получения полного workflow используйте:")
        logger.info(f"GET /workflow/{workflow_id}/full")
        
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}", exc_info=True)


if __name__ == "__main__":
    main()
