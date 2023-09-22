import base64
import hashlib
import hmac
import json
from datetime import datetime
from time import mktime
from typing import List
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websockets.sync.client as ws_client

from .base import Api, Message


class Spark(Api):
    max_tokens = 8192
    # "ws://spark-api.xf-yun.com/v1.1/chat"
    # "ws://spark-api.xf-yun.com/v2.1/chat"
    API_HOST = "spark-api.xf-yun.com"

    def __init__(self, appid: str, ak: str, sk: str, **kwargs):
        self.appid = appid
        self.ak = ak
        self.sk = sk
        if (
            self.appid is None
            or self.appid == ""
            or self.ak is None
            or self.ak == ""
            or self.sk is None
            or self.sk == ""
        ):
            raise ValueError("missing `appid`, `ak` or `sk`")

    def get_url(self, version: str):
        path = f"/v{version}/chat"
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.API_HOST + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + path + " HTTP/1.1"

        signature_sha = hmac.new(
            self.sk.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = f'api_key="{self.ak}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )

        v = {"authorization": authorization, "date": date, "host": self.API_HOST}
        url = f"ws://{self.API_HOST}{path}?{urlencode(v)}"
        return url

    def get_connection(self, version: str) -> ws_client.ClientConnection:
        url = self.get_url(version)
        conn = ws_client.connect(url)
        return conn

    def send_request(
        self,
        ws: ws_client.ClientConnection,
        version: str,
        messages: List[Message],
        **kwargs,
    ):
        params = {"domain": "general" if version == "1.1" else "generalv2"}
        params.update(kwargs)
        req = {
            "header": {"app_id": self.appid, "uid": "1234"},
            "parameter": {"chat": params},
            "payload": {"message": {"text": messages}},
        }
        ws.send(json.dumps(req))

    def generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        version = "1.1"
        if model == "spark2.1":
            version = "2.1"
        elif model != "spark1.1":
            raise ValueError("model must be spark1.1 or spark2.1")
        ws = self.get_connection(version)
        self.send_request(ws, version, messages, **kwargs)
        content = ""
        status = 0
        while status != 2:
            resp = ws.recv()
            resp_obj = json.loads(resp)
            header = resp_obj["header"]
            if header["code"] != 0:
                raise RuntimeError(header["message"])
            choices = resp_obj["payload"]["choices"]
            status = choices["status"]
            content += choices["text"][0]["content"]
        return content

    def stream_generate(self, model: str, messages: List[Message], **kwargs) -> str:
        messages = self.truncate(messages)
        version = "1.1"
        if model == "spark2.1":
            version = "2.1"
        elif model != "spark1.1":
            raise ValueError("model must be spark1.1 or spark2.1")
        ws = self.get_connection(version)
        self.send_request(ws, version, messages, **kwargs)
        status = 0
        while status != 2:
            resp = ws.recv()
            resp_obj = json.loads(resp)
            header = resp_obj["header"]
            if header["code"] != 0:
                raise RuntimeError(header["message"])
            choices = resp_obj["payload"]["choices"]
            status = choices["status"]
            yield choices["text"][0]["content"]

    def truncate(self, messages: List[Message]) -> List[Message]:
        # TODO: keep the total length of messages <= self.max_tokens
        return messages
