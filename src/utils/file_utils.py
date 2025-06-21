"""
文件操作相关的工具函数
"""

import os
import re
from typing import Optional


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    if not filename:
        return ""
    
    # 移除或替换不安全字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # 移除前后空格和点
    filename = filename.strip('. ')
    
    # 确保文件名不为空
    if not filename:
        return "untitled"
    
    return filename


def validate_filename(filename: str) -> bool:
    """验证文件名是否有效
    
    Args:
        filename: 要验证的文件名
        
    Returns:
        bool: 文件名是否有效
    """
    if not filename or not filename.strip():
        return False
    
    # 检查是否包含不安全字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        if char in filename:
            return False
    
    # 检查是否为保留名称（Windows）
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    if filename.upper() in reserved_names:
        return False
    
    return True


def ensure_directory_exists(directory_path: str) -> bool:
    """确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def get_safe_path(base_path: str, name: str) -> str:
    """获取安全的文件路径
    
    Args:
        base_path: 基础路径
        name: 文件或目录名
        
    Returns:
        str: 安全的完整路径
    """
    safe_name = sanitize_filename(name)
    return os.path.join(base_path, safe_name)


def get_unique_filename(directory: str, base_name: str, extension: str = "") -> str:
    """获取唯一的文件名（如果文件已存在，则添加数字后缀）
    
    Args:
        directory: 目录路径
        base_name: 基础文件名
        extension: 文件扩展名（包含点号）
        
    Returns:
        str: 唯一的文件名
    """
    safe_base = sanitize_filename(base_name)
    counter = 1
    
    while True:
        if counter == 1:
            filename = f"{safe_base}{extension}"
        else:
            filename = f"{safe_base}_{counter}{extension}"
        
        full_path = os.path.join(directory, filename)
        if not os.path.exists(full_path):
            return filename
        
        counter += 1
        
        # 防止无限循环
        if counter > 1000:
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            return f"{safe_base}_{unique_id}{extension}"


def is_valid_path(path: str) -> bool:
    """检查路径是否有效
    
    Args:
        path: 要检查的路径
        
    Returns:
        bool: 路径是否有效
    """
    try:
        # 检查路径长度（Windows限制）
        if len(path) > 260:
            return False
        
        # 检查路径中的每个部分
        parts = path.split(os.sep)
        for part in parts:
            if part and not validate_filename(part):
                return False
        
        return True
    except Exception:
        return False


def normalize_path(path: str) -> str:
    """标准化路径
    
    Args:
        path: 原始路径
        
    Returns:
        str: 标准化后的路径
    """
    # 标准化路径分隔符
    normalized = os.path.normpath(path)
    
    # 移除多余的分隔符
    normalized = re.sub(r'[/\\]+', os.sep, normalized)
    
    return normalized
