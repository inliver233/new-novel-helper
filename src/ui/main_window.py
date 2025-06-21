import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QMenu, QInputDialog, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QAction
from ..core.business_manager import BusinessManager
from ..core.config_manager import ConfigManager
from .search_dialog import SearchDialog
from .settings_dialog import SettingsDialog
from .ui_styles import UIStyles
from .ui_components import UIComponents
from .enhanced_category_tree import EnhancedCategoryTree
from .entry_window_manager import EntryWindowManager
from .context_menu_helper import ContextMenuHelper
from .status_indicator import StatusIndicatorBar, SaveStatusIndicator
from ..utils.logger import LoggerConfig, log_exception
from ..utils.time_utils import format_datetime_chinese, format_word_count, format_tags_display, count_text_stats

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

        # 初始化配置管理器
        self.config_manager = ConfigManager(data_path)

        # 初始化日志记录器
        self.logger = LoggerConfig.get_logger("main_window")

        # 初始化条目窗口管理器
        self.entry_window_manager = EntryWindowManager(self.business_manager, self.config_manager)
        self.setup_entry_window_manager()

        # 初始化上下文菜单辅助类
        self.context_menu_helper = ContextMenuHelper(self)

        # 当前选中的条目
        self.current_entry = None
        self.current_category_path = None
        self.is_content_modified = False

        # 拖拽模式相关
        self.adjust_action = None  # 调整按钮的引用

        # 自动保存相关
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_current_entry)
        self.auto_save_timer.setSingleShot(True)

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

        self.category_tree = EnhancedCategoryTree()
        self.category_tree.set_business_manager(self.business_manager)
        self.setup_category_tree()
        left_layout.addWidget(self.category_tree)

        splitter.addWidget(left_panel)

        # 中间：条目列表面板
        middle_panel, self.entry_list = UIComponents.create_entry_panel(self)
        self.entry_list.set_business_manager(self.business_manager)
        self.entry_list.set_entry_window_manager(self.entry_window_manager)
        splitter.addWidget(middle_panel)

        # 右侧：内容编辑器面板
        right_panel, self.title_edit, self.tags_edit, self.content_editor, self.details_info_label, self.status_indicator_bar = UIComponents.create_editor_panel(self)
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

        # 显示欢迎消息
        self.show_status_message("LoreMaster 已就绪", 3000)

    def setup_entry_window_manager(self):
        """设置条目窗口管理器"""
        # 连接信号
        self.entry_window_manager.entry_updated_in_window.connect(self.on_entry_updated_in_window)
        self.entry_window_manager.entry_deleted_in_window.connect(self.on_entry_deleted_in_window)

    def setup_styles(self):
        """设置应用程序样式"""
        # 设置应用程序字体
        font = UIStyles.get_application_font()
        self.setFont(font)

        # 设置主样式表
        self.setStyleSheet(UIStyles.get_main_stylesheet())

    def show_status_message(self, message: str, timeout: int = 5000):
        """在状态栏显示消息

        Args:
            message: 要显示的消息
            timeout: 消息显示时间（毫秒），0表示永久显示
        """
        self.status_bar.showMessage(message, timeout)
        if timeout > 0:
            self.logger.info(f"状态栏消息: {message}")

    def show_operation_result(self, operation: str, success: bool, details: str = ""):
        """显示操作结果

        Args:
            operation: 操作名称
            success: 是否成功
            details: 详细信息
        """
        if success:
            message = f"{operation}成功"
            if details:
                message += f": {details}"
            self.show_status_message(message, 3000)
        else:
            message = f"{operation}失败"
            if details:
                message += f": {details}"
            self.show_status_message(message, 5000)
            self.logger.warning(f"操作失败 - {operation}: {details}")

    def setup_category_tree(self):
        """设置并填充分类树"""
        self.populate_category_tree()

        self.category_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.category_tree.customContextMenuRequested.connect(self.context_menu_helper.show_category_context_menu)
        self.category_tree.itemSelectionChanged.connect(self.on_category_selection_changed)

    def populate_category_tree(self):
        """使用从文件系统获取的数据填充分类树"""
        try:
            category_data = self.business_manager.get_category_tree()
            self.category_tree.populate_from_data(category_data)
        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.critical(self, "错误", f"无法访问分类目录: {e}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            QMessageBox.critical(self, "错误", f"分类数据格式错误: {e}")

    def on_category_selection_changed(self):
        """当分类选择变化时，更新条目列表"""
        try:
            if self.is_content_modified and self.current_entry:
                self.save_current_entry()
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.show_operation_result("自动保存", False, f"文件系统错误: {e}")
            log_exception(self.logger, "切换分类时自动保存", e)
        except (json.JSONDecodeError, ValueError) as e:
            self.show_operation_result("自动保存", False, f"数据格式错误: {e}")
            log_exception(self.logger, "切换分类时自动保存", e)

        self.clear_editor()
        self.entry_list.clear()
        
        selected_items = self.category_tree.selectedItems()
        if not selected_items:
            self.current_category_path = None
            self.status_bar.clearMessage() # 清除路径显示
            self.update_status_bar() # 恢复默认统计信息
            return

        selected_item = selected_items[0]
        self.current_category_path = selected_item.data(0, Qt.ItemDataRole.UserRole)

        # 设置条目列表的当前分类路径
        self.entry_list.set_current_category_path(self.current_category_path)

        self.update_entry_list()

        # 在状态栏显示完整路径
        self.status_bar.showMessage(f"当前路径: {self.current_category_path}")

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
        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.warning(self, "错误", f"无法访问条目目录: {e}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            QMessageBox.warning(self, "错误", f"条目数据格式错误: {e}")

    def on_entry_selection_changed(self):
        """当条目选择变化时，更新内容编辑器"""
        try:
            # 保存当前条目
            if self.is_content_modified and self.current_entry and self.current_category_path:
                self.save_current_entry()
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.show_operation_result("自动保存", False, f"文件系统错误: {e}")
            log_exception(self.logger, "切换条目时自动保存", e)
        except (json.JSONDecodeError, ValueError) as e:
            self.show_operation_result("自动保存", False, f"数据格式错误: {e}")
            log_exception(self.logger, "切换条目时自动保存", e)

        current_item = self.entry_list.currentItem()
        if not current_item or not self.current_category_path:
            self.clear_editor()
            return

        entry_uuid = current_item.data(Qt.ItemDataRole.UserRole)

        try:
            self.current_entry = self.business_manager.get_entry(self.current_category_path, entry_uuid)
            self.load_entry_to_editor()
        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.warning(self, "错误", f"无法访问条目文件: {e}")
            self.clear_editor()
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            QMessageBox.warning(self, "错误", f"条目数据格式错误: {e}")
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

        # 更新详细信息显示
        self.update_entry_details()

        # 恢复信号
        self.title_edit.blockSignals(False)
        self.tags_edit.blockSignals(False)
        self.content_editor.blockSignals(False)

        self.is_content_modified = False

        # 清除状态指示器（加载条目时不应显示未保存状态）
        if self.config_manager.is_status_indicators_enabled():
            self.status_indicator_bar.hide_indicator("save_status")
            self.status_indicator_bar.hide_indicator("auto_save")

    def clear_editor(self):
        """清空编辑器"""
        self.current_entry = None
        self.title_edit.clear()
        self.tags_edit.clear()
        self.content_editor.clear()
        self.details_info_label.setText("请选择一个条目查看详细信息")
        self.is_content_modified = False

        # 清除状态指示器
        if self.config_manager.is_status_indicators_enabled():
            self.status_indicator_bar.hide_indicator("save_status")
            self.status_indicator_bar.hide_indicator("auto_save")

    def update_entry_details(self):
        """更新条目详细信息显示"""
        if not self.current_entry:
            self.details_info_label.setText("请选择一个条目查看详细信息")
            return

        # 获取条目信息
        created_at = format_datetime_chinese(self.current_entry.get_created_at())
        updated_at = format_datetime_chinese(self.current_entry.get_updated_at())

        # 统计文本信息
        stats = count_text_stats(self.current_entry.content)

        # 构建详细信息文本
        details_text = f"""创建: {created_at} | 更新: {updated_at}

字数: {stats['chinese_chars']} | 英文: {stats['english_words']} | 符号: {stats['symbols']} | 字符: {stats['total_chars']} | 行数: {stats['lines']}"""

        self.details_info_label.setText(details_text)

    def update_entry_details_realtime(self):
        """实时更新条目详细信息（主要是字数统计）"""
        if not self.current_entry:
            return

        # 获取当前编辑器中的内容
        current_content = self.content_editor.toPlainText()

        # 获取条目信息
        created_at = format_datetime_chinese(self.current_entry.get_created_at())
        updated_at = format_datetime_chinese(self.current_entry.get_updated_at())

        # 统计当前内容
        stats = count_text_stats(current_content)

        # 构建详细信息文本
        details_text = f"""创建: {created_at} | 更新: {updated_at}

字数: {stats['chinese_chars']} | 英文: {stats['english_words']} | 符号: {stats['symbols']} | 字符: {stats['total_chars']} | 行数: {stats['lines']}"""

        self.details_info_label.setText(details_text)

    def on_content_changed(self):
        """内容变化时的处理"""
        self.is_content_modified = True

        # 实时更新字数统计
        if self.current_entry:
            self.update_entry_details_realtime()

        # 更新状态指示器
        if self.config_manager.is_status_indicators_enabled():
            from .status_indicator import StatusType
            self.status_indicator_bar.update_indicator("save_status", StatusType.MODIFIED, "未保存")

        # 启动自动保存定时器
        if self.config_manager.is_auto_save_enabled() and self.current_entry:
            self.auto_save_timer.start(self.config_manager.get_auto_save_interval())

    def on_title_changed(self):
        """标题变化时的处理"""
        self.is_content_modified = True
        self.on_content_changed()  # 复用内容变化的处理逻辑

    def on_tags_changed(self):
        """标签变化时的处理"""
        self.is_content_modified = True
        self.on_content_changed()  # 复用内容变化的处理逻辑

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

        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.critical(self, "错误", f"无法创建条目文件: {e}")
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(self, "错误", f"条目数据格式错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建条目失败: {e}")

    def save_current_entry(self):
        """保存当前条目"""
        if not self.current_entry or not self.current_category_path:
            return

        # 显示保存中状态
        if self.config_manager.is_status_indicators_enabled():
            from .status_indicator import StatusType
            self.status_indicator_bar.update_indicator("save_status", StatusType.SAVING, "保存中...")

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

            # 同步到独立窗口
            self.entry_window_manager.sync_entry_update(
                self.current_category_path,
                self.current_entry.uuid,
                self.current_entry
            )

            self.is_content_modified = False
            self.update_status_bar()
            self.show_operation_result("保存条目", True, self.current_entry.title)

            # 显示保存成功状态，隐藏所有其他状态
            if self.config_manager.is_status_indicators_enabled():
                from .status_indicator import StatusType
                # 隐藏修改状态和自动保存状态
                self.status_indicator_bar.hide_indicator("auto_save")
                # 显示保存成功状态
                self.status_indicator_bar.update_indicator("save_status", StatusType.SAVED, "已保存")
                self.status_indicator_bar.show_indicator("save_status", 2000)  # 2秒后自动隐藏

        except (FileNotFoundError, PermissionError, OSError) as e:
            error_msg = f"文件系统错误: {e}"
            self.show_operation_result("保存条目", False, error_msg)
            log_exception(self.logger, "保存条目", e)

            # 显示保存错误状态
            if self.config_manager.is_status_indicators_enabled():
                from .status_indicator import StatusType
                self.status_indicator_bar.update_indicator("save_status", StatusType.ERROR, "保存失败")

        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"数据格式错误: {e}"
            self.show_operation_result("保存条目", False, error_msg)
            log_exception(self.logger, "保存条目", e)

            # 显示保存错误状态
            if self.config_manager.is_status_indicators_enabled():
                from .status_indicator import StatusType
                self.status_indicator_bar.update_indicator("save_status", StatusType.ERROR, "保存失败")

    def auto_save_current_entry(self):
        """自动保存当前条目"""
        if not self.is_content_modified or not self.current_entry or not self.current_category_path:
            return

        try:
            # 显示自动保存中状态
            if self.config_manager.is_status_indicators_enabled():
                from .status_indicator import StatusType
                self.status_indicator_bar.update_indicator("auto_save", StatusType.SAVING, "自动保存中...")

            # 获取编辑器中的内容
            title = self.title_edit.text().strip()
            content = self.content_editor.toPlainText()
            tags_text = self.tags_edit.text().strip()
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            if not title:
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

            # 同步到独立窗口
            self.entry_window_manager.sync_entry_update(
                self.current_category_path,
                self.current_entry.uuid,
                self.current_entry
            )

            self.is_content_modified = False
            self.logger.info(f"自动保存成功: {self.current_entry.title}")

            # 显示自动保存成功状态，并隐藏修改状态
            if self.config_manager.is_status_indicators_enabled():
                from .status_indicator import StatusType
                # 隐藏修改状态指示器
                self.status_indicator_bar.hide_indicator("save_status")
                # 显示自动保存成功状态
                self.status_indicator_bar.update_indicator("auto_save", StatusType.SAVED, "自动保存")
                self.status_indicator_bar.show_indicator("auto_save", 1500)  # 1.5秒后自动隐藏

        except Exception as e:
            self.logger.warning(f"自动保存失败: {e}")

            # 显示自动保存错误状态
            if self.config_manager.is_status_indicators_enabled():
                from .status_indicator import StatusType
                self.status_indicator_bar.update_indicator("auto_save", StatusType.ERROR, "自动保存失败")
                self.status_indicator_bar.show_indicator("auto_save", 3000)  # 3秒后自动隐藏

    def refresh_category_tree_display(self):
        """刷新分类树显示的辅助方法"""
        try:
            self.populate_category_tree()
            self.category_tree.refresh_all_appearances()
        except Exception as e:
            self.logger.error(f"刷新分类树显示失败: {e}")
            self.show_operation_result("刷新分类树", False, str(e))

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

                # 同步到独立窗口
                self.entry_window_manager.sync_entry_deletion(self.current_category_path, entry_uuid)

                QMessageBox.information(self, "成功", f"条目 '{entry_title}' 已删除")

            except (FileNotFoundError, PermissionError, OSError) as e:
                QMessageBox.critical(self, "错误", f"无法删除条目文件: {e}")
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

                # 同步到独立窗口
                self.entry_window_manager.sync_entry_update(
                    self.current_category_path,
                    self.current_entry.uuid,
                    self.current_entry
                )

            QMessageBox.information(self, "成功", f"条目已重命名为 '{new_title.strip()}'")

        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.critical(self, "错误", f"无法重命名条目文件: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重命名条目失败: {e}")



    def open_entry_in_new_window(self, item):
        """在新窗口中打开条目（右键菜单调用）"""
        if not item or not self.current_category_path:
            return

        try:
            entry_uuid = item.data(Qt.ItemDataRole.UserRole)
            entry = self.business_manager.get_entry(self.current_category_path, entry_uuid)

            # 使用条目窗口管理器打开或聚焦窗口，激活窗口
            self.entry_window_manager.open_or_focus_entry(self.current_category_path, entry, activate=True)

        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.critical(self, "错误", f"无法访问条目文件: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开条目窗口失败: {e}")

    def on_entry_updated_in_window(self, category_path: str, entry_uuid: str, entry):
        """处理来自独立窗口的条目更新"""
        try:
            # 如果更新的条目是当前正在编辑的条目，同步到主窗口
            if (self.current_entry and
                self.current_entry.uuid == entry_uuid and
                self.current_category_path == category_path):

                # 检查主窗口是否有未保存的修改
                if self.is_content_modified:
                    reply = QMessageBox.question(
                        self,
                        "数据冲突",
                        "此条目在独立窗口中被修改了，是否要放弃当前修改并重新加载？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.No:
                        return

                # 更新主窗口的条目数据
                self.current_entry = entry
                self.load_entry_to_editor()

            # 更新条目列表中的标题（如果标题发生了变化）
            if self.current_category_path == category_path:
                for i in range(self.entry_list.count()):
                    item = self.entry_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == entry_uuid:
                        item.setText(entry.title)
                        break

        except (AttributeError, ValueError) as e:
            print(f"同步条目更新失败（数据错误）: {e}")
        except Exception as e:
            print(f"同步条目更新失败: {e}")

    def on_entry_deleted_in_window(self, category_path: str, entry_uuid: str):
        """处理来自独立窗口的条目删除"""
        try:
            # 如果删除的是当前正在编辑的条目，清空编辑器
            if (self.current_entry and
                self.current_entry.uuid == entry_uuid and
                self.current_category_path == category_path):
                self.clear_editor()

            # 从条目列表中移除
            if self.current_category_path == category_path:
                for i in range(self.entry_list.count()):
                    item = self.entry_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == entry_uuid:
                        self.entry_list.takeItem(i)
                        break

        except (AttributeError, ValueError) as e:
            print(f"同步条目删除失败（数据错误）: {e}")
        except Exception as e:
            print(f"同步条目删除失败: {e}")

    def update_status_bar(self):
        """更新状态栏"""
        try:
            stats = self.business_manager.get_statistics()
            status_text = f"分类: {stats['total_categories']} | 条目: {stats['total_entries']} | 总字数: {stats['total_words']}"
            
            # 仅当没有选择分类时才显示全局统计信息
            if not self.current_category_path:
                 self.status_bar.showMessage(status_text)

        except (FileNotFoundError, PermissionError, OSError):
            self.status_bar.showMessage("无法访问数据目录")
        except Exception:
            self.status_bar.showMessage("就绪")



    def create_new_category(self, is_root: bool = False):
        """创建一个新的分类（文件夹）"""
        parent_path = None
        if not is_root:
            current_item = self.category_tree.currentItem()
            if not current_item:
                # 如果没有选中项，则在根目录创建
                parent_path = None
            else:
                parent_path = current_item.data(0, Qt.ItemDataRole.UserRole)

        category_name, ok = QInputDialog.getText(self, "新建分类", "请输入分类名称:")

        if ok and category_name.strip():
            try:
                self.business_manager.create_category(category_name.strip(), parent_path)
                # 刷新分类树显示
                self.refresh_category_tree_display()
                QMessageBox.information(self, "成功", f"分类 '{category_name}' 创建成功")
            except (FileExistsError, PermissionError, OSError) as e:
                QMessageBox.critical(self, "错误", f"无法创建分类目录: {e}")
            except ValueError as e:
                QMessageBox.critical(self, "错误", f"分类名称无效: {e}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建分类失败: {e}")

    def rename_category(self):
        """重命名选中的分类"""
        current_item = self.category_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要重命名的分类")
            return

        old_path = current_item.data(0, Qt.ItemDataRole.UserRole)
        old_name = current_item.text(0)

        new_name, ok = QInputDialog.getText(self, "重命名分类", "请输入新名称:", text=old_name)

        if ok and new_name.strip() and new_name.strip() != old_name:
            try:
                self.business_manager.rename_category(old_path, new_name.strip())
                self.refresh_category_tree_display()
                QMessageBox.information(self, "成功", f"分类已重命名为 '{new_name}'")
            except (FileNotFoundError, PermissionError, OSError) as e:
                QMessageBox.critical(self, "错误", f"无法重命名分类目录: {e}")
            except ValueError as e:
                QMessageBox.critical(self, "错误", f"分类名称无效: {e}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名分类失败: {e}")

    def delete_category(self):
        """删除选中的分类"""
        current_item = self.category_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要删除的分类")
            return

        path_to_delete = current_item.data(0, Qt.ItemDataRole.UserRole)
        category_name = current_item.text(0)
        
        try:
            # 检查分类是否为空
            entries = self.business_manager.get_entries_in_category(path_to_delete)
            subcategories = [d for d in os.listdir(path_to_delete) if os.path.isdir(os.path.join(path_to_delete, d))]

            message = f"您确定要删除分类 '{category_name}' 吗？此操作无法撤销。"
            if entries or subcategories:
                message = (f"分类 '{category_name}' 不为空，包含 {len(entries)} 个条目和 {len(subcategories)} 个子分类。\n"
                           f"您确定要永久删除该分类及其所有内容吗？此操作无法撤销。")

            reply = QMessageBox.question(
                self, "确认删除", message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.business_manager.delete_category(path_to_delete, force=True)
                self.refresh_category_tree_display()
                self.clear_editor()
                self.entry_list.clear()
                self.current_category_path = None
                QMessageBox.information(self, "成功", f"分类 '{category_name}' 已删除")

        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.critical(self, "错误", f"无法删除分类目录: {e}")
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
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # 关闭所有独立条目窗口
        self.entry_window_manager.close_all_windows()

        event.accept()

    def open_search_dialog(self):
        """打开搜索对话框"""
        dialog = SearchDialog(self.business_manager, self)
        dialog.entry_selected.connect(self.open_entry_from_search)
        dialog.exec()

    def open_entry_from_search(self, category_path: str, entry_uuid: str):
        """从搜索结果打开条目"""
        try:
            # 1. 在QTreeWidget中找到并选择分类项
            item_to_select = self._find_item_by_path(self.category_tree.invisibleRootItem(), category_path)
            if item_to_select:
                self.category_tree.setCurrentItem(item_to_select)
                self.category_tree.scrollToItem(item_to_select) # 滚动到该项
                self.current_category_path = category_path
                self.update_entry_list()

                # 2. 在条目列表中选择对应的条目
                for i in range(self.entry_list.count()):
                    item = self.entry_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == entry_uuid:
                        self.entry_list.setCurrentItem(item)
                        break
            else:
                 QMessageBox.warning(self, "错误", f"在分类树中找不到路径: {category_path}")

        except (FileNotFoundError, PermissionError, OSError) as e:
            QMessageBox.warning(self, "错误", f"无法访问条目文件: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开条目失败: {e}")

    def _find_item_by_path(self, parent_item, path: str):
        """在树中递归查找具有给定路径的项"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            item_path = child.data(0, Qt.ItemDataRole.UserRole)
            if item_path == path:
                return child
            # 递归搜索子项
            found_item = self._find_item_by_path(child, path)
            if found_item:
                return found_item
        return None

    def toggle_drag_mode(self, checked: bool):
        """切换拖拽排序模式"""
        try:
            # 更新业务管理器的拖拽模式状态
            self.business_manager.set_drag_mode(checked)

            # 更新分类树的拖拽功能
            self.category_tree.set_drag_enabled(checked)

            # 更新条目列表的拖拽功能
            self.entry_list.set_drag_enabled(checked)

            # 重新加载数据以应用新的排序
            self.populate_category_tree()
            self.update_entry_list()

            # 更新按钮状态和提示
            if self.adjust_action:
                if checked:
                    self.adjust_action.setText('调整 ✓')
                    self.adjust_action.setToolTip('拖拽排序模式已开启，可以拖拽调整顺序')
                else:
                    self.adjust_action.setText('调整')
                    self.adjust_action.setToolTip('开启/关闭拖拽排序模式')

            # 在状态栏显示模式变化
            mode_text = "拖拽排序模式已开启" if checked else "拖拽排序模式已关闭"
            self.status_bar.showMessage(mode_text, 3000)  # 显示3秒

        except (AttributeError, ValueError) as e:
            QMessageBox.warning(self, "错误", f"切换拖拽模式失败（配置错误）: {e}")
            # 恢复按钮状态
            if self.adjust_action:
                self.adjust_action.setChecked(not checked)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"切换拖拽模式失败: {e}")
            # 恢复按钮状态
            if self.adjust_action:
                self.adjust_action.setChecked(not checked)

    def open_settings_dialog(self):
        """打开设置对话框"""
        try:
            dialog = SettingsDialog(self.config_manager, self)
            dialog.settings_changed.connect(self.on_settings_changed)
            dialog.exec()

        except Exception as e:
            self.logger.error(f"打开设置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开设置对话框失败: {e}")

    def on_settings_changed(self):
        """设置发生变化时的处理"""
        try:
            # 重新加载配置
            self.config_manager.load_config()

            # 更新状态指示器显示
            if not self.config_manager.is_status_indicators_enabled():
                self.status_indicator_bar.clear_all()

            # 停止或重新配置自动保存定时器
            if not self.config_manager.is_auto_save_enabled():
                self.auto_save_timer.stop()

            self.logger.info("设置已更新")
            self.show_status_message("设置已保存", 2000)

        except Exception as e:
            self.logger.error(f"应用设置变化失败: {e}")
            QMessageBox.warning(self, "警告", f"应用设置变化失败: {e}")