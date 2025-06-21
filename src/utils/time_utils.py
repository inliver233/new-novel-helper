"""
时间工具模块
提供时间格式化和处理功能
"""

from datetime import datetime, timezone


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
