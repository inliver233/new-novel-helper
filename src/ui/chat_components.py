"""
现代化聊天界面组件
基于Cherry Studio的设计理念，实现专业的对话界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy, QMenu,
    QApplication, QToolButton, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QTextCursor, QAction, QPainter, QPen, QColor, QTextOption
from typing import List, Optional, Dict, Any
import re
import time
from datetime import datetime

from ..ai.models import Message, MessageBlock, Citation, MessageRole, MessageStatus, BlockType


class MessageBubble(QFrame):
    """消息气泡组件"""
    
    # 信号
    copy_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)  # message_id
    regenerate_requested = pyqtSignal(str)  # message_id
    citation_clicked = pyqtSignal(str)  # citation_id
    
    def __init__(self, message: Message, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.citations: List[Citation] = []
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        """设置UI - Cherry Studio风格"""
        self.setFrameStyle(QFrame.Shape.NoFrame)

        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 8, 20, 8)
        main_layout.setSpacing(12)

        # 头像区域
        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 头像 - 使用圆形背景
        self.avatar_frame = QFrame()
        self.avatar_frame.setFixedSize(40, 40)
        self.avatar_frame.setObjectName("avatarFrame")

        avatar_inner_layout = QVBoxLayout(self.avatar_frame)
        avatar_inner_layout.setContentsMargins(0, 0, 0, 0)
        avatar_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.is_user:
            self.avatar_label = QLabel("👤")
            self.avatar_frame.setStyleSheet("""
                QFrame#avatarFrame {
                    background-color: #10b981;
                    border-radius: 20px;
                }
            """)
        else:
            self.avatar_label = QLabel("🤖")
            self.avatar_frame.setStyleSheet("""
                QFrame#avatarFrame {
                    background-color: #3b82f6;
                    border-radius: 20px;
                }
            """)

        self.avatar_label.setFont(QFont("Segoe UI Emoji", 16))
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("color: white; background: transparent;")
        avatar_inner_layout.addWidget(self.avatar_label)

        avatar_layout.addWidget(self.avatar_frame)
        main_layout.addLayout(avatar_layout)

        # 消息内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # 消息头部（名称、时间、状态）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # 名称
        if self.is_user:
            self.name_label = QLabel("用户")
        else:
            model_name = getattr(self.message, 'model_id', 'gemini-2.5-pro-exp-03-25 | freegemini')
            self.name_label = QLabel(model_name)
        self.name_label.setObjectName("nameLabel")
        header_layout.addWidget(self.name_label)

        # 时间
        timestamp = getattr(self.message, 'created_at', datetime.now())
        if hasattr(timestamp, 'strftime'):
            time_str = timestamp.strftime("%m/%d %H:%M")
        else:
            time_str = str(timestamp)
        self.time_label = QLabel(time_str)
        self.time_label.setObjectName("timeLabel")
        header_layout.addWidget(self.time_label)

        header_layout.addStretch()

        # 状态指示器
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)

        content_layout.addLayout(header_layout)
        
        # 消息内容区域
        self.content_area = QTextEdit()
        self.content_area.setObjectName("contentArea")
        self.content_area.setReadOnly(True)
        self.content_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_area.setMaximumHeight(400)
        self.content_area.setMinimumHeight(40)

        # 设置初始内容
        if hasattr(self.message, 'content') and self.message.content:
            self.content_area.setPlainText(self.message.content)
        else:
            self.content_area.setPlainText("")

        content_layout.addWidget(self.content_area)

        # Token使用信息（仅AI消息）
        if not self.is_user:
            self.usage_label = QLabel()
            self.usage_label.setObjectName("usageLabel")
            self.usage_label.hide()  # 默认隐藏，有数据时显示
            content_layout.addWidget(self.usage_label)

        # 引用区域
        self.citations_area = QFrame()
        self.citations_area.setObjectName("citationsArea")
        self.citations_area.hide()  # 默认隐藏
        self.citations_layout = QVBoxLayout(self.citations_area)
        self.citations_layout.setContentsMargins(8, 8, 8, 8)
        self.citations_layout.setSpacing(4)
        content_layout.addWidget(self.citations_area)
        
        # 操作按钮区域
        self.actions_area = QFrame()
        self.actions_area.setObjectName("actionsArea")
        actions_layout = QHBoxLayout(self.actions_area)
        actions_layout.setContentsMargins(0, 4, 0, 0)
        actions_layout.setSpacing(8)
        
        # 复制按钮
        self.copy_btn = QToolButton()
        self.copy_btn.setText("📋")
        self.copy_btn.setToolTip("复制消息")
        self.copy_btn.clicked.connect(self.copy_message)
        actions_layout.addWidget(self.copy_btn)
        
        # 编辑按钮（仅用户消息）
        if self.is_user:
            self.edit_btn = QToolButton()
            self.edit_btn.setText("✏️")
            self.edit_btn.setToolTip("编辑消息")
            self.edit_btn.clicked.connect(self.edit_message)
            actions_layout.addWidget(self.edit_btn)
        
        # 重新生成按钮（仅AI消息）
        if not self.is_user:
            self.regenerate_btn = QToolButton()
            self.regenerate_btn.setText("🔄")
            self.regenerate_btn.setToolTip("重新生成")
            self.regenerate_btn.clicked.connect(self.regenerate_message)
            actions_layout.addWidget(self.regenerate_btn)
        
        actions_layout.addStretch()
        
        content_layout.addWidget(self.actions_area)
        
        # 添加内容布局到主布局
        main_layout.addLayout(content_layout)

        # 初始隐藏操作区域
        self.actions_area.hide()
    
    def setup_style(self):
        """设置样式 - Cherry Studio风格"""
        # 启用硬件加速和优化渲染
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)

        # 优化文本编辑器性能
        self.content_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_area.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.content_area.document().setDocumentMargin(8)

        # 通用样式
        self.setStyleSheet("""
            MessageBubble {
                background: transparent;
                margin: 4px 0;
            }
            #nameLabel {
                color: #e0e0e0;
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 2px;
            }
            #timeLabel {
                color: #9ca3af;
                font-size: 10px;
            }
            #statusLabel {
                color: #9ca3af;
                font-size: 10px;
            }
            #contentArea {
                background: transparent;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                selection-background-color: #3b82f6;
                padding: 8px 0;
                line-height: 1.5;
            }
            #usageLabel {
                color: #6b7280;
                font-size: 10px;
                margin-top: 4px;
            }
            #citationsArea {
                background-color: #1a1a1a;
                border: 1px solid #374151;
                border-radius: 6px;
                margin-top: 8px;
            }
            #actionsArea {
                background: transparent;
            }
            QToolButton {
                background: #374151;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 4px;
                color: #9ca3af;
                font-size: 12pt;
            }
            QToolButton:hover {
                background: #4b5563;
                color: #e0e0e0;
            }
        """)
    
    def update_status_display(self):
        """更新状态显示 - Cherry Studio风格"""
        if self.message.status == MessageStatus.STREAMING:
            # 显示简单的加载动画
            self.start_typing_animation()
        elif self.message.status == MessageStatus.SUCCESS:
            # 显示token使用信息（如果有）
            if hasattr(self.message, 'usage') and self.message.usage and not self.is_user:
                usage_text = f"Tokens: {getattr(self.message.usage, 'total_tokens', 0)}"
                if hasattr(self, 'usage_label'):
                    self.usage_label.setText(usage_text)
                    self.usage_label.show()
            self.status_label.hide()
        elif self.message.status == MessageStatus.ERROR:
            self.status_label.setText("❌ 错误")
            self.status_label.show()
        else:
            self.status_label.hide()
    
    def start_typing_animation(self):
        """开始打字动画 - Cherry Studio风格"""
        if not hasattr(self, 'typing_timer'):
            self.typing_timer = QTimer()
            self.typing_timer.timeout.connect(self.update_typing_animation)
            self.typing_dots = 0

        self.status_label.show()
        self.typing_timer.start(800)  # 稍慢一点的动画

    def stop_typing_animation(self):
        """停止打字动画"""
        if hasattr(self, 'typing_timer'):
            self.typing_timer.stop()
        self.status_label.hide()

    def update_typing_animation(self):
        """更新打字动画 - 简单的加载指示器"""
        # 使用简单的旋转字符
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        char = chars[self.typing_dots % len(chars)]
        self.status_label.setText(char)
        self.typing_dots += 1
    
    def set_content(self, content: str):
        """设置消息内容 - 优化性能版本"""
        # 使用QTimer延迟更新，避免频繁重绘
        if hasattr(self, '_content_update_timer'):
            self._content_update_timer.stop()

        self._pending_content = content
        self._content_update_timer = QTimer()
        self._content_update_timer.setSingleShot(True)
        self._content_update_timer.timeout.connect(self._update_content)
        self._content_update_timer.start(10)  # 10ms延迟

    def _update_content(self):
        """实际更新内容"""
        if hasattr(self, '_pending_content'):
            # 暂时禁用重绘以提高性能
            self.content_area.setUpdatesEnabled(False)
            self.content_area.blockSignals(True)

            # 确保内容正确设置
            self.content_area.setPlainText(self._pending_content)

            # 确保文字颜色正确
            if self.is_user:
                self.content_area.setStyleSheet("""
                    QTextEdit {
                        background: transparent;
                        border: none;
                        color: #ffffff;
                        font-size: 10pt;
                        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                        selection-background-color: rgba(255, 255, 255, 0.3);
                        padding: 4px;
                    }
                """)
            else:
                self.content_area.setStyleSheet("""
                    QTextEdit {
                        background: transparent;
                        border: none;
                        color: #e0e0e0;
                        font-size: 10pt;
                        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                        selection-background-color: #3b82f6;
                        padding: 4px;
                        line-height: 1.4;
                    }
                """)

            # 优化高度计算
            document = self.content_area.document()
            height = min(max(int(document.size().height() + 20), 40), 600)
            self.content_area.setFixedHeight(height)

            # 重新启用信号和重绘
            self.content_area.blockSignals(False)
            self.content_area.setUpdatesEnabled(True)

            # 强制刷新显示
            self.content_area.update()
            delattr(self, '_pending_content')

    def append_content(self, content: str):
        """追加内容（用于流式更新）- 优化性能版本"""
        # 批量更新以减少重绘次数
        if not hasattr(self, '_append_buffer'):
            self._append_buffer = ""
            self._append_timer = QTimer()
            self._append_timer.setSingleShot(True)
            self._append_timer.timeout.connect(self._flush_append_buffer)
            self._last_flush_time = 0

        self._append_buffer += content

        # 动态调整更新频率：内容越多，更新越频繁
        current_time = time.time()
        if len(self._append_buffer) > 100 or (current_time - self._last_flush_time) > 0.2:
            # 如果缓冲区内容较多或距离上次更新超过200ms，立即更新
            self._flush_append_buffer()
        else:
            # 否则延迟更新
            self._append_timer.start(100)  # 100ms批量更新

    def _flush_append_buffer(self):
        """刷新追加缓冲区"""
        if hasattr(self, '_append_buffer') and self._append_buffer:
            # 停止定时器
            if hasattr(self, '_append_timer'):
                self._append_timer.stop()

            # 暂时禁用重绘和信号
            self.content_area.setUpdatesEnabled(False)
            self.content_area.blockSignals(True)

            # 使用更高效的文本插入方式
            cursor = self.content_area.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(self._append_buffer)

            # 批量处理滚动和高度调整
            document = self.content_area.document()
            new_height = min(max(int(document.size().height() + 20), 40), 600)

            # 只有高度变化时才调整
            if self.content_area.height() != new_height:
                self.content_area.setFixedHeight(new_height)

            # 重新启用信号和重绘
            self.content_area.blockSignals(False)
            self.content_area.setUpdatesEnabled(True)

            # 延迟滚动以避免频繁操作
            QTimer.singleShot(10, self._delayed_scroll)

            self._append_buffer = ""
            self._last_flush_time = time.time()

    def _delayed_scroll(self):
        """延迟滚动到底部"""
        scrollbar = self.content_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_citations(self, citations: List[Citation]):
        """设置引用"""
        self.citations = citations
        
        # 清空现有引用
        for i in reversed(range(self.citations_layout.count())):
            child = self.citations_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        if not citations:
            self.citations_area.hide()
            return
        
        # 添加引用标题
        title_label = QLabel("📚 参考资料:")
        title_label.setStyleSheet("color: #9ca3af; font-weight: 600; font-size: 9pt; margin-bottom: 4px;")
        self.citations_layout.addWidget(title_label)
        
        # 添加引用项
        for i, citation in enumerate(citations[:3]):  # 最多显示3个引用
            citation_widget = CitationWidget(citation, i + 1)
            citation_widget.clicked.connect(lambda cid=citation.id: self.citation_clicked.emit(cid))
            self.citations_layout.addWidget(citation_widget)
        
        self.citations_area.show()
    
    def copy_message(self):
        """复制消息"""
        content = self.content_area.toPlainText()
        self.copy_requested.emit(content)
    
    def edit_message(self):
        """编辑消息"""
        self.edit_requested.emit(self.message.id)
    
    def regenerate_message(self):
        """重新生成消息"""
        self.regenerate_requested.emit(self.message.id)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.actions_area.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.actions_area.hide()
        super().leaveEvent(event)


class CitationWidget(QFrame):
    """引用组件"""

    clicked = pyqtSignal(str)  # citation_id

    def __init__(self, citation: Citation, index: int, parent=None):
        super().__init__(parent)
        self.citation = citation
        self.index = index
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # 索引标签
        self.index_label = QLabel(f"[{self.index}]")
        self.index_label.setFixedWidth(30)
        layout.addWidget(self.index_label)

        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        # 标题
        self.title_label = QLabel(self.citation.title or "无标题")
        self.title_label.setWordWrap(True)
        content_layout.addWidget(self.title_label)

        # 内容预览
        preview = self.citation.content[:100] + "..." if len(self.citation.content) > 100 else self.citation.content
        self.content_label = QLabel(preview)
        self.content_label.setWordWrap(True)
        content_layout.addWidget(self.content_label)

        # 来源信息
        source_info = f"来源: {self.citation.source}"
        if self.citation.score > 0:
            source_info += f" | 相关度: {self.citation.score:.2f}"
        self.source_label = QLabel(source_info)
        content_layout.addWidget(self.source_label)

        layout.addLayout(content_layout)
        layout.addStretch()

    def setup_style(self):
        """设置样式 - Cherry Studio风格"""
        self.setStyleSheet("""
            CitationWidget {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 6px;
                margin: 2px 0;
                padding: 2px;
            }
            CitationWidget:hover {
                background-color: #27272a;
                border-color: #3f3f46;
            }
            QLabel {
                color: #e4e4e7;
                font-size: 9pt;
                background: transparent;
                border: none;
            }
        """)

        # 设置不同样式
        self.index_label.setStyleSheet("color: #3b82f6; font-weight: 600; font-size: 8pt;")
        self.title_label.setStyleSheet("color: #f4f4f5; font-weight: 600; font-size: 9pt;")
        self.content_label.setStyleSheet("color: #a1a1aa; font-size: 8pt;")
        self.source_label.setStyleSheet("color: #71717a; font-size: 7pt;")

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.citation.id)
        super().mousePressEvent(event)


class TypingIndicator(QFrame):
    """打字指示器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        self.setup_animation()

    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        # AI头像
        avatar_label = QLabel("🤖")
        avatar_label.setFont(QFont("Segoe UI Emoji", 14))
        layout.addWidget(avatar_label)

        # 打字动画区域
        self.dots_container = QFrame()
        dots_layout = QHBoxLayout(self.dots_container)
        dots_layout.setContentsMargins(8, 4, 8, 4)
        dots_layout.setSpacing(4)

        # 创建三个点
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setObjectName(f"dot_{i}")
            dots_layout.addWidget(dot)
            self.dots.append(dot)

        layout.addWidget(self.dots_container)
        layout.addStretch()

    def setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            TypingIndicator {
                background: transparent;
            }
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #3f3f46;
                border-radius: 12px;
                border-left: 3px solid #fbbf24;
                max-width: 200px;
            }
            QLabel {
                color: #fbbf24;
                font-size: 12pt;
            }
        """)

    def setup_animation(self):
        """设置动画"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_dots)
        self.current_dot = 0

    def start_animation(self):
        """开始动画"""
        self.animation_timer.start(500)
        self.show()

    def stop_animation(self):
        """停止动画"""
        self.animation_timer.stop()
        self.hide()

    def animate_dots(self):
        """动画效果"""
        # 重置所有点的透明度
        for dot in self.dots:
            dot.setStyleSheet("color: rgba(251, 191, 36, 0.3);")

        # 高亮当前点
        self.dots[self.current_dot].setStyleSheet("color: #fbbf24;")

        # 移动到下一个点
        self.current_dot = (self.current_dot + 1) % 3


class ChatInputArea(QFrame):
    """聊天输入区域"""

    # 信号
    message_sent = pyqtSignal(str)  # 发送消息
    stop_generation = pyqtSignal()  # 停止生成
    knowledge_base_selected = pyqtSignal(list)  # 知识库选择信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_generating = False
        self.selected_knowledge_bases = []  # 选中的知识库
        self.rag_mode_enabled = True  # RAG模式是否启用
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 输入容器
        input_container = QFrame()
        input_container.setObjectName("inputContainer")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(8)

        # 输入框
        self.input_edit = QTextEdit()
        self.input_edit.setObjectName("inputEdit")
        self.input_edit.setPlaceholderText("输入您的问题... (Ctrl+Enter 发送)")
        self.input_edit.setMaximumHeight(120)
        self.input_edit.setMinimumHeight(40)
        input_layout.addWidget(self.input_edit)

        # 工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        # 知识库按钮
        self.knowledge_btn = QPushButton("📚 知识库")
        self.knowledge_btn.setObjectName("knowledgeBtn")
        self.knowledge_btn.setCheckable(True)
        self.knowledge_btn.setToolTip("选择知识库进行RAG检索")
        self.knowledge_btn.clicked.connect(self.toggle_knowledge_selection)
        toolbar_layout.addWidget(self.knowledge_btn)

        # RAG模式切换按钮
        self.rag_mode_btn = QPushButton("🤖 智能模式")
        self.rag_mode_btn.setObjectName("ragModeBtn")
        self.rag_mode_btn.setCheckable(True)
        self.rag_mode_btn.setChecked(True)
        self.rag_mode_btn.setToolTip("启用RAG智能回答模式")
        self.rag_mode_btn.clicked.connect(self.toggle_rag_mode)
        toolbar_layout.addWidget(self.rag_mode_btn)

        # 字符计数
        self.char_count_label = QLabel("0 字符")
        self.char_count_label.setObjectName("charCount")
        toolbar_layout.addWidget(self.char_count_label)

        toolbar_layout.addStretch()

        # 清空按钮
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self.clear_input)
        toolbar_layout.addWidget(self.clear_btn)

        # 发送/停止按钮
        self.send_btn = QPushButton("🚀 发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.clicked.connect(self.handle_send_click)
        toolbar_layout.addWidget(self.send_btn)

        input_layout.addLayout(toolbar_layout)
        layout.addWidget(input_container)

        # 连接信号
        self.input_edit.textChanged.connect(self.on_text_changed)
        self.input_edit.keyPressEvent = self.handle_key_press

    def setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            ChatInputArea {
                background-color: #2a2a2a;
                border-top: 1px solid #3f3f46;
            }
            #inputContainer {
                background-color: #1a1a1a;
                border: 1px solid #3f3f46;
                border-radius: 8px;
            }
            #inputEdit {
                background: transparent;
                border: none;
                color: #e0e0e0;
                font-size: 10pt;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                selection-background-color: #3b82f6;
            }
            #charCount {
                color: #6b7280;
                font-size: 8pt;
            }
            #knowledgeBtn, #ragModeBtn, #clearBtn {
                background-color: #374151;
                color: #9ca3af;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 9pt;
                font-weight: 500;
            }
            #knowledgeBtn:hover, #ragModeBtn:hover, #clearBtn:hover {
                background-color: #4b5563;
                color: #e0e0e0;
            }
            #knowledgeBtn:checked {
                background-color: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            #ragModeBtn:checked {
                background-color: #10b981;
                color: white;
                border-color: #10b981;
            }
            #sendBtn {
                background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 9pt;
                font-weight: 600;
                min-width: 80px;
            }
            #sendBtn:hover {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            }
            #sendBtn:disabled {
                background-color: #374151;
                color: #6b7280;
            }
        """)

    def handle_key_press(self, event):
        """处理按键事件"""
        # 保存原始方法
        original_key_press = QTextEdit.keyPressEvent

        # Ctrl+Enter 发送消息
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if not self.is_generating and self.input_edit.toPlainText().strip():
                self.send_message()
            return

        # 调用原始方法
        original_key_press(self.input_edit, event)

    def on_text_changed(self):
        """文本变化处理"""
        text = self.input_edit.toPlainText()
        char_count = len(text)
        self.char_count_label.setText(f"{char_count} 字符")

        # 更新发送按钮状态
        has_text = bool(text.strip())
        self.send_btn.setEnabled(has_text and not self.is_generating)

    def handle_send_click(self):
        """处理发送按钮点击"""
        if self.is_generating:
            self.stop_generation.emit()
        else:
            self.send_message()

    def send_message(self):
        """发送消息"""
        text = self.input_edit.toPlainText().strip()
        if text:
            self.message_sent.emit(text)
            self.input_edit.clear()

    def clear_input(self):
        """清空输入"""
        self.input_edit.clear()

    def set_generating(self, generating: bool):
        """设置生成状态"""
        self.is_generating = generating

        if generating:
            self.send_btn.setText("⏹️ 停止")
            self.send_btn.setStyleSheet("""
                QPushButton {
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 9pt;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                }
            """)
        else:
            self.send_btn.setText("🚀 发送")
            # 恢复原始样式
            self.setup_style()

        # 更新按钮状态
        has_text = bool(self.input_edit.toPlainText().strip())
        self.send_btn.setEnabled(has_text or generating)

    def toggle_knowledge_selection(self):
        """切换知识库选择"""
        if self.knowledge_btn.isChecked():
            # 打开知识库选择对话框
            self.open_knowledge_selector()
        else:
            self.selected_knowledge_bases = []
            self.knowledge_base_selected.emit([])
            self.update_knowledge_display()

    def open_knowledge_selector(self):
        """打开知识库选择器"""
        try:
            from .knowledge_base_selector import KnowledgeBaseSelectorDialog

            # 获取业务管理器（需要从父窗口获取）
            parent_window = self.window()
            if hasattr(parent_window, 'business_manager'):
                business_manager = parent_window.business_manager
            else:
                # 如果无法获取，取消选择
                self.knowledge_btn.setChecked(False)
                return

            dialog = KnowledgeBaseSelectorDialog(
                business_manager,
                self.selected_knowledge_bases,
                self
            )

            if dialog.exec() == dialog.DialogCode.Accepted:
                self.selected_knowledge_bases = dialog.get_selected_categories()
                self.knowledge_base_selected.emit(self.selected_knowledge_bases)
                self.update_knowledge_display()
            else:
                # 用户取消，恢复按钮状态
                self.knowledge_btn.setChecked(bool(self.selected_knowledge_bases))

        except Exception as e:
            print(f"打开知识库选择器失败: {e}")
            self.knowledge_btn.setChecked(False)

    def toggle_rag_mode(self):
        """切换RAG模式"""
        self.rag_mode_enabled = self.rag_mode_btn.isChecked()
        if self.rag_mode_enabled:
            self.rag_mode_btn.setText("🤖 智能模式")
            self.rag_mode_btn.setToolTip("启用RAG智能回答模式")
        else:
            self.rag_mode_btn.setText("💬 普通模式")
            self.rag_mode_btn.setToolTip("普通聊天模式")

    def update_knowledge_display(self):
        """更新知识库显示"""
        if self.selected_knowledge_bases:
            kb_text = "、".join(self.selected_knowledge_bases)
            self.knowledge_btn.setText(f"📚 {kb_text}")
            self.knowledge_btn.setToolTip(f"已选择知识库: {kb_text}")
        else:
            self.knowledge_btn.setText("📚 知识库")
            self.knowledge_btn.setToolTip("选择知识库进行RAG检索")

    def get_selected_knowledge_bases(self) -> list:
        """获取选中的知识库"""
        return self.selected_knowledge_bases

    def is_rag_mode_enabled(self) -> bool:
        """检查RAG模式是否启用"""
        return self.rag_mode_enabled
