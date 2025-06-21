"""
增强的分类树组件
提供清晰的层级结构显示，包括展开/折叠指示器、层级缩进和子项计数
"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QBrush, QColor


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
        
    def setup_tree(self):
        """设置树的基本属性"""
        self.setHeaderLabel("分类目录")
        self.setColumnCount(1)
        self.setRootIsDecorated(True)  # 显示根节点的展开/折叠图标
        self.setIndentation(20)  # 设置缩进距离
        self.setUniformRowHeights(False)  # 允许不同行高
        
        # 设置样式
        self.setStyleSheet(self.get_enhanced_tree_style())
        
    def get_enhanced_tree_style(self):
        """获取增强的树样式"""
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
