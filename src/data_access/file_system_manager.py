import os
import json
import shutil
from typing import List, Optional, Dict, Any
from ..models.entry import Entry

class FileSystemManager:
    """负责所有文件系统操作，封装对分类（文件夹）和条目（JSON 文件）的 CRUD 逻辑。"""

    def __init__(self, base_path: str):
        self.base_path = base_path
        # 确保基础路径存在
        os.makedirs(base_path, exist_ok=True)

    # ===== 分类（文件夹）管理 =====

    def create_category(self, category_name: str, parent_path: str = None) -> str:
        """创建一个新的分类（文件夹）。

        Args:
            category_name: 分类名称
            parent_path: 父分类路径，如果为None则在根目录创建

        Returns:
            str: 创建的分类的完整路径

        Raises:
            FileExistsError: 如果分类已存在
            OSError: 如果创建失败
        """
        if parent_path is None:
            category_path = os.path.join(self.base_path, category_name)
        else:
            category_path = os.path.join(parent_path, category_name)

        if os.path.exists(category_path):
            raise FileExistsError(f"分类 '{category_name}' 已存在")

        try:
            os.makedirs(category_path, exist_ok=False)
            return category_path
        except OSError as e:
            raise OSError(f"创建分类失败: {e}")

    def rename_category(self, old_path: str, new_name: str) -> str:
        """重命名一个分类（文件夹）。

        Args:
            old_path: 原分类路径
            new_name: 新分类名称

        Returns:
            str: 重命名后的分类路径

        Raises:
            FileNotFoundError: 如果原分类不存在
            FileExistsError: 如果新名称已存在
            OSError: 如果重命名失败
        """
        if not os.path.exists(old_path):
            raise FileNotFoundError(f"分类 '{old_path}' 不存在")

        parent_dir = os.path.dirname(old_path)
        new_path = os.path.join(parent_dir, new_name)

        if os.path.exists(new_path):
            raise FileExistsError(f"分类 '{new_name}' 已存在")

        try:
            os.rename(old_path, new_path)
            return new_path
        except OSError as e:
            raise OSError(f"重命名分类失败: {e}")

    def delete_category(self, path: str, force: bool = False):
        """删除一个分类（文件夹）。

        Args:
            path: 分类路径
            force: 是否强制删除（即使非空）

        Raises:
            FileNotFoundError: 如果分类不存在
            OSError: 如果删除失败
            ValueError: 如果分类非空且force=False
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"分类 '{path}' 不存在")

        if not force and os.listdir(path):
            raise ValueError(f"分类 '{path}' 不为空，请先删除其中的内容或使用force=True")

        try:
            shutil.rmtree(path)
        except OSError as e:
            raise OSError(f"删除分类失败: {e}")

    def list_categories(self, parent_path: str = None) -> List[str]:
        """列出指定路径下的所有分类。

        Args:
            parent_path: 父路径，如果为None则列出根目录下的分类

        Returns:
            List[str]: 分类名称列表
        """
        if parent_path is None:
            parent_path = self.base_path

        if not os.path.exists(parent_path):
            return []

        try:
            return [
                item for item in os.listdir(parent_path)
                if os.path.isdir(os.path.join(parent_path, item))
            ]
        except OSError:
            return []

    def get_category_tree(self, parent_path: str = None) -> List[Dict[str, Any]]:
        """
        递归地获取分类目录树。

        Args:
            parent_path: 父路径，如果为None则从根目录开始

        Returns:
            List[Dict[str, Any]]: 一个代表目录树的列表，每个元素是一个字典，
                                  包含 'name', 'path', 和 'children' 键。
        """
        if parent_path is None:
            parent_path = self.base_path
        
        return self._scan_directory_recursively(parent_path)

    def _scan_directory_recursively(self, current_path: str) -> List[Dict[str, Any]]:
        """
        递归扫描目录以构建树的辅助方法。
        """
        tree = []
        if not os.path.exists(current_path):
            return tree

        try:
            for item in os.listdir(current_path):
                path = os.path.join(current_path, item)
                if os.path.isdir(path):
                    node = {
                        'name': item,
                        'path': path,
                        'children': self._scan_directory_recursively(path)
                    }
                    tree.append(node)
        except OSError:
            # 忽略权限错误等问题
            pass
        
        return tree

    # ===== 条目（JSON文件）管理 =====

    def create_entry(self, category_path: str, entry: Entry) -> str:
        """在指定分类下创建一个新的条目（JSON 文件）。

        Args:
            category_path: 分类路径
            entry: Entry对象

        Returns:
            str: 创建的条目文件路径

        Raises:
            FileNotFoundError: 如果分类不存在
            FileExistsError: 如果条目已存在
            OSError: 如果创建失败
        """
        if not os.path.exists(category_path):
            raise FileNotFoundError(f"分类 '{category_path}' 不存在")

        file_path = os.path.join(category_path, f"{entry.uuid}.json")

        if os.path.exists(file_path):
            raise FileExistsError(f"条目 '{entry.uuid}' 已存在")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(entry.to_json())
            return file_path
        except OSError as e:
            raise OSError(f"创建条目失败: {e}")

    def get_entry(self, file_path: str) -> Entry:
        """根据路径读取一个条目（JSON 文件）。

        Args:
            file_path: 条目文件路径

        Returns:
            Entry: 条目对象

        Raises:
            FileNotFoundError: 如果文件不存在
            json.JSONDecodeError: 如果JSON格式错误
            OSError: 如果读取失败
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"条目文件 '{file_path}' 不存在")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Entry.from_json(content)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"条目文件格式错误: {e}", e.doc, e.pos)
        except OSError as e:
            raise OSError(f"读取条目失败: {e}")

    def save_entry(self, file_path: str, entry: Entry):
        """保存一个条目（JSON 文件）。

        Args:
            file_path: 条目文件路径
            entry: Entry对象

        Raises:
            OSError: 如果保存失败
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(entry.to_json())
        except OSError as e:
            raise OSError(f"保存条目失败: {e}")

    def update_entry(self, file_path: str, **kwargs) -> Entry:
        """更新一个现有的条目。

        Args:
            file_path: 条目文件路径
            **kwargs: 要更新的字段

        Returns:
            Entry: 更新后的条目对象

        Raises:
            FileNotFoundError: 如果文件不存在
        """
        entry = self.get_entry(file_path)
        entry.update_content(**kwargs)
        self.save_entry(file_path, entry)
        return entry

    def delete_entry(self, file_path: str):
        """删除一个条目（JSON 文件）。

        Args:
            file_path: 条目文件路径

        Raises:
            FileNotFoundError: 如果文件不存在
            OSError: 如果删除失败
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"条目文件 '{file_path}' 不存在")

        try:
            os.remove(file_path)
        except OSError as e:
            raise OSError(f"删除条目失败: {e}")

    def list_entries_in_category(self, category_path: str) -> List[Entry]:
        """列出一个分类下的所有条目。

        Args:
            category_path: 分类路径

        Returns:
            List[Entry]: 条目对象列表
        """
        if not os.path.exists(category_path):
            return []

        entries = []
        try:
            for filename in os.listdir(category_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(category_path, filename)
                    try:
                        entry = self.get_entry(file_path)
                        entries.append(entry)
                    except (json.JSONDecodeError, OSError):
                        # 跳过损坏的文件
                        continue
        except OSError:
            pass

        return entries

    def get_entry_names_in_category(self, category_path: str) -> List[str]:
        """获取分类下所有条目的标题列表。

        Args:
            category_path: 分类路径

        Returns:
            List[str]: 条目标题列表
        """
        entries = self.list_entries_in_category(category_path)
        return [entry.title for entry in entries]

    def find_entry_by_title(self, category_path: str, title: str) -> Optional[Entry]:
        """根据标题查找条目。

        Args:
            category_path: 分类路径
            title: 条目标题

        Returns:
            Optional[Entry]: 找到的条目，如果没找到则返回None
        """
        entries = self.list_entries_in_category(category_path)
        for entry in entries:
            if entry.title == title:
                return entry
        return None

    def get_entry_file_path(self, category_path: str, entry_uuid: str) -> str:
        """根据UUID获取条目文件路径。

        Args:
            category_path: 分类路径
            entry_uuid: 条目UUID

        Returns:
            str: 条目文件路径
        """
        return os.path.join(category_path, f"{entry_uuid}.json")