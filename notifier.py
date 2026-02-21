"""通知模块：通过 Telegram Bot HTTP API 发送翻译后的消息。"""

import requests
from datetime import datetime, timezone, timedelta

from config import BOT_TOKEN, CHAT_ID

# 北京时间
BJT = timezone(timedelta(hours=8))
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _build_text(
    channel_name: str,
    original_text: str,
    translated_text: str | None,
) -> str:
    """构建消息正文。"""
    now = datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")

    max_len = 1200
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


def _send_photo(image_url: str, caption: str) -> bool:
    """尝试发送图片，失败则返回 False。"""
    try:
        resp = requests.post(
            f"{BOT_API}/sendPhoto",
            json={"chat_id": CHAT_ID, "photo": image_url, "caption": caption[:1024]},
            timeout=15,
        )
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        print(f"  [图片发送失败，回退到纯文字] {resp.json().get('description', '')[:80]}")
    except Exception as e:
        print(f"  [图片发送异常，回退到纯文字] {e}")
    return False


def send_notification(
    channel_name: str,
    original_text: str,
    translated_text: str | None,
    image_url: str | None = None,
) -> bool:
    """发送通知到用户私聊。图片发送失败会自动回退到纯文字。"""
    text = _build_text(channel_name, original_text, translated_text)

    # 有图片时先尝试 sendPhoto
    photo_sent = False
    if image_url:
        photo_sent = _send_photo(image_url, text)

    # 图片发送成功且文字短 → 已包含在 caption 里，无需再发文字
    if photo_sent and len(text) <= 1024:
        return True

    # 图片发送成功但文字太长 → 追加发文字
    # 图片发送失败或无图片 → 直接发文字
    if image_url and not photo_sent:
        text = f"🖼️ [含图片，请查看原频道]\n\n{text}"

    try:
        resp = requests.post(
            f"{BOT_API}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=15,
        )
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        print(f"[通知错误] {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[通知错误] {e}")
        return False
