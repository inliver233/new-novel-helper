# -*- coding: utf-8 -*-
"""
定义了搜索策略的抽象基类。

该模块提供了一个标准化的接口，用于实现各种不同的搜索算法。
通过继承 `SearchStrategy`，可以轻松地创建和集成新的搜索实现，
例如基于全文索引、向量搜索或其他技术的策略。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SearchStrategy(ABC):
    """
    搜索策略的抽象基类 (ABC)。

    定义了所有搜索策略必须实现的通用接口，以确保它们可以
    在搜索服务中互换使用。
    """

    @abstractmethod
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        根据给定的查询执行搜索。

        这是执行搜索的核心方法。具体的实现将决定如何根据查询
        查找并返回匹配的条目。

        Args:
            query (str): 用户输入的搜索关键词。
            **kwargs: 额外的搜索参数，用于未来的扩展，例如按类别、
                      标签或日期范围进行过滤。

        Returns:
            List[Dict[str, Any]]: 搜索结果列表。每个结果是一个字典，
                                 应包含与 `SearchService` 期望的
                                 格式一致的字段，例如 'entry_id', 'title',
                                 'preview', 'path' 等。
        """
        raise NotImplementedError

    @abstractmethod
    def build_index(self) -> None:
        """
        构建或初始化搜索索引。

        对于需要预先建立索引的搜索策略（如全文搜索），此方法
        应包含构建索引的逻辑。对于简单的文件扫描策略，此方法
        可以为空。
        """
        raise NotImplementedError

    @abstractmethod
    def update_index(self, entry_path: str) -> None:
        """
        当单个条目发生变化时，增量更新索引。

        此方法用于在创建、更新或删除单个文件时，对现有索引进行
        快速的增量更新，避免完全重建索引带来的性能开销。

        Args:
            entry_path (str): 已更改（创建/更新/删除）的条目的文件路径。
        """
        raise NotImplementedError