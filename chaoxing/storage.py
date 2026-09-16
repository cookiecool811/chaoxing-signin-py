"""本地用户凭证存储，对应原项目 utils/file.ts。"""
from __future__ import annotations

import json
import os
from typing import Any

# data/storage.json 与本模块同级
# chaoxing/storage.py -> chaoxing/ -> 项目根/ -> data/
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
STORAGE_FILE = os.path.join(DATA_DIR, "storage.json")


def _ensure_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_storage() -> dict[str, Any]:
    """读取 storage.json，文件不存在时返回空结构。"""
    _ensure_dir()
    if not os.path.exists(STORAGE_FILE):
        return {"users": []}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_storage(data: dict[str, Any]) -> None:
    _ensure_dir()
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def store_user(phone: str, user: dict) -> list:
    """保存或更新一个用户，返回 users 列表。"""
    user["phone"] = phone
    data = load_storage()
    users = data.get("users", [])
    for i, u in enumerate(users):
        if u.get("phone") == phone:
            users[i] = user
            break
    else:
        users.append(user)
    data["users"] = users
    save_storage(data)
    return users


def get_user(phone: str) -> dict | None:
    data = load_storage()
    for u in data.get("users", []):
        if u.get("phone") == phone:
            return json.loads(json.dumps(u))  # 深拷贝
    return None


def list_users() -> list[str]:
    data = load_storage()
    return [u.get("phone", "") for u in data.get("users", [])]
