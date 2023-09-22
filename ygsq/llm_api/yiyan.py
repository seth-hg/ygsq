import json
import time
from http import HTTPStatus
from typing import List, Tuple

import requests

from .base import Api, Message


class Yiyan(Api):
    max_tokens = 11200
    TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}"
    API_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{}"

    def __init__(self, ak: str = None, sk: str = None, token: str = None, **kwargs):
        if token is None or token == "":
            if ak is None or ak == "" or sk is None or sk == "":
                raise ValueError("token or (ak, sk) is required")
            self.ak = ak
            self.sk = sk
            self.token = None
        else:
            self.ak = None
            self.sk = None
            self.token = token
        self.token_expire_time = None

    def get_api_endpoint(self, model: str) -> str:
        return self.API_URL.format(
            "eb-instant" if model == "ernie-turbo" else "completions"
        )

    def get_access_token(self) -> str:
        if self.token is None:
            # get token from server
            self.token, self.token_expire_time = self.get_new_token(self.ak, self.sk)
            return self.token

        if self.token_expire_time is None or self.token_expire_time > int(time.time()):
            return self.token
        self.token, self.token_expire_time = self.get_new_token(self.ak, self.sk)
        return self.token

    @classmethod
    def get_new_token(cls, ak: str, sk: str) -> Tuple[str, int]:
        url = cls.TOKEN_URL.format(ak, sk)
        now = int(time.time())
        resp = requests.get(url)
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f"get token failed, {resp}")
        resp_obj = json.loads(resp.text)
        token_expire_time = now + int(resp_obj["expires_in"])
        token = resp_obj["access_token"]
        return (token, token_expire_time)

    def send_request(self, model: str, messages: List[Message], stream, **kwargs):
        url = self.get_api_endpoint(model)
        body = {"messages": messages, "stream": stream}
        body.update(kwargs)
        resp = requests.post(
            url,
            json=body,
            params={"access_token": self.get_access_token()},
            stream=stream,
        )
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f"call failed, {resp}")
        return resp

    def generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        resp = self.send_request(model, messages, False, **kwargs)
        resp_obj = json.loads(resp.text)
        if resp_obj.get("error_code", 0) != 0:
            raise RuntimeError(f"server error, {resp_obj}")
        return resp_obj["result"]

    def stream_generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        resp = self.send_request(model, messages, True, **kwargs)
        buf = ""
        for chunk in resp.iter_content(chunk_size=1024, decode_unicode=True):
            idx = chunk.find("\n\n")
            if idx == -1:
                buf += chunk
                continue
            text = buf + chunk[:idx]
            buf = chunk[idx + 2 :]
            obj = json.loads(text[6:])
            yield obj["result"]

    def truncate(self, messages: List[Message]) -> List[Message]:
        # according to the document, messages will be automatically truncated on server side
        # https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lilb2lpf
        return messages
