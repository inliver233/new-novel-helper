"""
搜索对话框 - 提供全局搜索功能
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QCheckBox, QGroupBox,
    QTextEdit, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..core.business_manager import BusinessManager
from ..core.search_service import SearchService


class SearchDialog(QDialog):
    """搜索对话框"""
    
    entry_selected = pyqtSignal(str, str)  # category_path, entry_uuid
    
    def __init__(self, business_manager: BusinessManager, parent=None):
        super().__init__(parent)
        self.business_manager = business_manager
        # 创建搜索服务实例，复用business_manager的文件系统管理器
        self.search_service = SearchService(
            business_manager.data_path,
            business_manager.fs_manager
        )
        self.search_results = []

        self.setWindowTitle("搜索条目")
        self.setGeometry(200, 200, 900, 700)

        # 应用样式
        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        """设置搜索对话框样式"""
        # 设置字体
        font = QFont("Segoe UI", 9)
        self.setFont(font)

        # 应用与主窗口相同的专业深色主题样式
        style_sheet = """
        QDialog {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }

        QGroupBox {
            color: #e0e0e0;
            border: 1px solid #52525b;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 4px;
            font-weight: 500;
            font-size: 10pt;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            background-color: #1e1e1e;
            color: #cccccc;
        }

        QLineEdit {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #52525b;
            border-radius: 3px;
            padding: 8px 10px;
            font-size: 9pt;
        }

        QLineEdit:focus {
            border-color: #0e639c;
        }

        QPushButton {
            background-color: #0e639c;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 3px;
            font-weight: 500;
            font-size: 9pt;
        }

        QPushButton:hover {
            background-color: #1177bb;
        }

        QPushButton:pressed {
            background-color: #0d5a8a;
        }

        QPushButton:disabled {
            background-color: #3f3f46;
            color: #6d6d6d;
        }

        QCheckBox {
            color: #e0e0e0;
            font-size: 9pt;
        }

        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border-radius: 2px;
            border: 1px solid #52525b;
            background-color: #3c3c3c;
        }

        QCheckBox::indicator:checked {
            background-color: #0e639c;
            border-color: #0e639c;
        }

        QListWidget {
            background-color: #252526;
            color: #e0e0e0;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            selection-background-color: #37373d;
            outline: none;
            padding: 2px;
        }

        QListWidget::item {
            padding: 8px;
            border-radius: 2px;
            margin: 1px 0px;
        }

        QListWidget::item:hover {
            background-color: #2a2d2e;
        }

        QListWidget::item:selected {
            background-color: #37373d;
        }

        QTextEdit {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #52525b;
            border-radius: 3px;
            padding: 8px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 9pt;
        }

        QTextEdit:focus {
            border-color: #0e639c;
        }

        QLabel {
            color: #e0e0e0;
            font-size: 9pt;
        }

        QSplitter::handle {
            background-color: #3f3f46;
            width: 1px;
            height: 1px;
        }

        QSplitter::handle:hover {
            background-color: #52525b;
        }
        """

        self.setStyleSheet(style_sheet)

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 搜索输入区域
        search_group = QGroupBox("搜索设置")
        search_layout = QVBoxLayout(search_group)
        search_layout.setContentsMargins(12, 16, 12, 12)
        search_layout.setSpacing(10)

        # 搜索框
        search_input_layout = QHBoxLayout()
        search_input_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_input_layout.addWidget(self.search_input)

        self.search_button = QPushButton("搜索")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8a;
            }
        """)
        self.search_button.clicked.connect(self.perform_search)
        search_input_layout.addWidget(self.search_button)

        search_layout.addLayout(search_input_layout)

        # 搜索选项
        options_frame = QFrame()
        options_frame.setFrameStyle(QFrame.Shape.NoFrame)
        options_layout = QHBoxLayout(options_frame)
        options_layout.setContentsMargins(0, 6, 0, 0)
        options_layout.setSpacing(16)

        self.search_content_cb = QCheckBox("搜索内容")
        self.search_content_cb.setChecked(True)
        options_layout.addWidget(self.search_content_cb)

        self.search_tags_cb = QCheckBox("搜索标签")
        self.search_tags_cb.setChecked(True)
        options_layout.addWidget(self.search_tags_cb)

        options_layout.addStretch()
        search_layout.addWidget(options_frame)

        layout.addWidget(search_group)
        
        # 结果显示区域
        results_splitter = QSplitter(Qt.Orientation.Horizontal)
        results_splitter.setChildrenCollapsible(False)

        # 搜索结果列表
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(12, 16, 12, 12)
        results_layout.setSpacing(6)

        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self.on_result_selection_changed)
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        results_layout.addWidget(self.results_list)

        results_group.setMaximumWidth(380)
        results_group.setMinimumWidth(350)
        results_splitter.addWidget(results_group)

        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(12, 16, 12, 12)
        preview_layout.setSpacing(8)

        # 条目信息
        self.info_label = QLabel("选择一个搜索结果查看预览")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #3c3c3c;
                border: 1px solid #52525b;
                border-radius: 3px;
                padding: 8px;
                font-size: 9pt;
                color: #cccccc;
            }
        """)
        preview_layout.addWidget(self.info_label)

        # 内容预览
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("内容预览将在这里显示...")
        preview_layout.addWidget(self.preview_text)

        results_splitter.addWidget(preview_group)
        results_splitter.setSizes([350, 550])
        layout.addWidget(results_splitter)
        
        # 按钮区域
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.Shape.NoFrame)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.setSpacing(8)
        button_layout.addStretch()

        self.open_button = QPushButton("打开条目")
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8a;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #6d6d6d;
            }
        """)
        self.open_button.clicked.connect(self.open_selected_entry)
        self.open_button.setEnabled(False)
        button_layout.addWidget(self.open_button)

        self.close_button = QPushButton("关闭")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #6d6d6d;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #7d7d7d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
        """)
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addWidget(button_frame)
        
    def perform_search(self):
        """执行搜索"""
        query = self.search_input.text().strip()
        if not query:
            return

        search_in_content = self.search_content_cb.isChecked()
        search_in_tags = self.search_tags_cb.isChecked()

        try:
            # 调用简化的搜索服务
            self.search_results = self.search_service.search(
                query,
                search_in_title=True,  # 标题始终搜索
                search_in_content=search_in_content,
                search_in_tags=search_in_tags
            )
            self.update_results_list()
        except Exception as e:
            self.results_list.clear()
            item = QListWidgetItem(f"搜索失败: {e}")
            self.results_list.addItem(item)
            
    def update_results_list(self):
        """更新搜索结果列表"""
        self.results_list.clear()
        
        if not self.search_results:
            item = QListWidgetItem("未找到匹配的条目")
            self.results_list.addItem(item)
            return
            
        for i, result in enumerate(self.search_results):
            entry = result['entry']
            category_path = result['category_path']

            # 获取相对路径作为分类显示
            try:
                rel_path = category_path.replace(self.business_manager.data_path, "").strip("/\\")
                if not rel_path:
                    rel_path = "根目录"
            except:
                rel_path = "未知分类"

            # 创建显示文本（移除了匹配类型）
            display_text = f"{entry.title}\n分类: {rel_path}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, i)  # 存储结果索引
            self.results_list.addItem(item)
            
    def on_result_selection_changed(self):
        """搜索结果选择变化"""
        current_item = self.results_list.currentItem()
        if not current_item:
            self.clear_preview()
            return
            
        result_index = current_item.data(Qt.ItemDataRole.UserRole)
        if result_index is None or result_index >= len(self.search_results):
            self.clear_preview()
            return
            
        result = self.search_results[result_index]
        self.show_preview(result)
        self.open_button.setEnabled(True)
        
    def show_preview(self, result):
        """显示条目预览"""
        entry = result['entry']
        category_path = result['category_path']
        
        # 显示条目信息
        try:
            rel_path = category_path.replace(self.business_manager.data_path, "").strip("/\\")
            if not rel_path:
                rel_path = "根目录"
        except:
            rel_path = "未知分类"
            
        info_text = f"""
标题: {entry.title}
分类: {rel_path}
标签: {', '.join(entry.tags) if entry.tags else '无'}
字数: {len(entry.content)}
创建时间: {entry.get_created_at()}
更新时间: {entry.get_updated_at()}
        """.strip()
        
        self.info_label.setText(info_text)
        
        # 显示内容预览
        content = entry.content
        if len(content) > 500:
            content = content[:500] + "..."
            
        self.preview_text.setText(content)
        
    def clear_preview(self):
        """清空预览"""
        self.info_label.setText("选择一个搜索结果查看预览")
        self.preview_text.clear()
        self.open_button.setEnabled(False)
        
    def on_result_double_clicked(self, item):
        """双击搜索结果"""
        # item参数由Qt信号提供，但我们不需要使用它
        self.open_selected_entry()
        
    def open_selected_entry(self):
        """打开选中的条目"""
        current_item = self.results_list.currentItem()
        if not current_item:
            return
            
        result_index = current_item.data(Qt.ItemDataRole.UserRole)
        if result_index is None or result_index >= len(self.search_results):
            return
            
        result = self.search_results[result_index]
        entry = result['entry']
        category_path = result['category_path']
        
        # 发射信号
        self.entry_selected.emit(category_path, entry.uuid)
        self.close()
        
    def showEvent(self, event):
        """对话框显示时聚焦搜索框"""
        super().showEvent(event)
        self.search_input.setFocus()
        self.search_input.selectAll()
