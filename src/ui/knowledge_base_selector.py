"""
知识库选择器 - 参考Cherry Studio的知识库选择界面
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFrame, QCheckBox, QLineEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QWidget, QTreeWidgetItemIterator
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List, Dict, Any


class KnowledgeBaseItem(QFrame):
    """知识库项目组件"""
    
    toggled = pyqtSignal(str, bool)  # category_path, selected
    
    def __init__(self, category_path: str, category_name: str, entry_count: int, parent=None):
        super().__init__(parent)
        self.category_path = category_path
        self.category_name = category_name
        self.entry_count = entry_count
        self.is_selected = False
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # 选择框
        self.checkbox = QCheckBox()
        self.checkbox.toggled.connect(self.on_toggled)
        layout.addWidget(self.checkbox)
        
        # 图标
        icon_label = QLabel("📁")
        icon_label.setFixedSize(20, 20)
        layout.addWidget(icon_label)
        
        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # 名称
        self.name_label = QLabel(self.category_name)
        self.name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Medium))
        info_layout.addWidget(self.name_label)
        
        # 描述
        desc_text = f"{self.entry_count} 个条目"
        if self.category_path:
            desc_text += f" • {self.category_path}"
        self.desc_label = QLabel(desc_text)
        self.desc_label.setFont(QFont("Microsoft YaHei", 8))
        info_layout.addWidget(self.desc_label)
        
        layout.addLayout(info_layout, 1)
    
    def setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            KnowledgeBaseItem {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
                margin: 2px;
            }
            KnowledgeBaseItem:hover {
                background-color: #27272a;
                border-color: #3f3f46;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #27272a;
                border: 1px solid #52525b;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border: 1px solid #3b82f6;
                border-radius: 3px;
            }
            QLabel {
                color: #e4e4e7;
                background: transparent;
                border: none;
            }
        """)
    
    def on_toggled(self, checked: bool):
        """处理选择状态变化"""
        self.is_selected = checked
        self.toggled.emit(self.category_path, checked)
        
        # 更新样式
        if checked:
            self.setStyleSheet(self.styleSheet() + """
                KnowledgeBaseItem {
                    background-color: #1e3a8a;
                    border-color: #3b82f6;
                }
            """)
        else:
            self.setup_style()
    
    def set_selected(self, selected: bool):
        """设置选择状态"""
        self.checkbox.setChecked(selected)


class KnowledgeBaseSelectorDialog(QDialog):
    """知识库选择对话框"""
    
    def __init__(self, business_manager, selected_categories=None, parent=None):
        super().__init__(parent)
        self.business_manager = business_manager
        self.selected_categories = selected_categories or []
        self.knowledge_items = {}  # category_path -> KnowledgeBaseItem
        
        self.setup_dialog()
        self.setup_ui()
        self.load_knowledge_bases()
    
    def setup_dialog(self):
        """设置对话框"""
        self.setWindowTitle("选择知识库")
        self.setModal(True)
        self.resize(500, 600)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #0f0f0f;
                color: #e4e4e7;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QLabel {
                color: #e4e4e7;
            }
            QPushButton {
                background-color: #27272a;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3f3f46;
                border-color: #52525b;
            }
            QPushButton:pressed {
                background-color: #18181b;
            }
            #primaryBtn {
                background-color: #3b82f6;
                border-color: #3b82f6;
                color: white;
            }
            #primaryBtn:hover {
                background-color: #2563eb;
            }
            #primaryBtn:pressed {
                background-color: #1d4ed8;
            }
            QLineEdit {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 6px;
                padding: 8px;
                color: #e4e4e7;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
            QScrollArea {
                background-color: #0f0f0f;
                border: 1px solid #27272a;
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #27272a;
                border-radius: 8px;
                background-color: #0f0f0f;
            }
            QTabBar::tab {
                background-color: #18181b;
                color: #a1a1aa;
                border: 1px solid #27272a;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #0f0f0f;
                color: #e4e4e7;
                border-color: #3b82f6;
                border-bottom: 1px solid #0f0f0f;
            }
            QTabBar::tab:hover:!selected {
                background-color: #27272a;
                color: #e4e4e7;
            }
            QTreeWidget {
                background-color: #0f0f0f;
                border: none;
                color: #e4e4e7;
                alternate-background-color: #18181b;
                selection-background-color: #3b82f6;
            }
            QTreeWidget::item {
                padding: 4px;
                border: none;
            }
            QTreeWidget::item:hover {
                background-color: #27272a;
            }
            QTreeWidget::item:selected {
                background-color: #3b82f6;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
        """)
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("选择知识库")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 描述
        desc_label = QLabel("选择要用于RAG检索的知识库分类。AI将基于选中的分类中的条目来回答问题。")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #a1a1aa; font-size: 10pt;")
        layout.addWidget(desc_label)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入分类名称进行搜索...")
        self.search_edit.textChanged.connect(self.filter_knowledge_bases)
        # 防止回车键触发默认行为（全选）
        self.search_edit.returnPressed.connect(self.on_search_return_pressed)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, 1)

        # 列表视图标签页
        self.list_tab = QWidget()
        self.tab_widget.addTab(self.list_tab, "📋 列表视图")

        list_layout = QVBoxLayout(self.list_tab)
        list_layout.setContentsMargins(0, 8, 0, 0)

        # 知识库列表
        self.scroll_area = QListWidget()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_layout.addWidget(self.scroll_area)

        # 树视图标签页
        self.tree_tab = QWidget()
        self.tab_widget.addTab(self.tree_tab, "🌳 目录树")

        tree_layout = QVBoxLayout(self.tree_tab)
        tree_layout.setContentsMargins(0, 8, 0, 0)

        # 知识库树
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("知识库分类")
        self.tree_widget.setRootIsDecorated(True)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.itemChanged.connect(self.on_tree_item_changed)
        tree_layout.addWidget(self.tree_widget)
        
        # 选择统计
        self.stats_label = QLabel("已选择 0 个知识库")
        self.stats_label.setStyleSheet("color: #a1a1aa; font-size: 9pt;")
        layout.addWidget(self.stats_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 全选/全不选
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = QPushButton("全不选")
        self.select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(self.select_none_btn)
        
        button_layout.addStretch()
        
        # 确定/取消
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setObjectName("primaryBtn")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def load_knowledge_bases(self):
        """加载知识库"""
        try:
            # 清空现有项目
            self.scroll_area.clear()
            self.knowledge_items.clear()

            # 获取所有分类 - 使用更直接的方法
            all_categories = self._get_all_categories()

            if not all_categories:
                # 如果没有分类，显示提示信息
                self._show_no_categories_message()
                return

            # 为每个分类创建知识库项目
            for category_info in all_categories:
                category_path = category_info["path"]
                category_name = category_info["name"]
                entry_count = category_info["entry_count"]

                # 创建知识库项目
                item = KnowledgeBaseItem(category_path, category_name, entry_count)
                item.toggled.connect(self.on_item_toggled)

                # 检查是否已选择
                if category_path in self.selected_categories:
                    item.set_selected(True)

                # 添加到列表
                list_item = QListWidgetItem()
                list_item.setSizeHint(item.sizeHint())
                self.scroll_area.addItem(list_item)
                self.scroll_area.setItemWidget(list_item, item)

                self.knowledge_items[category_path] = item

            # 同时加载到树视图
            self.load_tree_view(all_categories)

            self.update_stats()
            print(f"成功加载 {len(all_categories)} 个知识库分类")

        except Exception as e:
            print(f"加载知识库失败: {e}")
            import traceback
            traceback.print_exc()

    def load_tree_view(self, categories):
        """加载树视图"""
        try:
            self.tree_widget.clear()

            # 按路径组织分类为树结构
            tree_data = self._organize_categories_as_tree(categories)

            # 创建树节点
            for root_name, children in tree_data.items():
                root_item = QTreeWidgetItem(self.tree_widget)
                root_item.setText(0, root_name)
                root_item.setFlags(root_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                root_item.setCheckState(0, Qt.CheckState.Unchecked)

                # 存储分类信息
                root_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "path": root_name,
                    "entry_count": children.get("entry_count", 0)
                })

                # 检查是否已选择
                if root_name in self.selected_categories:
                    root_item.setCheckState(0, Qt.CheckState.Checked)

                # 添加子分类（如果有）
                self._add_tree_children(root_item, children.get("children", {}))

            # 展开所有项目
            self.tree_widget.expandAll()

        except Exception as e:
            print(f"加载树视图失败: {e}")

    def _organize_categories_as_tree(self, categories):
        """将分类组织为树结构"""
        tree_data = {}

        for cat in categories:
            path = cat["path"]
            name = cat["name"]
            entry_count = cat["entry_count"]

            # 简单处理：如果路径包含分隔符，创建层级结构
            if "/" in path or "\\" in path:
                parts = path.replace("\\", "/").split("/")
                current_level = tree_data

                for i, part in enumerate(parts):
                    if part not in current_level:
                        current_level[part] = {
                            "entry_count": 0,
                            "children": {}
                        }

                    if i == len(parts) - 1:  # 最后一级
                        current_level[part]["entry_count"] = entry_count

                    current_level = current_level[part]["children"]
            else:
                # 直接作为根级分类
                tree_data[path] = {
                    "entry_count": entry_count,
                    "children": {}
                }

        return tree_data

    def _add_tree_children(self, parent_item, children_data):
        """添加树的子节点"""
        for child_name, child_info in children_data.items():
            child_item = QTreeWidgetItem(parent_item)
            child_item.setText(0, child_name)
            child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            child_item.setCheckState(0, Qt.CheckState.Unchecked)

            # 构建完整路径
            parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
            if parent_data:
                full_path = f"{parent_data['path']}/{child_name}"
            else:
                full_path = child_name

            child_item.setData(0, Qt.ItemDataRole.UserRole, {
                "path": full_path,
                "entry_count": child_info.get("entry_count", 0)
            })

            # 检查是否已选择
            if full_path in self.selected_categories:
                child_item.setCheckState(0, Qt.CheckState.Checked)

            # 递归添加子节点
            if child_info.get("children"):
                self._add_tree_children(child_item, child_info["children"])

    def on_tree_item_changed(self, item, column):
        """处理树项目状态变化"""
        if column == 0:  # 只处理第一列的复选框
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data:
                category_path = item_data["path"]
                is_checked = item.checkState(0) == Qt.CheckState.Checked

                # 更新选择状态
                if is_checked and category_path not in self.selected_categories:
                    self.selected_categories.append(category_path)
                elif not is_checked and category_path in self.selected_categories:
                    self.selected_categories.remove(category_path)

                # 同步更新列表视图中对应的项目
                if category_path in self.knowledge_items:
                    self.knowledge_items[category_path].set_selected(is_checked)

                self.update_stats()

    def _get_all_categories(self):
        """获取所有分类信息"""
        categories = []
        try:
            # 方法1：尝试使用 get_categories 方法
            if hasattr(self.business_manager, 'get_categories'):
                raw_categories = self.business_manager.get_categories()
                if raw_categories:
                    for cat in raw_categories:
                        category_path = cat.get("path", "")
                        category_name = cat.get("name", "未知分类")
                        entry_count = self._get_entry_count(category_path)

                        if entry_count > 0:  # 只显示有条目的分类
                            categories.append({
                                "path": category_path,
                                "name": category_name,
                                "entry_count": entry_count
                            })

            # 方法2：如果上面没有结果，尝试直接从数据目录读取
            if not categories:
                categories = self._scan_data_directory()

        except Exception as e:
            print(f"获取分类信息失败: {e}")
            # 方法3：最后的备选方案
            categories = self._get_fallback_categories()

        return categories

    def _get_entry_count(self, category_path):
        """获取分类下的条目数量"""
        try:
            if hasattr(self.business_manager, 'list_entries_in_category'):
                entries = self.business_manager.list_entries_in_category(category_path)
                return len(entries) if entries else 0
            elif hasattr(self.business_manager, 'get_entries'):
                # 尝试其他方法
                all_entries = self.business_manager.get_entries()
                count = 0
                for entry in all_entries:
                    if hasattr(entry, 'category') and entry.category == category_path:
                        count += 1
                return count
            else:
                return 1  # 默认假设有条目
        except:
            return 0

    def _scan_data_directory(self):
        """扫描数据目录获取分类"""
        categories = []
        try:
            import os
            data_path = getattr(self.business_manager, 'data_path', None)
            if data_path and os.path.exists(data_path):
                # 扫描数据目录中的分类文件夹
                for item in os.listdir(data_path):
                    item_path = os.path.join(data_path, item)
                    if os.path.isdir(item_path):
                        # 检查是否有条目文件
                        entry_files = [f for f in os.listdir(item_path) if f.endswith('.json')]
                        if entry_files:
                            categories.append({
                                "path": item,
                                "name": item,
                                "entry_count": len(entry_files)
                            })
        except Exception as e:
            print(f"扫描数据目录失败: {e}")

        return categories

    def _get_fallback_categories(self):
        """获取备选分类列表"""
        # 提供一些默认的分类选项
        return [
            {"path": "人物档案", "name": "人物档案", "entry_count": 1},
            {"path": "世界观", "name": "世界观", "entry_count": 1},
            {"path": "情节设定", "name": "情节设定", "entry_count": 1},
            {"path": "背景设定", "name": "背景设定", "entry_count": 1},
        ]

    def _show_no_categories_message(self):
        """显示无分类消息"""
        from PyQt6.QtWidgets import QLabel

        message_label = QLabel("暂无可用的知识库分类\n\n请先在主界面创建一些分类和条目")
        message_label.setStyleSheet("""
            QLabel {
                color: #a1a1aa;
                font-size: 12pt;
                text-align: center;
                padding: 40px;
            }
        """)
        message_label.setWordWrap(True)

        list_item = QListWidgetItem()
        list_item.setSizeHint(message_label.sizeHint())
        self.scroll_area.addItem(list_item)
        self.scroll_area.setItemWidget(list_item, message_label)
    
    def on_item_toggled(self, category_path: str, selected: bool):
        """处理项目选择状态变化"""
        if selected and category_path not in self.selected_categories:
            self.selected_categories.append(category_path)
        elif not selected and category_path in self.selected_categories:
            self.selected_categories.remove(category_path)

        # 同步更新树视图
        self._sync_tree_selection(category_path, selected)

        self.update_stats()

    def _sync_tree_selection(self, category_path: str, selected: bool):
        """同步树视图选择状态"""
        try:
            # 遍历树视图中的所有项目
            iterator = QTreeWidgetItemIterator(self.tree_widget)
            while iterator.value():
                item = iterator.value()
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                if item_data and item_data.get("path") == category_path:
                    # 暂时断开信号连接，避免循环触发
                    self.tree_widget.itemChanged.disconnect()
                    item.setCheckState(0, Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)
                    self.tree_widget.itemChanged.connect(self.on_tree_item_changed)
                    break
                iterator += 1
        except Exception as e:
            print(f"同步树视图选择状态失败: {e}")
    
    def update_stats(self):
        """更新选择统计"""
        count = len(self.selected_categories)
        self.stats_label.setText(f"已选择 {count} 个知识库")
    
    def filter_knowledge_bases(self, text: str):
        """过滤知识库"""
        text = text.lower().strip()

        # 如果搜索文本为空，显示所有项目
        if not text:
            for i in range(self.scroll_area.count()):
                item = self.scroll_area.item(i)
                if item:
                    item.setHidden(False)
            return

        # 过滤项目
        visible_count = 0
        for i in range(self.scroll_area.count()):
            item = self.scroll_area.item(i)
            if item:
                widget = self.scroll_area.itemWidget(item)
                if isinstance(widget, KnowledgeBaseItem):
                    # 检查名称和路径是否包含搜索文本
                    name_match = text in widget.category_name.lower()
                    path_match = text in widget.category_path.lower()
                    visible = name_match or path_match

                    item.setHidden(not visible)
                    if visible:
                        visible_count += 1
                else:
                    # 对于非KnowledgeBaseItem（如提示消息），也隐藏
                    item.setHidden(True)

        # 如果没有匹配项，显示"无结果"消息
        if visible_count == 0 and text:
            self._show_no_results_message(text)

    def _show_no_results_message(self, search_text: str):
        """显示无搜索结果消息"""
        from PyQt6.QtWidgets import QLabel

        # 检查是否已经有"无结果"消息
        for i in range(self.scroll_area.count()):
            item = self.scroll_area.item(i)
            if item:
                widget = self.scroll_area.itemWidget(item)
                if isinstance(widget, QLabel) and "无匹配结果" in widget.text():
                    return  # 已经有消息了

        # 创建无结果消息
        message_label = QLabel(f"无匹配结果\n\n搜索 '{search_text}' 没有找到相关的知识库分类")
        message_label.setStyleSheet("""
            QLabel {
                color: #71717a;
                font-size: 11pt;
                text-align: center;
                padding: 30px;
            }
        """)
        message_label.setWordWrap(True)

        list_item = QListWidgetItem()
        list_item.setSizeHint(message_label.sizeHint())
        self.scroll_area.addItem(list_item)
        self.scroll_area.setItemWidget(list_item, message_label)
    
    def select_all(self):
        """全选"""
        # 更新列表视图
        for item in self.knowledge_items.values():
            item.set_selected(True)

        # 更新树视图
        self._set_all_tree_items_checked(True)

    def select_none(self):
        """全不选"""
        # 更新列表视图
        for item in self.knowledge_items.values():
            item.set_selected(False)

        # 更新树视图
        self._set_all_tree_items_checked(False)

    def _set_all_tree_items_checked(self, checked: bool):
        """设置所有树项目的选中状态"""
        try:
            # 暂时断开信号连接
            self.tree_widget.itemChanged.disconnect()

            iterator = QTreeWidgetItemIterator(self.tree_widget)
            while iterator.value():
                item = iterator.value()
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                if item_data:  # 只处理有数据的项目
                    item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
                iterator += 1

            # 重新连接信号
            self.tree_widget.itemChanged.connect(self.on_tree_item_changed)

        except Exception as e:
            print(f"设置树项目选中状态失败: {e}")
            # 确保重新连接信号
            try:
                self.tree_widget.itemChanged.connect(self.on_tree_item_changed)
            except:
                pass
    
    def on_search_return_pressed(self):
        """处理搜索框回车键事件"""
        # 什么都不做，防止触发默认的对话框接受行为
        pass

    def get_selected_categories(self) -> List[str]:
        """获取选中的分类"""
        return self.selected_categories.copy()
