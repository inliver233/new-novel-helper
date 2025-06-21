"""
UI样式管理模块
负责管理应用程序的所有样式定义
"""

from PyQt6.QtGui import QFont


class UIStyles:
    """UI样式管理类"""

    # ===== 基础样式组件 =====

    @staticmethod
    def get_application_font():
        """获取应用程序字体"""
        return QFont("Segoe UI", 9)

    @staticmethod
    def get_base_button_style(background_color: str = "#0e639c",
                             hover_color: str = "#1177bb",
                             pressed_color: str = "#0d5a8a"):
        """获取基础按钮样式

        Args:
            background_color: 背景颜色
            hover_color: 悬停颜色
            pressed_color: 按下颜色
        """
        return f"""
            QPushButton {{
                background-color: {background_color};
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
                font-weight: 500;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
            QPushButton:disabled {{
                background-color: #3f3f46;
                color: #6d6d6d;
            }}
        """

    @staticmethod
    def get_base_input_style():
        """获取基础输入框样式"""
        return """
            QLineEdit {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #52525b;
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border-color: #0e639c;
            }
        """

    @staticmethod
    def get_base_text_edit_style():
        """获取基础文本编辑器样式"""
        return """
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #52525b;
                border-radius: 3px;
                padding: 8px;
                font-family: "Consolas", "Monaco", "Courier New", monospace;
                font-size: 10pt;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #0e639c;
            }
        """

    @staticmethod
    def get_base_group_box_style():
        """获取基础分组框样式"""
        return """
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
        """

    @staticmethod
    def get_base_list_widget_style():
        """获取基础列表控件样式"""
        return """
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
                padding: 6px 8px;
                border-radius: 2px;
                margin: 1px 0px;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QListWidget::item:selected {
                background-color: #37373d;
            }
        """

    @staticmethod
    def get_base_checkbox_style():
        """获取基础复选框样式"""
        return """
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
        """
    
    @staticmethod
    def get_main_stylesheet():
        """获取主样式表"""
        return """
        /* 主窗口样式 */
        QMainWindow {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }

        /* 菜单栏样式 */
        QMenuBar {
            background-color: #2d2d30;
            color: #e0e0e0;
            border: none;
            padding: 2px;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 8px 12px;
            border-radius: 3px;
        }

        QMenuBar::item:selected {
            background-color: #3f3f46;
        }

        QMenu {
            background-color: #2d2d30;
            color: #e0e0e0;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            padding: 2px;
        }

        QMenu::item {
            padding: 6px 16px;
            border-radius: 2px;
        }

        QMenu::item:selected {
            background-color: #3f3f46;
        }

        /* 工具栏样式 */
        QToolBar {
            background-color: #2d2d30;
            border: none;
            spacing: 2px;
            padding: 4px;
        }

        QToolBar QToolButton {
            background-color: transparent;
            color: #e0e0e0;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
            font-weight: 400;
        }

        QToolBar QToolButton:hover {
            background-color: #3f3f46;
        }

        QToolBar QToolButton:pressed {
            background-color: #484851;
        }

        /* 分割器样式 */
        QSplitter::handle {
            background-color: #3f3f46;
            width: 1px;
            height: 1px;
        }

        QSplitter::handle:hover {
            background-color: #52525b;
        }

        /* 树视图样式 */
        QTreeView {
            background-color: #252526;
            color: #e0e0e0;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            selection-background-color: #37373d;
            outline: none;
            padding: 2px;
        }

        QTreeView::item {
            padding: 4px 8px;
            border-radius: 2px;
            margin: 1px 0px;
        }

        QTreeView::item:hover {
            background-color: #2a2d2e;
        }

        QTreeView::item:selected {
            background-color: #37373d;
        }

        QTreeView::branch:has-children:!has-siblings:closed,
        QTreeView::branch:closed:has-children:has-siblings {
            border-image: none;
            image: url(none);
        }

        QTreeView::branch:open:has-children:!has-siblings,
        QTreeView::branch:open:has-children:has-siblings {
            border-image: none;
            image: url(none);
        }

        /* 列表控件样式 */
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
            padding: 6px 8px;
            border-radius: 2px;
            margin: 1px 0px;
        }

        QListWidget::item:hover {
            background-color: #2a2d2e;
        }

        QListWidget::item:selected {
            background-color: #37373d;
        }

        /* 按钮样式 */
        QPushButton {
            background-color: #0e639c;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 3px;
            font-weight: 400;
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

        /* 输入框样式 */
        QLineEdit {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #52525b;
            border-radius: 3px;
            padding: 6px 8px;
            font-size: 9pt;
        }

        QLineEdit:focus {
            border-color: #0e639c;
        }

        /* 文本编辑器样式 */
        QTextEdit {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #52525b;
            border-radius: 3px;
            padding: 8px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 10pt;
            line-height: 1.4;
        }

        QTextEdit:focus {
            border-color: #0e639c;
        }

        /* 分组框样式 */
        QGroupBox {
            color: #e0e0e0;
            border: 1px solid #52525b;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 4px;
            font-weight: 500;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            background-color: #1e1e1e;
        }

        /* 标签样式 */
        QLabel {
            color: #e0e0e0;
            font-size: 9pt;
        }

        /* 状态栏样式 */
        QStatusBar {
            background-color: #2d2d30;
            color: #e0e0e0;
            border-top: 1px solid #3f3f46;
            padding: 2px;
        }

        /* 滚动条样式 */
        QScrollBar:vertical {
            background-color: #2d2d30;
            width: 14px;
            border-radius: 0px;
        }

        QScrollBar::handle:vertical {
            background-color: #52525b;
            border-radius: 7px;
            min-height: 20px;
            margin: 2px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #6d6d6d;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }

        QScrollBar:horizontal {
            background-color: #2d2d30;
            height: 14px;
            border-radius: 0px;
        }

        QScrollBar::handle:horizontal {
            background-color: #52525b;
            border-radius: 7px;
            min-width: 20px;
            margin: 2px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #6d6d6d;
        }

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
        }
        """
    
    @staticmethod
    def get_category_title_style():
        """获取分类标题样式"""
        return """
            QLabel {
                font-size: 11pt;
                font-weight: 600;
                color: #cccccc;
                padding: 6px 4px;
                border-bottom: 1px solid #3f3f46;
                margin-bottom: 4px;
            }
        """
    
    @staticmethod
    def get_primary_button_style():
        """获取主要按钮样式"""
        base_style = UIStyles.get_base_button_style()
        return base_style + """
            QPushButton {
                margin-bottom: 4px;
            }
        """
    
    @staticmethod
    def get_group_box_style():
        """获取分组框样式"""
        return """
            QGroupBox {
                font-size: 10pt;
                font-weight: 500;
                color: #cccccc;
                border: 1px solid #52525b;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: #1e1e1e;
            }
        """
    
    @staticmethod
    def get_form_label_style():
        """获取表单标签样式"""
        return "QLabel { font-weight: 500; color: #cccccc; }"
    
    @staticmethod
    def get_content_label_style():
        """获取内容标签样式"""
        return """
            QLabel {
                font-size: 10pt;
                font-weight: 500;
                color: #cccccc;
                padding: 4px 0px;
                border-bottom: 1px solid #3f3f46;
                margin-bottom: 4px;
            }
        """
    
    @staticmethod
    def get_save_button_style():
        """获取保存按钮样式"""
        base_style = UIStyles.get_base_button_style()
        return base_style + """
            QPushButton {
                margin-top: 4px;
            }
        """

    @staticmethod
    def get_danger_button_style():
        """获取危险按钮样式（删除等操作）"""
        return UIStyles.get_base_button_style(
            background_color="#dc3545",
            hover_color="#c82333",
            pressed_color="#bd2130"
        )

    @staticmethod
    def get_line_edit_style():
        """获取输入框样式"""
        return UIStyles.get_base_input_style()

    @staticmethod
    def get_text_edit_style():
        """获取文本编辑器样式"""
        return UIStyles.get_base_text_edit_style()

    # ===== 专用样式函数 =====

    @staticmethod
    def get_dialog_style():
        """获取对话框样式"""
        return """
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
        """

    @staticmethod
    def get_secondary_button_style():
        """获取次要按钮样式（灰色）"""
        return UIStyles.get_base_button_style(
            background_color="#6d6d6d",
            hover_color="#7d7d7d",
            pressed_color="#5d5d5d"
        )

    @staticmethod
    def get_info_label_style():
        """获取信息标签样式"""
        return """
            QLabel {
                background-color: #3c3c3c;
                border: 1px solid #52525b;
                border-radius: 3px;
                padding: 8px;
                font-size: 9pt;
                color: #cccccc;
            }
        """

    @staticmethod
    def get_search_input_style():
        """获取搜索输入框样式"""
        base_style = UIStyles.get_base_input_style()
        return base_style.replace("padding: 6px 8px;", "padding: 8px 10px;")

    @staticmethod
    def get_preview_text_edit_style():
        """获取预览文本编辑器样式"""
        base_style = UIStyles.get_base_text_edit_style()
        return base_style.replace("font-size: 10pt;", "font-size: 9pt;")

    @staticmethod
    def get_enhanced_tree_style():
        """获取增强分类树样式"""
        return """
        QTreeWidget {
            background-color: #252526;
            color: #e0e0e0;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            selection-background-color: #37373d;
            outline: none;
            padding: 4px;
            font-size: 9pt;
            show-decoration-selected: 1;
        }

        QTreeWidget::item {
            padding: 8px 6px;
            border-radius: 3px;
            margin: 1px 0px;
            min-height: 26px;
            border-left: 3px solid transparent;
            background-color: transparent;
        }

        QTreeWidget::item:hover {
            background-color: rgba(42, 45, 46, 0.8);
            border-left: 3px solid #52525b;
        }

        QTreeWidget::item:selected {
            background-color: rgba(55, 55, 61, 0.9);
            color: #ffffff;
            border-left: 3px solid #0e639c;
            font-weight: 500;
        }

        QTreeWidget::item:selected:hover {
            background-color: rgba(64, 64, 71, 0.9);
            border-left: 3px solid #1177bb;
        }

        /* 自定义展开/折叠指示器 */
        QTreeWidget::branch {
            background-color: transparent;
        }

        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {
            border-image: none;
            image: none;
            background-color: transparent;
            width: 16px;
        }

        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {
            border-image: none;
            image: none;
            background-color: transparent;
            width: 16px;
        }
        """
