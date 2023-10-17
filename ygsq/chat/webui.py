import json
from typing import Dict
from datetime import datetime


import streamlit as st

from ygsq import llm_api

models = {
    "文心一言": "ernie",
    "文心一言 Turbo": "ernie-turbo",
    "ChatGLM 标准版": "chatglm_std",
    "ChatGLM Pro": "chatglm_pro",
    "ChatGLM Lite": "chatglm_lite",
    "星火1.5": "spark1.1",
    "星火2.0": "spark2.1",
    "通义千问 Turbo": "qwen-turbo",
    "通义千问 Plus": "qwen-plus",
}


def get_api_keys() -> Dict[str, str]:
    # get api tokens or keys from secrets
    if not st.secrets.load_if_toml_exists():
        return {}
    params = {}
    if v := st.secrets.get("YIYAN_ACCESS_TOKEN"):
        params["YIYAN_ACCESS_TOKEN"] = v
    if v := st.secrets.get("YIYAN_API_KEY"):
        params["YIYAN_API_KEY"] = v
    if v := st.secrets.get("YIYAN_SECRET_KEY"):
        params["YIYAN_SECRET_KEY"] = v

    if v := st.secrets.get("ZHIPU_API_KEY"):
        params["ZHIPU_API_KEY"] = v

    if v := st.secrets.get("SPARK_APP_ID"):
        params["SPARK_APP_ID"] = v
    if v := st.secrets.get("SPARK_API_KEY"):
        params["SPARK_API_KEY"] = v
    if v := st.secrets.get("SPARK_SECRET_KEY"):
        params["SPARK_SECRET_KEY"] = v

    if v := st.secrets.get("QWEN_API_KEY"):
        params["QWEN_API_KEY"] = v

    return params


def get_yiyan_api(model: str, defaults: Dict[str, str]) -> llm_api.Api:
    args = {}
    st.markdown(
        "请填写从[千帆平台](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ilkkrb0i5)获取的API Key + Secret Key或Access Token。"
    )
    ak = st.text_input("API Key", value=defaults.get("YIYAN_API_KEY", ""))
    sk = st.text_input("Secret Key", value=defaults.get("YIYAN_SECRET_KEY", ""))
    token = st.text_input("Access Token", value=defaults.get("YIYAN_ACCESS_TOKEN", ""))
    if token != "":
        args["token"] = token
    elif ak != "" and sk != "":
        args["ak"] = ak
        args["sk"] = sk
    else:
        return None
    return llm_api.create_api(model, **args)


def get_zhipu_api(model: str, defaults: Dict[str, str]) -> llm_api.Api:
    st.markdown("请填写从[智谱开放平台](https://open.bigmodel.cn/usercenter/apikeys)获取的API Key。")
    key = st.text_input("API Key", defaults.get("ZHIPU_API_KEY", ""))
    if key == "":
        return None
    return llm_api.create_api(model, key=key)


def get_spark_api(model: str, defaults: Dict[str, str]) -> llm_api.Api:
    st.markdown(
        "请填写从[讯飞开放平台](https://console.xfyun.cn/app/myapp)获取的APP ID、API Key和Secret Key。"
    )
    appid = st.text_input("APP ID", defaults.get("SPARK_APP_ID", ""))
    ak = st.text_input("API Key", defaults.get("SPARK_API_KEY", ""))
    sk = st.text_input("API Secret", defaults.get("SPARK_SECRET_KEY", ""))
    if appid == "" or ak == "" or sk == "":
        return None
    return llm_api.create_api(model, appid=appid, ak=ak, sk=sk)


def get_qwen_api(model: str, defaults: Dict[str, str]) -> llm_api.Api:
    st.markdown(
        "请填写从[DashScope](https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key)获取的API Key。"
    )
    key = st.text_input("API Key", defaults.get("QWEN_API_KEY", ""))
    if key == "":
        return None
    return llm_api.create_api(model, key=key)


api = None
extra_args = {}

st.set_page_config(
    page_title="YGSQ Chat",
    page_icon="🤖",
)


with st.sidebar:
    model_key = st.selectbox("Model", models.keys(), label_visibility="hidden")
    model = models[model_key]
    defaults = get_api_keys()
    if model.startswith("ernie"):
        api = get_yiyan_api(model, defaults)
    elif model.startswith("chatglm"):
        api = get_zhipu_api(model, defaults)
    elif model.startswith("spark"):
        api = get_spark_api(model, defaults)
    elif model.startswith("qwen"):
        api = get_qwen_api(model, defaults)
        st.divider()
        enable_search = st.toggle("enable_search", value=False)
        extra_args["enable_search"] = enable_search

if "history" not in st.session_state.keys():
    st.session_state.history = []


if len(st.session_state.history) > 0:
    for msg in st.session_state.history:
        with st.chat_message(msg.role):
            st.write(msg.content)
    _, col_download, col_clear = st.columns([5, 1, 1])
    with col_download:
        st.download_button(
            "保存",
            file_name=datetime.now().strftime("%Y%m%d_%H%M%S.json"),
            data=json.dumps(st.session_state.history, indent=2, ensure_ascii=False),
            use_container_width=True,
        )
    with col_clear:
        if st.button("清除", use_container_width=True):
            st.session_state.history = []
            st.rerun()


def slow_echo(prompt: str):
    """debug only"""
    import time

    prompt = prompt.upper() + " !!!"
    for c in prompt:
        time.sleep(0.1)
        yield c


if prompt := st.chat_input(disabled=api is None, placeholder="输入您的问题"):
    if prompt is None:
        st.stop()

    st.session_state.history.append(llm_api.Message(llm_api.Role.USER, prompt))
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        output = ""
        # for c in slow_echo(prompt):
        for c in api.stream_generate(model, st.session_state.history, **extra_args):
            output += c
            message_placeholder.write(output + "▌")
        st.session_state.history.append(llm_api.Message(llm_api.Role.ASSISTANT, output))
        st.rerun()
