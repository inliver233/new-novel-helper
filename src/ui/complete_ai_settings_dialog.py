"""
完整的AI设置对话框
支持Chat和RAG的独立配置，包括连接测试功能
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QGroupBox, QSpinBox, QTabWidget,
    QDialogButtonBox, QFrame, QCheckBox, QDoubleSpinBox, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional
import asyncio

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

from ..ai.streaming_client import StreamingConfig, StreamingAIClient


class ConnectionTestThread(QThread):
    """连接测试线程"""
    
    finished = pyqtSignal(bool, str)  # 成功状态, 消息
    
    def __init__(self, api_key: str, base_url: str, model: str, test_type: str = "chat"):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.test_type = test_type
    
    def run(self):
        """测试连接"""
        try:
            if not AIOHTTP_AVAILABLE:
                self.finished.emit(False, "aiohttp库未安装，请运行: pip install aiohttp")
                return
            
            if self.test_type == "chat":
                self._test_chat_connection()
            elif self.test_type == "rag":
                self._test_rag_connection()
                
        except Exception as e:
            self.finished.emit(False, f"连接测试出错：{str(e)}")
    
    def _test_chat_connection(self):
        """测试聊天连接"""
        config = StreamingConfig(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model
        )
        
        client = StreamingAIClient(config)
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(client.test_connection())
            if success:
                self.finished.emit(True, "聊天API连接测试成功！")
            else:
                self.finished.emit(False, "聊天API连接测试失败，请检查API密钥和网络连接。")
        finally:
            loop.close()
    
    def _test_rag_connection(self):
        """测试RAG连接"""
        # 对于RAG，我们可以测试基础的API连接
        # 这里简化为测试基本的HTTP连接
        try:
            import requests
            response = requests.get(f"{self.base_url.rstrip('/')}/models", 
                                  headers={"Authorization": f"Bearer {self.api_key}"},
                                  timeout=10)
            if response.status_code == 200:
                self.finished.emit(True, "RAG API连接测试成功！")
            else:
                self.finished.emit(False, f"RAG API连接测试失败，状态码: {response.status_code}")
        except Exception as e:
            self.finished.emit(False, f"RAG API连接测试失败: {str(e)}")


class ChatConfigWidget(QWidget):
    """聊天配置组件"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.test_thread: Optional[ConnectionTestThread] = None
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # API配置组
        api_group = QGroupBox("API配置")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(12)
        
        # API密钥
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("请输入聊天API密钥")
        api_layout.addRow("API密钥:", self.api_key_edit)
        
        # 显示/隐藏密钥
        self.show_key_checkbox = QCheckBox("显示密钥")
        self.show_key_checkbox.toggled.connect(self.toggle_key_visibility)
        api_layout.addRow("", self.show_key_checkbox)
        
        # API基础URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        api_layout.addRow("API地址:", self.base_url_edit)
        
        layout.addWidget(api_group)
        
        # 模型配置组
        model_group = QGroupBox("模型配置")
        model_layout = QFormLayout(model_group)
        model_layout.setSpacing(12)
        
        # 模型名称
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("gpt-3.5-turbo")
        model_layout.addRow("模型名称:", self.model_edit)
        
        layout.addWidget(model_group)
        
        # 参数配置组
        params_group = QGroupBox("参数配置")
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(12)
        
        # 温度参数
        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 2.0)
        self.temperature_spinbox.setSingleStep(0.1)
        self.temperature_spinbox.setValue(0.7)
        params_layout.addRow("温度参数:", self.temperature_spinbox)
        
        # 最大令牌数
        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(1, 8000)
        self.max_tokens_spinbox.setValue(2000)
        self.max_tokens_spinbox.setSuffix(" tokens")
        params_layout.addRow("最大令牌数:", self.max_tokens_spinbox)
        
        layout.addWidget(params_group)
        
        # 测试区域
        test_frame = QFrame()
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(0, 0, 0, 0)
        test_layout.setSpacing(8)
        
        # 测试按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.test_button = QPushButton("测试聊天连接")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        test_layout.addLayout(button_layout)
        
        # 测试结果显示
        self.test_result_label = QLabel("")
        self.test_result_label.setWordWrap(True)
        test_layout.addWidget(self.test_result_label)
        
        layout.addWidget(test_frame)
        layout.addStretch()
    
    def toggle_key_visibility(self, checked: bool):
        """切换密钥显示/隐藏"""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_settings(self):
        """加载设置"""
        self.api_key_edit.setText(self.config_manager.get_chat_api_key())
        self.base_url_edit.setText(self.config_manager.get_chat_base_url())
        self.model_edit.setText(self.config_manager.get_chat_model())
        self.temperature_spinbox.setValue(self.config_manager.get_chat_temperature())
        self.max_tokens_spinbox.setValue(self.config_manager.get_chat_max_tokens())
    
    def save_settings(self):
        """保存设置"""
        self.config_manager.set_chat_api_key(self.api_key_edit.text().strip())
        self.config_manager.set_chat_base_url(self.base_url_edit.text().strip())
        self.config_manager.set_chat_model(self.model_edit.text().strip())
        self.config_manager.set_chat_temperature(self.temperature_spinbox.value())
        self.config_manager.set_chat_max_tokens(self.max_tokens_spinbox.value())
    
    def test_connection(self):
        """测试连接"""
        api_key = self.api_key_edit.text().strip()
        base_url = self.base_url_edit.text().strip()
        model = self.model_edit.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return
        
        if not base_url:
            QMessageBox.warning(self, "警告", "请输入API地址")
            return
        
        if not model:
            QMessageBox.warning(self, "警告", "请输入模型名称")
            return
        
        # 禁用测试按钮
        self.test_button.setEnabled(False)
        self.test_button.setText("测试中...")
        self.test_result_label.setText("正在测试聊天连接...")
        
        # 创建测试线程
        self.test_thread = ConnectionTestThread(api_key, base_url, model, "chat")
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.start()
    
    def on_test_finished(self, success: bool, message: str):
        """测试完成"""
        self.test_button.setEnabled(True)
        self.test_button.setText("测试聊天连接")
        
        if success:
            self.test_result_label.setText(f"✅ {message}")
            self.test_result_label.setStyleSheet("QLabel { color: #10b981; }")
        else:
            self.test_result_label.setText(f"❌ {message}")
            self.test_result_label.setStyleSheet("QLabel { color: #ef4444; }")
        
        self.test_thread = None


class RAGConfigWidget(QWidget):
    """RAG配置组件"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.test_thread: Optional[ConnectionTestThread] = None
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # API配置组
        api_group = QGroupBox("RAG API配置")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(12)
        
        # API密钥
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("请输入RAG API密钥")
        api_layout.addRow("API密钥:", self.api_key_edit)
        
        # 显示/隐藏密钥
        self.show_key_checkbox = QCheckBox("显示密钥")
        self.show_key_checkbox.toggled.connect(self.toggle_key_visibility)
        api_layout.addRow("", self.show_key_checkbox)
        
        # API基础URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.siliconflow.cn/v1")
        api_layout.addRow("API地址:", self.base_url_edit)
        
        layout.addWidget(api_group)
        
        # 模型配置组
        model_group = QGroupBox("RAG模型配置")
        model_layout = QFormLayout(model_group)
        model_layout.setSpacing(12)
        
        # 聊天模型
        self.chat_model_edit = QLineEdit()
        self.chat_model_edit.setPlaceholderText("Qwen/Qwen2-7B-Instruct")
        model_layout.addRow("聊天模型:", self.chat_model_edit)
        
        # 嵌入模型
        self.embedding_model_edit = QLineEdit()
        self.embedding_model_edit.setPlaceholderText("bge-large-zh-v1.5")
        model_layout.addRow("嵌入模型:", self.embedding_model_edit)
        
        # 重排序模型
        self.rerank_model_edit = QLineEdit()
        self.rerank_model_edit.setPlaceholderText("bge-reranker-base")
        model_layout.addRow("重排序模型:", self.rerank_model_edit)
        
        layout.addWidget(model_group)
        
        # 参数配置组
        params_group = QGroupBox("RAG参数配置")
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(12)
        
        # 初筛数量
        self.top_k_retrieval_spinbox = QSpinBox()
        self.top_k_retrieval_spinbox.setRange(1, 100)
        self.top_k_retrieval_spinbox.setValue(20)
        params_layout.addRow("初筛数量:", self.top_k_retrieval_spinbox)
        
        # 重排序数量
        self.top_k_rerank_spinbox = QSpinBox()
        self.top_k_rerank_spinbox.setRange(1, 20)
        self.top_k_rerank_spinbox.setValue(5)
        params_layout.addRow("重排序数量:", self.top_k_rerank_spinbox)
        
        layout.addWidget(params_group)
        
        # 测试区域
        test_frame = QFrame()
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(0, 0, 0, 0)
        test_layout.setSpacing(8)
        
        # 测试按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.test_button = QPushButton("测试RAG连接")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        test_layout.addLayout(button_layout)
        
        # 测试结果显示
        self.test_result_label = QLabel("")
        self.test_result_label.setWordWrap(True)
        test_layout.addWidget(self.test_result_label)
        
        layout.addWidget(test_frame)
        layout.addStretch()
    
    def toggle_key_visibility(self, checked: bool):
        """切换密钥显示/隐藏"""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_settings(self):
        """加载设置"""
        self.api_key_edit.setText(self.config_manager.get_rag_api_key())
        self.base_url_edit.setText(self.config_manager.get_rag_base_url())
        self.chat_model_edit.setText(self.config_manager.get_rag_chat_model())
        self.embedding_model_edit.setText(self.config_manager.get_embedding_model())
        self.rerank_model_edit.setText(self.config_manager.get_rerank_model())
        self.top_k_retrieval_spinbox.setValue(self.config_manager.get_rag_top_k_retrieval())
        self.top_k_rerank_spinbox.setValue(self.config_manager.get_rag_top_k_rerank())
    
    def save_settings(self):
        """保存设置"""
        self.config_manager.set_rag_api_key(self.api_key_edit.text().strip())
        self.config_manager.set_rag_base_url(self.base_url_edit.text().strip())
        self.config_manager.set_rag_chat_model(self.chat_model_edit.text().strip())
        self.config_manager.set_embedding_model(self.embedding_model_edit.text().strip())
        self.config_manager.set_rerank_model(self.rerank_model_edit.text().strip())
        self.config_manager.set_rag_top_k_retrieval(self.top_k_retrieval_spinbox.value())
        self.config_manager.set_rag_top_k_rerank(self.top_k_rerank_spinbox.value())
    
    def test_connection(self):
        """测试连接"""
        api_key = self.api_key_edit.text().strip()
        base_url = self.base_url_edit.text().strip()
        model = self.chat_model_edit.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return
        
        if not base_url:
            QMessageBox.warning(self, "警告", "请输入API地址")
            return
        
        if not model:
            QMessageBox.warning(self, "警告", "请输入聊天模型名称")
            return
        
        # 禁用测试按钮
        self.test_button.setEnabled(False)
        self.test_button.setText("测试中...")
        self.test_result_label.setText("正在测试RAG连接...")
        
        # 创建测试线程
        self.test_thread = ConnectionTestThread(api_key, base_url, model, "rag")
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.start()
    
    def on_test_finished(self, success: bool, message: str):
        """测试完成"""
        self.test_button.setEnabled(True)
        self.test_button.setText("测试RAG连接")
        
        if success:
            self.test_result_label.setText(f"✅ {message}")
            self.test_result_label.setStyleSheet("QLabel { color: #10b981; }")
        else:
            self.test_result_label.setText(f"❌ {message}")
            self.test_result_label.setStyleSheet("QLabel { color: #ef4444; }")
        
        self.test_thread = None


class CompleteAISettingsDialog(QDialog):
    """完整的AI设置对话框"""

    def __init__(self, business_manager, parent=None):
        super().__init__(parent)
        self.business_manager = business_manager
        self.config_manager = business_manager.config_manager

        self.setup_dialog()
        self.setup_ui()
        self.setup_style()

    def setup_dialog(self):
        """设置对话框基本属性"""
        self.setWindowTitle("AI设置")
        self.setModal(True)
        self.resize(600, 700)

        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        self.setFont(font)

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("AI服务配置")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #e0e0e0; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 选项卡
        self.tab_widget = QTabWidget()

        # 聊天配置选项卡
        self.chat_widget = ChatConfigWidget(self.config_manager)
        self.tab_widget.addTab(self.chat_widget, "💬 聊天配置")

        # RAG配置选项卡
        self.rag_widget = RAGConfigWidget(self.config_manager)
        self.tab_widget.addTab(self.rag_widget, "🧠 RAG配置")

        layout.addWidget(self.tab_widget)

        # 按钮区域
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(button_box)

        # 连接按钮信号
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)

    def setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #3f3f46;
                border-radius: 6px;
                background-color: #2a2a2a;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #374151;
                color: #9ca3af;
                border: 1px solid #4b5563;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            QTabBar::tab:hover {
                background-color: #4b5563;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                color: #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #2a2a2a;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 8px;
                color: #e0e0e0;
                font-size: 10pt;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #3b82f6;
            }
            QCheckBox {
                color: #9ca3af;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #4b5563;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: normal;
            }
        """)

    def accept_settings(self):
        """接受设置"""
        try:
            # 保存聊天配置
            self.chat_widget.save_settings()

            # 保存RAG配置
            self.rag_widget.save_settings()

            # 保存配置文件
            self.config_manager.save()

            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败：{str(e)}")

    def closeEvent(self, event):
        """关闭事件"""
        # 停止正在进行的测试
        if hasattr(self.chat_widget, 'test_thread') and self.chat_widget.test_thread:
            self.chat_widget.test_thread.terminate()
            self.chat_widget.test_thread.wait()

        if hasattr(self.rag_widget, 'test_thread') and self.rag_widget.test_thread:
            self.rag_widget.test_thread.terminate()
            self.rag_widget.test_thread.wait()

        super().closeEvent(event)
