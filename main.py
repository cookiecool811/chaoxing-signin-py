"""手动签到入口（对应原项目 apps/server/src/index.ts）。

运行：python main.py
功能：选择用户 -> 查课 -> 找签到 -> 预签 -> 按类型完成签到。
"""
from __future__ import annotations

import getpass
import sys

from chaoxing import storage
from chaoxing.activity import get_ppt_active_info, pre_sign, traverse_course_activity
from chaoxing.sign import (
    general_sign,
    get_object_id_from_pan,
    location_sign,
    photo_sign,
    qrcode_sign,
)
from chaoxing.user import get_account_info, get_courses, user_login


def _choose_user():
    """返回 (params, phone, configs)。"""
    users = storage.list_users()
    configs: dict = {}

    if not users:
        # 没有本地用户，直接手动登录
        phone = input("手机号: ").strip()
        password = getpass.getpass("密码: ")
        result = user_login(phone, password)
        if result == "AuthFailed":
            sys.exit(0)
        storage.store_user(phone, {"phone": phone, "params": result})
        params = dict(result)
        params["phone"] = phone
        return params, phone, configs

    print("=== 选择用户 ===")
    for i, phone in enumerate(users):
        print(f"  [{i}] {phone}")
    print(f"  [{len(users)}] 手动登录")

    choice = input("请选择序号: ").strip()
    try:
        idx = int(choice)
    except ValueError:
        idx = len(users)

    if idx < 0 or idx > len(users):
        print("序号无效")
        sys.exit(0)

    if idx == len(users):
        # 手动登录
        phone = input("手机号: ").strip()
        password = getpass.getpass("密码: ")
        result = user_login(phone, password)
        if result == "AuthFailed":
            sys.exit(0)
        storage.store_user(phone, {"phone": phone, "params": result})
        params = dict(result)
        params["phone"] = phone
    else:
        user = storage.get_user(users[idx])
        if not user:
            print("用户不存在")
            sys.exit(0)
        params = dict(user["params"])
        params["phone"] = user["phone"]
        configs["monitor"] = user.get("monitor", {})
        configs["mailing"] = user.get("mailing", {})
        configs["cqserver"] = user.get("cqserver", {})

    return params, params.get("phone"), configs


def main() -> None:
    params, phone, configs = _choose_user()

    # 用户名
    name = get_account_info(params)
    print(f"你好，{name}")

    # 课程列表
    courses = get_courses(params["_uid"], params["_d"], params["vc3"])
    if courses == "AuthFailed" or courses == "NoCourse":
        sys.exit(0)

    # 找活动
    activity = traverse_course_activity(courses, params)
    if activity == "NoActivity":
        sys.exit(0)

    # 预签
    pre_sign(activity, params)

    other = activity["otherId"]
    active_id = activity["activeId"]

    if other == 2:
        # 二维码签到
        enc = input("enc（识别二维码可得 enc 参数）: ").strip()
        default_lnglat = configs.get("monitor", {}).get("lon") \
            and f"{configs['monitor']['lon']},{configs['monitor']['lat']}" \
            or "113.516288,34.817038"
        default_addr = configs.get("monitor", {}).get("address", "")
        lnglat = input(f"经纬度 [{default_lnglat}]: ").strip() or default_lnglat
        address = input(f"详细地址 [{default_addr}]: ").strip() or default_addr
        altitude = input("海拔 [100]: ").strip() or "100"
        lon, lat = lnglat.split(",")
        qrcode_sign(params, active_id, enc, name, lat, lon, address, altitude)

    elif other == 4:
        # 位置签到
        print("[获取经纬度] https://api.map.baidu.com/lbsapi/getpoint/index.html")
        preset = configs.get("monitor", {}).get("presetAddress", []) or []
        print("可选地址：")
        for i, item in enumerate(preset):
            print(f"  [{i}] {item['lon']},{item['lat']}/{item['address']}")
        print(f"  [{len(preset)}] 手动输入")
        choice = input("请选择序号: ").strip()
        try:
            idx = int(choice)
        except ValueError:
            idx = len(preset)

        if idx == len(preset):
            raw = input("位置参数（经纬度/地址，如 113.5,34.8/河南省郑州市XX）: ").strip()
            # 解析 lon,lat/address
            loc_part, addr = raw.split("/", 1)
            lon, lat = loc_part.split(",")
            preset.append({"lon": lon, "lat": lat, "address": addr})
        else:
            lon = preset[idx]["lon"]
            lat = preset[idx]["lat"]
            address = preset[idx]["address"]

        location_sign(params, active_id, name, lon, lat, address)
        configs["monitor"] = {"presetAddress": preset}

    elif other in (3, 5):
        # 手势 / 签到码
        general_sign(params, active_id, name)

    elif other == 0:
        info = get_ppt_active_info(active_id, params)
        if info.get("ifphoto") == 1:
            # 拍照签到
            print("请先到 https://pan-yz.chaoxing.com 根目录上传 0.jpg 或 0.png")
            input("上传完成后按回车继续...")
            object_id = get_object_id_from_pan(params)
            if object_id is None:
                sys.exit(0)
            photo_sign(params, active_id, object_id, name)
        else:
            general_sign(params, active_id, name)

    # 回写用户配置
    rest = {k: v for k, v in params.items() if k != "phone"}
    storage.store_user(phone, {
        "phone": phone,
        "params": rest,
        "monitor": configs.get("monitor", {}),
        "mailing": configs.get("mailing", {}),
        "cqserver": configs.get("cqserver", {}),
    })
    print("完成。")


if __name__ == "__main__":
    main()
