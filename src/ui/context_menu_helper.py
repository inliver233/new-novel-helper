"""
上下文菜单辅助类
负责创建和管理各种上下文菜单
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QPoint


class ContextMenuHelper:
    """上下文菜单辅助类"""
    
    def __init__(self, main_window):
        """
        初始化上下文菜单辅助类
        
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
    
    def create_category_context_menu(self, point: QPoint) -> QMenu:
        """
        创建分类树的上下文菜单
        
        Args:
            point: 右键点击的位置
            
        Returns:
            QMenu: 创建的上下文菜单
        """
        menu = QMenu(self.main_window)
        
        # 新建根分类
        new_category_action = QAction("新建根分类...", self.main_window)
        new_category_action.triggered.connect(
            lambda: self.main_window.create_new_category(is_root=True)
        )
        menu.addAction(new_category_action)

        # 检查是否点击在分类项上
        selected_item = self.main_window.category_tree.itemAt(point)

        if selected_item:
            # 新建子分类
            new_subcategory_action = QAction("新建子分类...", self.main_window)
            new_subcategory_action.triggered.connect(
                lambda: self.main_window.create_new_category(is_root=False)
            )
            menu.addAction(new_subcategory_action)
            
            menu.addSeparator()
            
            # 重命名分类
            rename_action = QAction("重命名分类...", self.main_window)
            rename_action.triggered.connect(self.main_window.rename_category)
            menu.addAction(rename_action)

            # 删除分类
            delete_action = QAction("删除分类", self.main_window)
            delete_action.triggered.connect(self.main_window.delete_category)
            menu.addAction(delete_action)

        return menu
    
    def create_entry_context_menu(self, point: QPoint) -> QMenu:
        """
        创建条目列表的上下文菜单
        
        Args:
            point: 右键点击的位置
            
        Returns:
            QMenu: 创建的上下文菜单
        """
        menu = QMenu(self.main_window)
        item = self.main_window.entry_list.itemAt(point)

        # 新建条目（总是可用）
        new_entry_action = QAction("新建条目", self.main_window)
        new_entry_action.triggered.connect(self.main_window.create_new_entry)
        menu.addAction(new_entry_action)

        if item:
            # 如果右键点击在条目上，添加相关选项
            menu.addSeparator()

            # 在新窗口中打开
            open_in_window_action = QAction("在新窗口中打开", self.main_window)
            open_in_window_action.triggered.connect(
                lambda: self.main_window.open_entry_in_new_window(item)
            )
            menu.addAction(open_in_window_action)

            menu.addSeparator()

            # 重命名条目
            rename_action = QAction("重命名条目", self.main_window)
            rename_action.triggered.connect(self.main_window.rename_current_entry)
            menu.addAction(rename_action)

            # 删除条目
            delete_action = QAction("删除条目", self.main_window)
            delete_action.triggered.connect(self.main_window.delete_current_entry)
            menu.addAction(delete_action)

        return menu
    
    def show_category_context_menu(self, point: QPoint):
        """
        显示分类树的上下文菜单
        
        Args:
            point: 右键点击的位置
        """
        menu = self.create_category_context_menu(point)
        menu.exec(self.main_window.category_tree.viewport().mapToGlobal(point))
    
    def show_entry_context_menu(self, point: QPoint):
        """
        显示条目列表的上下文菜单
        
        Args:
            point: 右键点击的位置
        """
        menu = self.create_entry_context_menu(point)
        menu.exec(self.main_window.entry_list.viewport().mapToGlobal(point))
