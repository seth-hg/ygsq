import os
from typing import List

import zhipuai

from .base import Api, Message


class ChatGLM(Api):
    max_tokens = 32 * 1024  # not sure about this

    def __init__(self, key: str = None, **kwargs):
        if key is None or key == "":
            key = os.environ.get("ZHIPU_API_KEY")
        if key is None or key == "":
            raise ValueError("Please provide a valid key for Zhipu API")
        self.key = key
        zhipuai.api_key = key

    def generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        resp = zhipuai.model_api.invoke(model=model, prompt=messages, **kwargs)
        if resp["code"] != 200:
            raise RuntimeError(f"server error, {resp}")
        return resp["data"]["choices"][0]["content"]

    def stream_generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        resp = zhipuai.model_api.sse_invoke(model=model, prompt=messages, **kwargs)
        for event in resp.events():
            yield event.data

    def truncate(self, messages: List[Message]) -> List[Message]:
        # according to the document, messages will be automatically truncated on server side
        # https://open.bigmodel.cn/dev/api#chatglm_std
        return messages
