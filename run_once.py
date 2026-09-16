"""
单次运行：登录 → 查课程 → 发现签到就签 → 退出。
供 GitHub Actions 每 5 分钟定时触发一次使用。

配置优先级：
1. 环境变量（GitHub Actions 注入）—— 推荐
2. user_config.py —— 本地调试用
"""
from __future__ import annotations

import json
import os
import sys

import config
from chaoxing.activity import (
    get_ppt_active_info,
    pre_sign,
    traverse_course_activity,
)
from chaoxing.notify import send_email
from chaoxing.sign import (
    general_sign,
    get_object_id_from_pan,
    location_sign_multi,
    photo_sign,
)
from chaoxing.user import get_account_info, get_courses, user_login


def load_config() -> dict:
    """从环境变量读配置，本地没有环境变量时回退到 user_config.py。"""
    env_phone = os.environ.get("CHAOXING_PHONE")
    env_password = os.environ.get("CHAOXING_PASSWORD")

    if env_phone and env_password:
        # GitHub Actions 模式
        # 位置格式：lon,lat,address;lon,lat,address（分号分隔多个）
        preset = []
        addr_raw = os.environ.get("CHAOXING_ADDRESS", "")
        for item in addr_raw.split(";"):
            item = item.strip()
            if not item:
                continue
            parts = item.split(",", 2)
            if len(parts) == 3:
                preset.append({"lon": parts[0], "lat": parts[1], "address": parts[2]})

        return {
            "phone": env_phone,
            "password": env_password,
            "preset_addresses": preset,
            "delay": int(os.environ.get("CHAOXING_DELAY", "0")),
        }

    # 本地调试模式
    import user_config
    return {
        "phone": user_config.PHONE,
        "password": user_config.PASSWORD,
        "preset_addresses": user_config.PRESET_ADDRESSES,
        "delay": user_config.DELAY_SECONDS,
    }


def do_sign(cookies: dict, name: str, activity: dict, preset_address: list, delay: int) -> str | None:
    active_id = activity["activeId"]
    if delay > 0:
        import time
        time.sleep(delay)
    pre_sign(activity, cookies)
    other = activity["otherId"]

    if other == 2:
        return "[二维码]需要人工处理"
    if other == 4:
        return location_sign_multi(cookies, active_id, name, preset_address)
    if other in (3, 5):
        return general_sign(cookies, active_id, name)
    if other == 0:
        info = get_ppt_active_info(active_id, cookies)
        if info.get("ifphoto") == 1:
            oid = get_object_id_from_pan(cookies)
            if oid is None:
                return None
            return photo_sign(cookies, active_id, oid, name)
        return general_sign(cookies, active_id, name)
    return None


def main() -> None:
    cfg = load_config()

    if not cfg["phone"] or not cfg["password"]:
        print("错误：未配置账号密码")
        sys.exit(1)

    print(f"[run_once] 登录 {cfg['phone']}")
    result = user_login(cfg["phone"], cfg["password"])
    if result == "AuthFailed":
        print("[run_once] 登录失败")
        sys.exit(1)
    params = result

    try:
        name = get_account_info(params)
        print(f"[run_once] 你好，{name}")
    except Exception:
        name = ""

    courses = get_courses(params["_uid"], params["_d"], params["vc3"])
    if courses in ("AuthFailed", "NoCourse"):
        print("[run_once] 无课程或凭证失效")
        sys.exit(0)

    activity = traverse_course_activity(courses, params)
    if activity == "NoActivity":
        print("[run_once] 本次无签到活动")
        sys.exit(0)

    print(f"[run_once] 发现活动：{activity.get('name', '')}")
    sign_result = do_sign(
        params, name, activity,
        preset_address=cfg["preset_addresses"],
        delay=cfg["delay"],
    )
    print(f"[run_once] 结果：{sign_result}")

    # 邮件推送（可选，本地配置）
    try:
        import user_config
        if user_config.EMAIL.get("ENABLED"):
            send_email(
                user_config.EMAIL,
                activity["activeId"], params.get("_uid", ""), name,
                sign_result or "",
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
