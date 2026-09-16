"""
全自动签到（监听模式）。
运行前请先编辑 user_config.py 填好账号密码和位置。
启动后会自动：登录 → 查课程 → 每 15 秒扫一次活动 → 检测到签到自动签上。
"""
from __future__ import annotations

import time

import config
import user_config
from chaoxing import storage
from chaoxing.activity import (
    get_ppt_active_info,
    pre_sign,
    traverse_course_activity,
)
from chaoxing.notify import CQBot, send_email
from chaoxing.sign import (
    general_sign,
    get_object_id_from_pan,
    location_sign_multi,
    photo_sign,
)
from chaoxing.user import get_account_info, get_courses, user_login


def do_sign(cookies: dict, name: str, activity: dict) -> str | None:
    """根据活动类型自动签到。"""
    active_id = activity["activeId"]
    pre_sign(activity, cookies)
    other = activity["otherId"]

    if other == 2:
        return "[二维码]需要人工处理，请用手动方式"
    if other == 4:
        return location_sign_multi(
            cookies, active_id, name,
            preset_address=user_config.PRESET_ADDRESSES,
        )
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
    # 1. 登录（优先用本地缓存的凭证，没有才用密码登录）
    phone = user_config.PHONE
    local = storage.get_user(phone)

    if local and local.get("params", {}).get("_uid"):
        print(f"[自动] 使用本地凭证登录 {phone}")
        params = local["params"]
    else:
        print(f"[自动] 用账号密码登录 {phone}")
        if not user_config.PASSWORD:
            print("错误：请先在 user_config.py 里填写 PASSWORD")
            return
        result = user_login(phone, user_config.PASSWORD)
        if result == "AuthFailed":
            print("登录失败，请检查手机号密码")
            return
        params = result
        storage.store_user(phone, {"phone": phone, "params": params})

    # 2. 取用户名和课程
    try:
        name = get_account_info(params)
        print(f"[自动] 你好，{name}")
    except Exception:
        name = ""

    courses = get_courses(params["_uid"], params["_d"], params["vc3"])
    if courses in ("AuthFailed", "NoCourse"):
        # 凭证过期，清掉本地缓存下次重新登录
        storage.store_user(phone, {"phone": phone, "params": {}})
        print("凭证已过期，请检查账号密码后重跑")
        return
    print(f"[自动] 共 {len(courses)} 门课程")

    # 3. 可选：连接 QQ 机器人
    cq_bot = None
    if user_config.CQ.get("ENABLED"):
        import asyncio
        cq_bot = CQBot(
            user_config.CQ["WS_URL"],
            user_config.CQ.get("TARGET_TYPE", "private"),
            user_config.CQ.get("TARGET_ID", 10001),
        )
        asyncio.run(cq_bot.connect())

    # 4. 主循环：定时轮询
    processed: set[str] = set()
    print(f"[自动] 开始监听，每 {config.POLL_INTERVAL} 秒扫描一次（Ctrl+C 退出）...\n")

    try:
        while True:
            activity = traverse_course_activity(courses, params)
            if isinstance(activity, dict) and activity["activeId"] not in processed:
                aid = activity["activeId"]
                print(f"\n>>> 发现新活动：{activity.get('name', '')}")
                processed.add(aid)

                delay = int(user_config.DELAY_SECONDS)
                if delay > 0:
                    print(f"等待 {delay} 秒...")
                    time.sleep(delay)

                result = do_sign(params, name, activity)

                # 推送
                if user_config.EMAIL.get("ENABLED"):
                    send_email(user_config.EMAIL, aid, params.get("_uid", ""), name, result or "")
                if cq_bot:
                    import asyncio
                    asyncio.run(cq_bot.send(f"{result or '完成'} - {name}"))

                print(f">>> 结果：{result}\n")

            time.sleep(config.POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[自动] 已停止")
        if cq_bot:
            import asyncio
            asyncio.run(cq_bot.close())


if __name__ == "__main__":
    main()
