"""
AI对话模块的数据模型
基于Cherry Studio的设计理念，适配Python/PyQt6架构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
import uuid
import json


class MessageRole(Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(Enum):
    """消息状态"""
    PENDING = "pending"
    STREAMING = "streaming"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class BlockType(Enum):
    """消息块类型"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    CODE = "code"
    CITATION = "citation"
    THINKING = "thinking"


class BlockStatus(Enum):
    """消息块状态"""
    PENDING = "pending"
    STREAMING = "streaming"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class Citation:
    """引用信息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    source: str = ""  # 来源：knowledge_base, web_search等
    url: Optional[str] = None
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "score": self.score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Citation':
        return cls(**data)


@dataclass
class MessageBlock:
    """消息块 - 消息的基本组成单元"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = ""
    type: BlockType = BlockType.TEXT
    status: BlockStatus = BlockStatus.PENDING
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "type": self.type.value,
            "status": self.status.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageBlock':
        return cls(
            id=data["id"],
            message_id=data["message_id"],
            type=BlockType(data["type"]),
            status=BlockStatus(data["status"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class Usage:
    """Token使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Usage':
        return cls(**data)


@dataclass
class Message:
    """消息实体"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    role: MessageRole = MessageRole.USER
    status: MessageStatus = MessageStatus.PENDING
    blocks: List[str] = field(default_factory=list)  # MessageBlock的ID列表
    citations: List[Citation] = field(default_factory=list)
    usage: Optional[Usage] = None
    model_id: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_text_content(self) -> str:
        """获取消息的文本内容（需要配合MessageBlock使用）"""
        # 这个方法需要在实际使用时通过MessageManager来实现
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role.value,
            "status": self.status.value,
            "blocks": self.blocks,
            "citations": [c.to_dict() for c in self.citations],
            "usage": self.usage.to_dict() if self.usage else None,
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data["id"],
            conversation_id=data["conversation_id"],
            role=MessageRole(data["role"]),
            status=MessageStatus(data["status"]),
            blocks=data.get("blocks", []),
            citations=[Citation.from_dict(c) for c in data.get("citations", [])],
            usage=Usage.from_dict(data["usage"]) if data.get("usage") else None,
            model_id=data.get("model_id"),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class Conversation:
    """对话会话"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "新对话"
    messages: List[str] = field(default_factory=list)  # Message的ID列表
    model_id: Optional[str] = None
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "messages": self.messages,
            "model_id": self.model_id,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        return cls(
            id=data["id"],
            title=data["title"],
            messages=data.get("messages", []),
            model_id=data.get("model_id"),
            system_prompt=data.get("system_prompt", ""),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class StreamChunk:
    """流式响应块"""
    type: str  # text_delta, citation, thinking, complete等
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamChunk':
        return cls(
            type=data["type"],
            content=data.get("content", ""),
            metadata=data.get("metadata", {})
        )


# 工厂函数
def create_user_message(conversation_id: str, content: str, **kwargs) -> Message:
    """创建用户消息"""
    return Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        status=MessageStatus.SUCCESS,
        **kwargs
    )


def create_assistant_message(conversation_id: str, model_id: str, **kwargs) -> Message:
    """创建AI助手消息"""
    return Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        status=MessageStatus.PENDING,
        model_id=model_id,
        **kwargs
    )


def create_text_block(message_id: str, content: str, **kwargs) -> MessageBlock:
    """创建文本块"""
    return MessageBlock(
        message_id=message_id,
        type=BlockType.TEXT,
        content=content,
        status=BlockStatus.SUCCESS,
        **kwargs
    )


def create_citation_block(message_id: str, citation: Citation, **kwargs) -> MessageBlock:
    """创建引用块"""
    return MessageBlock(
        message_id=message_id,
        type=BlockType.CITATION,
        content=citation.content,
        metadata={"citation": citation.to_dict()},
        status=BlockStatus.SUCCESS,
        **kwargs
    )
