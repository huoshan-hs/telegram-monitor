"""
Telegram 频道消息监控 + 翻译 + 通知（GitHub Actions 版）

单次运行模式：检查新消息 → 翻译 → 通知 → 保存状态 → 退出。
通过 GitHub Actions cron 定时调用实现持续监控。

本地使用:
    python monitor.py              # 单次运行
    python monitor.py --loop       # 循环模式（本地调试用）
"""

import sys
import json
import time
import os
import requests
from bs4 import BeautifulSoup

from config import CHANNELS, POLL_INTERVAL
from translator import translate
from notifier import send_notification

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


def load_state() -> dict:
    """加载上次运行的状态（各频道已处理的最新消息 ID）。"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    """保存状态到文件。"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_channel_messages(channel: str) -> list[dict]:
    """抓取频道最新的消息。"""
    url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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

        data_post = msg_div.get("data-post", "")
        try:
            msg_id = int(data_post.split("/")[-1])
        except (ValueError, IndexError):
            continue

        text_div = msg_div.select_one(".tgme_widget_message_text")
        if not text_div:
            continue
        text = text_div.get_text(separator="\n").strip()
        if not text:
            continue

        messages.append({"id": msg_id, "text": text, "channel": channel})

    return messages


def process_channel(channel: str, state: dict) -> None:
    """处理单个频道的新消息。"""
    messages = fetch_channel_messages(channel)
    if not messages:
        return

    messages.sort(key=lambda m: m["id"])
    last_seen = state.get(channel, 0)

    # 首次运行：只记录最新 ID
    if last_seen == 0:
        state[channel] = messages[-1]["id"]
        print(f"  ✅ @{channel} 初始化（最新 ID: {messages[-1]['id']}）")
        return

    new_messages = [m for m in messages if m["id"] > last_seen]
    if not new_messages:
        print(f"  @{channel}: 无新消息")
        return

    for msg in new_messages:
        print(f"\n[新消息] @{channel} (#{msg['id']}): {msg['text'][:60]}...")
        translated = translate(msg["text"])
        ok = send_notification(f"@{channel}", msg["text"], translated)
        if ok:
            label = "翻译并通知" if translated else "直接转发（中文）"
            print(f"  ✅ {label}")
        else:
            print(f"  ❌ 通知发送失败")
        state[channel] = msg["id"]


def run_once() -> None:
    """单次运行：检查所有频道 → 保存状态。"""
    state = load_state()
    print(f"[检查] {len(CHANNELS)} 个频道...")
    for ch in CHANNELS:
        process_channel(ch, state)
    save_state(state)
    print("[完成]")


def run_loop() -> None:
    """循环模式（本地调试用）。"""
    print("=" * 50)
    print("  Telegram 频道监控翻译通知系统")
    print("=" * 50)
    print(f"\n监控频道: {', '.join('@' + ch for ch in CHANNELS)}")
    print(f"轮询间隔: {POLL_INTERVAL} 秒\n")

    # 初始化
    run_once()

    print(f"\n[监控中] 按 Ctrl+C 停止\n")
    try:
        while True:
            time.sleep(POLL_INTERVAL)
            run_once()
    except KeyboardInterrupt:
        print("\n[停止] 已退出")


if __name__ == "__main__":
    if "--loop" in sys.argv:
        run_loop()
    else:
        run_once()
