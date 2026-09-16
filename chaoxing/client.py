"""HTTP 请求封装与 Cookie 序列化，对应原项目 utils/request.ts。"""
from __future__ import annotations

import requests
from requests import Response


class RequestResult:
    """统一返回结构：data(文本), headers, status_code。"""

    def __init__(self, data: str, headers: dict, status_code: int | None = None):
        self.data = data
        self.headers = headers
        self.status_code = status_code


def request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    data: str | bytes | dict | None = None,
) -> RequestResult:
    """发送 HTTP 请求，返回 RequestResult。

    - method: GET / POST
    - headers: 请求头
    - data: POST body（字符串则原样发送，dict 则表单编码）
    """
    method = (method or "GET").upper()
    headers = headers or {}

    if method == "POST":
        resp: Response = requests.post(url, headers=headers, data=data, timeout=20)
    else:
        resp = requests.get(url, headers=headers, timeout=20)

    return RequestResult(
        data=resp.text,
        headers=dict(resp.headers),
        status_code=resp.status_code,
    )


def cookie_serialize(cookies: dict) -> str:
    """把用户参数字典序列化为 Cookie 请求头字符串。

    对应原项目 request.ts 中的 cookieSerialize：
    fid=..; uf=..; _d=..; UID=..; vc3=..;
    """
    uid = cookies.get("_uid") or cookies.get("UID") or ""
    return (
        f"fid={cookies.get('fid', '-1')}; "
        f"uf={cookies.get('uf', '')}; "
        f"_d={cookies.get('_d', '')}; "
        f"UID={uid}; "
        f"vc3={cookies.get('vc3', '')};"
    )
