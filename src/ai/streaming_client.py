"""
流式AI客户端
基于Cherry Studio的流式处理设计，支持OpenAI兼容API
"""

import json
import asyncio
import logging

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None
from typing import Dict, List, Optional, AsyncGenerator, Callable, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import time

from .models import StreamChunk, Message, MessageRole, Citation


@dataclass
class StreamingConfig:
    """流式配置"""
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = True
    timeout: int = 30


class StreamingAIClient:
    """流式AI客户端"""
    
    def __init__(self, config: StreamingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    async def create_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """创建流式聊天完成"""

        if not AIOHTTP_AVAILABLE:
            yield StreamChunk(type="error", content="aiohttp库未安装，请运行: pip install aiohttp")
            return

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
            **kwargs
        }

        try:
            # 优化连接器设置以提高性能
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )

            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=10,
                sock_read=30
            )

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                read_bufsize=8192  # 优化读取缓冲区
            ) as session:
                async with session.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status} - {error_text}")

                    # 批量处理流式数据以提高性能
                    buffer = ""
                    async for chunk in response.content.iter_chunked(1024):  # 1KB块读取
                        buffer += chunk.decode('utf-8', errors='ignore')

                        # 按行分割处理
                        lines = buffer.split('\n')
                        buffer = lines[-1]  # 保留最后一个可能不完整的行

                        for line in lines[:-1]:
                            line = line.strip()
                            if not line:
                                continue

                            if line.startswith('data: '):
                                data_str = line[6:]  # 移除 'data: ' 前缀

                                if data_str == '[DONE]':
                                    yield StreamChunk(type="complete")
                                    return

                                try:
                                    data = json.loads(data_str)
                                    chunk = self._parse_stream_chunk(data)
                                    if chunk:
                                        yield chunk
                                except json.JSONDecodeError as e:
                                    self.logger.warning(f"解析JSON失败: {e}, 数据: {data_str}")
                                    continue

        except Exception as e:
            self.logger.error(f"流式请求失败: {e}")
            yield StreamChunk(type="error", content=str(e))
    
    def _parse_stream_chunk(self, data: Dict[str, Any]) -> Optional[StreamChunk]:
        """解析流式响应块"""
        try:
            choices = data.get('choices', [])
            if not choices:
                return None
            
            choice = choices[0]
            delta = choice.get('delta', {})
            
            # 处理内容增量
            if 'content' in delta and delta['content']:
                return StreamChunk(
                    type="text_delta",
                    content=delta['content']
                )
            
            # 处理完成信号
            finish_reason = choice.get('finish_reason')
            if finish_reason:
                return StreamChunk(
                    type="text_complete",
                    metadata={"finish_reason": finish_reason}
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"解析流式块失败: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            messages = [{"role": "user", "content": "Hello"}]
            async for chunk in self.create_chat_completion_stream(messages):
                if chunk.type in ["text_delta", "complete"]:
                    return True
                elif chunk.type == "error":
                    return False
            return False
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False


class StreamingWorker(QThread):
    """流式处理工作线程"""
    
    # 信号定义
    chunk_received = pyqtSignal(dict)  # 接收到流式块
    stream_started = pyqtSignal()      # 流开始
    stream_finished = pyqtSignal()     # 流结束
    error_occurred = pyqtSignal(str)   # 发生错误
    
    def __init__(self, client: StreamingAIClient, messages: List[Dict[str, str]], **kwargs):
        super().__init__()
        self.client = client
        self.messages = messages
        self.kwargs = kwargs
        self._stop_requested = False
    
    def run(self):
        """运行流式处理"""
        try:
            asyncio.run(self._stream_process())
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    async def _stream_process(self):
        """异步流式处理"""
        try:
            self.stream_started.emit()
            
            async for chunk in self.client.create_chat_completion_stream(self.messages, **self.kwargs):
                if self._stop_requested:
                    break
                
                self.chunk_received.emit(chunk.to_dict())
                
                if chunk.type == "complete":
                    break
                elif chunk.type == "error":
                    self.error_occurred.emit(chunk.content)
                    break
            
            self.stream_finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """停止流式处理"""
        self._stop_requested = True


class RAGStreamingClient(StreamingAIClient):
    """支持RAG的流式客户端"""

    def __init__(self, config: StreamingConfig, rag_engine=None):
        super().__init__(config)
        self.rag_engine = rag_engine
        self.selected_knowledge_bases = []  # 选中的知识库

    async def create_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """重写父类方法，集成RAG功能"""
        print(f"DEBUG: RAG客户端被调用，有RAG引擎: {self.rag_engine is not None}")
        print(f"DEBUG: 消息数量: {len(messages) if messages else 0}")

        if self.rag_engine and messages:
            # 获取最后一条用户消息作为查询
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break

            print(f"DEBUG: 用户消息: {user_message}")
            if user_message:
                print("DEBUG: 开始RAG流式处理")
                # 使用RAG流式完成
                async for chunk in self.create_rag_completion_stream(user_message, **kwargs):
                    yield chunk
                return

        print("DEBUG: 使用普通流式完成")
        # 如果没有RAG引擎或没有用户消息，使用普通流式完成
        async for chunk in super().create_chat_completion_stream(messages, **kwargs):
            yield chunk
    
    async def create_rag_completion_stream(
        self,
        query: str,
        conversation_history: List[Message] = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """创建RAG流式完成"""
        print(f"DEBUG: create_rag_completion_stream 被调用，查询: {query}")

        # 1. 先进行知识库检索
        citations = []
        if self.rag_engine:
            try:
                print("DEBUG: 有RAG引擎，开始检索")

                # 发送检索开始信号
                yield StreamChunk(type="retrieval_start", content="正在检索相关信息...")

                # 执行检索
                print("DEBUG: 调用 _search_knowledge_base")
                search_results = await self._search_knowledge_base(query)
                print(f"DEBUG: 检索结果: {len(search_results)} 个")

                if search_results:
                    # 创建引用
                    for result in search_results:
                        citation = Citation(
                            title=result.get("title", ""),
                            content=result.get("content", ""),
                            source="knowledge_base",
                            score=result.get("score", 0.0)
                        )
                        citations.append(citation)

                    # 创建了引用

                    # 发送引用信息
                    yield StreamChunk(
                        type="citations",
                        metadata={"citations": [c.to_dict() for c in citations]}
                    )

                # 发送检索完成信号
                yield StreamChunk(type="retrieval_complete")

            except Exception as e:
                self.logger.warning(f"知识库检索失败: {e}")
                yield StreamChunk(type="retrieval_error", content=str(e))
        
        # 2. 构建增强的提示词
        enhanced_messages = self._build_rag_messages(query, citations, conversation_history)
        
        # 3. 调用AI生成回复 - 直接调用父类方法避免无限递归
        async for chunk in super().create_chat_completion_stream(enhanced_messages, **kwargs):
            yield chunk
    
    async def _search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """搜索知识库"""
        print(f"DEBUG: _search_knowledge_base 被调用，查询: {query}")
        if not self.rag_engine:
            print("DEBUG: 没有RAG引擎")
            return []

        try:
            # 使用RAG引擎进行检索
            # 由于RAG引擎是同步的，我们在异步环境中调用它
            loop = asyncio.get_event_loop()

            # 如果有选中的知识库，设置到RAG引擎中
            print(f"DEBUG: hasattr(self, 'selected_knowledge_bases'): {hasattr(self, 'selected_knowledge_bases')}")
            if hasattr(self, 'selected_knowledge_bases'):
                print(f"DEBUG: self.selected_knowledge_bases = {self.selected_knowledge_bases}")

            if hasattr(self, 'selected_knowledge_bases') and self.selected_knowledge_bases:
                print(f"DEBUG: 有选中的知识库: {self.selected_knowledge_bases}")
                # 转换绝对路径为相对路径
                import os
                data_path = self.rag_engine.business_manager.data_path
                print(f"DEBUG: data_path = {data_path}")
                relative_paths = []
                for abs_path in self.selected_knowledge_bases:
                    if abs_path.startswith(data_path):
                        rel_path = abs_path[len(data_path):].lstrip(os.sep)
                        relative_paths.append(rel_path)
                        print(f"DEBUG: 转换 {abs_path} -> {rel_path}")
                    else:
                        relative_paths.append(abs_path)
                        print(f"DEBUG: 保持 {abs_path}")

                print(f"DEBUG: 转换后的相对路径: {relative_paths}")

                # 临时设置选中的知识库到RAG引擎
                original_filter = getattr(self.rag_engine, 'category_filter', None)
                self.rag_engine.category_filter = relative_paths
                print(f"DEBUG: 设置category_filter = {relative_paths}")

                try:
                    # 获取候选条目
                    print("DEBUG: 调用 _retrieve_candidates")
                    candidates = await loop.run_in_executor(
                        None,
                        self.rag_engine._retrieve_candidates,
                        query,
                        self.rag_engine._get_default_config()
                    )
                    print(f"DEBUG: _retrieve_candidates 返回 {len(candidates)} 个候选条目")
                finally:
                    # 恢复原始过滤器
                    if original_filter is not None:
                        self.rag_engine.category_filter = original_filter
                    else:
                        delattr(self.rag_engine, 'category_filter')
            else:
                # 没有选中知识库，搜索所有
                candidates = await loop.run_in_executor(
                    None,
                    self.rag_engine._retrieve_candidates,
                    query,
                    self.rag_engine._get_default_config()
                )

            # 转换为引用格式
            citations = []
            for entry in candidates[:5]:  # 最多返回5个引用
                citation_data = {
                    "title": entry.title,
                    "content": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                    "source": "knowledge_base",
                    "score": 0.8  # 默认分数
                }
                citations.append(citation_data)

            return citations

        except Exception as e:
            self.logger.error(f"知识库搜索失败: {e}")
            return []
    
    def _build_rag_messages(
        self,
        query: str,
        citations: List[Citation],
        conversation_history: List[Message] = None
    ) -> List[Dict[str, str]]:
        """构建RAG增强的消息"""

        # 如果有RAG引擎，使用它来构建更智能的提示词
        if self.rag_engine and citations:
            try:
                # 将Citation转换为Entry对象（简化版）
                from ..models.entry import Entry
                entries = []
                for citation in citations:
                    # 创建临时Entry对象用于RAG引擎
                    entry = Entry(
                        title=citation.title,
                        content=citation.content,
                        tags=[],
                        uuid=citation.id
                    )
                    entries.append(entry)

                # 构建对话历史
                history = []
                if conversation_history:
                    for msg in conversation_history[-8:]:  # 最近4轮对话
                        if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                            content = msg.get_text_content()
                            if content:
                                history.append({
                                    "role": msg.role.value,
                                    "content": content
                                })

                # 使用RAG引擎构建提示词
                messages = self.rag_engine._build_prompt(query, entries, history)
                return messages

            except Exception as e:
                self.logger.warning(f"使用RAG引擎构建提示词失败，使用默认方式: {e}")

        # 默认的消息构建方式
        messages = []

        # 添加系统提示词
        if citations:
            context = "\n\n".join([f"【{c.title}】\n{c.content}" for c in citations])
            system_prompt = f"""你是一个专业的AI助手。请基于以下参考资料回答用户的问题：

参考资料：
{context}

请注意：
1. 优先使用参考资料中的信息回答问题
2. 如果参考资料不足以回答问题，可以结合你的知识进行补充
3. 回答要准确、详细、有条理
4. 如果引用了参考资料，请在回答中适当标注"""
        else:
            system_prompt = """你是一个专业的AI助手。虽然没有找到直接相关的参考资料，但请基于你的知识为用户提供有帮助的回答。"""

        messages.append({"role": "system", "content": system_prompt})

        # 添加对话历史（如果有）
        if conversation_history:
            for msg in conversation_history[-10:]:  # 只保留最近10条消息
                if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                    content = msg.get_text_content()
                    if content:
                        messages.append({
                            "role": msg.role.value,
                            "content": content
                        })

        # 添加当前用户问题
        messages.append({"role": "user", "content": query})

        return messages


# 工厂函数
def create_streaming_client(config: StreamingConfig) -> StreamingAIClient:
    """创建流式客户端"""
    return StreamingAIClient(config)


def create_rag_streaming_client(config: StreamingConfig, rag_engine=None) -> RAGStreamingClient:
    """创建RAG流式客户端"""
    return RAGStreamingClient(config, rag_engine)
