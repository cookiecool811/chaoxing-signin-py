# 超星学习通自动签到

基于 Python 开发的超星学习通自动签到工具，支持本地运行与 GitHub Actions 云端定时部署，电脑关机也能自动签到。

## 功能

- 手机号 + 密码自动登录（DES-ECB 加密）
- 普通签到、手势签到、签到码签到
- 位置签到（支持多预设地址自动轮换）
- 拍照签到（从超星云盘读取图片）
- 二维码签到（手动提供 enc 参数）
- 自动轮询课程活动，检测到签到立即完成
- 支持邮件推送、QQ 机器人（go-cqhttp）通知
- **GitHub Actions 部署**：免费云端运行，关机不影响

## 环境要求

- Python 3.9+
- 依赖见 `requirements.txt`

## 安装

```bash
cd chaoxing-signin-py
pip install -r requirements.txt
```

## 本地使用

复制 `user_config.example.py` 为 `user_config.py`（该文件已被 `.gitignore` 忽略，不会泄露账号信息），填写：

```python
PHONE = "你的手机号"
PASSWORD = "你的密码"
PRESET_ADDRESSES = [
    {"lon": "经度", "lat": "纬度", "address": "详细地址"},
]
```

运行手动签到：

```bash
python main.py
```

运行自动监听（持续轮询，每 30 秒扫描一次课程）：

```bash
python monitor.py
```

## GitHub Actions 云端自动签到（推荐）

无需自己开电脑，部署到 GitHub 服务器定时运行，全程免费。

### 1. 推送代码到 GitHub

```bash
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

### 2. 配置 Secrets

进入仓库 **Settings → Secrets and variables → Actions**，添加以下 secrets：

| Name | 说明 | 示例 |
|---|---|---|
| `CHAOXING_PHONE` | 学习通手机号 | `13800138000` |
| `CHAOXING_PASSWORD` | 学习通密码 | `yourpassword` |
| `CHAOXING_ADDRESS` | 位置（经纬度/地址），多个用分号分隔 | `108.705,34.330,陕西省咸阳市` |
| `CHAOXING_DELAY` | 签到延时秒数（可选） | `0` |
| `PUSHPLUS_TOKEN` | PushPlus 微信推送 token（可选，失败/成功会推送） | `xxxxxxxx` |

### 3. 启用 Actions

进入仓库 **Actions** 标签页，手动触发一次 `chaoxing-signin` workflow 测试。

配置完成后，GitHub 会每 10 分钟自动运行一次 `run_once.py`（错开整点高峰以减少排队丢跑），发现签到活动即自动完成，无需人工干预。

> 经纬度获取：<https://api.map.baidu.com/lbsapi/getpoint/index.html>

## 注意事项

- **公开仓库 60 天无活动，定时任务会被 GitHub 自动禁用且不发通知**。本项目内置 `keepalive` 工作流，会在满 40 天无提交时自动保活；也可在 Actions 页面手动点 **Enable workflow** 恢复。
- 切勿把含真实账号密码的 `user_config.py` 提交到公开仓库。若曾提交，密码会永久保留在 git 历史中，应立即修改学习通密码。

## 签到类型说明

| 类型 | 自动处理方式 |
|---|---|
| 普通签到 | 自动完成 |
| 手势签到 | 自动完成 |
| 签到码签到 | 自动完成 |
| 位置签到 | 自动使用预设地址尝试 |
| 拍照签到 | 自动从超星云盘读取 `0.jpg`/`0.png` |
| 二维码签到 | 需要人工提供 enc 参数 |

## 目录结构

```
chaoxing-signin-py/
├── main.py              # 手动签到
├── monitor.py           # 本地持续监听
├── run_once.py          # 单次签到（GitHub Actions 调用）
├── config.py            # API 地址与常量
├── user_config.example.py  # 个人配置模板（复制为 user_config.py）
├── requirements.txt
├── .github/workflows/
│   ├── signin.yml       # GitHub Actions 定时签到
│   └── keepalive.yml    # 定时保活，防止 60 天自动禁用
└── chaoxing/
    ├── client.py        # HTTP 请求封装
    ├── storage.py       # 本地凭证存储
    ├── user.py          # 登录与课程获取
    ├── activity.py      # 活动遍历与预签
    ├── sign.py          # 各类签到实现
    └── notify.py        # 邮件、QQ 机器人推送
```

## 免责声明

本项目仅供学习交流使用，请勿用于商业用途。使用者需自行承担使用风险与责任。
