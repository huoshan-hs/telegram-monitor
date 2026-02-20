"""配置模块：从 .env 文件加载所有配置项。"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    """获取必需的环境变量，缺失时报错退出。"""
    value = os.getenv(name)
    if not value:
        print(f"[错误] 缺少环境变量: {name}")
        print(f"  请在 .env 文件中设置 {name}，参考 .env.example")
        sys.exit(1)
    return value


# Telegram Bot（用于发送通知）
BOT_TOKEN = _require("BOT_TOKEN")
CHAT_ID = int(_require("CHAT_ID"))

# 要监控的频道列表（用户名，不含 @）
_channels_str = _require("CHANNELS")
CHANNELS = [ch.strip().lstrip("@") for ch in _channels_str.split(",") if ch.strip()]

# 轮询间隔（秒）
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))

# 翻译目标语言
TARGET_LANG = os.getenv("TARGET_LANG", "zh-CN")
