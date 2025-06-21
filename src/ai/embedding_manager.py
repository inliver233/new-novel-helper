"""
向量管理器 - 协调向量存储和API客户端
负责按需生成、缓存和管理条目的向量表示
"""

import time
from typing import List, Dict, Optional, Any
from ..models.entry import Entry
from ..utils.logger import LoggerConfig, log_exception
from .siliconflow_client import SiliconFlowClient
from .embedding_store import EmbeddingStore


class EmbeddingManager:
    """向量管理器，负责条目向量的生成、存储和检索"""
    
    def __init__(self, business_manager, sf_client: SiliconFlowClient, embedding_store: EmbeddingStore):
        """
        初始化向量管理器
        
        Args:
            business_manager: 业务管理器实例，用于获取条目数据
            sf_client: SiliconFlow API客户端
            embedding_store: 向量存储管理器
        """
        self.business_manager = business_manager
        self.sf_client = sf_client
        self.embedding_store = embedding_store
        self.logger = LoggerConfig.get_logger("embedding_manager")
        
        # 批处理配置
        self.batch_size = 10  # 每批处理的条目数量
        self.batch_delay = 1.0  # 批次间延迟（秒）
    
    def ensure_embeddings_for_entries(self, entry_uuids: List[str], model: str) -> Dict[str, List[float]]:
        """
        确保指定条目都有向量表示，缺失的会自动生成
        
        Args:
            entry_uuids: 条目UUID列表
            model: 使用的向量化模型
            
        Returns:
            Dict[str, List[float]]: UUID到向量的映射
            
        Raises:
            Exception: 向量生成失败时抛出异常
        """
        try:
            # 检查哪些条目缺少向量
            missing_uuids = self.embedding_store.get_missing_embeddings(entry_uuids)
            
            if missing_uuids:
                self.logger.info(f"需要生成 {len(missing_uuids)} 个条目的向量")
                self._generate_missing_embeddings(missing_uuids, model)
            else:
                self.logger.info("所有条目都已有向量")
            
            # 返回所有请求条目的向量
            result = {}
            for uuid in entry_uuids:
                embedding = self.embedding_store.get_embedding(uuid)
                if embedding:
                    result[uuid] = embedding
                else:
                    self.logger.warning(f"条目 {uuid} 的向量仍然缺失")
            
            return result
            
        except Exception as e:
            error_msg = f"确保条目向量失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "embedding_manager_ensure_error")
            raise Exception(error_msg)
    
    def get_entry_embedding(self, entry_uuid: str, model: str) -> Optional[List[float]]:
        """
        获取单个条目的向量，如果不存在则生成
        
        Args:
            entry_uuid: 条目UUID
            model: 使用的向量化模型
            
        Returns:
            Optional[List[float]]: 向量数据，失败时返回None
        """
        try:
            # 先尝试从存储中获取
            embedding = self.embedding_store.get_embedding(entry_uuid)
            if embedding:
                return embedding
            
            # 如果不存在，则生成
            self.logger.info(f"为条目 {entry_uuid} 生成向量")
            entry = self._get_entry_by_uuid(entry_uuid)
            if entry:
                embedding = self._generate_and_store_embedding(entry, model)
                return embedding
            else:
                self.logger.warning(f"找不到条目: {entry_uuid}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取条目向量失败 {entry_uuid}: {str(e)}")
            log_exception(e, "embedding_manager_get_error")
            return None
    
    def _generate_missing_embeddings(self, missing_uuids: List[str], model: str) -> None:
        """
        批量生成缺失的向量
        
        Args:
            missing_uuids: 缺失向量的条目UUID列表
            model: 使用的向量化模型
        """
        total_count = len(missing_uuids)
        processed_count = 0
        
        # 分批处理
        for i in range(0, total_count, self.batch_size):
            batch_uuids = missing_uuids[i:i + self.batch_size]
            
            try:
                self.logger.info(f"处理批次 {i//self.batch_size + 1}, 条目数: {len(batch_uuids)}")
                
                # 获取批次中的所有条目
                batch_entries = []
                batch_texts = []
                valid_uuids = []
                
                for uuid in batch_uuids:
                    entry = self._get_entry_by_uuid(uuid)
                    if entry:
                        batch_entries.append(entry)
                        batch_texts.append(self._prepare_text_for_embedding(entry))
                        valid_uuids.append(uuid)
                    else:
                        self.logger.warning(f"跳过无效条目: {uuid}")
                
                if not batch_texts:
                    continue
                
                # 批量生成向量
                embeddings = self.sf_client.get_embeddings(batch_texts, model)
                
                # 保存向量
                embedding_dict = {}
                for uuid, embedding in zip(valid_uuids, embeddings):
                    embedding_dict[uuid] = embedding
                
                self.embedding_store.save_embeddings(embedding_dict)
                processed_count += len(valid_uuids)
                
                self.logger.info(f"成功处理 {len(valid_uuids)} 个条目的向量")
                
                # 批次间延迟，避免API限流
                if i + self.batch_size < total_count:
                    time.sleep(self.batch_delay)
                    
            except Exception as e:
                self.logger.error(f"批次处理失败: {str(e)}")
                log_exception(e, "embedding_manager_batch_error")
                # 继续处理下一批次
                continue
        
        self.logger.info(f"批量向量生成完成，成功处理: {processed_count}/{total_count}")
    
    def _generate_and_store_embedding(self, entry: Entry, model: str) -> Optional[List[float]]:
        """
        为单个条目生成并存储向量
        
        Args:
            entry: 条目对象
            model: 使用的向量化模型
            
        Returns:
            Optional[List[float]]: 生成的向量，失败时返回None
        """
        try:
            # 准备文本
            text = self._prepare_text_for_embedding(entry)
            
            # 生成向量
            embedding = self.sf_client.get_embedding(text, model)
            
            # 存储向量
            self.embedding_store.add_or_update_embedding(entry.uuid, embedding)
            
            self.logger.info(f"成功生成并存储条目向量: {entry.uuid}")
            return embedding
            
        except Exception as e:
            self.logger.error(f"生成条目向量失败 {entry.uuid}: {str(e)}")
            log_exception(e, "embedding_manager_generate_error")
            return None
    
    def _prepare_text_for_embedding(self, entry: Entry) -> str:
        """
        准备用于向量化的文本
        
        Args:
            entry: 条目对象
            
        Returns:
            str: 准备好的文本
        """
        # 组合标题和内容，标题权重更高
        text_parts = []
        
        # 添加标题（重复3次增加权重）
        if entry.title:
            text_parts.extend([entry.title] * 3)
        
        # 添加内容
        if entry.content:
            text_parts.append(entry.content)
        
        # 添加标签
        if entry.tags:
            tags_text = " ".join(entry.tags)
            text_parts.append(f"标签: {tags_text}")
        
        return " ".join(text_parts)
    
    def _get_entry_by_uuid(self, entry_uuid: str) -> Optional[Entry]:
        """
        根据UUID获取条目对象
        
        Args:
            entry_uuid: 条目UUID
            
        Returns:
            Optional[Entry]: 条目对象，找不到时返回None
        """
        try:
            # 遍历所有分类查找条目
            categories = self.business_manager.get_categories()
            
            for category in categories:
                category_path = category.get("path", "")
                try:
                    entries = self.business_manager.get_entries_in_category(category_path)
                    for entry in entries:
                        if entry.uuid == entry_uuid:
                            return entry
                except Exception as e:
                    self.logger.warning(f"搜索分类 {category_path} 时出错: {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"根据UUID获取条目失败 {entry_uuid}: {str(e)}")
            return None
    
    def remove_entry_embedding(self, entry_uuid: str) -> bool:
        """
        删除条目的向量
        
        Args:
            entry_uuid: 条目UUID
            
        Returns:
            bool: 是否成功删除
        """
        return self.embedding_store.remove_embedding(entry_uuid)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取向量管理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        store_stats = self.embedding_store.get_statistics()
        
        return {
            "embedding_store": store_stats,
            "batch_size": self.batch_size,
            "batch_delay": self.batch_delay
        }
