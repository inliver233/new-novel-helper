"""
日志系统配置模块
提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """日志配置类"""
    
    @staticmethod
    def setup_logger(name: str = "loremaster", 
                    log_level: int = logging.INFO,
                    log_dir: Optional[str] = None) -> logging.Logger:
        """
        设置并返回配置好的日志记录器
        
        Args:
            name: 日志记录器名称
            log_level: 日志级别
            log_dir: 日志文件目录，如果为None则不写入文件
            
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(name)
        
        # 避免重复配置
        if logger.handlers:
            return logger
            
        logger.setLevel(log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（如果指定了日志目录）
        if log_dir:
            try:
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"loremaster_{datetime.now().strftime('%Y%m%d')}.log")
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
            except (OSError, PermissionError) as e:
                logger.warning(f"无法创建日志文件: {e}")
        
        return logger
    
    @staticmethod
    def get_logger(name: str = "loremaster") -> logging.Logger:
        """
        获取已配置的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器
        """
        return logging.getLogger(name)


# 默认日志记录器
default_logger = LoggerConfig.setup_logger()


def log_exception(logger: logging.Logger, operation: str, exception: Exception):
    """
    记录异常信息的辅助函数
    
    Args:
        logger: 日志记录器
        operation: 操作描述
        exception: 异常对象
    """
    logger.error(f"{operation}失败: {type(exception).__name__}: {exception}")


def log_file_operation(logger: logging.Logger, operation: str, file_path: str, success: bool = True):
    """
    记录文件操作的辅助函数
    
    Args:
        logger: 日志记录器
        operation: 操作类型（如"读取"、"写入"、"删除"）
        file_path: 文件路径
        success: 操作是否成功
    """
    level = logging.INFO if success else logging.WARNING
    status = "成功" if success else "失败"
    logger.log(level, f"{operation}文件{status}: {file_path}")
