"""
状态指示器组件模块 - 提供各种状态的视觉指示
包括保存状态、同步状态等指示器
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from enum import Enum


class StatusType(Enum):
    """状态类型枚举"""
    SAVED = "saved"
    SAVING = "saving"
    MODIFIED = "modified"
    ERROR = "error"
    SYNCING = "syncing"
    SYNCED = "synced"


class StatusIndicator(QWidget):
    """单个状态指示器组件"""
    
    def __init__(self, status_type: StatusType, text: str = "", parent=None):
        super().__init__(parent)
        self.status_type = status_type
        self.text = text
        
        # 设置固定大小
        self.setFixedSize(120, 24)
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)
        
        # 状态图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # 状态文本
        self.text_label = QLabel(text)
        self.text_label.setFont(QFont("Segoe UI", 8))
        layout.addWidget(self.text_label)
        
        # 设置样式
        self.update_appearance()
        
        # 动画定时器（用于闪烁效果）
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.toggle_animation)
        self.animation_state = False
    
    def update_appearance(self):
        """更新外观"""
        colors = {
            StatusType.SAVED: ("#0e639c", "#ffffff", "✓"),      # 使用软件主色调蓝色
            StatusType.SAVING: ("#6d6d6d", "#ffffff", "⟳"),     # 使用软件灰色调
            StatusType.MODIFIED: ("#52525b", "#e0e0e0", "●"),    # 使用软件边框色
            StatusType.ERROR: ("#8b5a5a", "#ffffff", "✗"),      # 使用暗红色
            StatusType.SYNCING: ("#0e639c", "#ffffff", "↕"),     # 使用软件主色调
            StatusType.SYNCED: ("#0e639c", "#ffffff", "✓")      # 使用软件主色调
        }
        
        bg_color, text_color, icon = colors.get(self.status_type, ("#6c757d", "#ffffff", "?"))
        
        # 设置样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {bg_color};
            }}
        """)
        
        self.text_label.setStyleSheet(f"color: {text_color}; font-weight: 500;")
        
        # 设置图标
        self.icon_label.setText(icon)
        self.icon_label.setStyleSheet(f"""
            color: {text_color};
            font-weight: bold;
            font-size: 12px;
        """)
    
    def set_text(self, text: str):
        """设置状态文本"""
        self.text = text
        self.text_label.setText(text)
    
    def set_status(self, status_type: StatusType, text: str = ""):
        """设置状态类型和文本"""
        self.status_type = status_type
        if text:
            self.set_text(text)
        self.update_appearance()
        
        # 根据状态类型决定是否启动动画
        if status_type in [StatusType.SAVING, StatusType.SYNCING]:
            self.start_animation()
        else:
            self.stop_animation()
    
    def start_animation(self):
        """开始动画效果"""
        self.animation_timer.start(500)  # 每500ms切换一次
    
    def stop_animation(self):
        """停止动画效果"""
        self.animation_timer.stop()
        self.animation_state = False
        self.update_appearance()
    
    def toggle_animation(self):
        """切换动画状态"""
        self.animation_state = not self.animation_state
        
        if self.animation_state:
            # 淡化效果
            self.setStyleSheet(self.styleSheet().replace("border-radius: 12px;", 
                                                        "border-radius: 12px; opacity: 0.6;"))
        else:
            self.update_appearance()


class StatusIndicatorBar(QWidget):
    """状态指示器栏，包含多个状态指示器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        layout.addStretch()  # 右对齐
        
        # 状态指示器字典
        self.indicators = {}
        
        # 自动隐藏定时器
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self.auto_hide_indicators)
        self.auto_hide_timer.setSingleShot(True)
    
    def add_indicator(self, key: str, status_type: StatusType, text: str = "") -> StatusIndicator:
        """添加状态指示器"""
        if key in self.indicators:
            # 如果已存在，更新状态
            self.indicators[key].set_status(status_type, text)
            return self.indicators[key]
        
        # 创建新的指示器
        indicator = StatusIndicator(status_type, text)
        self.indicators[key] = indicator
        
        # 添加到布局（在stretch之前）
        layout = self.layout()
        layout.insertWidget(layout.count() - 1, indicator)
        
        return indicator
    
    def update_indicator(self, key: str, status_type: StatusType, text: str = ""):
        """更新状态指示器"""
        if key in self.indicators:
            self.indicators[key].set_status(status_type, text)
            self.show_indicator(key)
        else:
            # 如果指示器不存在，创建一个新的
            self.add_indicator(key, status_type, text)
    
    def remove_indicator(self, key: str):
        """移除状态指示器"""
        if key in self.indicators:
            indicator = self.indicators[key]
            self.layout().removeWidget(indicator)
            indicator.deleteLater()
            del self.indicators[key]
    
    def show_indicator(self, key: str, auto_hide_delay: int = 0):
        """显示指定的状态指示器"""
        if key in self.indicators:
            self.indicators[key].show()
            
            # 如果设置了自动隐藏延迟
            if auto_hide_delay > 0:
                self.auto_hide_timer.start(auto_hide_delay)
    
    def hide_indicator(self, key: str):
        """隐藏指定的状态指示器"""
        if key in self.indicators:
            self.indicators[key].hide()
    
    def auto_hide_indicators(self):
        """自动隐藏所有指示器（除了正在进行的操作）"""
        for key, indicator in self.indicators.items():
            if indicator.status_type not in [StatusType.SAVING, StatusType.SYNCING, StatusType.MODIFIED]:
                indicator.hide()
    
    def clear_all(self):
        """清除所有指示器"""
        for key in list(self.indicators.keys()):
            self.remove_indicator(key)



