"""
现代化AI聊天对话框
基于Cherry Studio设计理念的专业聊天界面
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget,
    QLabel, QPushButton, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QInputDialog, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QAction
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from pathlib import Path

from .chat_components import MessageBubble, ChatInputArea
from .optimized_message_renderer import OptimizedMessageRenderer
from ..ai.models import (
    Message, Conversation, Citation, MessageRole, MessageStatus, 
    create_user_message, create_assistant_message, create_text_block
)
from ..ai.message_manager import MessageManager
from ..ai.streaming_client import RAGStreamingClient, StreamingWorker, StreamingConfig, StreamingAIClient
from ..core.business_manager import BusinessManager


class ConversationListWidget(QListWidget):
    """对话列表组件"""
    
    conversation_selected = pyqtSignal(str)  # conversation_id
    conversation_deleted = pyqtSignal(str)   # conversation_id
    conversation_renamed = pyqtSignal(str, str)  # conversation_id, new_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        """设置UI"""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemClicked.connect(self.on_item_clicked)
    
    def setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
                padding: 8px 12px;
                margin: 2px 4px;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 10pt;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
        """)
    
    def add_conversation(self, conversation: Conversation):
        """添加对话"""
        item = QListWidgetItem(conversation.title)
        item.setData(Qt.ItemDataRole.UserRole, conversation.id)
        item.setToolTip(f"创建时间: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}")
        self.insertItem(0, item)  # 插入到顶部
    
    def update_conversation(self, conversation: Conversation):
        """更新对话"""
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conversation.id:
                item.setText(conversation.title)
                break
    
    def remove_conversation(self, conversation_id: str):
        """移除对话"""
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conversation_id:
                self.takeItem(i)
                break
    
    def on_item_clicked(self, item: QListWidgetItem):
        """项目点击事件"""
        conversation_id = item.data(Qt.ItemDataRole.UserRole)
        self.conversation_selected.emit(conversation_id)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.itemAt(position)
        if not item:
            return
        
        conversation_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        # 重命名
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self.rename_conversation(conversation_id, item))
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_conversation(conversation_id))
        menu.addAction(delete_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def rename_conversation(self, conversation_id: str, item: QListWidgetItem):
        """重命名对话"""
        current_name = item.text()
        new_name, ok = QInputDialog.getText(
            self, "重命名对话", "请输入新的对话名称:", text=current_name
        )
        
        if ok and new_name.strip() and new_name != current_name:
            self.conversation_renamed.emit(conversation_id, new_name.strip())
    
    def delete_conversation(self, conversation_id: str):
        """删除对话"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这个对话吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.conversation_deleted.emit(conversation_id)


class ModernChatDialog(QDialog):
    """现代化聊天对话框"""
    
    def __init__(self, business_manager: BusinessManager, parent=None):
        super().__init__(parent)
        self.business_manager = business_manager
        self.message_manager = MessageManager(str(Path(business_manager.data_path) / "chat.db"))
        
        # 当前状态
        self.current_conversation: Optional[Conversation] = None
        self.current_messages: List[Message] = []
        self.streaming_worker: Optional[StreamingWorker] = None
        self.current_ai_message: Optional[Message] = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_conversations()
        
        # 创建默认对话
        if not self.conversation_list.count():
            self.create_new_conversation()
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("AI助手 - 智能对话")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # 左侧面板 - 对话列表
        left_panel = self.create_left_panel()
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(400)
        splitter.addWidget(left_panel)

        # 右侧面板 - 聊天区域
        right_panel = self.create_right_panel()
        right_panel.setMinimumWidth(800)
        splitter.addWidget(right_panel)

        # 设置分割比例 - 更合理的比例
        splitter.setSizes([300, 1100])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        main_layout.addWidget(splitter)

        self.setup_style()
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel("💬 对话历史")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 新建对话按钮
        self.new_chat_btn = QPushButton("➕")
        self.new_chat_btn.setToolTip("新建对话")
        self.new_chat_btn.setFixedSize(32, 32)
        self.new_chat_btn.clicked.connect(self.create_new_conversation)
        title_layout.addWidget(self.new_chat_btn)
        
        layout.addWidget(title_frame)
        
        # 对话列表
        self.conversation_list = ConversationListWidget()
        layout.addWidget(self.conversation_list)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QFrame()
        panel.setObjectName("rightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 聊天标题栏
        self.chat_title_frame = self.create_chat_title_frame()
        layout.addWidget(self.chat_title_frame)
        
        # 消息显示区域 - 使用优化的渲染器
        self.messages_renderer = OptimizedMessageRenderer()
        self.messages_renderer.setObjectName("messagesRenderer")
        layout.addWidget(self.messages_renderer, 1)  # 给消息区域更多空间

        # 为了兼容性，保留一些旧的引用
        self.messages_scroll = self.messages_renderer
        self.messages_widget = self.messages_renderer.content_widget
        self.messages_layout = self.messages_renderer.content_layout
        
        # 移除打字指示器 - 使用消息内的状态指示器代替
        
        # 输入区域
        self.input_area = ChatInputArea()
        layout.addWidget(self.input_area)
        
        return panel
    
    def create_chat_title_frame(self) -> QFrame:
        """创建聊天标题栏"""
        frame = QFrame()
        frame.setObjectName("chatTitleFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # 对话标题
        self.chat_title_label = QLabel("选择或创建新对话")
        self.chat_title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        layout.addWidget(self.chat_title_label)
        
        layout.addStretch()
        
        # 状态指示器
        self.status_label = QLabel("🔴 未连接")
        layout.addWidget(self.status_label)
        
        # 设置按钮
        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)
        
        # 导出按钮
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.clicked.connect(self.export_conversation)
        layout.addWidget(self.export_btn)
        
        return frame

    def setup_style(self):
        """设置样式 - 参考Cherry Studio设计"""
        self.setStyleSheet("""
            QDialog {
                background-color: #0f0f0f;
                color: #e4e4e7;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }
            #leftPanel {
                background-color: #0f0f0f;
                border-right: 1px solid #27272a;
            }
            #titleFrame {
                background-color: #18181b;
                border-bottom: 1px solid #27272a;
                padding: 0px;
            }
            #titleFrame QLabel {
                color: #f4f4f5;
                font-weight: 600;
            }
            #titleFrame QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12pt;
                font-weight: 500;
                padding: 4px;
            }
            #titleFrame QPushButton:hover {
                background-color: #2563eb;
            }
            #titleFrame QPushButton:pressed {
                background-color: #1d4ed8;
            }
            #rightPanel {
                background-color: #0f0f0f;
            }
            #chatTitleFrame {
                background-color: #18181b;
                border-bottom: 1px solid #27272a;
                min-height: 60px;
            }
            #chatTitleFrame QLabel {
                color: #f4f4f5;
                font-weight: 600;
            }
            #chatTitleFrame QPushButton {
                background-color: #27272a;
                color: #a1a1aa;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 9pt;
                font-weight: 500;
            }
            #chatTitleFrame QPushButton:hover {
                background-color: #3f3f46;
                color: #e4e4e7;
                border-color: #52525b;
            }
            #messagesScroll {
                background-color: #0f0f0f;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                border-radius: 3px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3f3f46;
                border-radius: 3px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #52525b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QSplitter::handle {
                background-color: #27272a;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #3f3f46;
            }
        """)

    def setup_connections(self):
        """设置信号连接"""
        # 对话列表信号
        self.conversation_list.conversation_selected.connect(self.load_conversation)
        self.conversation_list.conversation_deleted.connect(self.delete_conversation)
        self.conversation_list.conversation_renamed.connect(self.rename_conversation)

        # 输入区域信号
        self.input_area.message_sent.connect(self.send_message)
        self.input_area.stop_generation.connect(self.stop_generation)
        self.input_area.knowledge_base_selected.connect(self.on_knowledge_base_selected)

        # 检查AI状态
        self.check_ai_status()

    def check_ai_status(self):
        """检查AI状态"""
        if self.business_manager.is_ai_available():
            self.status_label.setText("🟢 已连接")
            self.status_label.setStyleSheet("color: #10b981;")
        else:
            self.status_label.setText("🔴 未连接")
            self.status_label.setStyleSheet("color: #ef4444;")

    def load_conversations(self):
        """加载对话列表"""
        conversations = self.message_manager.list_conversations()
        for conversation in conversations:
            self.conversation_list.add_conversation(conversation)

    def create_new_conversation(self):
        """创建新对话"""
        conversation = self.message_manager.create_conversation()
        self.conversation_list.add_conversation(conversation)

        # 自动选择新对话
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conversation.id:
                self.conversation_list.setCurrentItem(item)
                self.load_conversation(conversation.id)
                break

    def load_conversation(self, conversation_id: str):
        """加载对话 - 优化性能版本"""
        conversation = self.message_manager.get_conversation(conversation_id)
        if not conversation:
            return

        self.current_conversation = conversation
        self.chat_title_label.setText(conversation.title)

        # 清空当前消息显示
        self.clear_messages_display()

        # 加载消息
        self.current_messages = self.message_manager.get_conversation_messages(conversation_id)

        # 批量显示消息以提高性能
        self.messages_widget.setUpdatesEnabled(False)  # 暂时禁用重绘

        try:
            for message in self.current_messages:
                self.add_message_to_display(message)
        finally:
            self.messages_widget.setUpdatesEnabled(True)  # 重新启用重绘

        # 滚动到底部
        QTimer.singleShot(100, self.scroll_to_bottom)

    def clear_messages_display(self):
        """清空消息显示 - 使用优化渲染器"""
        # 使用优化渲染器清空消息
        self.messages_renderer.clear_messages()

    def add_message_to_display(self, message: Message):
        """添加消息到显示区域 - 使用优化渲染器"""
        # 使用优化的渲染器添加消息
        bubble = self.messages_renderer.add_message(message)

        # 获取消息内容
        content = self.message_manager.get_message_text_content(message)
        if content:
            bubble.set_content(content)
        else:
            # 如果没有内容，设置默认内容
            if message.role == MessageRole.USER:
                bubble.set_content("用户消息")
            else:
                bubble.set_content("AI正在思考...")

        # 设置引用
        if hasattr(message, 'citations') and message.citations:
            bubble.set_citations(message.citations)

        # 连接信号
        bubble.copy_requested.connect(self.copy_to_clipboard)
        bubble.edit_requested.connect(self.edit_message)
        bubble.regenerate_requested.connect(self.regenerate_message)
        bubble.citation_clicked.connect(self.show_citation_detail)

        # 强制刷新显示
        bubble.update()
        self.messages_renderer.update()

        return bubble

    def send_message(self, text: str):
        """发送消息"""
        if not self.current_conversation:
            self.create_new_conversation()

        if not self.business_manager.is_ai_available():
            QMessageBox.warning(self, "警告", "AI服务未配置或不可用，请先配置AI设置。")
            return

        # 创建用户消息
        user_message = create_user_message(self.current_conversation.id, text)
        user_message = self.message_manager.add_message(user_message)

        # 创建文本块
        text_block = create_text_block(user_message.id, text)
        self.message_manager.add_message_block(text_block)
        user_message.blocks = [text_block.id]

        # 添加到当前消息列表
        self.current_messages.append(user_message)

        # 显示用户消息
        self.add_message_to_display(user_message)

        # 开始AI回复
        self.start_ai_response(text)

        # 滚动到底部
        self.scroll_to_bottom()

        # 自动重命名对话（如果是第一条消息）
        if len(self.current_messages) == 1:
            self.auto_rename_conversation(text)

    def start_ai_response(self, user_input: str):
        """开始AI回复"""
        # 创建AI消息
        model_id = self.business_manager.get_current_model_id()
        self.current_ai_message = create_assistant_message(
            self.current_conversation.id,
            model_id
        )
        self.current_ai_message.status = MessageStatus.STREAMING
        self.current_ai_message = self.message_manager.add_message(self.current_ai_message)

        # 添加到显示
        ai_bubble = self.add_message_to_display(self.current_ai_message)

        # 设置AI消息为流式状态
        ai_bubble.message.status = MessageStatus.STREAMING
        ai_bubble.update_status_display()

        # 设置输入区域为生成状态
        self.input_area.set_generating(True)

        # 创建流式客户端
        try:
            # 检查是否使用RAG模式
            use_rag = self.input_area.is_rag_mode_enabled()

            if use_rag and self.business_manager.ai_service_manager and self.business_manager.ai_service_manager.is_rag_available():
                # 使用RAG流式模式
                config = self.get_streaming_config()
                rag_engine = self.business_manager.ai_service_manager.rag_engine

                # 获取选中的知识库
                selected_knowledge_bases = self.input_area.get_selected_knowledge_bases()

                # 创建RAG客户端并传递知识库选择
                client = RAGStreamingClient(config, rag_engine)
                client.selected_knowledge_bases = selected_knowledge_bases  # 传递知识库选择

                # 构建消息历史
                messages = self.build_message_history()

                # 创建工作线程
                self.streaming_worker = StreamingWorker(client, messages)
                self.streaming_worker.chunk_received.connect(self.handle_stream_chunk)
                self.streaming_worker.stream_finished.connect(self.handle_stream_finished)
                self.streaming_worker.error_occurred.connect(self.handle_stream_error)

                # 开始流式处理
                self.streaming_worker.start()
            else:
                # 使用普通聊天模式
                config = self.get_streaming_config()
                client = StreamingAIClient(config)

                # 构建消息历史
                messages = self.build_message_history()

                # 创建工作线程
                self.streaming_worker = StreamingWorker(client, messages)
                self.streaming_worker.chunk_received.connect(self.handle_stream_chunk)
                self.streaming_worker.stream_finished.connect(self.handle_stream_finished)
                self.streaming_worker.error_occurred.connect(self.handle_stream_error)

                # 开始流式处理
                self.streaming_worker.start()

        except Exception as e:
            self.handle_stream_error(str(e))

    # 删除旧的RAG处理方法，现在使用统一的流式处理

    # 删除旧的RAG响应处理方法

    def create_mock_citations(self, categories: List[str], query: str) -> List[Citation]:
        """创建模拟引用（实际应该从RAG引擎获取）"""
        citations = []
        try:
            for i, category in enumerate(categories[:3]):  # 最多3个引用
                # 获取该分类下的一些条目作为引用
                entries = self.business_manager.list_entries_in_category(category)
                if entries:
                    entry = entries[0]  # 取第一个条目作为示例
                    citation = Citation(
                        id=f"citation_{i}",
                        title=f"{category} - {entry.title}",
                        content=entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                        source=category,
                        score=0.8 - i * 0.1  # 模拟相关性分数
                    )
                    citations.append(citation)
        except Exception as e:
            print(f"创建引用失败: {e}")

        return citations

    def show_retrieval_status(self, message: str):
        """显示检索状态"""
        self.status_label.setText(f"🔍 {message}")
        self.status_label.setStyleSheet("color: #3b82f6;")

    def hide_retrieval_status(self):
        """隐藏检索状态"""
        self.check_ai_status()

    def get_streaming_config(self) -> StreamingConfig:
        """获取流式配置"""
        # 这里需要根据实际的配置管理器来获取配置
        # 暂时使用默认配置
        return StreamingConfig(
            api_key=self.business_manager.config_manager.get_chat_api_key() or "",
            base_url=self.business_manager.config_manager.get_chat_base_url() or "",
            model=self.business_manager.config_manager.get_chat_model() or "gpt-3.5-turbo"
        )

    def build_message_history(self) -> List[Dict[str, str]]:
        """构建消息历史"""
        messages = []

        # 只取最近的10条消息作为上下文
        recent_messages = self.current_messages[-10:]

        for message in recent_messages:
            if message.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                content = self.message_manager.get_message_text_content(message)
                if content:
                    messages.append({
                        "role": message.role.value,
                        "content": content
                    })

        return messages

    def handle_stream_chunk(self, chunk_data: Dict[str, Any]):
        """处理流式数据块"""
        chunk_type = chunk_data.get("type", "")
        content = chunk_data.get("content", "")

        if chunk_type == "text_delta" and self.current_ai_message:
            # 更新AI消息内容
            self.append_ai_message_content(content)

        elif chunk_type == "citations":
            # 处理引用
            citations_data = chunk_data.get("metadata", {}).get("citations", [])
            citations = [Citation.from_dict(c) for c in citations_data]
            if self.current_ai_message:
                self.current_ai_message.citations = citations
                self.update_ai_message_citations(citations)

        elif chunk_type == "retrieval_start":
            # 检索开始
            self.show_retrieval_status("正在检索相关信息...")

        elif chunk_type == "retrieval_complete":
            # 检索完成
            self.hide_retrieval_status()

    def handle_stream_finished(self):
        """处理流式完成 - 优化性能版本"""
        self.input_area.set_generating(False)

        if self.current_ai_message:
            # 更新消息状态
            self.current_ai_message.status = MessageStatus.SUCCESS
            self.message_manager.update_message(self.current_ai_message)

            # 添加到当前消息列表
            self.current_messages.append(self.current_ai_message)

            # 更新显示
            self.update_ai_message_status()

        # 清理缓存
        if hasattr(self, '_current_ai_bubble'):
            delattr(self, '_current_ai_bubble')

        self.current_ai_message = None
        self.streaming_worker = None

    def handle_stream_error(self, error_message: str):
        """处理流式错误"""
        self.input_area.set_generating(False)

        if self.current_ai_message:
            self.current_ai_message.status = MessageStatus.ERROR
            self.message_manager.update_message(self.current_ai_message)
            self.update_ai_message_status()

        QMessageBox.critical(self, "错误", f"AI回复失败: {error_message}")

        self.current_ai_message = None
        self.streaming_worker = None

    def append_ai_message_content(self, content: str):
        """追加AI消息内容 - 使用优化渲染器"""
        if not self.current_ai_message:
            return

        # 使用优化渲染器追加内容
        self.messages_renderer.append_message_content(self.current_ai_message.id, content)

        # 优化滚动机制：减少滚动频率
        if not hasattr(self, '_scroll_timer'):
            self._scroll_timer = QTimer()
            self._scroll_timer.setSingleShot(True)
            self._scroll_timer.timeout.connect(self.scroll_to_bottom)
            self._last_scroll_time = 0

        # 动态调整滚动频率
        import time
        current_time = time.time()
        if (current_time - self._last_scroll_time) > 0.5:  # 最多每500ms滚动一次
            self.scroll_to_bottom()
            self._last_scroll_time = current_time
        else:
            self._scroll_timer.start(200)  # 延迟滚动

    def update_ai_message_content(self, content: str):
        """更新AI消息内容（用于RAG响应）- 使用优化渲染器"""
        if not self.current_ai_message:
            return

        # 使用优化渲染器更新内容
        self.messages_renderer.update_message_content(self.current_ai_message.id, content)

        # 滚动到底部
        self.scroll_to_bottom()

    def update_ai_message_citations(self, citations: List[Citation]):
        """更新AI消息引用 - 使用优化渲染器"""
        if not self.current_ai_message:
            return

        # 使用优化渲染器获取消息组件
        widget = self.messages_renderer.get_message_widget(self.current_ai_message.id)
        if widget and isinstance(widget, MessageBubble):
            widget.set_citations(citations)

    def update_ai_message_status(self):
        """更新AI消息状态 - 使用优化渲染器"""
        if not self.current_ai_message:
            return

        # 使用优化渲染器获取消息组件
        widget = self.messages_renderer.get_message_widget(self.current_ai_message.id)
        if widget and isinstance(widget, MessageBubble):
            widget.update_status_display()

    def show_retrieval_status(self, message: str):
        """显示检索状态"""
        # 可以在这里添加检索状态指示器
        pass

    def hide_retrieval_status(self):
        """隐藏检索状态"""
        pass

    def stop_generation(self):
        """停止生成"""
        if self.streaming_worker:
            self.streaming_worker.stop()
            self.streaming_worker = None

        self.input_area.set_generating(False)

        if self.current_ai_message:
            self.current_ai_message.status = MessageStatus.CANCELLED
            self.message_manager.update_message(self.current_ai_message)
            self.update_ai_message_status()
            self.current_ai_message = None

    def scroll_to_bottom(self):
        """滚动到底部 - 使用优化渲染器"""
        # 使用优化渲染器的滚动方法
        self.messages_renderer.scroll_to_bottom(animated=False)

    def auto_rename_conversation(self, first_message: str):
        """自动重命名对话"""
        if not self.current_conversation:
            return

        # 使用前30个字符作为标题
        title = first_message[:30]
        if len(first_message) > 30:
            title += "..."

        self.current_conversation.title = title
        self.message_manager.update_conversation(self.current_conversation)
        self.conversation_list.update_conversation(self.current_conversation)
        self.chat_title_label.setText(title)

    def delete_conversation(self, conversation_id: str):
        """删除对话"""
        self.message_manager.delete_conversation(conversation_id)
        self.conversation_list.remove_conversation(conversation_id)

        # 如果删除的是当前对话，清空显示
        if self.current_conversation and self.current_conversation.id == conversation_id:
            self.current_conversation = None
            self.current_messages = []
            self.clear_messages_display()
            self.chat_title_label.setText("选择或创建新对话")

    def rename_conversation(self, conversation_id: str, new_name: str):
        """重命名对话"""
        conversation = self.message_manager.get_conversation(conversation_id)
        if conversation:
            conversation.title = new_name
            self.message_manager.update_conversation(conversation)
            self.conversation_list.update_conversation(conversation)

            # 如果是当前对话，更新标题
            if self.current_conversation and self.current_conversation.id == conversation_id:
                self.current_conversation.title = new_name
                self.chat_title_label.setText(new_name)

    def copy_to_clipboard(self, text: str):
        """复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        # 可以添加提示
        self.status_label.setText("📋 已复制")
        QTimer.singleShot(2000, lambda: self.check_ai_status())

    def edit_message(self, message_id: str):
        """编辑消息"""
        # 这里可以实现消息编辑功能
        QMessageBox.information(self, "提示", "消息编辑功能正在开发中...")

    def regenerate_message(self, message_id: str):
        """重新生成消息"""
        # 这里可以实现重新生成功能
        QMessageBox.information(self, "提示", "重新生成功能正在开发中...")

    def show_citation_detail(self, citation_id: str):
        """显示引用详情"""
        # 这里可以实现引用详情显示
        QMessageBox.information(self, "提示", f"引用详情: {citation_id}")

    def on_knowledge_base_selected(self, knowledge_bases: list):
        """处理知识库选择"""
        # 这里可以根据选择的知识库更新RAG配置
        if knowledge_bases:
            self.status_label.setText(f"📚 已选择 {len(knowledge_bases)} 个知识库")
        else:
            self.check_ai_status()

    def on_message_clicked(self, message_id: str):
        """处理消息点击事件"""
        # 可以在这里添加消息点击处理逻辑
        pass

    def open_settings(self):
        """打开设置"""
        try:
            from .unified_ai_settings_dialog import UnifiedAISettingsDialog
            settings_dialog = UnifiedAISettingsDialog(self.business_manager, self)
            if settings_dialog.exec() == settings_dialog.DialogCode.Accepted:
                # 设置更新后，重新初始化AI服务
                if self.business_manager.ai_service_manager:
                    self.business_manager.ai_service_manager.reload_configuration()
                self.check_ai_status()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开设置失败：{str(e)}")

    def export_conversation(self):
        """导出对话"""
        if not self.current_conversation:
            QMessageBox.warning(self, "警告", "请先选择一个对话")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出对话",
            f"{self.current_conversation.title}.json",
            "JSON文件 (*.json)"
        )

        if file_path:
            try:
                data = self.message_manager.export_conversation(self.current_conversation.id)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "成功", "对话导出成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def closeEvent(self, event):
        """关闭事件"""
        # 停止正在进行的生成
        if self.streaming_worker:
            self.streaming_worker.stop()

        super().closeEvent(event)


    # 删除RAGWorker类，现在使用统一的流式处理
