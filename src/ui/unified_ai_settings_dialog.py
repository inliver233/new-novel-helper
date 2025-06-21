"""
统一的AI设置对话框
整合RAG和Chat配置，提供统一的设置界面
基于Cherry Studio的设计理念
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QGroupBox, QSpinBox, QTabWidget,
    QDialogButtonBox, QFrame, QCheckBox, QDoubleSpinBox, QMessageBox, QWidget,
    QComboBox, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette
from typing import Optional, Dict, Any
import asyncio

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

from ..ai.streaming_client import StreamingConfig, StreamingAIClient
from ..utils.logger import LoggerConfig


class ConnectionTestThread(QThread):
    """连接测试线程"""
    finished = pyqtSignal(bool, str, str)  # success, message, test_type
    
    def __init__(self, test_type: str, config: Dict[str, Any]):
        super().__init__()
        self.test_type = test_type
        self.config = config
        self.logger = LoggerConfig.get_logger("connection_test")
    
    def run(self):
        """运行连接测试"""
        try:
            if self.test_type == "chat":
                self._test_chat_connection()
            elif self.test_type == "rag":
                self._test_rag_connection()
        except Exception as e:
            self.finished.emit(False, f"测试失败: {str(e)}", self.test_type)
    
    def _test_chat_connection(self):
        """测试聊天连接"""
        try:
            config = StreamingConfig(
                api_key=self.config.get("api_key", ""),
                base_url=self.config.get("base_url", ""),
                model=self.config.get("model", "")
            )
            
            client = StreamingAIClient(config)
            
            # 运行异步测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(client.test_connection())
                if success:
                    self.finished.emit(True, "聊天API连接测试成功！", "chat")
                else:
                    self.finished.emit(False, "聊天API连接测试失败，请检查API密钥和网络连接。", "chat")
            finally:
                loop.close()
                
        except Exception as e:
            self.finished.emit(False, f"聊天连接测试失败: {str(e)}", "chat")
    
    def _test_rag_connection(self):
        """测试RAG连接"""
        try:
            from ..ai.siliconflow_client import SiliconFlowClient
            
            api_key = self.config.get("api_key", "")
            base_url = self.config.get("base_url", "")
            
            if not api_key or not api_key.strip():
                self.finished.emit(False, "RAG API密钥不能为空", "rag")
                return
            
            client = SiliconFlowClient(api_key, base_url)
            success = client.test_connection()
            
            if success:
                self.finished.emit(True, "RAG API连接测试成功！", "rag")
            else:
                self.finished.emit(False, "RAG API连接测试失败，请检查API密钥和网络连接。", "rag")
                
        except Exception as e:
            self.finished.emit(False, f"RAG连接测试失败: {str(e)}", "rag")


class UnifiedAISettingsDialog(QDialog):
    """统一的AI设置对话框"""
    
    def __init__(self, business_manager, parent=None):
        super().__init__(parent)
        self.business_manager = business_manager
        self.config_manager = business_manager.config_manager
        
        # 测试线程
        self.test_thread: Optional[ConnectionTestThread] = None
        
        self.setup_dialog()
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
    
    def setup_dialog(self):
        """设置对话框基本属性"""
        self.setWindowTitle("AI设置")
        self.setModal(True)
        self.resize(600, 700)
        
        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        self.setFont(font)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
                border-bottom: 2px solid #0078d4;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #e0e0e0;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 5px;
                color: #e0e0e0;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #999;
            }
            QCheckBox {
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 3px;
            }
            QLabel {
                color: #e0e0e0;
            }
            QProgressBar {
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #404040;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("AI服务配置")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #e0e0e0; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # RAG配置标签页
        self.rag_tab = self.create_rag_tab()
        self.tab_widget.addTab(self.rag_tab, "RAG配置")
        
        # 聊天配置标签页
        self.chat_tab = self.create_chat_tab()
        self.tab_widget.addTab(self.chat_tab, "聊天配置")
        
        # 按钮区域
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_rag_tab(self) -> QWidget:
        """创建RAG配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # API配置组
        api_group = QGroupBox("API配置")
        api_layout = QFormLayout(api_group)
        
        self.rag_api_key_edit = QLineEdit()
        self.rag_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.rag_api_key_edit.setPlaceholderText("请输入RAG API密钥")
        api_layout.addRow("API密钥:", self.rag_api_key_edit)
        
        self.rag_show_key_checkbox = QCheckBox("显示密钥")
        api_layout.addRow("", self.rag_show_key_checkbox)
        
        self.rag_base_url_edit = QLineEdit()
        self.rag_base_url_edit.setPlaceholderText("https://api.siliconflow.cn/v1")
        api_layout.addRow("API地址:", self.rag_base_url_edit)
        
        layout.addWidget(api_group)
        
        # 模型配置组
        model_group = QGroupBox("模型配置")
        model_layout = QFormLayout(model_group)
        
        self.embedding_model_edit = QLineEdit()
        self.embedding_model_edit.setPlaceholderText("bge-large-zh-v1.5")
        model_layout.addRow("向量化模型:", self.embedding_model_edit)
        
        self.rerank_model_edit = QLineEdit()
        self.rerank_model_edit.setPlaceholderText("bge-reranker-base")
        model_layout.addRow("重排序模型:", self.rerank_model_edit)
        
        self.rag_chat_model_edit = QLineEdit()
        self.rag_chat_model_edit.setPlaceholderText("Qwen/Qwen2-7B-Instruct")
        model_layout.addRow("对话模型:", self.rag_chat_model_edit)
        
        layout.addWidget(model_group)
        
        # RAG参数组
        params_group = QGroupBox("RAG参数")
        params_layout = QFormLayout(params_group)
        
        self.rag_top_k_retrieval_spinbox = QSpinBox()
        self.rag_top_k_retrieval_spinbox.setRange(1, 100)
        self.rag_top_k_retrieval_spinbox.setValue(20)
        params_layout.addRow("初筛数量:", self.rag_top_k_retrieval_spinbox)
        
        self.rag_top_k_rerank_spinbox = QSpinBox()
        self.rag_top_k_rerank_spinbox.setRange(1, 20)
        self.rag_top_k_rerank_spinbox.setValue(5)
        params_layout.addRow("重排序数量:", self.rag_top_k_rerank_spinbox)
        
        layout.addWidget(params_group)
        
        # 测试区域
        test_frame = self.create_rag_test_frame()
        layout.addWidget(test_frame)
        
        layout.addStretch()
        return widget

    def create_chat_tab(self) -> QWidget:
        """创建聊天配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # API配置组
        api_group = QGroupBox("API配置")
        api_layout = QFormLayout(api_group)

        self.chat_api_key_edit = QLineEdit()
        self.chat_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.chat_api_key_edit.setPlaceholderText("请输入聊天API密钥")
        api_layout.addRow("API密钥:", self.chat_api_key_edit)

        self.chat_show_key_checkbox = QCheckBox("显示密钥")
        api_layout.addRow("", self.chat_show_key_checkbox)

        self.chat_base_url_edit = QLineEdit()
        self.chat_base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        api_layout.addRow("API地址:", self.chat_base_url_edit)

        layout.addWidget(api_group)

        # 模型配置组
        model_group = QGroupBox("模型配置")
        model_layout = QFormLayout(model_group)

        self.chat_model_edit = QLineEdit()
        self.chat_model_edit.setPlaceholderText("gpt-3.5-turbo")
        model_layout.addRow("对话模型:", self.chat_model_edit)

        layout.addWidget(model_group)

        # 参数配置组
        params_group = QGroupBox("对话参数")
        params_layout = QFormLayout(params_group)

        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 2.0)
        self.temperature_spinbox.setSingleStep(0.1)
        self.temperature_spinbox.setValue(0.7)
        self.temperature_spinbox.setDecimals(1)
        params_layout.addRow("温度:", self.temperature_spinbox)

        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(1, 32000)
        self.max_tokens_spinbox.setValue(2000)
        params_layout.addRow("最大令牌数:", self.max_tokens_spinbox)

        layout.addWidget(params_group)

        # 测试区域
        test_frame = self.create_chat_test_frame()
        layout.addWidget(test_frame)

        layout.addStretch()
        return widget

    def create_rag_test_frame(self) -> QFrame:
        """创建RAG测试区域"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        # 测试按钮
        self.rag_test_button = QPushButton("测试RAG连接")
        self.rag_test_button.clicked.connect(self.test_rag_connection)
        layout.addWidget(self.rag_test_button)

        # 测试结果显示
        self.rag_test_result_label = QLabel("")
        self.rag_test_result_label.setStyleSheet("QLabel { color: #9ca3af; font-size: 9pt; }")
        self.rag_test_result_label.setWordWrap(True)
        layout.addWidget(self.rag_test_result_label)

        return frame

    def create_chat_test_frame(self) -> QFrame:
        """创建聊天测试区域"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        # 测试按钮
        self.chat_test_button = QPushButton("测试聊天连接")
        self.chat_test_button.clicked.connect(self.test_chat_connection)
        layout.addWidget(self.chat_test_button)

        # 测试结果显示
        self.chat_test_result_label = QLabel("")
        self.chat_test_result_label.setStyleSheet("QLabel { color: #9ca3af; font-size: 9pt; }")
        self.chat_test_result_label.setWordWrap(True)
        layout.addWidget(self.chat_test_result_label)

        return frame

    def setup_connections(self):
        """设置信号连接"""
        # 显示/隐藏密钥
        self.rag_show_key_checkbox.toggled.connect(self.toggle_rag_key_visibility)
        self.chat_show_key_checkbox.toggled.connect(self.toggle_chat_key_visibility)

    def toggle_rag_key_visibility(self, checked: bool):
        """切换RAG密钥显示/隐藏"""
        if checked:
            self.rag_api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.rag_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def toggle_chat_key_visibility(self, checked: bool):
        """切换聊天密钥显示/隐藏"""
        if checked:
            self.chat_api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.chat_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def load_settings(self):
        """加载设置"""
        try:
            # 加载RAG设置
            self.rag_api_key_edit.setText(self.config_manager.get_rag_api_key())
            self.rag_base_url_edit.setText(self.config_manager.get_rag_base_url())
            self.embedding_model_edit.setText(self.config_manager.get_embedding_model())
            self.rerank_model_edit.setText(self.config_manager.get_rerank_model())
            self.rag_chat_model_edit.setText(self.config_manager.get_rag_chat_model())
            self.rag_top_k_retrieval_spinbox.setValue(self.config_manager.get_rag_top_k_retrieval())
            self.rag_top_k_rerank_spinbox.setValue(self.config_manager.get_rag_top_k_rerank())

            # 加载聊天设置
            self.chat_api_key_edit.setText(self.config_manager.get_chat_api_key())
            self.chat_base_url_edit.setText(self.config_manager.get_chat_base_url())
            self.chat_model_edit.setText(self.config_manager.get_chat_model())
            self.temperature_spinbox.setValue(self.config_manager.get_chat_temperature())
            self.max_tokens_spinbox.setValue(self.config_manager.get_chat_max_tokens())

        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载设置失败：{str(e)}")

    def test_rag_connection(self):
        """测试RAG连接"""
        if self.test_thread and self.test_thread.isRunning():
            return

        config = {
            "api_key": self.rag_api_key_edit.text().strip(),
            "base_url": self.rag_base_url_edit.text().strip()
        }

        self.rag_test_button.setEnabled(False)
        self.rag_test_button.setText("测试中...")
        self.rag_test_result_label.setText("正在测试RAG连接...")

        self.test_thread = ConnectionTestThread("rag", config)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.start()

    def test_chat_connection(self):
        """测试聊天连接"""
        if self.test_thread and self.test_thread.isRunning():
            return

        config = {
            "api_key": self.chat_api_key_edit.text().strip(),
            "base_url": self.chat_base_url_edit.text().strip(),
            "model": self.chat_model_edit.text().strip()
        }

        self.chat_test_button.setEnabled(False)
        self.chat_test_button.setText("测试中...")
        self.chat_test_result_label.setText("正在测试聊天连接...")

        self.test_thread = ConnectionTestThread("chat", config)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.start()

    def on_test_finished(self, success: bool, message: str, test_type: str):
        """测试完成回调"""
        if test_type == "rag":
            self.rag_test_button.setEnabled(True)
            self.rag_test_button.setText("测试RAG连接")
            self.rag_test_result_label.setText(message)
            if success:
                self.rag_test_result_label.setStyleSheet("QLabel { color: #4ade80; font-size: 9pt; }")
            else:
                self.rag_test_result_label.setStyleSheet("QLabel { color: #f87171; font-size: 9pt; }")

        elif test_type == "chat":
            self.chat_test_button.setEnabled(True)
            self.chat_test_button.setText("测试聊天连接")
            self.chat_test_result_label.setText(message)
            if success:
                self.chat_test_result_label.setStyleSheet("QLabel { color: #4ade80; font-size: 9pt; }")
            else:
                self.chat_test_result_label.setStyleSheet("QLabel { color: #f87171; font-size: 9pt; }")

    def accept_settings(self):
        """接受设置"""
        try:
            # 保存RAG设置
            self.config_manager.set_rag_api_key(self.rag_api_key_edit.text().strip())
            self.config_manager.set_rag_base_url(self.rag_base_url_edit.text().strip())
            self.config_manager.set_embedding_model(self.embedding_model_edit.text().strip())
            self.config_manager.set_rerank_model(self.rerank_model_edit.text().strip())
            self.config_manager.set_rag_chat_model(self.rag_chat_model_edit.text().strip())
            self.config_manager.set_rag_top_k_retrieval(self.rag_top_k_retrieval_spinbox.value())
            self.config_manager.set_rag_top_k_rerank(self.rag_top_k_rerank_spinbox.value())

            # 保存聊天设置
            self.config_manager.set_chat_api_key(self.chat_api_key_edit.text().strip())
            self.config_manager.set_chat_base_url(self.chat_base_url_edit.text().strip())
            self.config_manager.set_chat_model(self.chat_model_edit.text().strip())
            self.config_manager.set_chat_temperature(self.temperature_spinbox.value())
            self.config_manager.set_chat_max_tokens(self.max_tokens_spinbox.value())

            # 保存配置文件
            self.config_manager.save()

            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败：{str(e)}")

    def closeEvent(self, event):
        """关闭事件"""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.terminate()
            self.test_thread.wait()
        super().closeEvent(event)
