# Telegram 频道监控翻译通知系统

自动监控 Telegram 公开频道，翻译新消息为中文，通过 Bot 私聊通知。

## 功能

- 监控指定的 Telegram 公开频道
- 自动将非中文消息翻译为中文（Google Translate）
- 通过 Telegram Bot 私聊发送通知
- 支持多频道同时监控

## 部署

本项目设计运行在 Render 免费后台 Worker 上。

### 环境变量

| 变量 | 说明 |
|------|------|
| `BOT_TOKEN` | Telegram Bot Token（@BotFather 获取） |
| `CHAT_ID` | 你的 Telegram 用户 ID（@userinfobot 获取） |
| `CHANNELS` | 要监控的频道用户名，逗号分隔 |
| `POLL_INTERVAL` | 轮询间隔（秒），默认 30 |
