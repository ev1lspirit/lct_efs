from __future__ import annotations
from typing import Callable


class Transition:
    def __init__(self, variable: str, case, state_id: str):
        self.variable = variable
        self.case: str = case
        self.state_id = state_id
        self.variables: set[str] = {variable}
        self.keys: set[str] = {case}

    def matches(self, context: dict) -> bool:
        return str(context.get(self.variable)) == self.case

    def __and__(self, other: Transition | CompoundTransition) -> CompoundTransition:
        if self.state_id != other.state_id:
            raise ValueError("Cannot combine transitions with different state ids")
        return CompoundTransition(
            lambda ctx: self.matches(ctx) and other.matches(ctx),
            state_id=self.state_id,
            variables=self.variables | other.variables,
            keys=self.keys | other.keys,
            debug=f"{self} & {other}",
        )

    def __or__(self, other: Transition | CompoundTransition) -> CompoundTransition:
        if self.state_id != other.state_id:
            raise ValueError("Cannot combine transitions with different state ids")
        return CompoundTransition(
            lambda ctx: self.matches(ctx) or other.matches(ctx),
            state_id=self.state_id,
            variables=self.variables | other.variables,
            keys=self.keys | other.keys,
            debug=f"{self} | {other}",
        )

    def __invert__(self) -> CompoundTransition:
        return CompoundTransition(
            lambda ctx: not self.matches(ctx),
            state_id=self.state_id,
            variables=self.variables,
            keys=self.keys,
            debug=f"~{self}",
        )

    def __repr__(self):
        return f"<T {self.variable}=={self.case} → {self.state_id}>"


class CompoundTransition:
    def __init__(self, func: Callable[[dict], bool], state_id: str, variables: set[str], keys: set[str], debug: str):
        self.func = func
        self.state_id = state_id
        self.variables = variables
        self.debug = debug
        self.keys = keys

    def matches(self, context: dict) -> bool:
        return self.func(context)

    def __and__(self, other: Transition | CompoundTransition) -> CompoundTransition:
        if self.state_id != other.state_id:
            raise ValueError("Cannot combine transitions with different state ids")
        return CompoundTransition(
            lambda ctx: self.matches(ctx) and other.matches(ctx),
            state_id=self.state_id,
            variables=self.variables | other.variables,
            keys=self.keys | other.keys,
            debug=f"({self.debug} & {other})",
        )

    def __or__(self, other: Transition | CompoundTransition) -> CompoundTransition:
        if self.state_id != other.state_id:
            raise ValueError("Cannot combine transitions with different state ids")
        return CompoundTransition(
            lambda ctx: self.matches(ctx) or other.matches(ctx),
            state_id=self.state_id,
            variables=self.variables | other.variables,
            keys=self.keys | other.keys,
            debug=f"({self.debug} | {other})",
        )

    def __invert__(self) -> CompoundTransition:
        return CompoundTransition(
            lambda ctx: not self.matches(ctx),  state_id=self.state_id, variables=self.variables, keys=self.keys, debug=f"~({self.debug})"
        )

    def __repr__(self):
        return f"<CT {self.debug}>"
