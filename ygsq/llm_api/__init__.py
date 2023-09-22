from typing import List

from .base import Api, Message, Role
from .chatglm import ChatGLM
from .qwen import Qwen
from .spark import Spark
from .yiyan import Yiyan

__all__ = [
    "Api",
    "Role",
    "Message",
    "Yiyan",
    "ChatGLM",
    "Spark",
    "Qwen",
    "Models",
    "create_api",
    "list_models",
]


class Models:
    Ernie = "ernie"
    ErnieTurbo = "ernie-turbo"
    ChatGLMPro = "chatglm_pro"
    ChatGLMStd = "chatglm_std"
    ChatGLMLite = "chatglm_lite"
    SparkV11 = "spark1.1"
    SparkV21 = "spark2.1"
    QwenTurbo = "qwen-turbo"
    QwenPlus = "qwen-plus"


__model_to_api = {
    Models.Ernie: Yiyan,
    Models.ErnieTurbo: Yiyan,
    Models.ChatGLMPro: ChatGLM,
    Models.ChatGLMStd: ChatGLM,
    Models.ChatGLMLite: ChatGLM,
    Models.SparkV11: Spark,
    Models.SparkV21: Spark,
    Models.QwenTurbo: Qwen,
    Models.QwenPlus: Qwen,
}


def create_api(model: str, **kwargs) -> Api:
    cls = __model_to_api.get(model)
    if cls is None:
        raise ValueError(f"Unknown model: {model}")
    return cls(**kwargs)


def list_models() -> List[str]:
    return list(__model_to_api.keys())
