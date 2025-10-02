#!/usr/bin/env python3
"""
Утилита для диагностики workflows в MongoDB
Использование: python check_workflows.py [workflow_id]
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.mongo.client import MongoDBClient
from config import settings
from bson import ObjectId
from bson.errors import InvalidId


def list_all_workflows():
    """Выводит список всех workflows в MongoDB"""
    print("=" * 80)
    print("📋 Список всех workflows в MongoDB")
    print("=" * 80)
    
    states_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION
    )
    
    try:
        workflows = states_client.get_all()
        
        if not workflows:
            print("⚠️  Workflows не найдены в коллекции '{}'".format(
                settings.STATES_MONGO_COLLECTION
            ))
            print("\n💡 Создайте workflow через POST /workflow/save")
            return []
        
        print(f"\n✅ Найдено workflows: {len(workflows)}")
        print("-" * 80)
        
        workflow_ids = []
        for idx, workflow in enumerate(workflows, 1):
            wf_id = str(workflow.get("_id", "N/A"))
            workflow_ids.append(wf_id)
            states = workflow.get("states", [])
            
            print(f"\n{idx}. Workflow ID: {wf_id}")
            print(f"   Количество состояний: {len(states)}")
            
            if states:
                initial_states = [s for s in states if s.get("initial_state")]
                final_states = [s for s in states if s.get("final_state")]
                
                if initial_states:
                    print(f"   Начальное состояние: {initial_states[0].get('name')}")
                if final_states:
                    print(f"   Финальные состояния: {[s.get('name') for s in final_states]}")
                
                print(f"   Все состояния:")
                for state in states[:5]:  # Показываем первые 5
                    print(f"     - {state.get('name')} ({state.get('state_type')})")
                if len(states) > 5:
                    print(f"     ... и еще {len(states) - 5} состояний")
        
        print("\n" + "=" * 80)
        return workflow_ids
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка workflows: {e}")
        return []


def check_workflow(workflow_id: str):
    """Проверяет конкретный workflow"""
    print("=" * 80)
    print(f"🔍 Проверка workflow: {workflow_id}")
    print("=" * 80)
    
    # Проверяем формат ID
    try:
        ObjectId(workflow_id)
        print("✅ Формат ID валидный (MongoDB ObjectId)")
    except InvalidId:
        print("❌ Невалидный формат ID!")
        print(f"   Ожидается: 24 hex символа (например: 507f1f77bcf86cd799439011)")
        print(f"   Получено: {workflow_id} ({len(workflow_id)} символов)")
        return False
    
    # Проверяем наличие в MongoDB
    states_client = MongoDBClient(
        database=settings.MONGO_DB,
        collection=settings.STATES_MONGO_COLLECTION
    )
    
    workflow = states_client.get(workflow_id)
    
    if not workflow:
        print(f"❌ Workflow {workflow_id} НЕ НАЙДЕН в MongoDB")
        print(f"\n📍 Коллекция: {settings.STATES_MONGO_COLLECTION}")
        print(f"📍 База данных: {settings.MONGO_DB}")
        print(f"📍 MongoDB URL: {settings.mongo_url}")
        print("\n💡 Возможные причины:")
        print("   1. Workflow с таким ID не существует")
        print("   2. Workflow был удален")
        print("   3. Неправильная база данных или коллекция")
        print("   4. Workflow был сохранен в другую коллекцию")
        print("\n💡 Рекомендации:")
        print("   - Используйте команду без аргументов для просмотра всех workflows")
        print("   - Создайте новый workflow: POST /workflow/save")
        return False
    
    print("✅ Workflow найден!")
    print(f"\n📦 Информация о workflow:")
    print(f"   ID: {workflow.get('_id')}")
    
    states = workflow.get("states", [])
    print(f"   Количество состояний: {len(states)}")
    
    if not states:
        print("   ⚠️  ВНИМАНИЕ: Workflow не содержит состояний!")
        return False
    
    # Анализируем состояния
    initial_states = [s for s in states if s.get("initial_state")]
    final_states = [s for s in states if s.get("final_state")]
    
    print(f"\n📊 Анализ состояний:")
    print(f"   Начальных состояний: {len(initial_states)}")
    if initial_states:
        for state in initial_states:
            print(f"     - {state.get('name')} ({state.get('state_type')})")
    
    print(f"   Финальных состояний: {len(final_states)}")
    if final_states:
        for state in final_states:
            print(f"     - {state.get('name')} ({state.get('state_type')})")
    
    # Типы состояний
    state_types = {}
    for state in states:
        st = state.get('state_type')
        state_types[st] = state_types.get(st, 0) + 1
    
    print(f"\n   Типы состояний:")
    for st, count in state_types.items():
        print(f"     - {st}: {count}")
    
    # Проверяем валидность
    print(f"\n✅ Валидация:")
    
    if len(initial_states) != 1:
        print(f"   ⚠️  Должно быть ровно 1 начальное состояние (найдено: {len(initial_states)})")
    else:
        print(f"   ✓ Начальное состояние OK")
    
    if len(final_states) < 1:
        print(f"   ⚠️  Должно быть минимум 1 финальное состояние (найдено: 0)")
    else:
        print(f"   ✓ Финальные состояния OK")
    
    print("\n" + "=" * 80)
    print("✅ Workflow валидный и готов к использованию!")
    print("=" * 80)
    return True


def main():
    print("\n🔧 MongoDB Workflow Checker")
    print(f"📍 База данных: {settings.MONGO_DB}")
    print(f"📍 Коллекция: {settings.STATES_MONGO_COLLECTION}\n")
    
    if len(sys.argv) > 1:
        workflow_id = sys.argv[1]
        check_workflow(workflow_id)
    else:
        workflow_ids = list_all_workflows()
        
        if workflow_ids:
            print("\n💡 Для детальной проверки используйте:")
            print(f"   python {sys.argv[0]} <workflow_id>")
            print(f"\nНапример:")
            print(f"   python {sys.argv[0]} {workflow_ids[0]}")


if __name__ == "__main__":
    main()
