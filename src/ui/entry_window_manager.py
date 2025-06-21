"""
条目窗口管理器模块
负责管理多个独立条目窗口的创建、跟踪、同步等功能
"""

import uuid
from typing import Dict, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QMessageBox
from ..models.entry import Entry
from .entry_window import EntryWindow


class EntryWindowManager(QObject):
    """条目窗口管理器"""
    
    # 信号定义
    entry_updated_in_window = pyqtSignal(str, str, Entry)  # category_path, entry_uuid, entry
    entry_deleted_in_window = pyqtSignal(str, str)  # category_path, entry_uuid
    
    def __init__(self, business_manager):
        super().__init__()
        self.business_manager = business_manager
        
        # 存储所有打开的条目窗口
        # key: window_id, value: EntryWindow
        self.windows: Dict[str, EntryWindow] = {}
        
        # 存储条目UUID到窗口ID的映射，用于快速查找
        # key: entry_uuid, value: set of window_ids
        self.entry_to_windows: Dict[str, set] = {}
        
    def create_entry_window(self, category_path: str, entry: Entry, activate: bool = True, main_window=None) -> Optional[EntryWindow]:
        """创建新的条目窗口

        Args:
            category_path: 分类路径
            entry: 条目对象
            activate: 是否激活窗口（抢夺焦点）
            main_window: 主窗口引用，用于恢复层级

        Returns:
            EntryWindow: 创建的窗口对象，如果创建失败则返回None
        """
        try:
            # 生成唯一的窗口ID
            window_id = str(uuid.uuid4())
            
            # 创建窗口
            window = EntryWindow(
                business_manager=self.business_manager,
                category_path=category_path,
                entry=entry,
                window_id=window_id
            )
            
            # 连接窗口信号
            self.connect_window_signals(window)
            
            # 注册窗口
            self.register_window(window_id, window, entry.uuid)
            
            # 显示窗口
            window.show()
            if activate:
                # 只在需要时激活窗口
                window.raise_()
                window.activateWindow()
            else:
                # 不激活时，确保新窗口不会影响其他窗口的层级
                # 设置窗口为非模态，并且不抢夺焦点
                window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

                # 如果提供了主窗口引用，在创建窗口后恢复主窗口层级
                if main_window:
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(300, lambda: self._restore_main_window(main_window))

            return window
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"创建条目窗口失败: {e}")
            return None
            
    def connect_window_signals(self, window: EntryWindow):
        """连接窗口信号"""
        window.entry_updated.connect(self.on_entry_updated)
        window.entry_deleted.connect(self.on_entry_deleted)
        window.window_closed.connect(self.on_window_closed)
        
    def register_window(self, window_id: str, window: EntryWindow, entry_uuid: str):
        """注册窗口"""
        # 添加到窗口字典
        self.windows[window_id] = window
        
        # 添加到条目映射
        if entry_uuid not in self.entry_to_windows:
            self.entry_to_windows[entry_uuid] = set()
        self.entry_to_windows[entry_uuid].add(window_id)
        
    def unregister_window(self, window_id: str):
        """注销窗口"""
        if window_id not in self.windows:
            return
            
        window = self.windows[window_id]
        entry_uuid = window.get_entry_uuid()
        
        # 从窗口字典中移除
        del self.windows[window_id]
        
        # 从条目映射中移除
        if entry_uuid in self.entry_to_windows:
            self.entry_to_windows[entry_uuid].discard(window_id)
            if not self.entry_to_windows[entry_uuid]:
                del self.entry_to_windows[entry_uuid]
                
    def get_windows_for_entry(self, entry_uuid: str) -> List[EntryWindow]:
        """获取指定条目的所有窗口"""
        if entry_uuid not in self.entry_to_windows:
            return []
            
        windows = []
        for window_id in self.entry_to_windows[entry_uuid]:
            if window_id in self.windows:
                windows.append(self.windows[window_id])
                
        return windows
        
    def has_window_for_entry(self, entry_uuid: str) -> bool:
        """检查是否已有指定条目的窗口"""
        return entry_uuid in self.entry_to_windows and len(self.entry_to_windows[entry_uuid]) > 0
        
    def focus_existing_window(self, entry_uuid: str, activate: bool = True) -> bool:
        """聚焦到已存在的条目窗口

        Args:
            entry_uuid: 条目UUID
            activate: 是否激活窗口（抢夺焦点）

        Returns:
            bool: 如果找到并聚焦了窗口则返回True，否则返回False
        """
        windows = self.get_windows_for_entry(entry_uuid)
        if windows:
            # 聚焦到第一个窗口
            window = windows[0]
            window.show()
            if activate:
                window.raise_()
                window.activateWindow()
            return True
        return False
        
    def sync_entry_update(self, category_path: str, entry_uuid: str, updated_entry: Entry):
        """同步条目更新到所有相关窗口"""
        windows = self.get_windows_for_entry(entry_uuid)
        for window in windows:
            # 只同步到其他窗口（不是发起更新的窗口）
            if window.get_category_path() == category_path:
                window.update_entry_data(updated_entry)
                
    def sync_entry_deletion(self, category_path: str, entry_uuid: str):
        """同步条目删除到所有相关窗口"""
        windows = self.get_windows_for_entry(entry_uuid)
        for window in windows:
            if window.get_category_path() == category_path:
                # 关闭窗口
                window.close()
                
    def close_all_windows(self):
        """关闭所有窗口"""
        # 创建窗口列表的副本，因为关闭窗口时会修改原字典
        windows_to_close = list(self.windows.values())
        for window in windows_to_close:
            window.close()
            
    def get_window_count(self) -> int:
        """获取当前打开的窗口数量"""
        return len(self.windows)
        
    def get_all_windows(self) -> List[EntryWindow]:
        """获取所有打开的窗口"""
        return list(self.windows.values())
        
    # 信号处理方法
    def on_entry_updated(self, category_path: str, entry_uuid: str, entry: Entry):
        """处理条目更新信号"""
        # 同步到其他窗口
        self.sync_entry_update(category_path, entry_uuid, entry)
        
        # 转发信号给主窗口
        self.entry_updated_in_window.emit(category_path, entry_uuid, entry)
        
    def on_entry_deleted(self, category_path: str, entry_uuid: str):
        """处理条目删除信号"""
        # 同步到其他窗口
        self.sync_entry_deletion(category_path, entry_uuid)
        
        # 转发信号给主窗口
        self.entry_deleted_in_window.emit(category_path, entry_uuid)
        
    def on_window_closed(self, window_id: str):
        """处理窗口关闭信号"""
        self.unregister_window(window_id)
        
    def open_or_focus_entry(self, category_path: str, entry: Entry, activate: bool = True) -> EntryWindow:
        """打开或聚焦条目窗口

        如果条目已有窗口则聚焦，否则创建新窗口

        Args:
            category_path: 分类路径
            entry: 条目对象
            activate: 是否激活窗口（抢夺焦点）

        Returns:
            EntryWindow: 窗口对象
        """
        # 检查是否已有窗口
        if self.has_window_for_entry(entry.uuid):
            if self.focus_existing_window(entry.uuid, activate):
                return self.get_windows_for_entry(entry.uuid)[0]

        # 创建新窗口
        return self.create_entry_window(category_path, entry, activate)

    def _restore_main_window(self, main_window):
        """恢复主窗口层级"""
        try:
            if main_window and main_window.isVisible():
                # 温和地提升主窗口层级，不激活
                main_window.raise_()
        except Exception as e:
            print(f"恢复主窗口层级失败: {e}")
