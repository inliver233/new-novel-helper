"""
向量存储管理器 - 负责向量的持久化存储和检索
使用JSON文件作为简单的存储后端，便于调试和快速实现
"""

import os
import json
import threading
from typing import Dict, List, Optional, Any
from ..utils.logger import LoggerConfig, log_exception, log_file_operation


class EmbeddingStore:
    """向量存储管理器，负责向量的保存、加载和管理"""
    
    def __init__(self, storage_path: str):
        """
        初始化向量存储
        
        Args:
            storage_path: 存储文件路径，通常为 data/embeddings.json
        """
        self.storage_path = storage_path
        self.logger = LoggerConfig.get_logger("embedding_store")
        
        # 内存缓存，提高访问速度
        self._cache: Dict[str, List[float]] = {}
        self._cache_loaded = False
        
        # 线程锁，确保并发安全
        self._lock = threading.RLock()
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # 初始化时加载现有数据
        self._load_cache()
    
    def _load_cache(self) -> None:
        """从文件加载向量数据到内存缓存"""
        with self._lock:
            if self._cache_loaded:
                return
                
            try:
                if os.path.exists(self.storage_path):
                    with open(self.storage_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # 验证数据格式
                    if isinstance(data, dict):
                        self._cache = data
                        self.logger.info(f"成功加载 {len(self._cache)} 个向量到缓存")
                    else:
                        self.logger.warning("向量文件格式不正确，使用空缓存")
                        self._cache = {}
                else:
                    self.logger.info("向量文件不存在，使用空缓存")
                    self._cache = {}
                    
                self._cache_loaded = True
                
            except Exception as e:
                self.logger.error(f"加载向量缓存失败: {str(e)}")
                log_exception(e, "embedding_store_load_error")
                self._cache = {}
                self._cache_loaded = True
    
    def _save_cache(self) -> None:
        """将内存缓存保存到文件"""
        try:
            # 创建临时文件，避免写入过程中文件损坏
            temp_path = self.storage_path + ".tmp"
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            
            # 原子性替换文件
            if os.path.exists(self.storage_path):
                os.replace(temp_path, self.storage_path)
            else:
                os.rename(temp_path, self.storage_path)
            
            log_file_operation("save", self.storage_path, f"保存 {len(self._cache)} 个向量")
            self.logger.info(f"成功保存 {len(self._cache)} 个向量到文件")
            
        except Exception as e:
            self.logger.error(f"保存向量缓存失败: {str(e)}")
            log_exception(e, "embedding_store_save_error")
            
            # 清理临时文件
            temp_path = self.storage_path + ".tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            raise Exception(f"保存向量失败: {str(e)}")
    
    def load_embeddings(self) -> Dict[str, List[float]]:
        """
        加载所有向量数据
        
        Returns:
            Dict[str, List[float]]: entry_uuid到向量的映射
        """
        with self._lock:
            self._load_cache()
            return self._cache.copy()
    
    def save_embeddings(self, embeddings: Dict[str, List[float]]) -> None:
        """
        批量保存向量数据
        
        Args:
            embeddings: entry_uuid到向量的映射
        """
        with self._lock:
            self._cache.update(embeddings)
            self._save_cache()
    
    def get_embedding(self, entry_uuid: str) -> Optional[List[float]]:
        """
        获取指定条目的向量
        
        Args:
            entry_uuid: 条目UUID
            
        Returns:
            Optional[List[float]]: 向量数据，如果不存在则返回None
        """
        with self._lock:
            self._load_cache()
            return self._cache.get(entry_uuid)
    
    def add_or_update_embedding(self, entry_uuid: str, embedding: List[float]) -> None:
        """
        添加或更新单个条目的向量
        
        Args:
            entry_uuid: 条目UUID
            embedding: 向量数据
        """
        with self._lock:
            self._cache[entry_uuid] = embedding
            self._save_cache()
    
    def remove_embedding(self, entry_uuid: str) -> bool:
        """
        删除指定条目的向量
        
        Args:
            entry_uuid: 条目UUID
            
        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if entry_uuid in self._cache:
                del self._cache[entry_uuid]
                self._save_cache()
                self.logger.info(f"删除向量: {entry_uuid}")
                return True
            return False
    
    def has_embedding(self, entry_uuid: str) -> bool:
        """
        检查是否存在指定条目的向量
        
        Args:
            entry_uuid: 条目UUID
            
        Returns:
            bool: 是否存在向量
        """
        with self._lock:
            self._load_cache()
            return entry_uuid in self._cache
    
    def get_missing_embeddings(self, entry_uuids: List[str]) -> List[str]:
        """
        获取缺失向量的条目UUID列表
        
        Args:
            entry_uuids: 要检查的条目UUID列表
            
        Returns:
            List[str]: 缺失向量的条目UUID列表
        """
        with self._lock:
            self._load_cache()
            return [uuid for uuid in entry_uuids if uuid not in self._cache]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            self._load_cache()
            
            stats = {
                "total_embeddings": len(self._cache),
                "storage_path": self.storage_path,
                "file_exists": os.path.exists(self.storage_path),
                "file_size": 0
            }
            
            if stats["file_exists"]:
                try:
                    stats["file_size"] = os.path.getsize(self.storage_path)
                except:
                    pass
            
            return stats
    
    def clear_all(self) -> None:
        """清空所有向量数据"""
        with self._lock:
            self._cache.clear()
            self._save_cache()
            self.logger.warning("已清空所有向量数据")
    
    def backup(self, backup_path: str) -> bool:
        """
        备份向量数据
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            with self._lock:
                self._load_cache()
                
                # 确保备份目录存在
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"成功备份向量数据到: {backup_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"备份向量数据失败: {str(e)}")
            log_exception(e, "embedding_store_backup_error")
            return False
