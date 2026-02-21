"""通知模块：通过 Telegram Bot HTTP API 发送翻译后的消息。"""

import requests
from datetime import datetime, timezone, timedelta

from config import BOT_TOKEN, CHAT_ID

# 北京时间
BJT = timezone(timedelta(hours=8))
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _build_caption(
    channel_name: str,
    original_text: str,
    translated_text: str | None,
) -> str:
    """构建消息正文。"""
    now = datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")

    # Telegram caption 上限 1024，message 上限 4096
    max_len = 800
    original_display = original_text[:max_len] + "..." if len(original_text) > max_len else original_text

    if translated_text:
        return (
            f"📢 来自频道: {channel_name}\n"
            f"🕐 {now}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🌐 原文:\n{original_display}\n\n"
            f"🇨🇳 中文翻译:\n{translated_text}"
        )
    else:
        return (
            f"📢 来自频道: {channel_name}\n"
            f"🕐 {now}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{original_display}"
        )


def send_notification(
    channel_name: str,
    original_text: str,
    translated_text: str | None,
    image_url: str | None = None,
) -> bool:
    """发送通知到用户私聊。支持图片+文字。

    Args:
        channel_name: 来源频道名称
        original_text: 原始消息文本
        translated_text: 翻译后的文本（None 表示原文已是中文）
        image_url: 图片 URL（None 表示无图片）

    Returns:
        是否发送成功
    """
    caption = _build_caption(channel_name, original_text, translated_text)

    try:
        if image_url:
            # 有图片：用 sendPhoto
            # caption 上限 1024 字符，超出则拆分为 photo + message
            if len(caption) <= 1024:
                resp = requests.post(
                    f"{BOT_API}/sendPhoto",
                    json={"chat_id": CHAT_ID, "photo": image_url, "caption": caption},
                    timeout=15,
                )
            else:
                # 先发图片，再发文字
                requests.post(
                    f"{BOT_API}/sendPhoto",
                    json={"chat_id": CHAT_ID, "photo": image_url},
                    timeout=15,
                )
                resp = requests.post(
                    f"{BOT_API}/sendMessage",
                    json={"chat_id": CHAT_ID, "text": caption},
                    timeout=15,
                )
        else:
            # 无图片：用 sendMessage
            resp = requests.post(
                f"{BOT_API}/sendMessage",
                json={"chat_id": CHAT_ID, "text": caption},
                timeout=15,
            )

        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        else:
            print(f"[通知错误] {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[通知错误] {e}")
        return False
