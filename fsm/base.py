from abc import ABC, abstractmethod


class FSMBase(ABC):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        ...
