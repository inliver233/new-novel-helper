from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QTreeView, QMenu, QInputDialog, QMessageBox, QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt, QDir, QPoint
from PyQt6.QtGui import QFileSystemModel, QAction
from ..core.business_manager import BusinessManager
from .search_dialog import SearchDialog
from .ui_styles import UIStyles
from .ui_components import UIComponents

class MainWindow(QMainWindow):
    """应用程序的主窗口"""

    def __init__(self, data_path: str):
        super().__init__()
        self.setWindowTitle("LoreMaster - 小说辅助工具")
        self.setGeometry(100, 100, 1400, 900)

        # 设置应用样式
        self.setup_styles()

        # 初始化业务管理器
        self.business_manager = BusinessManager(data_path)
        self.data_path = data_path

        # 当前选中的条目
        self.current_entry = None
        self.current_category_path = None
        self.is_content_modified = False

        # 创建菜单栏和工具栏
        UIComponents.create_menu_bar(self)
        UIComponents.create_tool_bar(self)

        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # 创建一个水平分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：分类树面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(12)

        # 分类树标题
        category_title = UIComponents.create_category_title_label()
        left_layout.addWidget(category_title)

        self.category_tree = QTreeView()
        self.setup_category_tree(data_path)
        left_layout.addWidget(self.category_tree)

        splitter.addWidget(left_panel)

        # 中间：条目列表面板
        middle_panel, self.entry_list = UIComponents.create_entry_panel(self)
        splitter.addWidget(middle_panel)

        # 右侧：内容编辑器面板
        right_panel, self.title_edit, self.tags_edit, self.content_editor = UIComponents.create_editor_panel(self)
        splitter.addWidget(right_panel)

        # 设置分割器的初始大小比例和样式
        splitter.setSizes([280, 320, 700])
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)

        # 创建状态栏
        self.status_bar = UIComponents.create_status_bar(self)

        # 连接信号
        self.content_editor.textChanged.connect(self.on_content_changed)

        # 显示统计信息
        self.update_status_bar()

    def setup_styles(self):
        """设置应用程序样式"""
        # 设置应用程序字体
        font = UIStyles.get_application_font()
        self.setFont(font)

        # 设置主样式表
        self.setStyleSheet(UIStyles.get_main_stylesheet())











    def setup_category_tree(self, data_path: str):
        """设置分类树以显示文件系统目录"""
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(data_path)
        self.fs_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.Dirs)

        self.category_tree.setModel(self.fs_model)
        self.category_tree.setRootIndex(self.fs_model.index(data_path))
        
        self.category_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.category_tree.customContextMenuRequested.connect(self.on_category_context_menu)
        
        self.category_tree.selectionModel().selectionChanged.connect(self.on_category_selection_changed)

        for i in range(1, self.fs_model.columnCount()):
            self.category_tree.hideColumn(i)
    
    def on_category_selection_changed(self, selected, deselected):
        """当分类选择变化时，更新条目列表"""
        try:
            # 1. 保存对前一个条目的任何挂起更改
            if self.is_content_modified and self.current_entry:
                self.save_current_entry()
        except Exception as e:
            # 在后台打印错误，避免不必要地打扰用户
            print(f"切换分类时保存旧条目失败: {e}")

        # 2. 重置UI和状态，这是修复BUG的关键步骤
        # 在加载新分类的任何内容之前，清除编辑器和条目列表。
        # 这可以防止使用新分类路径和旧条目ID的无效组合。
        self.clear_editor()
        self.entry_list.clear()
        
        # 3. 获取新选择的分类路径
        indexes = self.category_tree.selectionModel().selectedIndexes()
        if not indexes:
            self.current_category_path = None
            return

        # 4. 更新当前分类路径并加载其条目
        selected_index = indexes[0]
        self.current_category_path = self.fs_model.filePath(selected_index)
        self.update_entry_list()

    def update_entry_list(self):
        """更新条目列表"""
        self.entry_list.clear()

        if not self.current_category_path:
            return

        try:
            entries = self.business_manager.get_entries_in_category(self.current_category_path)
            for entry in entries:
                item = QListWidgetItem(entry.title)
                item.setData(Qt.ItemDataRole.UserRole, entry.uuid)
                self.entry_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载条目列表失败: {e}")

    def on_entry_selection_changed(self):
        """当条目选择变化时，更新内容编辑器"""
        try:
            # 保存当前条目
            if self.is_content_modified and self.current_entry and self.current_category_path:
                self.save_current_entry()
        except Exception as e:
            print(f"保存当前条目时出错: {e}")

        current_item = self.entry_list.currentItem()
        if not current_item or not self.current_category_path:
            self.clear_editor()
            return

        entry_uuid = current_item.data(Qt.ItemDataRole.UserRole)

        try:
            self.current_entry = self.business_manager.get_entry(self.current_category_path, entry_uuid)
            self.load_entry_to_editor()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载条目失败: {e}")
            self.clear_editor()

    def load_entry_to_editor(self):
        """将条目加载到编辑器"""
        if not self.current_entry:
            return

        # 阻止信号触发
        self.title_edit.blockSignals(True)
        self.tags_edit.blockSignals(True)
        self.content_editor.blockSignals(True)

        # 设置内容
        self.title_edit.setText(self.current_entry.title)
        self.tags_edit.setText(", ".join(self.current_entry.tags))
        self.content_editor.setText(self.current_entry.content)

        # 恢复信号
        self.title_edit.blockSignals(False)
        self.tags_edit.blockSignals(False)
        self.content_editor.blockSignals(False)

        self.is_content_modified = False

    def clear_editor(self):
        """清空编辑器"""
        self.current_entry = None
        self.title_edit.clear()
        self.tags_edit.clear()
        self.content_editor.clear()
        self.is_content_modified = False

    def on_content_changed(self):
        """内容变化时的处理"""
        self.is_content_modified = True

    def on_title_changed(self):
        """标题变化时的处理"""
        self.is_content_modified = True

    def on_tags_changed(self):
        """标签变化时的处理"""
        self.is_content_modified = True

    def create_new_entry(self):
        """创建新条目"""
        if not self.current_category_path:
            QMessageBox.warning(self, "提示", "请先选择一个分类")
            return

        # 保存当前条目
        if self.is_content_modified:
            self.save_current_entry()

        title, ok = QInputDialog.getText(self, "新建条目", "请输入条目标题:")
        if not ok or not title.strip():
            return

        try:
            entry = self.business_manager.create_entry(
                self.current_category_path,
                title.strip()
            )

            # 更新条目列表
            self.update_entry_list()

            # 选中新创建的条目
            for i in range(self.entry_list.count()):
                item = self.entry_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == entry.uuid:
                    self.entry_list.setCurrentItem(item)
                    break

            QMessageBox.information(self, "成功", f"条目 '{title}' 创建成功")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建条目失败: {e}")

    def save_current_entry(self):
        """保存当前条目"""
        if not self.current_entry or not self.current_category_path:
            return

        try:
            # 获取编辑器中的内容
            title = self.title_edit.text().strip()
            content = self.content_editor.toPlainText()
            tags_text = self.tags_edit.text().strip()
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            if not title:
                # 如果标题为空，使用原标题
                title = self.current_entry.title

            # 更新条目
            self.business_manager.update_entry(
                self.current_category_path,
                self.current_entry.uuid,
                title=title,
                content=content,
                tags=tags
            )

            # 更新当前条目对象
            self.current_entry.update_content(title=title, content=content, tags=tags)

            # 更新条目列表中的标题
            current_item = self.entry_list.currentItem()
            if current_item:
                current_item.setText(title)

            self.is_content_modified = False
            self.update_status_bar()

        except Exception as e:
            print(f"保存条目失败: {e}")
            # 不显示错误对话框，避免在切换时干扰用户

    def delete_current_entry(self):
        """删除当前条目"""
        current_item = self.entry_list.currentItem()
        if not current_item or not self.current_category_path:
            QMessageBox.warning(self, "提示", "请先选择要删除的条目")
            return

        entry_title = current_item.text()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"您确定要删除条目 '{entry_title}' 吗？此操作无法撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                entry_uuid = current_item.data(Qt.ItemDataRole.UserRole)
                self.business_manager.delete_entry(self.current_category_path, entry_uuid)

                # 从列表中移除
                row = self.entry_list.row(current_item)
                self.entry_list.takeItem(row)

                # 清空编辑器
                self.clear_editor()

                QMessageBox.information(self, "成功", f"条目 '{entry_title}' 已删除")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除条目失败: {e}")

    def rename_current_entry(self):
        """重命名当前选中的条目"""
        current_item = self.entry_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要重命名的条目")
            return

        if not self.current_category_path:
            QMessageBox.warning(self, "提示", "请先选择一个分类")
            return

        # 获取当前条目信息
        entry_uuid = current_item.data(Qt.ItemDataRole.UserRole)
        old_title = current_item.text()

        # 弹出输入对话框
        new_title, ok = QInputDialog.getText(self, "重命名条目", "请输入新标题:", text=old_title)

        if not ok or not new_title.strip():
            return

        if new_title.strip() == old_title:
            return  # 标题没有变化

        try:
            # 更新条目标题
            self.business_manager.update_entry(
                self.current_category_path,
                entry_uuid,
                title=new_title.strip()
            )

            # 更新列表项显示
            current_item.setText(new_title.strip())

            # 如果当前正在编辑这个条目，也更新编辑器中的标题
            if self.current_entry and self.current_entry.uuid == entry_uuid:
                self.current_entry.title = new_title.strip()
                self.title_edit.setText(new_title.strip())

            QMessageBox.information(self, "成功", f"条目已重命名为 '{new_title.strip()}'")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"重命名条目失败: {e}")

    def on_entry_context_menu(self, point: QPoint):
        """条目列表右键菜单"""
        item = self.entry_list.itemAt(point)

        menu = QMenu(self)

        # 新建条目
        new_entry_action = QAction("新建条目", self)
        new_entry_action.triggered.connect(self.create_new_entry)
        menu.addAction(new_entry_action)

        if item:
            # 如果右键点击在条目上，添加重命名和删除选项
            menu.addSeparator()

            rename_action = QAction("重命名条目", self)
            rename_action.triggered.connect(self.rename_current_entry)
            menu.addAction(rename_action)

            delete_action = QAction("删除条目", self)
            delete_action.triggered.connect(self.delete_current_entry)
            menu.addAction(delete_action)

        menu.exec(self.entry_list.viewport().mapToGlobal(point))

    def update_status_bar(self):
        """更新状态栏"""
        try:
            stats = self.business_manager.get_statistics()
            status_text = f"分类: {stats['total_categories']} | 条目: {stats['total_entries']} | 总字数: {stats['total_words']}"
            self.status_bar.showMessage(status_text)
        except Exception:
            self.status_bar.showMessage("就绪")

    def on_category_context_menu(self, point: QPoint):
        """当在分类树上右键单击时显示上下文菜单"""
        menu = QMenu(self)

        new_category_action = QAction("新建分类...", self)
        new_category_action.triggered.connect(self.create_new_category)
        menu.addAction(new_category_action)

        if self.category_tree.currentIndex().isValid():
            menu.addSeparator()
            rename_action = QAction("重命名分类...", self)
            rename_action.triggered.connect(self.rename_category)
            menu.addAction(rename_action)

            delete_action = QAction("删除分类", self)
            delete_action.triggered.connect(self.delete_category)
            menu.addAction(delete_action)

        menu.exec(self.category_tree.viewport().mapToGlobal(point))

    def create_new_category(self):
        """创建一个新的分类（文件夹）"""
        current_index = self.category_tree.currentIndex()

        if not current_index.isValid():
            parent_path = None
        else:
            parent_path = self.fs_model.filePath(current_index)

        category_name, ok = QInputDialog.getText(self, "新建分类", "请输入分类名称:")

        if ok and category_name.strip():
            try:
                self.business_manager.create_category(category_name.strip(), parent_path)
                QMessageBox.information(self, "成功", f"分类 '{category_name}' 创建成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建分类失败: {e}")

    def rename_category(self):
        """重命名选中的分类"""
        current_index = self.category_tree.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, "提示", "请先选择要重命名的分类")
            return

        old_path = self.fs_model.filePath(current_index)
        old_name = self.fs_model.fileName(current_index)

        new_name, ok = QInputDialog.getText(self, "重命名分类", "请输入新名称:", text=old_name)

        if ok and new_name.strip() and new_name.strip() != old_name:
            try:
                self.business_manager.rename_category(old_path, new_name.strip())
                QMessageBox.information(self, "成功", f"分类已重命名为 '{new_name}'")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名分类失败: {e}")

    def delete_category(self):
        """删除选中的分类"""
        current_index = self.category_tree.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, "提示", "请先选择要删除的分类")
            return

        path_to_delete = self.fs_model.filePath(current_index)
        category_name = self.fs_model.fileName(current_index)

        # 检查分类是否为空
        try:
            entries = self.business_manager.get_entries_in_category(path_to_delete)
            subcategories = self.business_manager.get_categories(path_to_delete)

            if entries or subcategories:
                reply = QMessageBox.question(
                    self,
                    "确认删除",
                    f"分类 '{category_name}' 不为空，包含 {len(entries)} 个条目和 {len(subcategories)} 个子分类。\n"
                    f"您确定要永久删除该分类及其所有内容吗？此操作无法撤销。",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                force = True
            else:
                reply = QMessageBox.question(
                    self,
                    "确认删除",
                    f"您确定要删除分类 '{category_name}' 吗？此操作无法撤销。",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                force = False

            if reply == QMessageBox.StandardButton.Yes:
                self.business_manager.delete_category(path_to_delete, force)

                # 清空编辑器和条目列表
                self.clear_editor()
                self.entry_list.clear()
                self.current_category_path = None

                QMessageBox.information(self, "成功", f"分类 '{category_name}' 已删除")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除分类失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_content_modified:
            reply = QMessageBox.question(
                self,
                "保存更改",
                "当前条目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_current_entry()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def open_search_dialog(self):
        """打开搜索对话框"""
        dialog = SearchDialog(self.business_manager, self)
        dialog.entry_selected.connect(self.open_entry_from_search)
        dialog.exec()

    def open_entry_from_search(self, category_path: str, entry_uuid: str):
        """从搜索结果打开条目"""
        try:
            # 在分类树中选择对应的分类
            index = self.fs_model.index(category_path)
            if index.isValid():
                self.category_tree.setCurrentIndex(index)
                self.current_category_path = category_path
                self.update_entry_list()

                # 在条目列表中选择对应的条目
                for i in range(self.entry_list.count()):
                    item = self.entry_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == entry_uuid:
                        self.entry_list.setCurrentItem(item)
                        break

        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开条目失败: {e}")