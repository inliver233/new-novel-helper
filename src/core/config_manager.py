"""
配置管理模块 - 处理应用程序设置的保存和加载
提供统一的配置管理接口，支持各种应用设置
"""

import os
import json
from typing import Any, Dict, Optional
from PyQt6.QtCore import QSettings
from ..utils.logger import LoggerConfig, log_exception


class ConfigManager:
    """配置管理器，负责应用程序设置的保存和加载"""
    
    # 默认配置值
    DEFAULT_CONFIG = {
        "auto_save": {
            "enabled": True,
            "interval": 3000,  # 毫秒
            "show_indicator": True
        },
        "ui": {
            "theme": "dark",
            "font_size": 12,
            "show_status_indicators": True
        },
        "editor": {
            "word_wrap": True,
            "show_line_numbers": False,
            "auto_indent": True
        },
        "backup": {
            "enabled": True,
            "max_backups": 10,
            "backup_interval": 300000  # 5分钟
        }
    }
    
    def __init__(self, data_path: str):
        """
        初始化配置管理器
        
        Args:
            data_path: 数据目录路径
        """
        self.data_path = data_path
        self.config_file = os.path.join(data_path, "config.json")
        self.logger = LoggerConfig.get_logger("config_manager")
        
        # 使用QSettings作为备用配置存储
        self.qsettings = QSettings("LoreMaster", "LoreMaster")
        
        # 当前配置
        self._config = {}
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            # 首先尝试从JSON文件加载
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._config = self._merge_config(self.DEFAULT_CONFIG.copy(), file_config)
                    self.logger.info("从JSON文件加载配置成功")
            else:
                # 如果JSON文件不存在，尝试从QSettings迁移
                self._migrate_from_qsettings()
                
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"加载配置文件失败，使用默认配置: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
            
        # 确保配置完整性
        self._ensure_config_integrity()
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 保存到JSON文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            # 同时保存到QSettings作为备份
            self._save_to_qsettings()
            
            self.logger.info("配置保存成功")
            return True
            
        except (OSError, json.JSONEncodeError) as e:
            self.logger.error(f"保存配置失败: {e}")
            log_exception(self.logger, "保存配置", e)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键，如 "auto_save.enabled"
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
                    
            return value
            
        except (KeyError, TypeError, AttributeError) as e:
            self.logger.warning(f"获取配置值失败 {key}: {e}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            keys = key.split('.')
            config = self._config
            
            # 导航到目标位置
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                elif not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            
            # 自动保存配置
            return self.save_config()
            
        except (KeyError, TypeError, AttributeError, OSError, json.JSONEncodeError) as e:
            self.logger.error(f"设置配置值失败 {key}: {e}")
            log_exception(self.logger, "设置配置值", e)
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置节
        
        Args:
            section: 节名称
            
        Returns:
            配置节字典
        """
        return self.get(section, {})
    
    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        更新配置节
        
        Args:
            section: 节名称
            values: 要更新的值字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            current_section = self.get_section(section)
            current_section.update(values)
            return self.set(section, current_section)
            
        except Exception as e:
            self.logger.error(f"更新配置节失败 {section}: {e}")
            return False
    
    def reset_to_default(self, section: Optional[str] = None) -> bool:
        """
        重置配置到默认值
        
        Args:
            section: 要重置的节名称，None表示重置全部
            
        Returns:
            bool: 重置是否成功
        """
        try:
            if section:
                if section in self.DEFAULT_CONFIG:
                    self._config[section] = self.DEFAULT_CONFIG[section].copy()
                else:
                    self.logger.warning(f"未知的配置节: {section}")
                    return False
            else:
                self._config = self.DEFAULT_CONFIG.copy()
            
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
    
    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """合并配置字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _ensure_config_integrity(self) -> None:
        """确保配置完整性"""
        self._config = self._merge_config(self.DEFAULT_CONFIG.copy(), self._config)
    
    def _migrate_from_qsettings(self) -> None:
        """从QSettings迁移配置"""
        try:
            # 尝试从QSettings读取一些基本配置
            auto_save_enabled = self.qsettings.value("auto_save/enabled", True, type=bool)
            auto_save_interval = self.qsettings.value("auto_save/interval", 3000, type=int)
            
            self._config = self.DEFAULT_CONFIG.copy()
            self._config["auto_save"]["enabled"] = auto_save_enabled
            self._config["auto_save"]["interval"] = auto_save_interval
            
            # 保存迁移后的配置
            self.save_config()
            self.logger.info("从QSettings迁移配置成功")
            
        except Exception as e:
            self.logger.warning(f"从QSettings迁移配置失败: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def _save_to_qsettings(self) -> None:
        """保存配置到QSettings作为备份"""
        try:
            # 保存关键配置到QSettings
            self.qsettings.setValue("auto_save/enabled", self._config["auto_save"]["enabled"])
            self.qsettings.setValue("auto_save/interval", self._config["auto_save"]["interval"])
            self.qsettings.setValue("ui/theme", self._config["ui"]["theme"])
            self.qsettings.sync()
            
        except Exception as e:
            self.logger.warning(f"保存到QSettings失败: {e}")

    # 便捷方法
    def is_auto_save_enabled(self) -> bool:
        """检查自动保存是否启用"""
        return self.get("auto_save.enabled", True)

    def get_auto_save_interval(self) -> int:
        """获取自动保存间隔（毫秒）"""
        return self.get("auto_save.interval", 3000)

    def set_auto_save_enabled(self, enabled: bool) -> bool:
        """设置自动保存启用状态"""
        return self.set("auto_save.enabled", enabled)

    def set_auto_save_interval(self, interval: int) -> bool:
        """设置自动保存间隔"""
        return self.set("auto_save.interval", max(1000, interval))  # 最小1秒

    def is_status_indicators_enabled(self) -> bool:
        """检查状态指示器是否启用"""
        return self.get("ui.show_status_indicators", True)

    def set_status_indicators_enabled(self, enabled: bool) -> bool:
        """设置状态指示器启用状态"""
        return self.set("ui.show_status_indicators", enabled)
