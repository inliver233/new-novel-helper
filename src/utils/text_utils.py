"""
文本处理工具模块
提供文本统计、格式化和处理功能
"""

import re
from typing import Dict


def count_text_stats(text: str) -> Dict[str, int]:
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
