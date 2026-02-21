"""
Telegram 频道消息监控 + 翻译 + 通知

运行模式:
    python monitor.py                  # 单次检查
    python monitor.py --loop           # 本地持续监控
    python monitor.py --duration 240   # 循环指定秒数后退出（GitHub Actions 用）
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

        # 提取图片 URL（从 background-image style 中）
        image_url = None
        photo_wrap = msg_div.select_one(".tgme_widget_message_photo_wrap")
        if photo_wrap:
            style = photo_wrap.get("style", "")
            if "background-image:url('" in style:
                image_url = style.split("background-image:url('")[1].split("')")[0]
            elif "background-image:url(" in style:
                image_url = style.split("background-image:url(")[1].split(")")[0].strip("'\"")

        # 提取文本（排除引用内容）
        text_div = msg_div.select_one(".tgme_widget_message_text")
        text = ""
        if text_div:
            # 先移除引用块，避免混入引用内容
            for reply_el in text_div.select(".tgme_widget_message_reply"):
                reply_el.decompose()
            text = text_div.get_text(separator="\n").strip()

        # 跳过既无文字也无图片的消息
        if not text and not image_url:
            continue

        messages.append({
            "id": msg_id,
            "text": text,
            "channel": channel,
            "image_url": image_url,
        })

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
        return

    for msg in new_messages:
        desc = msg['text'][:60] if msg['text'] else '[图片]'
        print(f"\n[新消息] @{channel} (#{msg['id']}): {desc}...")
        translated = translate(msg["text"]) if msg["text"] else None
        ok = send_notification(
            f"@{channel}", msg["text"] or "[图片消息]", translated,
            image_url=msg.get("image_url"),
        )
        if ok:
            has_img = " +图片" if msg.get("image_url") else ""
            label = f"翻译并通知{has_img}" if translated else f"直接转发{has_img}"
            print(f"  ✅ {label}")
        else:
            print(f"  ❌ 通知发送失败")
        state[channel] = msg["id"]


def check_all() -> None:
    """检查所有频道一次并保存状态。"""
    state = load_state()
    for ch in CHANNELS:
        process_channel(ch, state)
    save_state(state)


def run_duration(seconds: int) -> None:
    """在指定时间内持续循环检查（GitHub Actions 用）。

    每次 Actions cron（5分钟）触发时，在内部循环 4 分钟，
    每 POLL_INTERVAL 秒检查一次，实现近实时监控。
    """
    print(f"[启动] 持续监控 {seconds} 秒，间隔 {POLL_INTERVAL} 秒")
    print(f"[频道] {', '.join('@' + ch for ch in CHANNELS)}")

    end_time = time.time() + seconds
    check_all()  # 立即检查一次

    while time.time() < end_time:
        time.sleep(POLL_INTERVAL)
        check_all()

    print(f"[结束] 本轮监控完成")


def run_loop() -> None:
    """本地持续监控模式。"""
    print("=" * 50)
    print("  Telegram 频道监控翻译通知系统")
    print("=" * 50)
    print(f"\n监控频道: {', '.join('@' + ch for ch in CHANNELS)}")
    print(f"轮询间隔: {POLL_INTERVAL} 秒")
    print(f"[监控中] 按 Ctrl+C 停止\n")

    check_all()
    try:
        while True:
            time.sleep(POLL_INTERVAL)
            check_all()
    except KeyboardInterrupt:
        print("\n[停止] 已退出")


if __name__ == "__main__":
    if "--loop" in sys.argv:
        run_loop()
    elif "--duration" in sys.argv:
        idx = sys.argv.index("--duration")
        dur = int(sys.argv[idx + 1])
        run_duration(dur)
    else:
        check_all()
