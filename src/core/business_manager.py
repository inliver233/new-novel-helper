"""
业务逻辑层 - 处理应用的核心业务逻辑
作为UI层和数据访问层之间的桥梁
"""

import os
from typing import List, Optional, Dict
from ..data_access.file_system_manager import FileSystemManager
from ..models.entry import Entry


class BusinessManager:
    """业务逻辑管理器，封装应用的核心业务逻辑"""

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.fs_manager = FileSystemManager(data_path)
        self.drag_mode_enabled = False  # 拖拽模式状态
    
    # ===== 分类管理业务逻辑 =====
    
    def create_category(self, category_name: str, parent_path: str = None) -> str:
        """创建新分类
        
        Args:
            category_name: 分类名称
            parent_path: 父分类路径
            
        Returns:
            str: 创建的分类路径
            
        Raises:
            ValueError: 如果分类名称无效
            FileExistsError: 如果分类已存在
        """
        # 验证分类名称
        if not category_name or not category_name.strip():
            raise ValueError("分类名称不能为空")
        
        # 清理分类名称，移除不安全字符
        safe_name = self._sanitize_filename(category_name.strip())
        if not safe_name:
            raise ValueError("分类名称包含无效字符")
        
        return self.fs_manager.create_category(safe_name, parent_path)
    
    def rename_category(self, old_path: str, new_name: str) -> str:
        """重命名分类
        
        Args:
            old_path: 原分类路径
            new_name: 新分类名称
            
        Returns:
            str: 重命名后的分类路径
        """
        safe_name = self._sanitize_filename(new_name.strip())
        if not safe_name:
            raise ValueError("分类名称包含无效字符")
        
        return self.fs_manager.rename_category(old_path, safe_name)
    
    def delete_category(self, path: str, force: bool = False):
        """删除分类
        
        Args:
            path: 分类路径
            force: 是否强制删除
        """
        self.fs_manager.delete_category(path, force)
    

    def get_category_tree(self) -> List[Dict]:
        """获取完整的分类目录树

        Returns:
            List[Dict]: 代表目录树的嵌套列表
        """
        return self.fs_manager.get_category_tree(use_custom_order=self.drag_mode_enabled)
    
    # ===== 条目管理业务逻辑 =====
    
    def create_entry(self, category_path: str, title: str, content: str = "", 
                    tags: Optional[List[str]] = None) -> Entry:
        """创建新条目
        
        Args:
            category_path: 分类路径
            title: 条目标题
            content: 条目内容
            tags: 标签列表
            
        Returns:
            Entry: 创建的条目对象
            
        Raises:
            ValueError: 如果标题无效
            FileNotFoundError: 如果分类不存在
        """
        # 验证标题
        if not title or not title.strip():
            raise ValueError("条目标题不能为空")
        
        # 创建条目对象
        entry = Entry.create_new(title.strip(), content, tags or [])
        
        # 保存到文件系统
        self.fs_manager.create_entry(category_path, entry)
        
        return entry
    
    def get_entry(self, category_path: str, entry_uuid: str) -> Entry:
        """获取条目
        
        Args:
            category_path: 分类路径
            entry_uuid: 条目UUID
            
        Returns:
            Entry: 条目对象
        """
        file_path = self.fs_manager.get_entry_file_path(category_path, entry_uuid)
        return self.fs_manager.get_entry(file_path)
    
    def get_entry_by_title(self, category_path: str, title: str) -> Optional[Entry]:
        """根据标题获取条目
        
        Args:
            category_path: 分类路径
            title: 条目标题
            
        Returns:
            Optional[Entry]: 条目对象，如果没找到则返回None
        """
        return self.fs_manager.find_entry_by_title(category_path, title)
    
    def update_entry(self, category_path: str, entry_uuid: str, **kwargs) -> Entry:
        """更新条目
        
        Args:
            category_path: 分类路径
            entry_uuid: 条目UUID
            **kwargs: 要更新的字段
            
        Returns:
            Entry: 更新后的条目对象
        """
        file_path = self.fs_manager.get_entry_file_path(category_path, entry_uuid)
        return self.fs_manager.update_entry(file_path, **kwargs)
    
    def delete_entry(self, category_path: str, entry_uuid: str):
        """删除条目
        
        Args:
            category_path: 分类路径
            entry_uuid: 条目UUID
        """
        file_path = self.fs_manager.get_entry_file_path(category_path, entry_uuid)
        self.fs_manager.delete_entry(file_path)
    
    def get_entries_in_category(self, category_path: str) -> List[Entry]:
        """获取分类下的所有条目

        Args:
            category_path: 分类路径

        Returns:
            List[Entry]: 条目列表
        """
        return self.fs_manager.list_entries_in_category(category_path, use_custom_order=self.drag_mode_enabled)
    
    def get_entry_titles_in_category(self, category_path: str) -> List[str]:
        """获取分类下所有条目的标题
        
        Args:
            category_path: 分类路径
            
        Returns:
            List[str]: 条目标题列表
        """
        return self.fs_manager.get_entry_names_in_category(category_path)

    # ===== 拖拽排序管理 =====

    def set_drag_mode(self, enabled: bool):
        """设置拖拽模式状态

        Args:
            enabled: 是否启用拖拽模式
        """
        self.drag_mode_enabled = enabled

    def is_drag_mode_enabled(self) -> bool:
        """检查拖拽模式是否启用

        Returns:
            bool: 拖拽模式状态
        """
        return self.drag_mode_enabled

    def save_category_order(self, category_path: str, categories_order: List[str]):
        """保存分类的排序

        Args:
            category_path: 分类路径
            categories_order: 子分类名称的排序列表
        """
        # 获取当前的条目排序
        order_info = self.fs_manager.load_order_info(category_path)
        entries_order = order_info.get("entries", [])

        # 保存新的排序
        self.fs_manager.save_order_info(category_path, categories_order, entries_order)

    def save_entries_order(self, category_path: str, entries_order: List[str]):
        """保存条目的排序

        Args:
            category_path: 分类路径
            entries_order: 条目UUID的排序列表
        """
        # 获取当前的分类排序
        order_info = self.fs_manager.load_order_info(category_path)
        categories_order = order_info.get("categories", [])

        # 保存新的排序
        self.fs_manager.save_order_info(category_path, categories_order, entries_order)

    def move_category(self, source_path: str, target_parent_path: str, new_name: str = None) -> str:
        """移动分类到新的父分类下

        Args:
            source_path: 源分类路径
            target_parent_path: 目标父分类路径
            new_name: 新名称（可选）

        Returns:
            str: 新的分类路径

        Raises:
            ValueError: 如果移动操作无效
            OSError: 如果移动失败
        """
        import shutil

        if not os.path.exists(source_path):
            raise ValueError(f"源分类不存在: {source_path}")

        if not os.path.exists(target_parent_path):
            raise ValueError(f"目标父分类不存在: {target_parent_path}")

        # 确定新名称
        if new_name is None:
            new_name = os.path.basename(source_path)

        new_path = os.path.join(target_parent_path, new_name)

        # 检查目标路径是否已存在
        if os.path.exists(new_path):
            raise ValueError(f"目标位置已存在同名分类: {new_name}")

        # 检查是否试图移动到自己的子目录
        if new_path.startswith(source_path + os.sep):
            raise ValueError("不能将分类移动到自己的子目录中")

        try:
            shutil.move(source_path, new_path)
            return new_path
        except OSError as e:
            raise OSError(f"移动分类失败: {e}")

    # ===== 工具方法 =====
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除或替换不安全字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # 移除前后空格和点
        filename = filename.strip('. ')
        
        return filename
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息
        
        Returns:
            Dict[str, int]: 统计信息
        """
        total_categories = 0
        total_entries = 0
        total_words = 0
        
        for root, dirs, files in os.walk(self.data_path):
            total_categories += len(dirs)
            
            for file in files:
                if file.endswith('.json'):
                    total_entries += 1
                    try:
                        file_path = os.path.join(root, file)
                        entry = self.fs_manager.get_entry(file_path)
                        total_words += entry.get_word_count()
                    except Exception:
                        continue
        
        return {
            'total_categories': total_categories,
            'total_entries': total_entries,
            'total_words': total_words
        }
