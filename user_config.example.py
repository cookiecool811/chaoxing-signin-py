"""
===================== 个人配置模板 =====================
复制本文件为 user_config.py，再填写你自己的信息。
user_config.py 已被 .gitignore 忽略，不会被提交。
"""

# ---------- 账号 ----------
PHONE = "你的手机号"
PASSWORD = "你的学习通密码"

# ---------- 签到行为 ----------
DELAY_SECONDS = 0    # 检测到签到后延迟多少秒再签（防检测，一般 0~5 即可）

# ---------- 预设位置（位置签到用，可填多个，签到失败会自动轮流试）----------
# 经纬度获取：https://api.map.baidu.com/lbsapi/getpoint/index.html
PRESET_ADDRESSES = [
    {
        "lon": "108.705000",     # 经度
        "lat": "34.330000",      # 纬度
        "address": "陕西省咸阳市秦都区",  # 详细地址
    },
]

# ---------- 推送通知（不需要就留空）----------
CQ = {
    "ENABLED": False,
    "WS_URL": "ws://127.0.0.1:8080",
    "TARGET_TYPE": "group",      # group=群聊, private=私聊
    "TARGET_ID": 10001,
}

EMAIL = {
    "ENABLED": False,
    "HOST": "smtp.qq.com",
    "SSL": True,
    "PORT": 465,
    "USER": "your@qq.com",
    "PASS": "授权码",
    "TO": "your@qq.com",
}
