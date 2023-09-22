import os
from http import HTTPStatus
from typing import List

import dashscope

from .base import Api, Message


class Qwen(Api):
    max_tokens = 6 * 1024

    def __init__(self, key: str = None, **kwargs):
        if key is None or key == "":
            key = os.environ.get("DASHSCOPE_API_KEY")
        if key is None or key == "":
            raise ValueError("Please set DASHSCOPE_API_KEY environment variable")
        self.key = key

    def generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        resp = dashscope.Generation.call(
            model,
            messages=messages,
            result_format="message",
            api_key=self.key,
            stream=False,
            **kwargs
        )
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(
                "Request id: %s, Status code: %s, error code: %s, error message: %s"
                % (
                    resp.request_id,
                    resp.status_code,
                    resp.code,
                    resp.message,
                )
            )
        response_message = resp.output.choices[0].message
        return response_message.content

    def stream_generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        for resp in dashscope.Generation.call(
            model,
            messages=messages,
            result_format="message",
            api_key=self.key,
            stream=True,
            **kwargs
        ):
            if resp.status_code != HTTPStatus.OK:
                raise RuntimeError(
                    "Request id: %s, Status code: %s, error code: %s, error message: %s"
                    % (
                        resp.request_id,
                        resp.status_code,
                        resp.code,
                        resp.message,
                    )
                )
            response_message = resp.output.choices[0].message
            yield response_message.content

    def truncate(self, messages: List[Message]) -> List[Message]:
        # TODO: not sure
        return messages
