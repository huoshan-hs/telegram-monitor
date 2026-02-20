"""
Telegram 频道消息监控 + 翻译 + 通知（网页抓取版）

主程序：通过抓取 Telegram 公开频道的网页预览获取新消息，
自动翻译为中文，通过 Bot 私聊发送通知。

无需 api_id / api_hash，只需 Bot Token。

使用方式:
    1. 复制 .env.example 为 .env 并填写配置
    2. pip install -r requirements.txt
    3. python monitor.py
"""

import time
import json
import requests
from bs4 import BeautifulSoup

from config import CHANNELS, POLL_INTERVAL
from translator import translate
from notifier import send_notification


# 记录每个频道已处理的最新消息 ID，避免重复通知
_last_seen: dict[str, int] = {}


def fetch_channel_messages(channel: str) -> list[dict]:
    """抓取频道最新的消息。

    通过 Telegram 的公开网页预览 (t.me/s/channel) 获取消息。

    Returns:
        消息列表，每条包含 id, text, channel
    """
    url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            },
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"  [抓取错误] {channel}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    messages = []

    for widget in soup.select(".tgme_widget_message_wrap"):
        msg_div = widget.select_one(".tgme_widget_message")
        if not msg_div:
            continue

        # 提取消息 ID
        data_post = msg_div.get("data-post", "")
        try:
            msg_id = int(data_post.split("/")[-1])
        except (ValueError, IndexError):
            continue

        # 提取文本内容
        text_div = msg_div.select_one(".tgme_widget_message_text")
        if not text_div:
            continue
        text = text_div.get_text(separator="\n").strip()
        if not text:
            continue

        messages.append({"id": msg_id, "text": text, "channel": channel})

    return messages


def process_channel(channel: str) -> None:
    """处理单个频道的新消息。"""
    messages = fetch_channel_messages(channel)
    if not messages:
        return

    # 按 ID 排序
    messages.sort(key=lambda m: m["id"])

    last_seen = _last_seen.get(channel, 0)

    # 首次运行时，只记录最新 ID，不发送历史消息
    if last_seen == 0:
        _last_seen[channel] = messages[-1]["id"]
        print(f"  ✅ @{channel} 已初始化（最新消息 ID: {messages[-1]['id']}）")
        return

    # 处理新消息
    new_messages = [m for m in messages if m["id"] > last_seen]
    for msg in new_messages:
        print(f"\n[新消息] @{channel} (#{msg['id']}): {msg['text'][:60]}...")

        # 翻译
        translated = translate(msg["text"])

        # 发送通知
        ok = send_notification(f"@{channel}", msg["text"], translated)
        if ok:
            label = "翻译并通知" if translated else "直接转发（中文）"
            print(f"  ✅ {label}")
        else:
            print(f"  ❌ 通知发送失败")

        _last_seen[channel] = msg["id"]


def main() -> None:
    """主函数。"""
    print("=" * 50)
    print("  Telegram 频道监控翻译通知系统")
    print("  （网页抓取版 · 无需 API 凭据）")
    print("=" * 50)
    print(f"\n监控频道: {', '.join('@' + ch for ch in CHANNELS)}")
    print(f"轮询间隔: {POLL_INTERVAL} 秒")
    print(f"\n[初始化] 正在获取各频道最新状态...")

    # 初始化：记录当前最新消息 ID
    for ch in CHANNELS:
        process_channel(ch)

    print(f"\n[监控中] 开始监控，按 Ctrl+C 停止\n")

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            for ch in CHANNELS:
                process_channel(ch)
    except KeyboardInterrupt:
        print("\n\n[停止] 已退出监控")


if __name__ == "__main__":
    main()
