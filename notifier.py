"""通知模块：通过 Telegram Bot HTTP API 发送翻译后的消息。"""

import requests
from datetime import datetime, timezone, timedelta

from config import BOT_TOKEN, CHAT_ID

# 北京时间
BJT = timezone(timedelta(hours=8))
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_notification(
    channel_name: str,
    original_text: str,
    translated_text: str | None,
) -> bool:
    """发送通知到用户私聊。

    Args:
        channel_name: 来源频道名称
        original_text: 原始消息文本
        translated_text: 翻译后的文本（None 表示原文已是中文）

    Returns:
        是否发送成功
    """
    now = datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")

    # 截断过长的原文（Telegram 消息上限 4096 字符）
    max_len = 1500
    original_display = original_text[:max_len] + "..." if len(original_text) > max_len else original_text

    if translated_text:
        message = (
            f"📢 来自频道: {channel_name}\n"
            f"🕐 {now}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🌐 原文:\n{original_display}\n\n"
            f"🇨🇳 中文翻译:\n{translated_text}"
        )
    else:
        message = (
            f"📢 来自频道: {channel_name}\n"
            f"🕐 {now}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{original_display}"
        )

    try:
        resp = requests.post(
            f"{BOT_API}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message},
            timeout=10,
        )
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        else:
            print(f"[通知错误] {resp.text}")
            return False
    except Exception as e:
        print(f"[通知错误] {e}")
        return False
