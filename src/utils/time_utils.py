"""
时间工具模块
提供时间格式化和处理功能
"""

from datetime import datetime, timezone
from typing import Optional


def format_datetime_chinese(iso_time_str: str) -> str:
    """
    将ISO格式的时间字符串转换为中文友好的显示格式

    Args:
        iso_time_str: ISO格式的时间字符串，如 "2025-04-05T20:31:00.123456+00:00"

    Returns:
        str: 格式化后的中文时间字符串，如 "2025-04-05 20:31"
    """
    if not iso_time_str:
        return "未知"

    try:
        # 解析ISO格式时间
        dt = datetime.fromisoformat(iso_time_str.replace('Z', '+00:00'))

        # 转换为本地时间
        local_dt = dt.astimezone()

        # 格式化为中文友好格式
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return "格式错误"


def count_text_stats(text: str) -> dict:
    """
    统计文本的详细信息

    Args:
        text: 要统计的文本

    Returns:
        dict: 包含各种统计信息的字典
    """
    if not text:
        return {
            'total_chars': 0,
            'chinese_chars': 0,
            'english_words': 0,
            'symbols': 0,
            'lines': 0
        }

    total_chars = len(text)
    lines = len(text.splitlines())

    # 统计各类字符
    chinese_chars = 0
    english_chars = 0
    symbols = 0

    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
            chinese_chars += 1
        elif char.isalpha():  # 英文字符
            english_chars += 1
        elif not char.isspace() and char != '\n' and char != '\r':  # 符号（排除空白字符和换行符）
            symbols += 1

    # 英文单词计数 - 更准确的方法
    import re
    # 使用正则表达式匹配英文单词（连续的字母）
    english_words = len(re.findall(r'[a-zA-Z]+', text))

    return {
        'total_chars': total_chars,
        'chinese_chars': chinese_chars,
        'english_words': english_words,
        'symbols': symbols,
        'lines': lines
    }


def format_word_count(count: int) -> str:
    """
    格式化字数显示
    
    Args:
        count: 字数
        
    Returns:
        str: 格式化后的字数字符串
    """
    if count < 1000:
        return str(count)
    elif count < 10000:
        return f"{count / 1000:.1f}k"
    else:
        return f"{count / 10000:.1f}万"


def format_tags_display(tags: list) -> str:
    """
    格式化标签显示
    
    Args:
        tags: 标签列表
        
    Returns:
        str: 格式化后的标签字符串
    """
    if not tags:
        return "无"
    
    if len(tags) <= 3:
        return " | ".join(tags)
    else:
        return " | ".join(tags[:3]) + f" 等{len(tags)}个"


def get_time_ago(iso_time_str: str) -> str:
    """
    获取相对时间描述（多久前）
    
    Args:
        iso_time_str: ISO格式的时间字符串
        
    Returns:
        str: 相对时间描述，如 "2小时前"、"3天前"
    """
    if not iso_time_str:
        return "未知"
    
    try:
        # 解析ISO格式时间
        dt = datetime.fromisoformat(iso_time_str.replace('Z', '+00:00'))
        
        # 获取当前时间
        now = datetime.now(timezone.utc)
        
        # 计算时间差
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}小时前"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"
    except (ValueError, TypeError):
        return "未知"
