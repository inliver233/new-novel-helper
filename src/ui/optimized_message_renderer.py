"""
优化的消息渲染器
基于Cherry Studio的高性能消息渲染实现
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QPainter
from typing import List, Dict, Optional
import weakref

from .chat_components import MessageBubble
from ..ai.models import Message, MessageRole


class OptimizedMessageRenderer(QScrollArea):
    """优化的消息渲染器 - 参考Cherry Studio实现"""
    
    message_clicked = pyqtSignal(str)  # message_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages: List[Message] = []
        self.message_widgets: Dict[str, MessageBubble] = {}
        self.visible_range = (0, 0)  # 可见消息范围
        self.viewport_height = 0
        self.total_height = 0
        
        # 性能优化设置
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        
        # 启用硬件加速
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        self.setup_ui()
        self.setup_performance_optimizations()
    
    def setup_ui(self):
        """设置UI"""
        # 创建内容容器
        self.content_widget = QFrame()
        self.content_widget.setObjectName("messageContainer")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 20)  # 底部留20px边距
        self.content_layout.setSpacing(8)
        # 移除addStretch()以确保能滚动到底部
        
        self.setWidget(self.content_widget)
        
        # 设置样式
        self.setStyleSheet("""
            OptimizedMessageRenderer {
                background-color: #1a1a1a;
                border: none;
            }
            #messageContainer {
                background-color: #1a1a1a;
            }
        """)
    
    def setup_performance_optimizations(self):
        """设置性能优化"""
        # 虚拟化滚动
        self.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
        # 批量更新定时器
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.batch_update_visible_messages)
        
        # 渲染缓存
        self.render_cache = weakref.WeakValueDictionary()
        
        # 滚动优化
        self.scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.scroll_animation.setDuration(300)
    
    def add_message(self, message: Message) -> MessageBubble:
        """添加消息 - 优化版本"""
        # 检查是否已存在
        if message.id in self.message_widgets:
            return self.message_widgets[message.id]
        
        # 创建消息气泡
        is_user = message.role == MessageRole.USER
        bubble = MessageBubble(message, is_user)
        
        # 连接信号
        bubble.copy_requested.connect(self.on_copy_requested)
        bubble.edit_requested.connect(self.on_edit_requested)
        bubble.regenerate_requested.connect(self.on_regenerate_requested)
        
        # 添加到布局末尾
        self.content_layout.addWidget(bubble)
        
        # 缓存
        self.messages.append(message)
        self.message_widgets[message.id] = bubble
        
        # 批量更新可见性
        self.schedule_visibility_update()
        
        return bubble
    
    def update_message_content(self, message_id: str, content: str):
        """更新消息内容"""
        if message_id in self.message_widgets:
            self.message_widgets[message_id].set_content(content)
    
    def append_message_content(self, message_id: str, content: str):
        """追加消息内容"""
        if message_id in self.message_widgets:
            self.message_widgets[message_id].append_content(content)
    
    def remove_message(self, message_id: str):
        """移除消息"""
        if message_id in self.message_widgets:
            widget = self.message_widgets[message_id]
            self.content_layout.removeWidget(widget)
            widget.deleteLater()
            del self.message_widgets[message_id]
            
            # 从消息列表中移除
            self.messages = [m for m in self.messages if m.id != message_id]
    
    def clear_messages(self):
        """清空所有消息"""
        # 批量删除以提高性能
        self.content_widget.setUpdatesEnabled(False)
        
        try:
            for widget in self.message_widgets.values():
                self.content_layout.removeWidget(widget)
                widget.deleteLater()
            
            self.message_widgets.clear()
            self.messages.clear()
            self.render_cache.clear()
        finally:
            self.content_widget.setUpdatesEnabled(True)
    
    def scroll_to_bottom(self, animated: bool = True):
        """滚动到底部 - 确保能滚动到真正的底部"""
        # 强制更新布局以确保正确的滚动范围
        self.content_widget.updateGeometry()
        self.updateGeometry()

        # 使用QTimer延迟滚动，确保布局更新完成
        QTimer.singleShot(10, lambda: self._do_scroll_to_bottom(animated))

    def _do_scroll_to_bottom(self, animated: bool = True):
        """实际执行滚动到底部"""
        scrollbar = self.verticalScrollBar()
        target_value = scrollbar.maximum()

        if animated and abs(scrollbar.value() - target_value) > 100:
            # 使用动画滚动
            self.scroll_animation.stop()
            self.scroll_animation.setStartValue(scrollbar.value())
            self.scroll_animation.setEndValue(target_value)
            self.scroll_animation.start()
        else:
            # 直接滚动
            scrollbar.setValue(target_value)
    
    def scroll_to_message(self, message_id: str, animated: bool = True):
        """滚动到指定消息"""
        if message_id in self.message_widgets:
            widget = self.message_widgets[message_id]
            self.ensureWidgetVisible(widget, 50, 50)
    
    def on_scroll(self, value: int):
        """滚动事件处理"""
        self.schedule_visibility_update()
    
    def schedule_visibility_update(self):
        """调度可见性更新"""
        # 减少更新频率以提高性能
        if not hasattr(self, '_last_visibility_update'):
            self._last_visibility_update = 0

        import time
        current_time = time.time()
        if (current_time - self._last_visibility_update) > 0.1:  # 最多每100ms更新一次
            self.batch_update_visible_messages()
            self._last_visibility_update = current_time
        else:
            self.update_timer.start(100)  # 延迟更新
    
    def batch_update_visible_messages(self):
        """批量更新可见消息"""
        # 计算可见区域
        viewport_rect = self.viewport().rect()
        scroll_value = self.verticalScrollBar().value()
        
        visible_top = scroll_value
        visible_bottom = scroll_value + viewport_rect.height()
        
        # 更新消息可见性（虚拟化）
        for message_id, widget in self.message_widgets.items():
            widget_rect = widget.geometry()
            widget_top = widget_rect.top()
            widget_bottom = widget_rect.bottom()
            
            # 检查是否在可见区域内（包含缓冲区）
            buffer = 200  # 200px缓冲区
            is_visible = (widget_bottom >= visible_top - buffer and 
                         widget_top <= visible_bottom + buffer)
            
            # 优化：只有状态改变时才更新
            if widget.isVisible() != is_visible:
                widget.setVisible(is_visible)
    
    def get_message_widget(self, message_id: str) -> Optional[MessageBubble]:
        """获取消息组件"""
        return self.message_widgets.get(message_id)
    
    def get_all_messages(self) -> List[Message]:
        """获取所有消息"""
        return self.messages.copy()
    
    def on_copy_requested(self, text: str):
        """处理复制请求"""
        # 这里可以添加复制到剪贴板的逻辑
        pass
    
    def on_edit_requested(self, message_id: str):
        """处理编辑请求"""
        # 发射信号给父组件处理
        pass
    
    def on_regenerate_requested(self, message_id: str):
        """处理重新生成请求"""
        # 发射信号给父组件处理
        pass
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.schedule_visibility_update()
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self.schedule_visibility_update()


class MessageAnimator:
    """消息动画器 - 参考Cherry Studio的动画实现"""
    
    def __init__(self):
        self.animations = {}
    
    def animate_message_in(self, widget: QWidget, duration: int = 300):
        """消息进入动画"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 从右侧滑入
        start_rect = widget.geometry()
        start_rect.moveLeft(start_rect.left() + 50)
        end_rect = widget.geometry()
        
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.start()
        
        self.animations[widget] = animation
    
    def animate_message_out(self, widget: QWidget, duration: int = 200):
        """消息退出动画"""
        animation = QPropertyAnimation(widget, b"opacity")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.finished.connect(widget.deleteLater)
        animation.start()
        
        self.animations[widget] = animation
