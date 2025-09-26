from pydantic import ValidationError

from workflow_builder.states import IntegrationState, TechnicalState, WorkflowState
from workflow_builder.automaton.automaton import Automaton
import pytest
from pydantic import ValidationError


class TestAutomaton:
    def test_init(self):
        states = [
            TechnicalState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=True,
            ),
            IntegrationState(
                context_variable="y",
                transitions=[],
                expressions=[],
            ),
        ]
        automaton = Automaton(states=states)
        assert automaton.states == states

    def test_init_invalid(self):
        states = [
            TechnicalState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=True,
            ),
            IntegrationState(
                context_variable="y",
                transitions=[],
                expressions=[],
            ),
            IntegrationState(
                context_variable="z",
                transitions=[],
                expressions=[],
            ),
        ]
        with pytest.raises(ValidationError):
            Automaton(states=states)

    def test_iter(self):
        states = [
            TechnicalState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=True,
            ),
            IntegrationState(
                context_variable="y",
                transitions=[],
                expressions=[],
            ),
        ]
        automaton = Automaton(states=states)
        iterator = iter(automaton)
        assert next(iterator) == states[0]
        assert next(iterator) == states[1]

    def test_next(self):
        states = [
            TechnicalState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=True,
            ),
            TechnicalState(
                context_variable="y",
                transitions=[],
                expressions=[],
            ),
        ]
        automaton = Automaton(states=states)
        iterator = iter(automaton)
        assert next(iterator) == states[0]
        assert next(iterator) == states[1]
        with pytest.raises(StopIteration):
            next(iterator)

    def test_init_multiple_initial_states(self):
        """Test that multiple initial states raise ValidationError"""
        states = [
            TechnicalState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=True,
            ),
            TechnicalState(
                context_variable="y",
                transitions=[],
                expressions=[],
                initial_state=True,  # Second initial state
            ),
        ]
        with pytest.raises(ValidationError):
            Automaton(states=states)

    def test_init_no_initial_state(self):
        """Test that no initial state raises ValidationError"""
        states = [
            TechnicalState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=False,
            ),
            IntegrationState(
                context_variable="y",
                transitions=[],
                expressions=[],
            ),
        ]
        with pytest.raises(ValidationError):
            Automaton(states=states)

    def test_for_loop_iteration(self):
        """Test that Automaton can be used in a for loop"""
        states = [
            IntegrationState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=True,
            ),
            IntegrationState(
                context_variable="y",
                transitions=[],
                expressions=[],
            ),
        ]
        automaton = Automaton(states=states)

        collected_states = []
        for state in automaton:
            collected_states.append(state)

        assert collected_states == states

    def test_list_comprehension(self):
        """Test that Automaton works with list comprehensions"""
        states = [
            TechnicalState(
                context_variable="x",
                transitions=[],
                expressions=[],
                initial_state=True,
            ),
            IntegrationState(
                context_variable="y",
                transitions=[],
                expressions=[],
            ),
        ]
        automaton = Automaton(states=states)

        context_vars = [state.context_variable for state in automaton]
        assert context_vars == ["x", "y"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
