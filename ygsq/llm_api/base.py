import json
from abc import ABC
from typing import List, Tuple, abstractmethod


class Role:
    USER = "user"
    ASSISTANT = "assistant"


class Message(dict):
    def __init__(self, role: str, content: str):
        super().__init__(self, role=role, content=content)
        self.role = role
        self.content = content


class Api(ABC):
    @abstractmethod
    def generate(self, model: str, messages: List[Message], **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream_generate(self, model: str, messages: List[Message], **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def truncate(self, messages: List[Message]) -> List[Message]:
        raise NotImplementedError
