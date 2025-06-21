"""
搜索服务模块 - 专门处理条目搜索相关的所有逻辑
提供一个简化的、高效的搜索功能。
"""

import os
from typing import List, Dict, Any, Optional

from ..data_access.file_system_manager import FileSystemManager
from ..models.entry import Entry


class SearchService:
    """
    搜索服务类，封装所有搜索相关的逻辑。
    提供一个简化的接口来搜索条目。
    """

    def __init__(self, data_path: str, fs_manager: Optional[FileSystemManager] = None):
        """
        初始化搜索服务。

        Args:
            data_path (str): 数据根目录的路径。
            fs_manager (Optional[FileSystemManager]): 文件系统管理器实例。
                                                     如果为 None，则会创建一个新的实例。
        """
        self.data_path = data_path
        self.fs_manager = fs_manager or FileSystemManager(data_path)

    def search(self, query: str, search_in_title: bool = True,
               search_in_content: bool = True, search_in_tags: bool = True) -> List[Dict[str, Any]]:
        """
        在所有条目中执行不区分大小写的搜索。

        Args:
            query (str): 搜索关键词。
            search_in_title (bool): 是否在标题中搜索。默认为 True。
            search_in_content (bool): 是否在内容中搜索。默认为 True。
            search_in_tags (bool): 是否在标签中搜索。默认为 True。

        Returns:
            List[Dict[str, Any]]: 搜索结果列表。
                                  每个结果是一个包含 'entry' 和 'category_path' 的字典。
        """
        if not query or not query.strip():
            return []

        processed_query = query.strip().lower()
        results: List[Dict[str, Any]] = []
        found_uuids = set()

        for root, _, files in os.walk(self.data_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        entry = self.fs_manager.get_entry(file_path)

                        if entry.uuid in found_uuids:
                            continue

                        # 检查标题
                        if search_in_title and processed_query in entry.title.lower():
                            results.append({'entry': entry, 'category_path': root})
                            found_uuids.add(entry.uuid)
                            continue

                        # 检查内容
                        if search_in_content and processed_query in entry.content.lower():
                            results.append({'entry': entry, 'category_path': root})
                            found_uuids.add(entry.uuid)
                            continue

                        # 检查标签
                        if search_in_tags:
                            for tag in entry.tags:
                                if processed_query in tag.lower():
                                    results.append({'entry': entry, 'category_path': root})
                                    found_uuids.add(entry.uuid)
                                    break  # 找到一个匹配的标签就足够了

                    except Exception as e:
                        print(f"搜索时跳过损坏或无法读取的文件: {file_path} - {e}")
                        continue
        return results
