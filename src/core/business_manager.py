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
    
    def get_categories(self, parent_path: str = None) -> List[str]:
        """获取分类列表
        
        Args:
            parent_path: 父分类路径
            
        Returns:
            List[str]: 分类名称列表
        """
        return self.fs_manager.list_categories(parent_path)
    
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
        return self.fs_manager.list_entries_in_category(category_path)
    
    def get_entry_titles_in_category(self, category_path: str) -> List[str]:
        """获取分类下所有条目的标题
        
        Args:
            category_path: 分类路径
            
        Returns:
            List[str]: 条目标题列表
        """
        return self.fs_manager.get_entry_names_in_category(category_path)
    

    
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
