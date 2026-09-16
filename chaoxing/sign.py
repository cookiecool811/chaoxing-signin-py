"""各种签到实现：普通/手势/签到码、位置、拍照、二维码，对应 functions/*.ts。"""
from __future__ import annotations

import json
import time
from urllib.parse import quote

import config
from chaoxing.client import cookie_serialize, request


# ---------- 普通 / 手势 / 签到码 ----------
def general_sign(cookies: dict, active_id: str, name: str, fid: str | None = None) -> str:
    fid = fid or cookies.get("fid", "-1")
    url = (
        f"{config.PPTSIGN}?activeId={active_id}&uid={cookies.get('_uid', '')}"
        f"&clientip=&latitude=-1&longitude=-1&appType=15&fid={fid}&name={quote(name)}"
    )
    r = request(url, headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"})
    msg = "[通用]签到成功" if r.data == "success" else f"[通用]{r.data}"
    print(msg)
    return msg


# ---------- 位置签到 ----------
def location_sign(
    cookies: dict,
    active_id: str,
    name: str,
    lon: str,
    lat: str,
    address: str,
    fid: str | None = None,
) -> str:
    fid = fid or cookies.get("fid", "-1")
    url = (
        f"{config.PPTSIGN}?name={quote(name)}&address={quote(address)}"
        f"&activeId={active_id}&uid={cookies.get('_uid', '')}"
        f"&clientip=&latitude={lat}&longitude={lon}&fid={fid}&appType=15&ifTiJiao=1"
    )
    r = request(url, headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"})
    msg = "[位置]签到成功" if r.data == "success" else f"[位置]{r.data}"
    print(msg)
    return msg


def location_sign_multi(
    cookies: dict,
    active_id: str,
    name: str,
    preset_address: list[dict],
    fid: str | None = None,
) -> str:
    """多个预设位置轮换尝试，对应原项目 monitor 中的位置签到。"""
    msg = ""
    for item in preset_address:
        msg = location_sign(
            cookies, active_id, name,
            lon=item["lon"], lat=item["lat"], address=item["address"], fid=fid,
        )
        if "成功" in msg:
            return msg
        time.sleep(1)
    return msg


# ---------- 拍照签到 ----------
def get_object_id_from_pan(cookies: dict) -> str | None:
    """从超星云盘根目录找 0.jpg / 0.png 的 objectId。"""
    r = request(config.PANCHAOXING, headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"})
    data = r.data

    start = data.find('enc ="') + 6
    enc = data[start: data.find('"', start)]

    start = data.find('_rootdir = "') + 12
    parent_id = data[start: data.find('"', start)]

    url = (
        f"{config.PANLIST}?puid=0&shareid=0&parentId={parent_id}"
        f"&page=1&size=50&enc={enc}"
    )
    body = f"puid=0&shareid=0&parentId={parent_id}&page=1&size=50&enc={enc}"
    r2 = request(
        url, method="POST",
        headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"},
        data=body,
    )
    obj_list = json.loads(r2.data).get("list", [])
    for obj in obj_list:
        if obj.get("name") in ("0.jpg", "0.png"):
            return obj.get("objectId")

    print("未查询到符合要求的图片，请去网盘检查！")
    return None


def photo_sign(cookies: dict, active_id: str, object_id: str, name: str, fid: str | None = None) -> str:
    fid = fid or cookies.get("fid", "-1")
    url = (
        f"{config.PPTSIGN}?activeId={active_id}&uid={cookies.get('_uid', '')}"
        f"&clientip=&useragent=&latitude=-1&longitude=-1&appType=15&fid={fid}"
        f"&objectId={object_id}&name={quote(name)}"
    )
    r = request(url, headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"})
    msg = "[拍照]签到成功" if r.data == "success" else f"[拍照]{r.data}"
    print(msg)
    return msg


# ---------- 二维码签到 ----------
def qrcode_sign(
    cookies: dict,
    active_id: str,
    enc: str,
    name: str,
    lat: str,
    lon: str,
    address: str,
    altitude: str = "100",
    fid: str | None = None,
) -> str:
    fid = fid or cookies.get("fid", "-1")
    loc = (
        '{"result":"1","address":"' + address + '","latitude":' + lat
        + ',"longitude":' + lon + ',"altitude":' + altitude + "}"
    )
    raw = (
        f"{config.PPTSIGN}?enc={enc}&name={quote(name)}&activeId={active_id}"
        f"&uid={cookies.get('_uid', '')}&clientip=&location={quote(loc, safe='')}"
        f"&latitude=-1&longitude=-1&fid={fid}&appType=15"
    )
    r = request(raw, headers={"Cookie": cookie_serialize(cookies), "User-Agent": "Mozilla/5.0"})
    msg = "[二维码]签到成功" if r.data == "success" else f"[二维码]{r.data}"
    print(msg)
    return msg
