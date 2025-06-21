"""
AI设置对话框
用于配置AI聊天服务的参数和连接设置
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QGroupBox, QSpinBox, QComboBox,
    QDialogButtonBox, QFrame, QCheckBox, QDoubleSpinBox, QMessageBox
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


class ChatConnectionTestThread(QThread):
    """聊天连接测试线程"""
    
    finished = pyqtSignal(bool, str)  # 成功状态, 消息
    
    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def run(self):
        """测试连接"""
        try:
            if not AIOHTTP_AVAILABLE:
                self.finished.emit(False, "aiohttp库未安装，请运行: pip install aiohttp")
                return

            # 创建流式客户端配置
            config = StreamingConfig(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model
            )
            
            # 创建客户端并测试
            client = StreamingAIClient(config)
            
            # 运行异步测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(client.test_connection())
                if success:
                    self.finished.emit(True, "连接测试成功！")
                else:
                    self.finished.emit(False, "连接测试失败，请检查API密钥和网络连接。")
            finally:
                loop.close()
                
        except Exception as e:
            self.finished.emit(False, f"连接测试出错：{str(e)}")


class SimpleAISettingsDialog(QDialog):
    """简化的AI设置对话框"""
    
    def __init__(self, business_manager, parent=None):
        super().__init__(parent)
        self.business_manager = business_manager
        self.config_manager = business_manager.config_manager
        
        # 测试线程
        self.test_thread: Optional[ChatConnectionTestThread] = None
        
        self.setup_dialog()
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
    
    def setup_dialog(self):
        """设置对话框基本属性"""
        self.setWindowTitle("AI聊天设置")
        self.setModal(True)
        self.resize(500, 400)
        
        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        self.setFont(font)
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("AI聊天配置")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #e0e0e0; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # API配置组
        api_group = self.create_api_group()
        layout.addWidget(api_group)
        
        # 模型配置组
        model_group = self.create_model_group()
        layout.addWidget(model_group)
        
        # 参数配置组
        params_group = self.create_params_group()
        layout.addWidget(params_group)
        
        # 测试区域
        test_frame = self.create_test_frame()
        layout.addWidget(test_frame)
        
        # 按钮区域
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet("""
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
        """)
        layout.addWidget(button_box)
        
        # 连接按钮信号
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
    
    def create_api_group(self) -> QGroupBox:
        """创建API配置组"""
        group = QGroupBox("API配置")
        group.setStyleSheet("""
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
        """)
        
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # API密钥
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("请输入API密钥")
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 8px;
                color: #e0e0e0;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        
        api_key_label = QLabel("API密钥:")
        api_key_label.setStyleSheet("color: #e0e0e0; font-weight: normal;")
        layout.addRow(api_key_label, self.api_key_edit)
        
        # 显示/隐藏密钥
        self.show_key_checkbox = QCheckBox("显示密钥")
        self.show_key_checkbox.setStyleSheet("QCheckBox { color: #9ca3af; }")
        layout.addRow("", self.show_key_checkbox)
        
        # API基础URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        self.base_url_edit.setStyleSheet(self.api_key_edit.styleSheet())
        
        base_url_label = QLabel("API地址:")
        base_url_label.setStyleSheet("color: #e0e0e0; font-weight: normal;")
        layout.addRow(base_url_label, self.base_url_edit)
        
        return group
    
    def create_model_group(self) -> QGroupBox:
        """创建模型配置组"""
        group = QGroupBox("模型配置")
        group.setStyleSheet("""
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
        """)
        
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # 模型名称
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("gpt-3.5-turbo")
        self.model_edit.setStyleSheet(self.api_key_edit.styleSheet())
        
        model_label = QLabel("模型名称:")
        model_label.setStyleSheet("color: #e0e0e0; font-weight: normal;")
        layout.addRow(model_label, self.model_edit)
        
        return group
    
    def create_params_group(self) -> QGroupBox:
        """创建参数配置组"""
        group = QGroupBox("参数配置")
        group.setStyleSheet("""
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
        """)
        
        layout = QFormLayout(group)
        layout.setSpacing(12)
        
        # 温度参数
        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 2.0)
        self.temperature_spinbox.setSingleStep(0.1)
        self.temperature_spinbox.setValue(0.7)
        self.temperature_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2a2a2a;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
                font-size: 10pt;
            }
            QDoubleSpinBox:focus {
                border-color: #3b82f6;
            }
        """)
        
        temperature_label = QLabel("温度参数:")
        temperature_label.setStyleSheet("color: #e0e0e0; font-weight: normal;")
        layout.addRow(temperature_label, self.temperature_spinbox)
        
        # 最大令牌数
        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(1, 8000)
        self.max_tokens_spinbox.setValue(2000)
        self.max_tokens_spinbox.setSuffix(" tokens")
        self.max_tokens_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #2a2a2a;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
                font-size: 10pt;
            }
            QSpinBox:focus {
                border-color: #3b82f6;
            }
        """)
        
        max_tokens_label = QLabel("最大令牌数:")
        max_tokens_label.setStyleSheet("color: #e0e0e0; font-weight: normal;")
        layout.addRow(max_tokens_label, self.max_tokens_spinbox)
        
        return group
    
    def create_test_frame(self) -> QFrame:
        """创建测试区域"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.NoFrame)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 测试按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.test_button = QPushButton("测试连接")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }
        """)
        button_layout.addWidget(self.test_button)
        
        layout.addLayout(button_layout)
        
        # 测试结果显示
        self.test_result_label = QLabel("")
        self.test_result_label.setStyleSheet("QLabel { color: #9ca3af; font-size: 9pt; }")
        self.test_result_label.setWordWrap(True)
        layout.addWidget(self.test_result_label)
        
        return frame
    
    def setup_connections(self):
        """设置信号连接"""
        # 显示/隐藏密钥
        self.show_key_checkbox.toggled.connect(self.toggle_key_visibility)
        
        # 测试连接
        self.test_button.clicked.connect(self.test_connection)
    
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
        self.test_result_label.setText("正在测试连接...")
        
        # 创建测试线程
        self.test_thread = ChatConnectionTestThread(api_key, base_url, model)
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.start()
    
    def on_test_finished(self, success: bool, message: str):
        """测试完成"""
        self.test_button.setEnabled(True)
        self.test_button.setText("测试连接")
        
        if success:
            self.test_result_label.setText(f"✅ {message}")
            self.test_result_label.setStyleSheet("QLabel { color: #10b981; font-size: 9pt; }")
        else:
            self.test_result_label.setText(f"❌ {message}")
            self.test_result_label.setStyleSheet("QLabel { color: #ef4444; font-size: 9pt; }")
        
        self.test_thread = None
    
    def accept_settings(self):
        """接受设置"""
        try:
            # 保存设置
            self.config_manager.set_chat_api_key(self.api_key_edit.text().strip())
            self.config_manager.set_chat_base_url(self.base_url_edit.text().strip())
            self.config_manager.set_chat_model(self.model_edit.text().strip())
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
