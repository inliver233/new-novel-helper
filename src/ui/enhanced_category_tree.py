"""
增强的分类树组件
提供清晰的层级结构显示，包括展开/折叠指示器、层级缩进和子项计数
"""

import os
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMessageBox, QApplication
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QFont, QBrush, QColor, QDrag
from .ui_styles import UIStyles


class EnhancedCategoryTreeItem(QTreeWidgetItem):
    """增强的分类树项目，支持层级显示和子项计数"""
    
    def __init__(self, parent, name, path, children_count=0):
        super().__init__(parent, [name])
        self.category_path = path
        self.children_count = children_count
        self.original_name = name
        self.setData(0, Qt.ItemDataRole.UserRole, path)

        # 设置工具提示显示完整路径和子项信息
        tooltip = f"分类名称: {name}\n路径: {path}"
        if children_count > 0:
            tooltip += f"\n包含子分类: {children_count} 个"
        else:
            tooltip += f"\n这是叶子分类（无子分类）"
        self.setToolTip(0, tooltip)


class EnhancedCategoryTree(QTreeWidget):
    """增强的分类树，提供清晰的层级结构显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_tree()

        # 拖拽相关属性
        self.drag_enabled = False
        self.drag_start_position = None
        self.business_manager = None  # 将在主窗口中设置

        # 拖拽视觉反馈
        self.drop_indicator_item = None  # 当前高亮的目标项
        self.original_background = None  # 保存原始背景色
        self.reorder_indicator_item = None  # 重排序指示器项
        self.reorder_indicator_position = None  # 重排序指示器位置 ("above" 或 "below")
        
    def setup_tree(self):
        """设置树的基本属性"""
        self.setHeaderLabel("分类目录")
        self.setColumnCount(1)
        self.setRootIsDecorated(True)  # 显示根节点的展开/折叠图标
        self.setIndentation(20)  # 设置缩进距离
        self.setUniformRowHeights(False)  # 允许不同行高

        # 初始化拖拽设置
        self.setDragDropMode(QTreeWidget.DragDropMode.NoDragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)

        # 设置样式
        self.setStyleSheet(UIStyles.get_enhanced_tree_style())
    
    def populate_from_data(self, category_data):
        """从分类数据填充树"""
        self.clear()
        self._add_items_recursively(self, category_data, 0)

        # 只展开第一级，其他级别保持折叠
        self._expand_first_level_only()

        # 连接展开/折叠信号以更新显示
        self.itemExpanded.connect(self._on_item_expanded)
        self.itemCollapsed.connect(self._on_item_collapsed)
        
    def _add_items_recursively(self, parent_widget, items, level):
        """递归地向树中添加项目"""
        for item_data in items:
            children = item_data.get('children', [])
            children_count = len(children)
            
            # 创建增强的树项目
            tree_item = EnhancedCategoryTreeItem(
                parent_widget, 
                item_data['name'], 
                item_data['path'],
                children_count
            )
            
            # 设置层级相关的显示属性
            self._setup_item_appearance(tree_item, level, children_count)
            
            # 递归添加子项目
            if children:
                self._add_items_recursively(tree_item, children, level + 1)
                
    def _setup_item_appearance(self, item, level, children_count):
        """设置项目的外观"""
        # 根据层级设置不同的字体和颜色
        font = QFont()

        # 使用原始名称，避免重复添加图标和计数
        if isinstance(item, EnhancedCategoryTreeItem):
            original_text = item.original_name
        else:
            original_text = item.text(0)

        # 统一的图标系统：有子分类用大三角，无子分类用大圆点
        if children_count > 0:
            icon = "▶"  # 大三角表示有子分类
            count_text = f" [{children_count}]"
        else:
            icon = "●"  # 大圆点表示无子分类
            count_text = ""

        if level == 0:  # 根级分类
            font.setBold(True)
            font.setPointSize(10)
            item.setForeground(0, QBrush(QColor("#ffffff")))
            item.setText(0, f"{icon} {original_text}{count_text}")

        elif level == 1:  # 二级分类
            font.setBold(False)
            font.setPointSize(9)
            item.setForeground(0, QBrush(QColor("#e0e0e0")))
            item.setText(0, f"  {icon} {original_text}{count_text}")

        elif level == 2:  # 三级分类
            font.setBold(False)
            font.setPointSize(9)
            item.setForeground(0, QBrush(QColor("#cccccc")))
            item.setText(0, f"    {icon} {original_text}{count_text}")

        else:  # 四级及以上分类
            font.setBold(False)
            font.setPointSize(8)
            item.setForeground(0, QBrush(QColor("#aaaaaa")))
            indent = "  " * level
            item.setText(0, f"{indent}{icon} {original_text}{count_text}")

        item.setFont(0, font)
            
    def _get_item_level(self, item):
        """获取项目的层级深度"""
        level = 0
        parent = item.parent()
        while parent:
            level += 1
            parent = parent.parent()
        return level

    def _expand_first_level_only(self):
        """只显示第一级分类，所有子级都折叠"""
        # 首先折叠所有项目
        self.collapseAll()

        # 不需要展开任何项目，因为我们只想显示第一级
        # 第一级项目默认就是可见的，不需要展开



    def _on_item_expanded(self, item):
        """当项目展开时的处理"""
        # 可以在这里添加展开时的特殊处理逻辑
        pass

    def _on_item_collapsed(self, item):
        """当项目折叠时的处理"""
        # 可以在这里添加折叠时的特殊处理逻辑
        pass

    def refresh_item_appearance(self, item):
        """刷新单个项目的外观"""
        if isinstance(item, EnhancedCategoryTreeItem):
            level = self._get_item_level(item)
            children_count = item.childCount()
            item.children_count = children_count
            self._setup_item_appearance(item, level, children_count)

    def refresh_all_appearances(self):
        """刷新所有项目的外观"""
        def refresh_recursive(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                self.refresh_item_appearance(child)
                refresh_recursive(child)

        refresh_recursive(self.invisibleRootItem())

    # ===== 拖拽功能 =====

    def set_business_manager(self, business_manager):
        """设置业务管理器引用"""
        self.business_manager = business_manager

    def set_drag_enabled(self, enabled: bool):
        """设置拖拽功能是否启用"""
        self.drag_enabled = enabled
        if enabled:
            self.setDragDropMode(QTreeWidget.DragDropMode.DragDrop)
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
        else:
            self.setDragDropMode(QTreeWidget.DragDropMode.NoDragDrop)
            self.setDragEnabled(False)
            self.setAcceptDrops(False)

    def mimeTypes(self):
        """返回支持的MIME类型"""
        return ["text/plain"]

    def mimeData(self, items):
        """创建拖拽数据"""
        if not items or not self.drag_enabled:
            return None

        item = items[0]
        if isinstance(item, EnhancedCategoryTreeItem):
            mime_data = QMimeData()
            mime_data.setText(f"category:{item.category_path}")
            return mime_data
        return None

    def canDropMimeData(self, data, action, row, column, parent):
        """检查是否可以放置数据"""
        if not self.drag_enabled:
            return False

        if not data.hasText():
            return False

        text = data.text()
        if not text.startswith("category:"):
            return False

        # 如果有父项，检查是否可以放置
        if parent.isValid():
            parent_item = self.itemFromIndex(parent)
            if isinstance(parent_item, EnhancedCategoryTreeItem):
                source_path = text[9:]  # 移除 "category:" 前缀
                target_path = parent_item.category_path
                return self.can_drop_on_target(source_path, target_path)

        return True  # 可以放置到根级别

    def dropMimeData(self, data, action, row, column, parent):
        """处理放置数据"""
        if not self.canDropMimeData(data, action, row, column, parent):
            return False

        text = data.text()
        source_path = text[9:]  # 移除 "category:" 前缀

        try:
            if parent.isValid():
                # 移动到目标分类下
                parent_item = self.itemFromIndex(parent)
                if isinstance(parent_item, EnhancedCategoryTreeItem):
                    target_path = parent_item.category_path
                    self.move_category_to_target(source_path, target_path)
            else:
                # 移动到根级别
                self.move_category_to_root(source_path)

            return True

        except Exception as e:
            QMessageBox.warning(self, "错误", f"移动分类失败: {e}")
            return False

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if self.drag_enabled and event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("category:"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if not self.drag_enabled:
            self.clear_drop_indicator()
            event.ignore()
            return

        if not event.mimeData().hasText():
            self.clear_drop_indicator()
            event.ignore()
            return

        text = event.mimeData().text()
        if not text.startswith("category:"):
            self.clear_drop_indicator()
            event.ignore()
            return

        # 获取目标项和拖拽类型
        target_item = self.itemAt(event.position().toPoint())
        source_path = text[9:]  # 移除 "category:" 前缀

        # 判断拖拽类型
        drop_type = self.get_drop_type(event.position().toPoint(), target_item, source_path)

        if drop_type == "reorder":
            # 显示插入位置指示器
            self.show_reorder_indicator(event.position().toPoint(), target_item)
            event.acceptProposedAction()
        elif drop_type == "move_into" and target_item:
            # 高亮目标分类
            self.highlight_drop_target(target_item)
            event.acceptProposedAction()
        elif drop_type == "move_to_root":
            # 移动到根级别
            self.clear_drop_indicator()
            event.acceptProposedAction()
        else:
            # 无效操作
            self.clear_drop_indicator()
            event.ignore()

        # 调用父类方法以确保正常的拖拽处理
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.clear_drop_indicator()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """拖拽放置事件"""
        # 获取拖拽信息
        target_item = self.itemAt(event.position().toPoint())
        source_path = event.mimeData().text()[9:]  # 移除 "category:" 前缀
        drop_type = self.get_drop_type(event.position().toPoint(), target_item, source_path)

        # 清除视觉反馈
        self.clear_drop_indicator()

        if not self.drag_enabled:
            event.ignore()
            return

        if not event.mimeData().hasText():
            event.ignore()
            return

        text = event.mimeData().text()
        if not text.startswith("category:"):
            event.ignore()
            return

        try:
            if drop_type == "reorder":
                # 重排序操作
                self.reorder_category(source_path, target_item, event.position().toPoint())
            elif drop_type == "move_into" and target_item:
                # 移动到目标分类下
                target_path = target_item.category_path
                self.move_category_to_target(source_path, target_path)
            elif drop_type == "move_to_root":
                # 移动到根级别
                self.move_category_to_root(source_path)
            else:
                event.ignore()
                return

            event.acceptProposedAction()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"操作失败: {e}")
            event.ignore()

    def can_drop_on_target(self, source_path: str, target_path: str) -> bool:
        """检查是否可以将源分类放置到目标分类"""
        # 不能移动到自己
        if source_path == target_path:
            return False

        # 不能移动到自己的子目录
        if target_path.startswith(source_path + "/") or target_path.startswith(source_path + "\\"):
            return False

        return True

    def move_category_to_target(self, source_path: str, target_path: str):
        """将分类移动到目标分类下"""
        if not self.business_manager:
            raise ValueError("业务管理器未设置")

        # 获取源分类名称
        source_name = os.path.basename(source_path)

        # 执行移动
        new_path = self.business_manager.move_category(source_path, target_path, source_name)

        # 刷新树
        self.refresh_tree()

    def move_category_to_root(self, source_path: str):
        """将分类移动到根级别"""
        if not self.business_manager:
            raise ValueError("业务管理器未设置")

        # 获取源分类名称
        source_name = os.path.basename(source_path)

        # 移动到根目录
        root_path = self.business_manager.data_path
        new_path = self.business_manager.move_category(source_path, root_path, source_name)

        # 刷新树
        self.refresh_tree()

    def reorder_category(self, source_path: str, target_item, pos):
        """重排序分类"""
        if not self.business_manager:
            raise ValueError("业务管理器未设置")

        # 获取源分类和目标分类的父目录
        source_parent = os.path.dirname(source_path)
        target_parent = os.path.dirname(target_item.category_path)

        if source_parent != target_parent:
            raise ValueError("只能在同一父目录下重排序")

        # 获取源分类名称和目标分类名称
        source_name = os.path.basename(source_path)
        target_name = os.path.basename(target_item.category_path)

        # 获取当前父目录的排序信息
        order_info = self.business_manager.fs_manager.load_order_info(source_parent)
        current_categories = order_info.get("categories", [])

        # 如果当前没有排序信息，创建默认排序
        if not current_categories:
            # 获取所有子分类
            all_categories = [
                item for item in os.listdir(source_parent)
                if os.path.isdir(os.path.join(source_parent, item))
            ]
            current_categories = sorted(all_categories)

        # 确保源分类和目标分类都在列表中
        if source_name not in current_categories:
            current_categories.append(source_name)
        if target_name not in current_categories:
            current_categories.append(target_name)

        # 移除源分类
        current_categories.remove(source_name)

        # 找到目标分类的位置
        target_index = current_categories.index(target_name)

        # 判断插入位置
        item_rect = self.visualItemRect(target_item)
        if pos.y() < item_rect.center().y():
            # 插入到目标分类之前
            insert_index = target_index
        else:
            # 插入到目标分类之后
            insert_index = target_index + 1

        # 插入源分类
        current_categories.insert(insert_index, source_name)

        # 保存新的排序
        self.business_manager.save_category_order(source_parent, current_categories)

        # 刷新树
        self.refresh_tree()

    def refresh_tree(self):
        """刷新整个树"""
        if self.business_manager:
            # 保存当前展开状态
            expanded_paths = self.get_expanded_paths()

            # 重新填充树
            category_data = self.business_manager.get_category_tree()
            self.populate_from_data(category_data)

            # 恢复展开状态
            self.restore_expanded_paths(expanded_paths)

    def get_expanded_paths(self) -> set:
        """获取当前展开的路径"""
        expanded_paths = set()

        def collect_expanded(item):
            if item.isExpanded():
                path = item.data(0, Qt.ItemDataRole.UserRole)
                if path:
                    expanded_paths.add(path)

            for i in range(item.childCount()):
                collect_expanded(item.child(i))

        collect_expanded(self.invisibleRootItem())
        return expanded_paths

    def restore_expanded_paths(self, expanded_paths: set):
        """恢复展开状态"""
        def restore_expanded(item):
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and path in expanded_paths:
                item.setExpanded(True)

            for i in range(item.childCount()):
                restore_expanded(item.child(i))

        restore_expanded(self.invisibleRootItem())

    # ===== 视觉反馈方法 =====

    def highlight_drop_target(self, target_item):
        """高亮显示拖拽目标"""
        # 先清除之前的高亮
        self.clear_drop_indicator()

        if target_item and isinstance(target_item, EnhancedCategoryTreeItem):
            # 保存原始背景色
            self.drop_indicator_item = target_item
            self.original_background = target_item.background(0)

            # 设置高亮背景色（蓝色半透明）
            highlight_color = QColor(30, 144, 255, 80)  # 蓝色，透明度80
            target_item.setBackground(0, QBrush(highlight_color))

    def clear_drop_indicator(self):
        """清除拖拽指示器"""
        if self.drop_indicator_item and self.original_background is not None:
            # 恢复原始背景色
            self.drop_indicator_item.setBackground(0, self.original_background)

        self.drop_indicator_item = None
        self.original_background = None
        self.reorder_indicator_item = None
        self.reorder_indicator_position = None
        self.update()  # 触发重绘以清除重排序指示器

    def get_drop_type(self, pos, target_item, source_path):
        """判断拖拽类型"""
        if not target_item:
            return "move_to_root"

        if not isinstance(target_item, EnhancedCategoryTreeItem):
            return "invalid"

        # 获取源分类的父路径
        source_parent = os.path.dirname(source_path)
        target_parent = os.path.dirname(target_item.category_path)

        # 如果在同一父目录下，判断是重排序还是移动到目标内部
        if source_parent == target_parent:
            # 获取项目的矩形区域
            item_rect = self.visualItemRect(target_item)

            # 判断鼠标位置：如果在项目的边缘区域，则是重排序
            edge_threshold = 8  # 边缘区域的像素阈值

            if (pos.y() < item_rect.top() + edge_threshold or
                pos.y() > item_rect.bottom() - edge_threshold):
                return "reorder"
            else:
                # 检查是否可以移动到目标内部
                if self.can_drop_on_target(source_path, target_item.category_path):
                    return "move_into"
                else:
                    return "invalid"
        else:
            # 不同父目录，只能移动到目标内部
            if self.can_drop_on_target(source_path, target_item.category_path):
                return "move_into"
            else:
                return "invalid"

    def show_reorder_indicator(self, pos, target_item):
        """显示重排序指示器"""
        if not target_item or not isinstance(target_item, EnhancedCategoryTreeItem):
            return

        # 清除高亮指示器
        if self.drop_indicator_item:
            self.drop_indicator_item.setBackground(0, self.original_background)
            self.drop_indicator_item = None
            self.original_background = None

        # 设置重排序指示器
        self.reorder_indicator_item = target_item

        # 判断插入位置
        item_rect = self.visualItemRect(target_item)
        if pos.y() < item_rect.center().y():
            self.reorder_indicator_position = "above"
        else:
            self.reorder_indicator_position = "below"

        self.update()  # 触发重绘

    def paintEvent(self, event):
        """重写绘制事件以显示重排序指示器"""
        super().paintEvent(event)

        # 绘制重排序指示器
        if (self.reorder_indicator_item and self.reorder_indicator_position and
            self.drag_enabled):

            from PyQt6.QtGui import QPainter, QPen

            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 设置画笔（蓝色粗线）
            pen = QPen(QColor(30, 144, 255), 3)
            painter.setPen(pen)

            # 获取目标项的矩形区域
            item_rect = self.visualItemRect(self.reorder_indicator_item)

            # 计算指示器位置
            if self.reorder_indicator_position == "above":
                y = item_rect.top()
            else:  # "below"
                y = item_rect.bottom()

            # 绘制水平线
            x_start = item_rect.left()
            x_end = item_rect.right()
            painter.drawLine(x_start, y, x_end, y)

            painter.end()
