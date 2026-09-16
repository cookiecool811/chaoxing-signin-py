"""课程活动遍历、预签到，对应 functions/activity.ts。"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from chaoxing.client import cookie_serialize, request


def _get_activity_one(course: dict, cookies: dict) -> dict:
    """查询单门课的最新活动。命中有效签到则返回活动 dict，否则抛异常。"""
    url = (
        f"{config.ACTIVELIST}?fid=0&courseId={course['courseId']}"
        f"&classId={course['classId']}&_={int(time.time() * 1000)}"
    )
    result = request(url, headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"})
    data = json.loads(result.data)

    if data.get("data") is None:
        raise RuntimeError("Too Frequent")

    active_list = data["data"].get("activeList", [])
    if not active_list:
        raise LookupError("Not Available")

    first = active_list[0]
    other_id = int(first["otherId"])
    if 0 <= other_id <= 5 and first.get("status") == 1:
        # 活动开始超过 2 小时则忽略
        if (time.time() * 1000 - int(first["startTime"])) / 1000 < 7200:
            print(f"检测到活动：{first.get('nameOne', '')}")
            return {
                "activeId": first["id"],
                "name": first.get("nameOne", ""),
                "courseId": course["courseId"],
                "classId": course["classId"],
                "otherId": other_id,
            }
    raise LookupError("Not Available")


def traverse_course_activity(courses: list[dict], cookies: dict) -> dict | str:
    """遍历所有课程找有效签到活动。每 5 个并发请求，任一命中即返回。"""
    print("正在查询有效签到活动，等待时间视网络情况而定...")

    if len(courses) == 1:
        try:
            return _get_activity_one(courses[0], cookies)
        except Exception:
            print("未检测到有效签到活动！")
            return "NoActivity"

    # 分批，每批 5 个线程
    batch_size = 5
    for start in range(0, len(courses), batch_size):
        batch = courses[start: start + batch_size]
        with ThreadPoolExecutor(max_workers=len(batch)) as pool:
            futures = {pool.submit(_get_activity_one, c, cookies): c for c in batch}
            for fut in as_completed(futures):
                try:
                    return fut.result()
                except Exception:
                    continue
    print("未检测到有效签到活动！")
    return "NoActivity"


def get_ppt_active_info(active_id: str, cookies: dict) -> dict:
    """根据 activeId 获取活动详情（含 ifphoto 等）。"""
    result = request(
        f"{config.PPTACTIVEINFO}?activeId={active_id}",
        headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"},
    )
    return json.loads(result.data)["data"]


def pre_sign(activity: dict, cookies: dict) -> None:
    """预签到：preSign + analysis + analysis2 + 500ms 延时。"""
    uid = cookies.get("_uid", "")
    request(
        f"{config.PRESIGN}?courseId={activity['courseId']}&classId={activity['classId']}"
        f"&activePrimaryId={activity['activeId']}&general=1&sys=1&ls=1&appType=15"
        f"&&tid=&uid={uid}&ut=s",
        headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"},
    )
    print("[预签]已请求")

    # analysis
    r1 = request(
        f"{config.ANALYSIS}?vs=1&DB_STRATEGY=RANDOM&aid={activity['activeId']}",
        headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"},
    )
    code = r1.data
    code_start = code.find("code='+'") + 8
    code = code[code_start:]
    code_end = code.find("'")
    code = code[:code_end]

    # analysis2
    r2 = request(
        f"{config.ANALYSIS2}?DB_STRATEGY=RANDOM&code={code}",
        headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"},
    )
    print(f"analysis 请求结果：{r2.data}")

    time.sleep(0.5)


def get_sign_type(ppt_info: dict) -> str:
    """根据 getPPTActiveInfo 的返回判断签到类型。"""
    other = ppt_info.get("otherId")
    if other == 0:
        return "拍照签到" if ppt_info.get("ifphoto") == 1 else "普通签到"
    return {2: "二维码签到", 3: "手势签到", 4: "位置签到", 5: "签到码签到"}.get(other, "未知")


def get_sign_result(raw: str) -> str:
    return {
        "success": "成功",
        "fail": "失败",
        "fail-need-qrcode": "请发送二维码",
    }.get(raw, raw)
