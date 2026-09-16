"""
===================== 你的个人配置（只改这个文件）=====================
把下面的手机号、密码、位置填好，保存后运行 python monitor.py 即可全自动签到。
"""

# ---------- 账号 ----------
PHONE = "15686178110"
PASSWORD = "Zgj200538710!"        # ←←← 在这里填你的学习通登录密码

# ---------- 签到行为 ----------
DELAY_SECONDS = 0    # 检测到签到后延迟多少秒再签（防检测，一般 0~5 即可）

# ---------- 预设位置（位置签到用，最多填几个，签到失败会自动轮流试）----------
# 经纬度获取：https://api.map.baidu.com/lbsapi/getpoint/index.html
# 点一下地图，右上角会出现"经度,纬度"，复制过来填到 lon / lat
# address 填详细地址，会显示在老师端
PRESET_ADDRESSES = [
    {
        "lon": "108.705000",     # 经度（咸阳示例，改成你自己的）
        "lat": "34.330000",      # 纬度
        "address": "陕西省咸阳市秦都区",  # 详细地址
    },
]

# ---------- 推送通知（不需要就留空）----------
# QQ 机器人（go-cqhttp），不需要就保持 ENABLED = False
CQ = {
    "ENABLED": False,
    "WS_URL": "ws://127.0.0.1:8080",
    "TARGET_TYPE": "group",      # group=群聊, private=私聊
    "TARGET_ID": 10001,          # 群号或QQ号
}

# 邮件通知，不需要就保持 ENABLED = False
EMAIL = {
    "ENABLED": False,
    "HOST": "smtp.qq.com",
    "SSL": True,
    "PORT": 465,
    "USER": "your@qq.com",
    "PASS": "授权码",
    "TO": "your@qq.com",
}
