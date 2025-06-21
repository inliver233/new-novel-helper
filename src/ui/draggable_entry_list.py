"""
可拖拽的条目列表组件
支持条目在同一分类内的重新排序
"""

import json
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMessageBox, QApplication
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QPainter, QPen, QColor, QCursor


class DraggableEntryList(QListWidget):
    """支持拖拽排序的条目列表"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_list()
        
        # 拖拽相关属性
        self.drag_enabled = False
        self.business_manager = None
        self.current_category_path = None
        self.entry_window_manager = None  # 条目窗口管理器引用

        # 插入位置指示器
        self.drop_indicator_row = -1  # 插入位置行号，-1表示无指示器

        # 拖拽到窗口外检测
        self.drag_start_position = None
        
    def setup_list(self):
        """设置列表的基本属性"""
        # 初始化拖拽设置 - 默认为普通模式（可拖拽到窗口外）
        self.setDragDropMode(QListWidget.DragDropMode.DragOnly)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        # 启用自定义拖拽处理
        self.setDragEnabled(True)
        
    def set_business_manager(self, business_manager):
        """设置业务管理器引用"""
        self.business_manager = business_manager

    def set_current_category_path(self, category_path: str):
        """设置当前分类路径"""
        self.current_category_path = category_path

    def set_entry_window_manager(self, entry_window_manager):
        """设置条目窗口管理器引用"""
        self.entry_window_manager = entry_window_manager
        
    def set_drag_enabled(self, enabled: bool):
        """设置拖拽功能是否启用（调整模式）"""
        self.drag_enabled = enabled
        if enabled:
            # 调整模式：只允许内部重排序，不允许拖拽到窗口外
            self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
            self.setDefaultDropAction(Qt.DropAction.MoveAction)
            self.setDragEnabled(True)
        else:
            # 普通模式：允许拖拽到窗口外创建新窗口
            self.setDragDropMode(QListWidget.DragDropMode.DragOnly)
            self.setDefaultDropAction(Qt.DropAction.MoveAction)
            self.setDragEnabled(True)
    
    def startDrag(self, supportedActions):
        """开始拖拽操作"""
        current_item = self.currentItem()
        if not current_item:
            return

        # 记录拖拽开始位置和条目信息
        self.drag_start_position = QCursor.pos()
        entry_uuid = current_item.data(Qt.ItemDataRole.UserRole)

        # 创建拖拽数据
        mime_data = QMimeData()
        mime_data.setText(f"entry:{entry_uuid}")

        # 创建拖拽对象
        drag = QDrag(self)
        drag.setMimeData(mime_data)

        # 执行拖拽
        drop_action = drag.exec(supportedActions)

        # 检查拖拽结果
        self.handle_drag_result(drop_action, entry_uuid)

    def handle_drag_result(self, drop_action, entry_uuid: str):
        """处理拖拽结果"""
        # 获取主窗口引用，用于后续恢复层级
        main_window = self.window()

        # 只在普通模式（非调整模式）下允许拖拽到窗口外
        if self.drag_enabled:
            # 调整模式下，不处理拖拽到窗口外的情况
            # 但仍需要确保主窗口保持层级
            self.restore_main_window_level(main_window)
            return

        current_pos = QCursor.pos()
        window_rect = main_window.geometry()

        # 检查鼠标最终位置是否在主窗口外部
        if not window_rect.contains(current_pos):
            # 拖拽到窗口外部，创建独立窗口
            self.handle_drag_outside(entry_uuid)
            # 创建窗口后，恢复主窗口层级
            self.restore_main_window_level(main_window)
        elif drop_action == Qt.DropAction.IgnoreAction:
            # 拖拽被取消或无效，但在窗口内部，可能是用户取消了操作
            self.restore_main_window_level(main_window)

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        # 只在调整模式下处理内部拖拽
        if self.drag_enabled and event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("entry:"):
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
        if not text.startswith("entry:"):
            self.clear_drop_indicator()
            event.ignore()
            return

        # 计算插入位置并显示指示器
        self.update_drop_indicator(event.position().toPoint())
        event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.clear_drop_indicator()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """拖拽放置事件"""
        # 清除指示器
        target_row = self.drop_indicator_row
        self.clear_drop_indicator()

        if not self.drag_enabled:
            event.ignore()
            return

        if not event.mimeData().hasText():
            event.ignore()
            return

        text = event.mimeData().text()
        if not text.startswith("entry:"):
            event.ignore()
            return

        source_uuid = text[6:]  # 移除 "entry:" 前缀

        try:
            if target_row >= 0:
                # 使用指示器位置
                self.reorder_entries(source_uuid, target_row)
            else:
                # 放置到列表末尾
                self.reorder_entries(source_uuid, self.count())

            event.acceptProposedAction()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"重新排序失败: {e}")
            event.ignore()
    
    def reorder_entries(self, source_uuid: str, target_row: int):
        """重新排序条目"""
        if not self.business_manager or not self.current_category_path:
            raise ValueError("业务管理器或分类路径未设置")
        
        # 获取当前所有条目的UUID列表
        current_order = []
        for i in range(self.count()):
            item = self.item(i)
            uuid = item.data(Qt.ItemDataRole.UserRole)
            current_order.append(uuid)
        
        # 找到源条目的当前位置
        try:
            source_row = current_order.index(source_uuid)
        except ValueError:
            raise ValueError(f"找不到源条目: {source_uuid}")
        
        # 移除源条目
        current_order.pop(source_row)
        
        # 调整目标位置（如果目标位置在源位置之后，需要减1）
        if target_row > source_row:
            target_row -= 1
        
        # 确保目标位置在有效范围内
        target_row = max(0, min(target_row, len(current_order)))
        
        # 在目标位置插入源条目
        current_order.insert(target_row, source_uuid)
        
        # 保存新的排序
        self.business_manager.save_entries_order(self.current_category_path, current_order)
        
        # 刷新列表显示
        self.refresh_list()
    
    def refresh_list(self):
        """刷新列表显示"""
        if not self.business_manager or not self.current_category_path:
            return
            
        # 保存当前选中的条目
        current_item = self.currentItem()
        selected_uuid = None
        if current_item:
            selected_uuid = current_item.data(Qt.ItemDataRole.UserRole)
        
        # 清空列表
        self.clear()
        
        # 重新加载条目
        try:
            entries = self.business_manager.get_entries_in_category(self.current_category_path)
            for entry in entries:
                item = QListWidgetItem(entry.title)
                item.setData(Qt.ItemDataRole.UserRole, entry.uuid)
                self.addItem(item)
                
                # 恢复选中状态
                if entry.uuid == selected_uuid:
                    self.setCurrentItem(item)
                    
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新条目列表失败: {e}")

    # ===== 视觉反馈方法 =====

    def update_drop_indicator(self, pos):
        """更新插入位置指示器"""
        # 计算插入位置
        target_row = self.calculate_insert_position(pos)

        if target_row != self.drop_indicator_row:
            self.drop_indicator_row = target_row
            self.update()  # 触发重绘

    def calculate_insert_position(self, pos):
        """计算插入位置"""
        if self.count() == 0:
            return 0

        # 找到鼠标位置对应的项
        item = self.itemAt(pos)
        if item is None:
            # 鼠标在列表外或空白区域，插入到末尾
            return self.count()

        # 获取项的行号和矩形区域
        row = self.row(item)
        item_rect = self.visualItemRect(item)

        # 判断是插入到项的上方还是下方
        if pos.y() < item_rect.center().y():
            # 插入到项的上方
            return row
        else:
            # 插入到项的下方
            return row + 1

    def clear_drop_indicator(self):
        """清除插入位置指示器"""
        if self.drop_indicator_row >= 0:
            self.drop_indicator_row = -1
            self.update()  # 触发重绘

    def paintEvent(self, event):
        """重写绘制事件以显示插入指示器"""
        super().paintEvent(event)

        # 绘制插入位置指示器
        if self.drop_indicator_row >= 0 and self.drag_enabled:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 设置画笔（蓝色粗线）
            pen = QPen(QColor(30, 144, 255), 3)  # 蓝色，3像素宽
            painter.setPen(pen)

            # 计算指示器位置
            if self.drop_indicator_row == 0:
                # 插入到第一项之前
                y = 0
            elif self.drop_indicator_row >= self.count():
                # 插入到最后一项之后
                if self.count() > 0:
                    last_item = self.item(self.count() - 1)
                    last_rect = self.visualItemRect(last_item)
                    y = last_rect.bottom()
                else:
                    y = 0
            else:
                # 插入到指定项之前
                target_item = self.item(self.drop_indicator_row)
                target_rect = self.visualItemRect(target_item)
                y = target_rect.top()

            # 绘制水平线
            painter.drawLine(0, y, self.viewport().width(), y)
            painter.end()

    def handle_drag_outside(self, entry_uuid: str):
        """处理拖拽到窗口外部的情况"""
        if not self.entry_window_manager:
            print("警告：条目窗口管理器未设置")
            return

        if not self.business_manager:
            print("警告：业务管理器未设置")
            return

        if not self.current_category_path:
            print("警告：当前分类路径未设置")
            return

        try:
            # 获取条目数据
            entry = self.business_manager.get_entry(self.current_category_path, entry_uuid)

            # 获取主窗口引用
            main_window = self.window()

            # 创建独立窗口，但不激活（不抢夺焦点），并传递主窗口引用
            window = self.entry_window_manager.create_entry_window(
                self.current_category_path,
                entry,
                activate=False,
                main_window=main_window
            )

            if window:
                print(f"成功创建独立窗口：{entry.title}")
            else:
                print("创建独立窗口失败：窗口管理器返回None")

        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"创建独立窗口时出错（文件系统错误）: {e}")
            QMessageBox.warning(self, "错误", f"创建独立窗口失败（文件系统错误）: {e}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"创建独立窗口时出错（数据格式错误）: {e}")
            QMessageBox.warning(self, "错误", f"创建独立窗口失败（数据格式错误）: {e}")
        except (RuntimeError, AttributeError, TypeError) as e:
            print(f"创建独立窗口时出错（运行时错误）: {e}")
            QMessageBox.warning(self, "错误", f"创建独立窗口失败（运行时错误）: {e}")

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def restore_main_window_level(self, main_window):
        """恢复主窗口的显示层级"""
        if main_window:
            # 使用QTimer延迟执行，确保拖拽操作完全结束
            from PyQt6.QtCore import QTimer
            # 延迟时间稍微长一点，确保拖拽完全结束
            QTimer.singleShot(200, lambda: self._do_restore_window_level(main_window))

    def _do_restore_window_level(self, main_window):
        """实际执行窗口层级恢复"""
        try:
            # 温和地恢复主窗口层级，不激活窗口
            if main_window.isVisible() and not main_window.isMinimized():
                # 只有当主窗口可见且未最小化时才提升层级
                main_window.raise_()

                # 确保窗口在正确的状态
                current_state = main_window.windowState()
                if current_state & Qt.WindowState.WindowMinimized:
                    main_window.setWindowState(current_state & ~Qt.WindowState.WindowMinimized)

        except Exception as e:
            print(f"恢复主窗口层级时出错: {e}")


