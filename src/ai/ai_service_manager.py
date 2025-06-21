"""
AI服务管理器 - 统一管理AI相关服务
基于Cherry Studio模式，提供统一的AI服务接口
"""

from typing import Optional, Dict, Any, List
import os
from ..utils.logger import LoggerConfig, log_exception


class AIServiceManager:
    """AI服务管理器，统一管理所有AI相关服务"""
    
    def __init__(self, business_manager, config_manager):
        """
        初始化AI服务管理器
        
        Args:
            business_manager: 业务管理器实例
            config_manager: 配置管理器实例
        """
        self.business_manager = business_manager
        self.config_manager = config_manager
        self.logger = LoggerConfig.get_logger("ai_service_manager")
        
        # AI服务组件
        self.sf_client = None
        self.embedding_store = None
        self.embedding_manager = None
        self.rag_engine = None
        
        # 服务状态
        self.services_initialized = False
        self.last_error = None
        
        # 自动初始化
        self.initialize_services()
    
    def initialize_services(self) -> bool:
        """
        初始化所有AI服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检查配置
            if not self._check_configuration():
                self.logger.info("AI配置不完整，跳过服务初始化")
                return False
            
            # 初始化各个服务组件
            if not self._initialize_siliconflow_client():
                return False
                
            if not self._initialize_embedding_services():
                return False
                
            if not self._initialize_rag_engine():
                return False
            
            self.services_initialized = True
            self.last_error = None
            self.logger.info("AI服务初始化成功")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"AI服务初始化失败: {e}")
            log_exception(e, "ai_service_manager_init_error")
            self.services_initialized = False
            return False
    
    def _check_configuration(self) -> bool:
        """检查AI配置是否完整"""
        try:
            # 检查RAG配置
            rag_api_key = self.config_manager.get_rag_api_key()
            if not rag_api_key or not rag_api_key.strip():
                return False
            
            # 检查必要的模型配置
            embedding_model = self.config_manager.get_embedding_model()
            chat_model = self.config_manager.get_rag_chat_model()
            
            if not embedding_model or not chat_model:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"配置检查失败: {e}")
            return False
    
    def _initialize_siliconflow_client(self) -> bool:
        """初始化SiliconFlow客户端"""
        try:
            from .siliconflow_client import SiliconFlowClient
            
            api_key = self.config_manager.get_rag_api_key()
            base_url = self.config_manager.get_rag_base_url()
            
            self.sf_client = SiliconFlowClient(api_key, base_url)
            return True
            
        except Exception as e:
            self.logger.error(f"SiliconFlow客户端初始化失败: {e}")
            return False
    
    def _initialize_embedding_services(self) -> bool:
        """初始化向量化相关服务"""
        try:
            from .embedding_store import EmbeddingStore
            from .embedding_manager import EmbeddingManager
            
            # 初始化向量存储
            data_path = self.business_manager.data_path
            embedding_file = os.path.join(data_path, "embeddings.json")
            self.embedding_store = EmbeddingStore(embedding_file)
            
            # 初始化向量管理器
            self.embedding_manager = EmbeddingManager(
                self.business_manager, 
                self.sf_client, 
                self.embedding_store
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"向量化服务初始化失败: {e}")
            return False
    
    def _initialize_rag_engine(self) -> bool:
        """初始化RAG引擎"""
        try:
            from .rag_engine import RagEngine
            
            self.rag_engine = RagEngine(
                self.business_manager,
                self.sf_client,
                self.embedding_manager
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"RAG引擎初始化失败: {e}")
            return False
    
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        return self.services_initialized and self.rag_engine is not None
    
    def is_chat_available(self) -> bool:
        """检查普通聊天服务是否可用"""
        return self.config_manager.is_chat_configured()
    
    def is_rag_available(self) -> bool:
        """检查RAG服务是否可用"""
        return self.is_available()
    
    def get_rag_config(self) -> Dict[str, Any]:
        """获取RAG配置"""
        return {
            "embedding_model": self.config_manager.get_embedding_model(),
            "rerank_model": self.config_manager.get_rerank_model(),
            "chat_model": self.config_manager.get_rag_chat_model(),
            "rag_top_k_retrieval": self.config_manager.get_rag_top_k_retrieval(),
            "rag_top_k_rerank": self.config_manager.get_rag_top_k_rerank()
        }
    
    def get_chat_config(self) -> Dict[str, Any]:
        """获取聊天配置"""
        return {
            "api_key": self.config_manager.get_chat_api_key(),
            "base_url": self.config_manager.get_chat_base_url(),
            "model": self.config_manager.get_chat_model(),
            "temperature": self.config_manager.get_chat_temperature(),
            "max_tokens": self.config_manager.get_chat_max_tokens()
        }
    
    def ask_with_rag(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        使用RAG进行问答
        
        Args:
            query: 用户查询
            history: 对话历史
            
        Returns:
            str: AI回答
        """
        try:
            if not self.is_rag_available():
                if not self.initialize_services():
                    return "RAG服务暂不可用，请检查配置。"
            
            config = self.get_rag_config()
            return self.rag_engine.answer(query, history, config)
            
        except Exception as e:
            error_msg = f"RAG问答失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "ai_service_manager_rag_error")
            return f"抱歉，处理您的问题时出现了错误：{str(e)}"
    
    def test_rag_connection(self) -> bool:
        """测试RAG连接"""
        try:
            if not self.sf_client:
                self.initialize_services()
            
            if self.sf_client:
                return self.sf_client.test_connection()
            
            return False
            
        except Exception as e:
            self.logger.error(f"RAG连接测试失败: {e}")
            return False
    
    def test_chat_connection(self) -> bool:
        """测试普通聊天连接"""
        try:
            from .streaming_client import StreamingConfig, StreamingAIClient
            
            chat_config = self.get_chat_config()
            config = StreamingConfig(
                api_key=chat_config["api_key"],
                base_url=chat_config["base_url"],
                model=chat_config["model"]
            )
            
            client = StreamingAIClient(config)
            
            # 这里需要异步测试，暂时返回配置是否完整
            return bool(chat_config["api_key"] and chat_config["api_key"].strip())
            
        except Exception as e:
            self.logger.error(f"聊天连接测试失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取AI服务统计信息"""
        stats = {
            "services_initialized": self.services_initialized,
            "rag_available": self.is_rag_available(),
            "chat_available": self.is_chat_available(),
            "last_error": self.last_error,
            "embedding_store": None,
            "embedding_manager": None
        }
        
        if self.embedding_store:
            stats["embedding_store"] = self.embedding_store.get_statistics()
        
        if self.embedding_manager:
            stats["embedding_manager"] = self.embedding_manager.get_statistics()
        
        return stats
    
    def reload_configuration(self) -> bool:
        """重新加载配置并重新初始化服务"""
        self.services_initialized = False
        self.sf_client = None
        self.embedding_store = None
        self.embedding_manager = None
        self.rag_engine = None
        
        return self.initialize_services()
