# 超星学习通签到（Python 版）

从 TypeScript 项目 [cxOrz/chaoxing-sign-in](https://github.com/cxOrz/chaoxing-sign-in) 移植而来，可直接在 PyCharm 中运行。

## 功能

- 手机号 + 密码登录（DES-ECB 加密，与原版一致）
- 普通签到 / 手势签到 / 签到码签到
- 位置签到（支持多预设地址轮换）
- 拍照签到（从超星云盘根目录读取 `0.jpg` / `0.png`）
- 二维码签到（需手动提供 `enc` 参数）
- 本地多用户凭证存储（`data/storage.json`）
- 监听模式：定时轮询课程活动，发现即自动签到
- 推送：邮件（SMTP）、go-cqhttp（QQ 机器人 WebSocket）

## 与原版差异

| 原版 (Node.js) | Python 版 |
|---|---|
| 环信 IM WebSocket 实时推送 | 定时轮询课程活动（默认 15 秒） |
| React + Koa Web UI | 纯命令行交互 |
| Tencent Cloud OCR 识别二维码 | 未实现（需自行配置，可后续加） |
| monorepo (pnpm + Turborepo) | 扁平 Python 包结构 |

## 环境要求

- Python 3.9+
- 依赖见 `requirements.txt`

## 安装

```bash
cd chaoxing-signin-py
pip install -r requirements.txt
```

## 使用

### 手动签到

```bash
python main.py
```

按提示选择用户、登录、选择课程活动类型即可。

### 监听模式（自动签到）

```bash
python monitor.py
```

首次运行会交互式配置：
- 签到延时（秒）
- 预设位置（位置签到用）
- 邮件推送（可选）
- go-cqhttp（QQ 机器人，可选）

配置会保存在 `data/storage.json`，下次运行可直接复用。

## 签到类型说明

| otherId | 类型 | 说明 |
|---|---|---|
| 0 | 普通/拍照 | `ifphoto=1` 为拍照签到，否则普通 |
| 2 | 二维码签到 | 需手动提供 enc 参数 |
| 3 | 手势签到 | 自动完成 |
| 4 | 位置签到 | 需预设经纬度和地址 |
| 5 | 签到码签到 | 自动完成 |

位置经纬度获取：<https://api.map.baidu.com/lbsapi/getpoint/index.html>

## 目录结构

```
chaoxing-signin-py/
├── main.py              # 手动签到入口
├── monitor.py           # 监听模式入口
├── config.py            # API 地址与常量
├── requirements.txt
├── data/
│   └── storage.json     # 用户凭证（自动生成）
└── chaoxing/
    ├── client.py        # HTTP 封装、Cookie 序列化
    ├── storage.py       # 本地 JSON 存储
    ├── user.py          # 登录、课程、用户信息
    ├── activity.py      # 活动遍历、预签
    ├── sign.py          # 各种签到实现
    └── notify.py        # 邮件 / PushPlus / CQ 机器人
```

## 免责声明

本项目仅用于学习交流，请勿用于商业用途。使用者自负行为责任。
