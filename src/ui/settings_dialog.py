"""
设置对话框模块 - 提供应用程序设置界面
采用模块化设计，便于扩展新的设置选项
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QCheckBox, QSpinBox, QLabel, QPushButton,
    QFormLayout, QDialogButtonBox, QMessageBox, QSlider,
    QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .ui_styles import UIStyles
from ..core.config_manager import ConfigManager
from ..utils.logger import LoggerConfig


class SettingsDialog(QDialog):
    """设置对话框主窗口"""
    
    # 信号
    settings_changed = pyqtSignal()  # 设置发生变化时发出
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = LoggerConfig.get_logger("settings_dialog")
        
        # 设置窗口属性
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        # 应用样式
        self.setStyleSheet(UIStyles.get_main_stylesheet())
        
        # 创建界面
        self.setup_ui()
        
        # 加载当前设置
        self.load_settings()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 创建标题
        title_label = QLabel("应用程序设置")
        title_label.setStyleSheet(UIStyles.get_category_title_style())
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(UIStyles.get_tab_widget_style())
        
        # 自动保存选项卡
        self.auto_save_tab = AutoSaveSettingsTab(self.config_manager)
        self.tab_widget.addTab(self.auto_save_tab, "自动保存")
        
        # UI选项卡
        self.ui_tab = UISettingsTab(self.config_manager)
        self.tab_widget.addTab(self.ui_tab, "界面设置")
        
        # 编辑器选项卡
        self.editor_tab = EditorSettingsTab(self.config_manager)
        self.tab_widget.addTab(self.editor_tab, "编辑器")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 重置按钮
        reset_btn = QPushButton("重置默认")
        reset_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        reset_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        # 标准按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(UIStyles.get_dialog_button_style())
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """加载当前设置到界面"""
        try:
            self.auto_save_tab.load_settings()
            self.ui_tab.load_settings()
            self.editor_tab.load_settings()
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
            QMessageBox.warning(self, "错误", f"加载设置失败: {e}")
    
    def accept_settings(self):
        """应用设置并关闭对话框"""
        try:
            # 保存各个选项卡的设置
            self.auto_save_tab.save_settings()
            self.ui_tab.save_settings()
            self.editor_tab.save_settings()
            
            # 发出设置变化信号
            self.settings_changed.emit()
            
            # 关闭对话框
            self.accept()
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")
    
    def reset_to_default(self):
        """重置到默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置到默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.reset_to_default()
                self.load_settings()
                QMessageBox.information(self, "成功", "设置已重置到默认值")
                
            except Exception as e:
                self.logger.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "错误", f"重置设置失败: {e}")


class AutoSaveSettingsTab(QWidget):
    """自动保存设置选项卡"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 自动保存组
        auto_save_group = QGroupBox("自动保存设置")
        auto_save_group.setStyleSheet(UIStyles.get_group_box_style())
        auto_save_layout = QFormLayout(auto_save_group)
        
        # 启用自动保存
        self.auto_save_enabled = QCheckBox("启用自动保存")
        self.auto_save_enabled.setToolTip("编辑时自动保存内容，避免意外丢失")
        auto_save_layout.addRow(self.auto_save_enabled)
        
        # 自动保存间隔
        interval_layout = QHBoxLayout()
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setSuffix(" 秒")
        self.auto_save_interval.setToolTip("自动保存的时间间隔")
        
        interval_layout.addWidget(self.auto_save_interval)
        interval_layout.addStretch()
        
        auto_save_layout.addRow("保存间隔:", interval_layout)
        
        # 显示保存指示器
        self.show_save_indicator = QCheckBox("显示保存状态指示器")
        self.show_save_indicator.setToolTip("在编辑器中显示保存状态的视觉指示")
        auto_save_layout.addRow(self.show_save_indicator)
        
        layout.addWidget(auto_save_group)
        
        # 说明文本
        info_label = QLabel(
            "自动保存功能可以在您编辑内容时自动保存更改，"
            "避免因意外关闭或系统故障导致的内容丢失。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 11px; padding: 8px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
    
    def load_settings(self):
        """加载设置"""
        self.auto_save_enabled.setChecked(self.config_manager.is_auto_save_enabled())
        self.auto_save_interval.setValue(self.config_manager.get_auto_save_interval() // 1000)
        self.show_save_indicator.setChecked(self.config_manager.get("auto_save.show_indicator", True))
    
    def save_settings(self):
        """保存设置"""
        self.config_manager.set_auto_save_enabled(self.auto_save_enabled.isChecked())
        self.config_manager.set_auto_save_interval(self.auto_save_interval.value() * 1000)
        self.config_manager.set("auto_save.show_indicator", self.show_save_indicator.isChecked())


class UISettingsTab(QWidget):
    """界面设置选项卡"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_group.setStyleSheet(UIStyles.get_group_box_style())
        ui_layout = QFormLayout(ui_group)
        
        # 显示状态指示器
        self.show_status_indicators = QCheckBox("显示状态指示器")
        self.show_status_indicators.setToolTip("在界面中显示各种状态指示器")
        ui_layout.addRow(self.show_status_indicators)
        
        # 字体大小
        font_layout = QHBoxLayout()
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setSuffix(" pt")
        font_layout.addWidget(self.font_size)
        font_layout.addStretch()
        
        ui_layout.addRow("字体大小:", font_layout)
        
        layout.addWidget(ui_group)
        layout.addStretch()
    
    def load_settings(self):
        """加载设置"""
        self.show_status_indicators.setChecked(self.config_manager.is_status_indicators_enabled())
        self.font_size.setValue(self.config_manager.get("ui.font_size", 12))
    
    def save_settings(self):
        """保存设置"""
        self.config_manager.set_status_indicators_enabled(self.show_status_indicators.isChecked())
        self.config_manager.set("ui.font_size", self.font_size.value())


class EditorSettingsTab(QWidget):
    """编辑器设置选项卡"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 编辑器设置组
        editor_group = QGroupBox("编辑器设置")
        editor_group.setStyleSheet(UIStyles.get_group_box_style())
        editor_layout = QFormLayout(editor_group)
        
        # 自动换行
        self.word_wrap = QCheckBox("自动换行")
        self.word_wrap.setToolTip("在编辑器中启用自动换行")
        editor_layout.addRow(self.word_wrap)
        
        # 显示行号
        self.show_line_numbers = QCheckBox("显示行号")
        self.show_line_numbers.setToolTip("在编辑器中显示行号")
        editor_layout.addRow(self.show_line_numbers)
        
        # 自动缩进
        self.auto_indent = QCheckBox("自动缩进")
        self.auto_indent.setToolTip("编辑时自动缩进")
        editor_layout.addRow(self.auto_indent)
        
        layout.addWidget(editor_group)
        layout.addStretch()
    
    def load_settings(self):
        """加载设置"""
        self.word_wrap.setChecked(self.config_manager.get("editor.word_wrap", True))
        self.show_line_numbers.setChecked(self.config_manager.get("editor.show_line_numbers", False))
        self.auto_indent.setChecked(self.config_manager.get("editor.auto_indent", True))
    
    def save_settings(self):
        """保存设置"""
        self.config_manager.set("editor.word_wrap", self.word_wrap.isChecked())
        self.config_manager.set("editor.show_line_numbers", self.show_line_numbers.isChecked())
        self.config_manager.set("editor.auto_indent", self.auto_indent.isChecked())
