#!/usr/bin/env python3
"""
Скрипт для поиска и просмотра workflows в MongoDB.
Использование: python find_workflows.py
"""

import sys
from storage.mongo.client import MongoDBClient
from config import settings
from bson.objectid import ObjectId


def print_separator(char="=", length=70):
    """Печатает разделитель"""
    print(char * length)


def find_all_workflows():
    """Находит и показывает все workflows"""
    print_separator()
    print("🔍 ПОИСК ВСЕХ WORKFLOWS В MONGODB")
    print_separator()
    
    try:
        client = MongoDBClient(settings.MONGO_DB, settings.STATES_MONGO_COLLECTION)
        workflows = client.get_all()
        
        if not workflows:
            print("\n❌ Workflows не найдены в базе данных")
            return
        
        print(f"\n✅ Найдено workflows: {len(workflows)}\n")
        
        for i, wf in enumerate(workflows, 1):
            wf_id = str(wf['_id'])
            states = wf.get('states', [])
            states_count = len(states)
            
            print(f"{i}. 📦 Workflow ID: {wf_id}")
            print(f"   ├─ States: {states_count}")
            
            # Подсчитываем типы состояний
            state_types = {}
            for state in states:
                state_type = state.get('state_type', 'unknown')
                state_types[state_type] = state_types.get(state_type, 0) + 1
            
            print(f"   │  └─ Типы: ", end="")
            print(", ".join([f"{k}: {v}" for k, v in state_types.items()]))
            
            # Получить context
            ctx_client = MongoDBClient(settings.MONGO_DB, settings.WORKFLOW_MONGO_COLLECTION)
            context = ctx_client.get(wf_id)
            if context:
                # Удаляем _id из подсчёта
                context_vars = {k: v for k, v in context.items() if k != '_id'}
                print(f"   ├─ Context vars: {len(context_vars)}")
                # Показываем первые 5 переменных
                sample_vars = list(context_vars.keys())[:5]
                if sample_vars:
                    print(f"   │  └─ Примеры: {', '.join(sample_vars)}")
            else:
                print(f"   ├─ Context: ❌ Не найден")
            
            # Получить screens
            scr_client = MongoDBClient(settings.MONGO_DB, settings.SCREENS_MONGO_COLLECTION)
            screens = list(scr_client.collection.find({"workflow_id": wf_id}))
            print(f"   └─ Screens: {len(screens)}")
            
            if screens:
                screen_names = [s.get('state_id', 'unknown') for s in screens[:3]]
                print(f"      └─ Примеры: {', '.join(screen_names)}", end="")
                if len(screens) > 3:
                    print(f" ... (+{len(screens) - 3} ещё)")
                else:
                    print()
            
            print()
        
        print_separator()
        
    except Exception as e:
        print(f"\n❌ Ошибка при поиске workflows: {e}")
        import traceback
        traceback.print_exc()


def find_workflow_by_id(workflow_id: str):
    """Находит и показывает конкретный workflow по ID"""
    print_separator()
    print(f"🔍 ПОИСК WORKFLOW: {workflow_id}")
    print_separator()
    
    try:
        # Проверяем формат ID
        try:
            obj_id = ObjectId(workflow_id)
        except:
            print(f"\n❌ Неверный формат ID: {workflow_id}")
            print("   ID должен быть в формате ObjectId (24 hex символа)")
            return
        
        client = MongoDBClient(settings.MONGO_DB, settings.STATES_MONGO_COLLECTION)
        workflow = client.get(workflow_id)
        
        if not workflow:
            print(f"\n❌ Workflow с ID {workflow_id} не найден")
            return
        
        print(f"\n✅ Workflow найден!\n")
        
        # States
        states = workflow.get('states', [])
        print(f"📦 States: {len(states)}")
        
        state_types = {}
        state_names = []
        for state in states:
            state_type = state.get('state_type', 'unknown')
            state_name = state.get('name', 'unknown')
            state_types[state_type] = state_types.get(state_type, 0) + 1
            state_names.append(f"{state_name} ({state_type})")
        
        print(f"   Типы состояний:")
        for st_type, count in state_types.items():
            print(f"   ├─ {st_type}: {count}")
        
        print(f"\n   Первые 5 состояний:")
        for name in state_names[:5]:
            print(f"   ├─ {name}")
        if len(state_names) > 5:
            print(f"   └─ ... (+{len(state_names) - 5} ещё)")
        
        # Context
        print(f"\n📝 Context:")
        ctx_client = MongoDBClient(settings.MONGO_DB, settings.WORKFLOW_MONGO_COLLECTION)
        context = ctx_client.get(workflow_id)
        
        if context:
            context_vars = {k: v for k, v in context.items() if k != '_id'}
            print(f"   Переменных: {len(context_vars)}")
            print(f"   Переменные:")
            for key, value in list(context_vars.items())[:10]:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                print(f"   ├─ {key}: {value_str}")
            if len(context_vars) > 10:
                print(f"   └─ ... (+{len(context_vars) - 10} ещё)")
        else:
            print(f"   ❌ Context не найден")
        
        # Screens
        print(f"\n🖥️  Screens:")
        scr_client = MongoDBClient(settings.MONGO_DB, settings.SCREENS_MONGO_COLLECTION)
        screens = list(scr_client.collection.find({"workflow_id": workflow_id}))
        
        if screens:
            print(f"   Экранов: {len(screens)}")
            print(f"   Список экранов:")
            for screen in screens:
                state_id = screen.get('state_id', 'unknown')
                screen_data = screen.get('screen', {})
                screen_name = screen_data.get('name', 'N/A')
                print(f"   ├─ {state_id}: {screen_name}")
        else:
            print(f"   ❌ Screens не найдены")
        
        print()
        print_separator()
        
    except Exception as e:
        print(f"\n❌ Ошибка при поиске workflow: {e}")
        import traceback
        traceback.print_exc()


def show_latest_workflow():
    """Показывает последний созданный workflow"""
    print_separator()
    print("🔍 ПОСЛЕДНИЙ СОЗДАННЫЙ WORKFLOW")
    print_separator()
    
    try:
        client = MongoDBClient(settings.MONGO_DB, settings.STATES_MONGO_COLLECTION)
        workflows = client.get_all()
        
        if not workflows:
            print("\n❌ Workflows не найдены")
            return
        
        # Последний workflow (с максимальным _id)
        latest = max(workflows, key=lambda x: x['_id'])
        workflow_id = str(latest['_id'])
        
        print(f"\n✅ Найден последний workflow: {workflow_id}\n")
        
        # Показываем детали
        find_workflow_by_id(workflow_id)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "latest":
            show_latest_workflow()
        elif command == "all":
            find_all_workflows()
        else:
            # Предполагаем, что это ID workflow
            find_workflow_by_id(command)
    else:
        # По умолчанию показываем все workflows
        find_all_workflows()
        
        print("\n💡 Использование:")
        print("   python find_workflows.py              - Показать все workflows")
        print("   python find_workflows.py all          - Показать все workflows")
        print("   python find_workflows.py latest       - Показать последний workflow")
        print("   python find_workflows.py <workflow_id> - Показать конкретный workflow")
        print()


if __name__ == "__main__":
    main()
