"""用户登录、课程列表、用户信息、IM 参数，对应 functions/user.ts。"""
from __future__ import annotations

from Crypto.Cipher import DES
from Crypto.Util.Padding import pad

import config
from chaoxing.client import cookie_serialize, request


def _encrypt_password(password: str) -> str:
    """超星登录密码加密：DES-ECB-PKCS7。

    crypto-js 传入的 key 是 15 字节，但其 DES 实现按 8 字节截取，
    实际生效的 key 是前 8 字节 "u2oh6Vu^"。
    结果取 hex 大写，与 crypto-js 的 ciphertext.toString() 一致。
    """
    key = config.DES_KEY.encode("utf-8")[:8]
    cipher = DES.new(key, DES.MODE_ECB)
    encrypted = cipher.encrypt(pad(password.encode("utf-8"), 8))
    return encrypted.hex().upper()


def user_login(uname: str, password: str) -> dict | str:
    """登录成功返回用户参数字典，失败返回字符串 'AuthFailed'。"""
    enc_pwd = _encrypt_password(password)
    formdata = (
        f"uname={uname}&password={enc_pwd}&fid=-1&t=true"
        f"&refer=https%253A%252F%252Fi.chaoxing.com"
        f"&forbidotherlogin=0&validate="
    )

    result = request(
        config.LOGIN,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0",
        },
        data=formdata,
    )

    try:
        body = result.data
        # 超星登录接口返回 JSON
        import json
        info = json.loads(body)
    except Exception:
        print("网络异常，换个环境重试")
        return "AuthFailed"

    if not info.get("status"):
        print("登录失败")
        return "AuthFailed"

    # 直接使用 requests 解析好的 cookie 字典，
    # 避免手动拆分 Set-Cookie 时被 Expires 中的逗号干扰
    cookies_map = result.cookies

    print("登录成功")
    params = {
        "fid": "-1",
        "pid": "-1",
        "refer": "http%3A%2F%2Fi.chaoxing.com",
        "_blank": "1",
        "t": True,
        "vc3": cookies_map.get("vc3", ""),
        "_uid": cookies_map.get("_uid", ""),
        "_d": cookies_map.get("_d", ""),
        "uf": cookies_map.get("uf", ""),
        "lv": cookies_map.get("lv", ""),
    }
    return params


def get_courses(uid: str, d: str, vc3: str) -> list | str:
    """获取课程列表，返回 [{courseId, classId}]。"""
    formdata = "courseType=1&courseFolderId=0&courseFolderSize=0"
    result = request(
        config.COURSELIST,
        method="POST",
        headers={
            "Accept": "text/html, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8;",
            "Cookie": f"_uid={uid}; _d={d}; vc3={vc3}",
            "User-Agent": "Mozilla/5.0",
        },
        data=formdata,
        allow_redirects=False,
    )

    # 不跟随重定向，302 即代表鉴权失效（跟随重定向时永远拿不到 302）
    if result.status_code in (301, 302):
        print("身份过期，请重新登录！")
        return "AuthFailed"

    data = result.data
    courses: list[dict] = []
    i = 1
    while True:
        i = data.find("course_", i)
        if i == -1:
            break
        end = data.find("_", i + 7)
        course_id = data[i + 7: end]
        class_id = data[end + 1: data.find('"', i + 1)]
        courses.append({"courseId": course_id, "classId": class_id})
        i = end

    if not courses:
        print("[提示]无课程可查.")
        return "NoCourse"
    return courses


def get_account_info(cookies: dict) -> str:
    """获取用户名。"""
    result = request(
        config.ACCOUNTMANAGE,
        headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"},
    )
    data = result.data
    pos = data.find("messageName") + 20
    end = data.find('"', pos)
    return data[pos: end]


def get_im_params(cookies: dict) -> dict | str:
    """获取 IM（环信）连接所需参数。监听模式用。"""
    result = request(
        config.WEBIM,
        headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"},
    )
    data = result.data
    if not data:
        print("身份凭证似乎过期，请重新登录")
        return "AuthFailed"

    params = {}
    idx = data.find('id="myName"')
    params["myName"] = data[idx + 35: data.find("<", idx + 35)]
    idx = data.find('id="myToken"')
    params["myToken"] = data[idx + 36: data.find("<", idx + 36)]
    idx = data.find('id="myTuid"')
    params["myTuid"] = data[idx + 35: data.find("<", idx + 35)]
    params["myPuid"] = cookies.get("_uid", "")
    return params
