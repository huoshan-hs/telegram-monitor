"""翻译模块：使用 Google Translate 将文本翻译为目标语言。"""

import re
from deep_translator import GoogleTranslator

from config import TARGET_LANG


def is_chinese(text: str) -> bool:
    """判断文本是否主要为中文。

    当中文字符占比超过 50% 时视为中文文本。
    """
    if not text:
        return True
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total_chars = len(re.findall(r"\S", text))  # 非空白字符
    if total_chars == 0:
        return True
    return chinese_chars / total_chars > 0.5


def translate(text: str) -> str | None:
    """将文本翻译为中文。

    如果文本已经是中文，返回 None（表示无需翻译）。
    翻译失败时返回 None 并打印错误。
    """
    if not text or not text.strip():
        return None

    if is_chinese(text):
        return None

    try:
        result = GoogleTranslator(source="auto", target=TARGET_LANG).translate(text)
        return result
    except Exception as e:
        print(f"[翻译错误] {e}")
        return None
