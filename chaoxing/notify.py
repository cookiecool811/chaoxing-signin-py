"""推送通知：邮件、PushPlus、go-cqhttp(QQ机器人)，对应 utils/mailer.ts 与 functions/cq.ts。"""
from __future__ import annotations

import asyncio
import json
import smtplib
from email.mime.text import MIMEText

import requests


# ---------- 邮件 ----------
def send_email(mailing: dict, aid: str, uid: str, realname: str, status: str | None) -> None:
    """通过 SMTP 发送签到结果邮件。"""
    host = mailing.get("host", "smtp.qq.com")
    port = int(mailing.get("port", 465))
    user = mailing.get("user", "")
    pwd = mailing.get("pass", "")
    to = mailing.get("to", "")
    use_ssl = bool(mailing.get("ssl", True))

    html = (
        f"<table border='1'><thead><th>aid</th><th>uid</th><th>name</th><th>status</th>"
        f"</thead><tbody><td>{aid}</td><td>{uid}</td><td>{realname}</td><td>{status}</td></tbody></table>"
    )
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = "服务器签到反馈"
    msg["From"] = f"CLI <{user}>"
    msg["To"] = to

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
        server.login(user, pwd)
        server.sendmail(user, [to], msg.as_string())
        server.quit()
        print("[邮件]发送成功")
    except Exception as e:
        print(f"[邮件]发送失败: {e}")


# ---------- PushPlus ----------
def pushplus_send(token: str, title: str, content: str) -> None:
    try:
        requests.post(
            "http://www.pushplus.plus/send",
            json={"token": token, "title": title, "content": content, "template": "html"},
            timeout=10,
        )
        print("[PushPlus]已发送")
    except Exception as e:
        print(f"[PushPlus]发送失败: {e}")


# ---------- go-cqhttp (QQ机器人) ----------
class CQBot:
    """通过 WebSocket 连接 go-cqhttp，发送消息。对应 functions/cq.ts。"""

    def __init__(self, ws_url: str, target_type: str = "private", target_id: int = 10001):
        self.ws_url = ws_url
        self.target_type = target_type  # group / private
        self.target_id = int(target_id)
        self._ws = None

    async def connect(self) -> None:
        try:
            import websockets
            self._ws = await websockets.connect(self.ws_url)
            print(f"[CQ]已连接 {self.ws_url}")
        except Exception as e:
            print(f"[CQ]连接失败: {e}")
            self._ws = None

    async def send(self, text: str) -> None:
        if not self._ws:
            return
        payload = {
            "action": "send_msg",
            "params": {
                "message_type": self.target_type,
                "message": text,
                "auto_escape": True,
            },
        }
        if self.target_type == "private":
            payload["params"]["user_id"] = self.target_id
        else:
            payload["params"]["group_id"] = self.target_id
        try:
            await self._ws.send(json.dumps(payload))
        except Exception as e:
            print(f"[CQ]发送失败: {e}")

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None
