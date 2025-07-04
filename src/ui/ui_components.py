"""
UI组件创建模块
负责创建和配置各种UI组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QTextEdit, QLineEdit, QGroupBox, QFormLayout,
    QFrame, QMenuBar, QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from .ui_styles import UIStyles
from .draggable_entry_list import DraggableEntryList
from .status_indicator import StatusIndicatorBar


class UIComponents:
    """UI组件创建类"""
    
    @staticmethod
    def create_entry_panel(main_window):
        """创建条目列表面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 标题区域
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.Shape.NoFrame)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("条目列表")
        title_label.setStyleSheet(UIStyles.get_category_title_style())
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addWidget(title_frame)

        # 新建条目按钮
        new_entry_btn = QPushButton("新建条目")
        new_entry_btn.setStyleSheet(UIStyles.get_primary_button_style())
        new_entry_btn.clicked.connect(main_window.create_new_entry)
        layout.addWidget(new_entry_btn)

        # 条目列表
        entry_list = DraggableEntryList()
        entry_list.itemSelectionChanged.connect(main_window.on_entry_selection_changed)
        entry_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        entry_list.customContextMenuRequested.connect(main_window.context_menu_helper.show_entry_context_menu)
        layout.addWidget(entry_list)

        return panel, entry_list
    
    @staticmethod
    def create_editor_panel(main_window):
        """创建编辑器面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 条目信息区域
        info_group = QGroupBox("条目信息")
        info_group.setStyleSheet(UIStyles.get_group_box_style())
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(16, 20, 16, 16)

        # 标题输入框
        title_label = QLabel("标题:")
        title_label.setStyleSheet(UIStyles.get_form_label_style())
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("请输入条目标题...")
        title_edit.textChanged.connect(main_window.on_title_changed)
        info_layout.addRow(title_label, title_edit)

        # 标签输入框
        tags_label = QLabel("标签:")
        tags_label.setStyleSheet(UIStyles.get_form_label_style())
        tags_edit = QLineEdit()
        tags_edit.setPlaceholderText("请输入标签，用逗号分隔...")
        tags_edit.textChanged.connect(main_window.on_tags_changed)
        info_layout.addRow(tags_label, tags_edit)

        layout.addWidget(info_group)

        # 条目详细信息区域
        details_group = QGroupBox("详细信息")
        details_group.setStyleSheet(UIStyles.get_group_box_style())
        details_layout = QVBoxLayout(details_group)
        details_layout.setSpacing(8)
        details_layout.setContentsMargins(16, 20, 16, 16)

        # 创建详细信息标签
        details_info_label = QLabel()
        details_info_label.setStyleSheet("""
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
        details_info_label.setWordWrap(True)
        details_info_label.setText("请选择一个条目查看详细信息")
        details_layout.addWidget(details_info_label)

        layout.addWidget(details_group)

        # 内容编辑器区域
        content_frame = QFrame()
        content_frame.setFrameStyle(QFrame.Shape.NoFrame)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        content_label = QLabel("内容:")
        content_label.setStyleSheet(UIStyles.get_content_label_style())
        content_layout.addWidget(content_label)

        content_editor = QTextEdit()
        content_editor.setPlaceholderText("在这里编写您的内容...")
        content_layout.addWidget(content_editor)

        layout.addWidget(content_frame)

        # 保存按钮和状态指示器区域
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.Shape.NoFrame)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)

        # 保存按钮（适中宽度）
        save_btn = QPushButton("保存条目")
        save_btn.setStyleSheet(UIStyles.get_save_button_style())
        save_btn.clicked.connect(main_window.save_current_entry)
        save_btn.setMaximumWidth(180)  # 调整按钮宽度，更协调
        save_btn.setMinimumWidth(140)  # 设置最小宽度，确保按钮不会太小
        button_layout.addWidget(save_btn)

        # 状态指示器（移到保存按钮右侧）
        status_indicator_bar = StatusIndicatorBar()
        button_layout.addWidget(status_indicator_bar)

        button_layout.addStretch()  # 推到左侧

        layout.addWidget(button_frame)

        return panel, title_edit, tags_edit, content_editor, details_info_label, status_indicator_bar
    
    @staticmethod
    def create_menu_bar(main_window):
        """创建菜单栏"""
        menubar = main_window.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')

        new_entry_action = QAction('新建条目(&N)', main_window)
        new_entry_action.setShortcut(QKeySequence.StandardKey.New)
        new_entry_action.triggered.connect(main_window.create_new_entry)
        file_menu.addAction(new_entry_action)

        save_action = QAction('保存(&S)', main_window)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(main_window.save_current_entry)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction('退出(&X)', main_window)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(main_window.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu('编辑(&E)')

        delete_entry_action = QAction('删除条目(&D)', main_window)
        delete_entry_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_entry_action.triggered.connect(main_window.delete_current_entry)
        edit_menu.addAction(delete_entry_action)

        # 分类菜单
        category_menu = menubar.addMenu('分类(&C)')

        new_category_action = QAction('新建分类(&N)', main_window)
        new_category_action.triggered.connect(main_window.create_new_category)
        category_menu.addAction(new_category_action)

        rename_category_action = QAction('重命名分类(&R)', main_window)
        rename_category_action.triggered.connect(main_window.rename_category)
        category_menu.addAction(rename_category_action)

        delete_category_action = QAction('删除分类(&D)', main_window)
        delete_category_action.triggered.connect(main_window.delete_category)
        category_menu.addAction(delete_category_action)

        # 搜索菜单
        search_menu = menubar.addMenu('搜索(&S)')

        search_action = QAction('搜索条目(&F)', main_window)
        search_action.setShortcut(QKeySequence.StandardKey.Find)
        search_action.triggered.connect(main_window.open_search_dialog)
        search_menu.addAction(search_action)
    
    @staticmethod
    def create_tool_bar(main_window):
        """创建工具栏"""
        toolbar = main_window.addToolBar('主工具栏')

        # 新建条目
        new_entry_action = QAction('新建条目', main_window)
        new_entry_action.triggered.connect(main_window.create_new_entry)
        toolbar.addAction(new_entry_action)

        toolbar.addSeparator()

        # 保存
        save_action = QAction('保存', main_window)
        save_action.triggered.connect(main_window.save_current_entry)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # 新建分类
        new_category_action = QAction('新建分类', main_window)
        new_category_action.triggered.connect(main_window.create_new_category)
        toolbar.addAction(new_category_action)

        toolbar.addSeparator()

        # 搜索
        search_action = QAction('搜索', main_window)
        search_action.triggered.connect(main_window.open_search_dialog)
        toolbar.addAction(search_action)

        toolbar.addSeparator()

        # 调整模式切换
        adjust_action = QAction('调整', main_window)
        adjust_action.setCheckable(True)
        adjust_action.setChecked(False)
        adjust_action.setToolTip('开启/关闭拖拽排序模式')
        adjust_action.triggered.connect(main_window.toggle_drag_mode)
        toolbar.addAction(adjust_action)

        toolbar.addSeparator()

        # 设置按钮
        settings_action = QAction('设置', main_window)
        settings_action.setToolTip('打开应用程序设置')
        settings_action.triggered.connect(main_window.open_settings_dialog)
        toolbar.addAction(settings_action)

        # 保存调整按钮的引用，以便后续更新状态
        main_window.adjust_action = adjust_action
    
    @staticmethod
    def create_status_bar(main_window):
        """创建状态栏"""
        status_bar = main_window.statusBar()
        return status_bar
    
    @staticmethod
    def create_category_title_label():
        """创建分类标题标签"""
        category_title = QLabel("分类目录")
        category_title.setStyleSheet(UIStyles.get_category_title_style())
        return category_title
