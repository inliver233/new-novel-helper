"""
RAG引擎 - 检索增强生成的核心实现
整合搜索、向量化、重排序和对话生成的完整流程
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from ..models.entry import Entry
from ..utils.logger import LoggerConfig, log_exception
from .siliconflow_client import SiliconFlowClient
from .embedding_manager import EmbeddingManager


class RagEngine:
    """RAG引擎，实现检索增强生成的完整流程"""
    
    def __init__(self, business_manager, sf_client: SiliconFlowClient, embedding_manager: EmbeddingManager):
        """
        初始化RAG引擎
        
        Args:
            business_manager: 业务管理器实例
            sf_client: SiliconFlow API客户端
            embedding_manager: 向量管理器
        """
        self.business_manager = business_manager
        self.sf_client = sf_client
        self.embedding_manager = embedding_manager
        self.logger = LoggerConfig.get_logger("rag_engine")
    
    def answer(self, query: str, history: List[Dict[str, str]] = None, 
               config: Optional[Dict[str, Any]] = None) -> str:
        """
        RAG主流程：根据查询生成答案
        
        Args:
            query: 用户查询
            history: 对话历史，格式为[{"role": "user", "content": "..."}, ...]
            config: 配置参数，包含模型名称和参数
            
        Returns:
            str: 生成的答案
            
        Raises:
            Exception: RAG流程失败时抛出异常
        """
        try:
            if not query or not query.strip():
                return "请输入有效的问题。"
            
            # 使用默认配置
            if config is None:
                config = self._get_default_config()
            
            self.logger.info(f"开始RAG流程，查询: {query[:100]}...")
            
            # 1. 召回阶段：使用现有搜索服务获取候选条目
            candidate_entries = self._retrieve_candidates(query, config)
            reranked_entries = []

            if candidate_entries:
                # 2. 向量化阶段：确保候选条目都有向量
                entry_embeddings = self._ensure_candidate_embeddings(candidate_entries, config)

                # 3. 初筛阶段：基于向量相似度筛选
                top_entries = self._vector_similarity_filter(query, candidate_entries, entry_embeddings, config)

                if top_entries:
                    # 4. 重排序阶段：使用重排序模型精确排序
                    reranked_entries = self._rerank_entries(query, top_entries, config)

            # 5. 构建Prompt：组装知识片段和查询（即使没有找到相关条目也继续）
            prompt_messages = self._build_prompt(query, reranked_entries, history)

            # 6. 生成答案：调用对话模型
            answer = self._generate_answer(prompt_messages, config)
            
            self.logger.info("RAG流程完成")
            return answer
            
        except Exception as e:
            error_msg = f"RAG流程失败: {str(e)}"
            self.logger.error(error_msg)
            log_exception(e, "rag_engine_answer_error")
            return f"抱歉，处理您的问题时出现了错误：{str(e)}"
    
    def _retrieve_candidates(self, query: str, config: Dict[str, Any]) -> List[Entry]:
        """
        召回阶段：使用搜索服务获取候选条目

        Args:
            query: 查询文本
            config: 配置参数

        Returns:
            List[Entry]: 候选条目列表
        """
        try:
            # 使用现有的搜索服务
            print(f"DEBUG: 调用搜索服务，查询: {query}")
            search_results = self.business_manager.search_service.search(query)
            print(f"DEBUG: 搜索服务返回 {len(search_results)} 个结果")

            # 转换搜索结果为Entry对象
            candidate_entries = []
            for result in search_results:
                try:
                    # 搜索服务返回的格式是 {'entry': entry, 'category_path': root}
                    entry = result.get("entry")
                    category_path = result.get("category_path", "")

                    if entry:
                        # 从绝对目录路径中提取相对分类路径
                        relative_category_path = self._extract_category_path_from_dir(category_path)
                        print(f"DEBUG: 处理搜索结果条目: {entry.title}, 绝对路径: {category_path}, 相对路径: {relative_category_path}")

                        # 如果设置了分类过滤器，检查是否匹配
                        if hasattr(self, 'category_filter') and self.category_filter:
                            print(f"DEBUG: 检查分类过滤器: {self.category_filter}")
                            # 检查条目是否属于选中的分类
                            is_match = any(relative_category_path.startswith(selected_cat) for selected_cat in self.category_filter)
                            print(f"DEBUG: 分类匹配结果: {is_match}")
                            if not is_match:
                                print(f"DEBUG: 跳过不匹配的条目: {entry.title}")
                                continue  # 跳过不匹配的条目

                        candidate_entries.append(entry)
                        print(f"DEBUG: 添加候选条目: {entry.title}")
                except Exception as e:
                    self.logger.warning(f"获取搜索结果条目失败: {str(e)}")
                    continue

            # 限制候选数量
            max_candidates = config.get("max_candidates", 50)
            candidate_entries = candidate_entries[:max_candidates]

            self.logger.info(f"召回 {len(candidate_entries)} 个候选条目（分类过滤: {getattr(self, 'category_filter', None)}）")
            return candidate_entries

        except Exception as e:
            self.logger.error(f"召回阶段失败: {str(e)}")
            return []
    
    def _ensure_candidate_embeddings(self, candidates: List[Entry], config: Dict[str, Any]) -> Dict[str, List[float]]:
        """
        向量化阶段：确保候选条目都有向量
        
        Args:
            candidates: 候选条目列表
            config: 配置参数
            
        Returns:
            Dict[str, List[float]]: UUID到向量的映射
        """
        try:
            candidate_uuids = [entry.uuid for entry in candidates]
            embedding_model = config.get("embedding_model", "bge-large-zh-v1.5")
            
            embeddings = self.embedding_manager.ensure_embeddings_for_entries(
                candidate_uuids, embedding_model
            )
            
            self.logger.info(f"确保 {len(embeddings)} 个条目的向量")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"向量化阶段失败: {str(e)}")
            return {}
    
    def _vector_similarity_filter(self, query: str, candidates: List[Entry], 
                                 embeddings: Dict[str, List[float]], 
                                 config: Dict[str, Any]) -> List[Tuple[Entry, float]]:
        """
        初筛阶段：基于向量相似度筛选
        
        Args:
            query: 查询文本
            candidates: 候选条目列表
            embeddings: 条目向量映射
            config: 配置参数
            
        Returns:
            List[Tuple[Entry, float]]: (条目, 相似度分数) 的列表，按相似度降序排列
        """
        try:
            # 生成查询向量
            embedding_model = config.get("embedding_model", "bge-large-zh-v1.5")
            query_embedding = self.sf_client.get_embedding(query, embedding_model)
            
            if not query_embedding:
                self.logger.error("无法生成查询向量")
                return []
            
            # 计算相似度
            similarities = []
            query_vector = np.array(query_embedding).reshape(1, -1)
            
            for entry in candidates:
                entry_embedding = embeddings.get(entry.uuid)
                if entry_embedding:
                    entry_vector = np.array(entry_embedding).reshape(1, -1)
                    similarity = cosine_similarity(query_vector, entry_vector)[0][0]
                    similarities.append((entry, float(similarity)))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 取前K个
            top_k = config.get("rag_top_k_retrieval", 20)
            top_similarities = similarities[:top_k]
            
            self.logger.info(f"向量相似度筛选，保留前 {len(top_similarities)} 个条目")
            return top_similarities
            
        except Exception as e:
            self.logger.error(f"向量相似度筛选失败: {str(e)}")
            return []
    
    def _rerank_entries(self, query: str, top_entries: List[Tuple[Entry, float]], 
                       config: Dict[str, Any]) -> List[Entry]:
        """
        重排序阶段：使用重排序模型精确排序
        
        Args:
            query: 查询文本
            top_entries: 初筛后的条目列表
            config: 配置参数
            
        Returns:
            List[Entry]: 重排序后的条目列表
        """
        try:
            if not top_entries:
                return []
            
            # 准备文档文本
            documents = []
            entries = []
            
            for entry, _ in top_entries:
                doc_text = self._prepare_document_for_rerank(entry)
                documents.append(doc_text)
                entries.append(entry)
            
            # 调用重排序API
            rerank_model = config.get("rerank_model", "bge-reranker-base")
            top_k_rerank = config.get("rag_top_k_rerank", 5)
            
            rerank_results = self.sf_client.rerank(
                query=query,
                documents=documents,
                model=rerank_model,
                top_k=top_k_rerank
            )
            
            # 根据重排序结果重新排列条目
            reranked_entries = []
            for result in rerank_results:
                index = result.get("index", -1)
                if 0 <= index < len(entries):
                    reranked_entries.append(entries[index])
            
            self.logger.info(f"重排序完成，最终选择 {len(reranked_entries)} 个条目")
            return reranked_entries
            
        except Exception as e:
            self.logger.warning(f"重排序失败，使用原始排序: {str(e)}")
            # 如果重排序失败，返回原始的前N个条目
            top_k_rerank = config.get("rag_top_k_rerank", 5)
            return [entry for entry, _ in top_entries[:top_k_rerank]]

    def _build_prompt(self, query: str, entries: List[Entry],
                     history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        构建Prompt：组装知识片段和查询

        Args:
            query: 用户查询
            entries: 相关条目列表（可能为空）
            history: 对话历史

        Returns:
            List[Dict[str, str]]: 消息列表
        """
        # 构建系统提示
        if entries:
            # 有相关条目时，构建知识库内容
            knowledge_parts = []
            for i, entry in enumerate(entries, 1):
                content = f"【条目{i}：{entry.title}】\n{entry.content}"
                if entry.tags:
                    content += f"\n标签：{', '.join(entry.tags)}"
                knowledge_parts.append(content)

            knowledge_text = "\n\n".join(knowledge_parts)

            system_prompt = f"""你是一个专业的小说创作助手，基于用户提供的知识库内容来回答问题。

知识库内容：
{knowledge_text}

请根据以上知识库内容回答用户的问题。要求：
1. 优先使用知识库中的信息
2. 如果知识库中没有直接相关的信息，可以基于你的知识进行合理推测和建议
3. 回答要准确、详细且有条理
4. 可以结合多个条目的信息进行综合回答
5. 保持专业和友好的语调"""
        else:
            # 没有相关条目时，使用通用的小说创作助手提示
            system_prompt = """你是一个专业的小说创作助手。虽然在当前知识库中没有找到直接相关的信息，但你可以基于你的专业知识来帮助用户。

请回答用户的问题，要求：
1. 基于你的专业知识提供有用的建议和信息
2. 如果是关于小说创作的问题，提供具体的写作技巧和建议
3. 回答要准确、详细且有条理
4. 可以提供相关的例子和参考
5. 保持专业和友好的语调
6. 如果合适，可以建议用户在知识库中添加相关内容以便将来参考"""

        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]

        # 添加历史对话（最近的几轮）
        if history:
            # 只保留最近的4轮对话，避免上下文过长
            recent_history = history[-8:]  # 4轮对话 = 8条消息
            messages.extend(recent_history)

        # 添加当前查询
        messages.append({"role": "user", "content": query})

        return messages

    def _generate_answer(self, messages: List[Dict[str, str]], config: Dict[str, Any]) -> str:
        """
        生成答案：调用对话模型

        Args:
            messages: 消息列表
            config: 配置参数

        Returns:
            str: 生成的答案
        """
        try:
            chat_model = config.get("chat_model", "deepseek-ai/deepseek-v2")

            # 调用对话API
            response = self.sf_client.chat_completion(
                messages=messages,
                model=chat_model,
                temperature=0.7,
                max_tokens=2000
            )

            # 提取答案
            choices = response.get("choices", [])
            if choices:
                answer = choices[0].get("message", {}).get("content", "")
                if answer:
                    return answer.strip()

            return "抱歉，无法生成回答。"

        except Exception as e:
            self.logger.error(f"生成答案失败: {str(e)}")
            return f"生成答案时出现错误：{str(e)}"

    def _prepare_document_for_rerank(self, entry: Entry) -> str:
        """
        为重排序准备文档文本

        Args:
            entry: 条目对象

        Returns:
            str: 准备好的文档文本
        """
        parts = [entry.title]
        if entry.content:
            # 限制内容长度，避免重排序API的长度限制
            content = entry.content[:500] + "..." if len(entry.content) > 500 else entry.content
            parts.append(content)
        if entry.tags:
            parts.append(f"标签: {', '.join(entry.tags)}")

        return " ".join(parts)

    def _extract_category_path(self, file_path: str) -> str:
        """
        从文件路径中提取分类路径

        Args:
            file_path: 文件路径

        Returns:
            str: 分类路径
        """
        try:
            # 移除文件名，保留目录路径
            import os
            dir_path = os.path.dirname(file_path)

            # 移除数据根目录前缀
            data_path = self.business_manager.data_path
            if dir_path.startswith(data_path):
                category_path = dir_path[len(data_path):].lstrip(os.sep)
                return category_path

            return dir_path

        except Exception as e:
            self.logger.warning(f"提取分类路径失败: {str(e)}")
            return ""

    def _extract_category_path_from_dir(self, dir_path: str) -> str:
        """
        从目录路径中提取分类路径

        Args:
            dir_path: 目录路径

        Returns:
            str: 分类路径
        """
        try:
            import os

            # 移除数据根目录前缀
            data_path = self.business_manager.data_path
            print(f"DEBUG: 数据根目录: {data_path}")
            print(f"DEBUG: 目录路径: {dir_path}")

            if dir_path.startswith(data_path):
                category_path = dir_path[len(data_path):].lstrip(os.sep)
                print(f"DEBUG: 提取的分类路径: '{category_path}'")
                return category_path

            print(f"DEBUG: 目录路径不以数据根目录开头，返回原路径")
            return dir_path

        except Exception as e:
            self.logger.warning(f"从目录路径提取分类路径失败: {str(e)}")
            return ""

    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            "embedding_model": "bge-large-zh-v1.5",
            "rerank_model": "bge-reranker-base",
            "chat_model": "deepseek-ai/deepseek-v2",
            "rag_top_k_retrieval": 20,
            "rag_top_k_rerank": 5,
            "max_candidates": 50
        }
