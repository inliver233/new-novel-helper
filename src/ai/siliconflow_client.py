"""
硅基流动API客户端 - 封装与SiliconFlow平台的HTTP通信
支持Embedding、Rerank和Chat Completion三种API调用
"""

import json
import requests
from typing import List, Dict, Any, Optional
from ..utils.logger import LoggerConfig, log_exception


class SiliconFlowClient:
    """硅基流动API客户端，提供OpenAI兼容的API接口"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1"):
        """
        初始化客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.logger = LoggerConfig.get_logger("siliconflow_client")
        
        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_embedding(self, text: str, model: str) -> List[float]:
        """
        获取单个文本的向量表示
        
        Args:
            text: 要向量化的文本
            model: 使用的模型名称
            
        Returns:
            List[float]: 向量表示
            
        Raises:
            Exception: API调用失败时抛出异常
        """
        embeddings = self.get_embeddings([text], model)
        return embeddings[0] if embeddings else []
    
    def get_embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        """
        批量获取文本的向量表示
        
        Args:
            texts: 要向量化的文本列表
            model: 使用的模型名称
            
        Returns:
            List[List[float]]: 向量表示列表
            
        Raises:
            Exception: API调用失败时抛出异常
        """
        url = f"{self.base_url}/embeddings"
        
        payload = {
            "model": model,
            "input": texts
        }
        
        try:
            self.logger.info(f"调用Embedding API，文本数量: {len(texts)}, 模型: {model}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 提取向量数据
            embeddings = []
            for item in result.get("data", []):
                embeddings.append(item.get("embedding", []))
            
            self.logger.info(f"成功获取 {len(embeddings)} 个向量")
            return embeddings
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Embedding API调用失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "siliconflow_embedding_error")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Embedding处理失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "siliconflow_embedding_processing_error")
            raise Exception(error_msg)
    
    def rerank(self, query: str, documents: List[str], model: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 待排序的文档列表
            model: 使用的重排序模型
            top_k: 返回前k个结果，如果为None则返回所有结果
            
        Returns:
            List[Dict]: 重排序结果，包含index、document和score字段
            
        Raises:
            Exception: API调用失败时抛出异常
        """
        url = f"{self.base_url}/rerank"
        
        payload = {
            "model": model,
            "query": query,
            "documents": documents
        }
        
        if top_k is not None:
            payload["top_k"] = top_k
        
        try:
            self.logger.info(f"调用Rerank API，查询: {query[:50]}..., 文档数量: {len(documents)}, 模型: {model}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 提取重排序结果
            rerank_results = result.get("results", [])
            
            self.logger.info(f"成功重排序 {len(rerank_results)} 个文档")
            return rerank_results
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Rerank API调用失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "siliconflow_rerank_error")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Rerank处理失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "siliconflow_rerank_processing_error")
            raise Exception(error_msg)
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """
        进行对话生成
        
        Args:
            messages: 对话消息列表，格式为[{"role": "user", "content": "..."}]
            model: 使用的对话模型
            **kwargs: 其他参数，如temperature、max_tokens等
            
        Returns:
            Dict: API响应结果
            
        Raises:
            Exception: API调用失败时抛出异常
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        try:
            self.logger.info(f"调用Chat API，消息数量: {len(messages)}, 模型: {model}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            self.logger.info("成功获取对话响应")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Chat API调用失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "siliconflow_chat_error")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Chat处理失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "siliconflow_chat_processing_error")
            raise Exception(error_msg)
    
    def test_connection(self) -> bool:
        """
        测试API连接是否正常

        Returns:
            bool: 连接是否成功
        """
        try:
            # 使用一个简单的chat请求来测试连接
            test_messages = [{"role": "user", "content": "Hello"}]
            response = self.chat_completion(
                messages=test_messages,
                model="Qwen/Qwen2-7B-Instruct",
                max_tokens=10,
                temperature=0.1
            )

            # 检查响应格式
            if "choices" in response and len(response["choices"]) > 0:
                return True
            else:
                self.logger.error("API响应格式不正确")
                return False

        except Exception as e:
            self.logger.error(f"API连接测试失败: {str(e)}")
            return False
