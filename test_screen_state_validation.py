"""
Тест для проверки валидации workflow с screen states, 
где transitions содержат variable: null
"""
import pytest
from validators.automaton import AutomatonValidator
from workflow_builder.state_parser.contract import (
    StateModel, 
    IntegrationExpressionModel, 
    EventModel,
    TransitionModel
)


def test_screen_state_with_null_variable_in_transitions():
    """
    Проверяет, что workflow с screen state, содержащим transitions 
    с variable: null, успешно проходит валидацию
    """
    states = [
        StateModel(
            state_type="integration",
            name="Загрузка данных",
            screen={},
            initial_state=True,
            final_state=False,
            expressions=[
                IntegrationExpressionModel(
                    variable="data_response",
                    url="https://api.example.com/data",
                    params={},
                    method="get"
                )
            ],
            transitions=[
                TransitionModel(
                    state_id="Экран просмотра",
                    case=None,
                    variable="data_response"
                )
            ]
        ),
        StateModel(
            state_type="screen",
            name="Экран просмотра",
            screen={"id": "screen-view", "type": "Screen", "name": "Просмотр"},
            initial_state=False,
            final_state=True,  # Финальное состояние может не иметь transitions
            expressions=[
                EventModel(event_name="submitForm"),
                EventModel(event_name="cancelForm")
            ],
            transitions=[
                # ВАЖНО: variable: None здесь - это нормально для screen state
                TransitionModel(
                    case="submitForm",
                    state_id="Экран просмотра",  # Переход на само себя
                    variable=None  # Явно указано None
                ),
                TransitionModel(
                    case="cancelForm",
                    state_id="Экран просмотра",
                    variable=None
                )
            ]
        )
    ]
    
    # Валидируем workflow - это должно пройти без ошибок
    try:
        validator = AutomatonValidator(states=states)
        validator.run()
        
        print("✅ Workflow успешно прошёл валидацию!")
        print(f"   Количество состояний: {len(states)}")
        
        # Проверяем, что screen state корректно обработан
        screen_state = next((s for s in states if s.name == "Экран просмотра"), None)
        assert screen_state is not None
        assert screen_state.state_type == "screen"
        assert len(screen_state.transitions) == 2
        
        print(f"   Screen state найден: {screen_state.name}")
        print(f"   Transitions: {len(screen_state.transitions)}")
        
    except ValueError as e:
        pytest.fail(f"Валидация не прошла: {e}")


def test_integration_state_with_null_variable_should_fail():
    """
    Проверяет, что integration state с variable: None в transition 
    вызывает ошибку (это некорректно для integration)
    """
    states = [
        StateModel(
            state_type="integration",
            name="Загрузка данных",
            screen={},
            initial_state=True,
            final_state=False,
            expressions=[
                IntegrationExpressionModel(
                    variable="data_response",
                    url="https://api.example.com/data",
                    params={},
                    method="get"
                )
            ],
            transitions=[
                TransitionModel(
                    state_id="Следующий шаг",
                    case=None,
                    variable=None  # ❌ Для integration это ошибка!
                )
            ]
        ),
        StateModel(
            state_type="technical",
            name="Следующий шаг",
            screen={},
            initial_state=False,
            final_state=True,
            expressions=[],
            transitions=[]
        )
    ]
    
    # Это должно вызвать ошибку валидации
    with pytest.raises(ValueError, match="Variable can't be None"):
        validator = AutomatonValidator(states=states)
        validator.run()


def test_technical_state_with_null_variable_is_ok():
    """
    Проверяет, что technical state с variable: None в transition 
    проходит валидацию (это нормально для technical)
    """
    states = [
        StateModel(
            state_type="integration",
            name="Начало",
            screen={},
            initial_state=True,
            final_state=False,
            expressions=[
                IntegrationExpressionModel(
                    variable="start_response",
                    url="https://api.example.com/start",
                    params={},
                    method="get"
                )
            ],
            transitions=[
                TransitionModel(
                    state_id="Подготовка",
                    case=None,
                    variable="start_response"
                )
            ]
        ),
        StateModel(
            state_type="technical",
            name="Подготовка",
            screen={},
            initial_state=False,
            final_state=False,
            expressions=[],
            transitions=[
                TransitionModel(
                    case=None,
                    state_id="Конец",
                    variable=None  # ✅ Для technical это OK
                )
            ]
        ),
        StateModel(
            state_type="technical",
            name="Конец",
            screen={},
            initial_state=False,
            final_state=True,
            expressions=[],
            transitions=[]
        )
    ]
    
    try:
        validator = AutomatonValidator(states=states)
        validator.run()
        
        print("✅ Technical state с variable: None прошёл валидацию!")
        
    except ValueError as e:
        pytest.fail(f"Валидация не прошла: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
