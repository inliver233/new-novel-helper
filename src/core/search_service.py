"""
搜索服务模块 - 专门处理条目搜索相关的所有逻辑
提供一个简化的、高效的搜索功能。
"""

import os
import json
from typing import List, Dict, Any, Optional

from ..data_access.file_system_manager import FileSystemManager
from ..models.entry import Entry
from ..utils.logger import LoggerConfig, log_exception
from .search_strategy import SearchStrategy


class SimpleSearchStrategy(SearchStrategy):
    """
    一个简单的搜索策略，通过直接扫描文件系统来执行搜索。
    """

    def __init__(self, data_path: str, fs_manager: Optional[FileSystemManager] = None):
        """
        初始化简单搜索策略。

        Args:
            data_path (str): 数据根目录的路径。
            fs_manager (Optional[FileSystemManager]): 文件系统管理器实例。
                                                     如果为 None，则会创建一个新的实例。
        """
        self.data_path = data_path
        self.fs_manager = fs_manager or FileSystemManager(data_path)
        self.logger = LoggerConfig.get_logger("simple_search_strategy")

    def build_index(self, **kwargs: Any) -> None:
        """此策略不需要预先构建索引。"""
        pass

    def update_index(self, entry: Entry, **kwargs: Any) -> None:
        """此策略不需要更新索引。"""
        pass

    def search(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        在所有条目中执行不区分大小写的搜索。

        Args:
            query (str): 搜索关键词。
            **kwargs: 包含搜索选项的字典，例如:
                      search_in_title (bool): 是否在标题中搜索。
                      search_in_content (bool): 是否在内容中搜索。
                      search_in_tags (bool): 是否在标签中搜索。

        Returns:
            List[Dict[str, Any]]: 搜索结果列表。
                                  每个结果是一个包含 'entry' 和 'category_path' 的字典。
        """
        if not query or not query.strip():
            return []

        search_in_title = kwargs.get('search_in_title', True)
        search_in_content = kwargs.get('search_in_content', True)
        search_in_tags = kwargs.get('search_in_tags', True)

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

                    except (FileNotFoundError, PermissionError, OSError) as e:
                        log_exception(self.logger, f"搜索时访问文件 {file_path}", e)
                        continue
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        log_exception(self.logger, f"搜索时解析文件 {file_path}", e)
                        continue
        return results


class SearchService:
    """
    搜索服务类，作为策略管理器，将搜索任务委托给具体的搜索策略。
    """

    def __init__(self, strategy: SearchStrategy):
        """
        初始化搜索服务。

        Args:
            strategy (SearchStrategy): 用于执行搜索的策略实例。
        """
        self.strategy = strategy

    def build_index(self, **kwargs: Any) -> None:
        """构建搜索索引（委托给策略）。"""
        self.strategy.build_index(**kwargs)

    def update_index(self, entry: Entry, **kwargs: Any) -> None:
        """更新搜索索引（委托给策略）。"""
        self.strategy.update_index(entry, **kwargs)

    def search(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        执行搜索（委托给策略）。

        Args:
            query (str): 搜索关键词。
            **kwargs: 传递给策略的其他搜索参数。

        Returns:
            List[Dict[str, Any]]: 搜索结果。
        """
        return self.strategy.search(query, **kwargs)
