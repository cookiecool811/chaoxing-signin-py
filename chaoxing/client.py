"""HTTP 请求封装与 Cookie 序列化，对应原项目 utils/request.ts。"""
from __future__ import annotations

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# 全局复用 Session：自动携带重试策略，避免单次网络抖动直接失败
_session = requests.Session()
_retry = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1.0,          # 重试间隔：1s、2s、4s 递增
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET", "POST"),
    raise_on_status=False,
)
_session.mount("https://", HTTPAdapter(max_retries=_retry))
_session.mount("http://", HTTPAdapter(max_retries=_retry))


class RequestResult:
    """统一返回结构：data(文本), headers, status_code, cookies。"""

    def __init__(
        self,
        data: str,
        headers: dict,
        status_code: int | None = None,
        cookies: dict | None = None,
    ):
        self.data = data
        self.headers = headers
        self.status_code = status_code
        self.cookies = cookies or {}


def request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    data: str | bytes | dict | None = None,
    allow_redirects: bool = True,
) -> RequestResult:
    """发送 HTTP 请求，返回 RequestResult。

    - method: GET / POST
    - headers: 请求头
    - data: POST body（字符串则原样发送，dict 则表单编码）
    - allow_redirects: 是否跟随 302 重定向，设 False 可直接识别鉴权失效
    - 内置 3 次自动重试（连接错误、429、5xx）
    """
    method = (method or "GET").upper()
    headers = headers or {}

    if method == "POST":
        resp: Response = _session.post(
            url, headers=headers, data=data, timeout=20,
            allow_redirects=allow_redirects,
        )
    else:
        resp = _session.get(
            url, headers=headers, timeout=20,
            allow_redirects=allow_redirects,
        )

    return RequestResult(
        data=resp.text,
        headers=dict(resp.headers),
        status_code=resp.status_code,
        cookies=resp.cookies.get_dict(),
    )


def cookie_serialize(cookies: dict) -> str:
    """把用户参数字典序列化为 Cookie 请求头字符串。

    同时包含 UID 与 _uid：超星 mooc 域近期起强制校验 _uid，
    缺字段会被 302 重定向到登录页。
    """
    uid = cookies.get("_uid") or cookies.get("UID") or ""
    return (
        f"fid={cookies.get('fid', '-1')}; "
        f"uf={cookies.get('uf', '')}; "
        f"_d={cookies.get('_d', '')}; "
        f"UID={uid}; "
        f"_uid={uid}; "
        f"vc3={cookies.get('vc3', '')};"
    )
