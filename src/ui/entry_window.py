"""
独立条目窗口模块
提供独立的条目编辑界面，支持多窗口同时编辑不同条目
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QGroupBox, QFormLayout, QPushButton,
    QMessageBox, QFrame, QMenuBar, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent
from ..models.entry import Entry
from .ui_styles import UIStyles
from ..utils.time_utils import format_datetime_chinese, count_text_stats


class EntryWindow(QMainWindow):
    """独立的条目编辑窗口"""
    
    # 信号定义
    entry_updated = pyqtSignal(str, str, Entry)  # category_path, entry_uuid, entry
    entry_deleted = pyqtSignal(str, str)  # category_path, entry_uuid
    window_closed = pyqtSignal(str)  # window_id
    
    def __init__(self, business_manager, category_path: str, entry: Entry, window_id: str):
        super().__init__()
        
        # 基本属性
        self.business_manager = business_manager
        self.category_path = category_path
        self.entry = entry
        self.window_id = window_id
        self.is_content_modified = False
        
        # 自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.setSingleShot(True)
        
        # 初始化UI
        self.setup_window()
        self.setup_styles()
        self.create_menu_bar()
        self.create_main_content()
        self.create_status_bar()
        
        # 加载条目内容
        self.load_entry_content()
        
        # 连接信号
        self.connect_signals()
        
    def setup_window(self):
        """设置窗口基本属性"""
        self.setWindowTitle(f"条目编辑 - {self.entry.title}")
        self.setGeometry(200, 200, 800, 600)

        # 设置窗口属性，确保不会影响其他窗口的层级
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # 默认可以激活

        # 设置窗口标志，确保是独立窗口
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint |
                           Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)
        
    def setup_styles(self):
        """设置窗口样式"""
        # 设置应用程序字体
        font = UIStyles.get_application_font()
        self.setFont(font)
        
        # 设置主样式表
        self.setStyleSheet(UIStyles.get_main_stylesheet())
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 保存操作
        save_action = QAction('保存(&S)', self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_entry)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # 关闭窗口
        close_action = QAction('关闭(&C)', self)
        close_action.setShortcut(QKeySequence.StandardKey.Close)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑(&E)')
        
        # 撤销/重做
        undo_action = QAction('撤销(&U)', self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo_content)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction('重做(&R)', self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo_content)
        edit_menu.addAction(redo_action)
        
    def create_main_content(self):
        """创建主要内容区域"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # 条目信息区域
        info_group = QGroupBox("条目信息")
        info_group.setStyleSheet(UIStyles.get_group_box_style())
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(16, 20, 16, 16)
        
        # 标题输入框
        title_label = QLabel("标题:")
        title_label.setStyleSheet(UIStyles.get_form_label_style())
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("请输入条目标题...")
        self.title_edit.setStyleSheet(UIStyles.get_line_edit_style())
        info_layout.addRow(title_label, self.title_edit)
        
        # 标签输入框
        tags_label = QLabel("标签:")
        tags_label.setStyleSheet(UIStyles.get_form_label_style())
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("请输入标签，用逗号分隔...")
        self.tags_edit.setStyleSheet(UIStyles.get_line_edit_style())
        info_layout.addRow(tags_label, self.tags_edit)
        
        main_layout.addWidget(info_group)

        # 条目详细信息区域
        details_group = QGroupBox("详细信息")
        details_group.setStyleSheet(UIStyles.get_group_box_style())
        details_layout = QVBoxLayout(details_group)
        details_layout.setSpacing(8)
        details_layout.setContentsMargins(16, 20, 16, 16)

        # 创建详细信息标签
        self.details_info_label = QLabel()
        self.details_info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                line-height: 1.4;
                padding: 8px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.details_info_label.setWordWrap(True)
        self.details_info_label.setText("加载中...")
        details_layout.addWidget(self.details_info_label)

        main_layout.addWidget(details_group)

        # 内容编辑区域
        content_group = QGroupBox("内容")
        content_group.setStyleSheet(UIStyles.get_group_box_style())
        content_layout = QVBoxLayout(content_group)
        content_layout.setContentsMargins(16, 20, 16, 16)
        content_layout.setSpacing(12)
        
        # 内容编辑器
        self.content_editor = QTextEdit()
        self.content_editor.setPlaceholderText("请输入条目内容...")
        self.content_editor.setStyleSheet(UIStyles.get_text_edit_style())
        content_layout.addWidget(self.content_editor)
        
        main_layout.addWidget(content_group)
        
        # 按钮区域
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.setStyleSheet(UIStyles.get_primary_button_style())
        self.save_button.clicked.connect(self.save_entry)
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        
        # 删除按钮
        self.delete_button = QPushButton("删除条目")
        self.delete_button.setStyleSheet(UIStyles.get_danger_button_style())
        self.delete_button.clicked.connect(self.delete_entry)
        button_layout.addWidget(self.delete_button)
        
        main_layout.addWidget(button_frame)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()
        
    def load_entry_content(self):
        """加载条目内容到编辑器"""
        self.title_edit.setText(self.entry.title)
        self.content_editor.setPlainText(self.entry.content)

        # 加载标签
        if self.entry.tags:
            tags_text = ", ".join(self.entry.tags)
            self.tags_edit.setText(tags_text)

        # 更新详细信息显示
        self.update_entry_details()

        # 重置修改标志
        self.is_content_modified = False
        self.update_window_title()
        
    def connect_signals(self):
        """连接信号和槽"""
        self.title_edit.textChanged.connect(self.on_content_changed)
        self.tags_edit.textChanged.connect(self.on_content_changed)
        self.content_editor.textChanged.connect(self.on_content_changed)
        
    def on_content_changed(self):
        """内容发生变化时的处理"""
        self.is_content_modified = True
        self.update_window_title()
        self.update_status_bar()

        # 实时更新详细信息
        self.update_entry_details_realtime()

        # 启动自动保存定时器（3秒后保存）
        self.auto_save_timer.start(3000)
        
    def update_window_title(self):
        """更新窗口标题"""
        title = f"条目编辑 - {self.entry.title}"
        if self.is_content_modified:
            title += " *"
        self.setWindowTitle(title)
        
    def update_status_bar(self):
        """更新状态栏"""
        word_count = len(self.content_editor.toPlainText())
        status_text = f"字数: {word_count}"
        
        if self.is_content_modified:
            status_text += " | 未保存"
        else:
            status_text += " | 已保存"
            
        self.status_bar.showMessage(status_text)

    def update_entry_details(self):
        """更新条目详细信息显示"""
        if not self.entry:
            self.details_info_label.setText("加载中...")
            return

        # 获取条目信息
        created_at = format_datetime_chinese(self.entry.get_created_at())
        updated_at = format_datetime_chinese(self.entry.get_updated_at())

        # 统计文本信息
        stats = count_text_stats(self.entry.content)

        # 构建详细信息文本
        details_text = f"""创建: {created_at} | 更新: {updated_at}

字数: {stats['chinese_chars']} | 英文: {stats['english_words']} | 符号: {stats['symbols']} | 字符: {stats['total_chars']} | 行数: {stats['lines']}"""

        self.details_info_label.setText(details_text)

    def update_entry_details_realtime(self):
        """实时更新条目详细信息（主要是字数统计）"""
        if not self.entry:
            return

        # 获取当前编辑器中的内容
        current_content = self.content_editor.toPlainText()

        # 获取条目信息
        created_at = format_datetime_chinese(self.entry.get_created_at())
        updated_at = format_datetime_chinese(self.entry.get_updated_at())

        # 统计当前内容
        stats = count_text_stats(current_content)

        # 构建详细信息文本
        details_text = f"""创建: {created_at} | 更新: {updated_at}

字数: {stats['chinese_chars']} | 英文: {stats['english_words']} | 符号: {stats['symbols']} | 字符: {stats['total_chars']} | 行数: {stats['lines']}"""

        self.details_info_label.setText(details_text)

    def save_entry(self):
        """保存条目"""
        try:
            # 获取编辑器中的内容
            title = self.title_edit.text().strip()
            content = self.content_editor.toPlainText()
            tags_text = self.tags_edit.text().strip()
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            if not title:
                QMessageBox.warning(self, "警告", "标题不能为空")
                return False

            # 更新条目
            self.business_manager.update_entry(
                self.category_path,
                self.entry.uuid,
                title=title,
                content=content,
                tags=tags
            )

            # 更新本地条目对象
            self.entry.update_content(title=title, content=content, tags=tags)

            # 重置修改标志
            self.is_content_modified = False
            self.update_window_title()
            self.update_status_bar()

            # 发送更新信号
            self.entry_updated.emit(self.category_path, self.entry.uuid, self.entry)

            # 显示保存成功消息
            self.status_bar.showMessage("保存成功", 2000)

            return True

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
            return False

    def auto_save(self):
        """自动保存"""
        if self.is_content_modified:
            self.save_entry()

    def delete_entry(self):
        """删除条目"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除条目 '{self.entry.title}' 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除条目
                self.business_manager.delete_entry(self.category_path, self.entry.uuid)

                # 发送删除信号
                self.entry_deleted.emit(self.category_path, self.entry.uuid)

                # 关闭窗口
                self.close()

            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def undo_content(self):
        """撤销内容编辑"""
        self.content_editor.undo()

    def redo_content(self):
        """重做内容编辑"""
        self.content_editor.redo()

    def update_entry_data(self, entry: Entry):
        """从外部更新条目数据（用于同步）"""
        if entry.uuid != self.entry.uuid:
            return

        # 检查是否有未保存的修改
        if self.is_content_modified:
            reply = QMessageBox.question(
                self,
                "数据冲突",
                "此条目在其他地方被修改了，是否要放弃当前修改并重新加载？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # 更新条目数据
        self.entry = entry
        self.load_entry_content()

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        if self.is_content_modified:
            reply = QMessageBox.question(
                self,
                "未保存的修改",
                "有未保存的修改，是否要保存？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_entry():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # 发送窗口关闭信号
        self.window_closed.emit(self.window_id)

        # 停止自动保存定时器
        self.auto_save_timer.stop()

        event.accept()

    def get_entry_uuid(self) -> str:
        """获取条目UUID"""
        return self.entry.uuid

    def get_category_path(self) -> str:
        """获取分类路径"""
        return self.category_path
