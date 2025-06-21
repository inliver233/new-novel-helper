"""
消息管理器
负责消息和对话的存储、检索、更新等操作
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .models import (
    Message, MessageBlock, Conversation, Citation, Usage,
    MessageRole, MessageStatus, BlockType, BlockStatus,
    create_user_message, create_assistant_message, create_text_block
)


class MessageManager:
    """消息管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    model_id TEXT,
                    system_prompt TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    model_id TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    usage_prompt_tokens INTEGER,
                    usage_completion_tokens INTEGER,
                    usage_total_tokens INTEGER,
                    metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS message_blocks (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    content TEXT,
                    metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    url TEXT,
                    score REAL,
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_blocks_message ON message_blocks(message_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_citations_message ON citations(message_id)")
    
    # 对话管理
    def create_conversation(self, title: str = "新对话", **kwargs) -> Conversation:
        """创建新对话"""
        conversation = Conversation(title=title, **kwargs)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations 
                (id, title, model_id, system_prompt, temperature, max_tokens, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation.id, conversation.title, conversation.model_id,
                conversation.system_prompt, conversation.temperature, conversation.max_tokens,
                json.dumps(conversation.metadata), conversation.created_at.isoformat(),
                conversation.updated_at.isoformat()
            ))
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 获取消息ID列表
            message_cursor = conn.execute(
                "SELECT id FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conversation_id,)
            )
            message_ids = [row[0] for row in message_cursor.fetchall()]
            
            return Conversation(
                id=row['id'],
                title=row['title'],
                messages=message_ids,
                model_id=row['model_id'],
                system_prompt=row['system_prompt'] or "",
                temperature=row['temperature'] or 0.7,
                max_tokens=row['max_tokens'] or 2000,
                metadata=json.loads(row['metadata'] or '{}'),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
    
    def list_conversations(self, limit: int = 50) -> List[Conversation]:
        """列出对话"""
        conversations = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
            
            for row in cursor.fetchall():
                # 获取消息ID列表
                message_cursor = conn.execute(
                    "SELECT id FROM messages WHERE conversation_id = ? ORDER BY created_at",
                    (row['id'],)
                )
                message_ids = [msg_row[0] for msg_row in message_cursor.fetchall()]
                
                conversation = Conversation(
                    id=row['id'],
                    title=row['title'],
                    messages=message_ids,
                    model_id=row['model_id'],
                    system_prompt=row['system_prompt'] or "",
                    temperature=row['temperature'] or 0.7,
                    max_tokens=row['max_tokens'] or 2000,
                    metadata=json.loads(row['metadata'] or '{}'),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                conversations.append(conversation)
        
        return conversations
    
    def update_conversation(self, conversation: Conversation):
        """更新对话"""
        conversation.updated_at = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE conversations 
                SET title = ?, model_id = ?, system_prompt = ?, temperature = ?, 
                    max_tokens = ?, metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                conversation.title, conversation.model_id, conversation.system_prompt,
                conversation.temperature, conversation.max_tokens,
                json.dumps(conversation.metadata), conversation.updated_at.isoformat(),
                conversation.id
            ))
    
    def delete_conversation(self, conversation_id: str):
        """删除对话"""
        with sqlite3.connect(self.db_path) as conn:
            # 删除相关的引用
            conn.execute("DELETE FROM citations WHERE message_id IN (SELECT id FROM messages WHERE conversation_id = ?)", (conversation_id,))
            # 删除相关的消息块
            conn.execute("DELETE FROM message_blocks WHERE message_id IN (SELECT id FROM messages WHERE conversation_id = ?)", (conversation_id,))
            # 删除相关的消息
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            # 删除对话
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    
    # 消息管理
    def add_message(self, message: Message) -> Message:
        """添加消息"""
        with sqlite3.connect(self.db_path) as conn:
            # 插入消息
            usage_data = message.usage
            conn.execute("""
                INSERT INTO messages 
                (id, conversation_id, role, status, model_id, temperature, max_tokens,
                 usage_prompt_tokens, usage_completion_tokens, usage_total_tokens,
                 metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.id, message.conversation_id, message.role.value, message.status.value,
                message.model_id, message.temperature, message.max_tokens,
                usage_data.prompt_tokens if usage_data else None,
                usage_data.completion_tokens if usage_data else None,
                usage_data.total_tokens if usage_data else None,
                json.dumps(message.metadata), message.created_at.isoformat(),
                message.updated_at.isoformat()
            ))
            
            # 插入引用
            for citation in message.citations:
                conn.execute("""
                    INSERT INTO citations (id, message_id, title, content, source, url, score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    citation.id, message.id, citation.title, citation.content,
                    citation.source, citation.url, citation.score
                ))
        
        return message
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """获取消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 获取消息基本信息
            cursor = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 获取消息块ID列表
            block_cursor = conn.execute(
                "SELECT id FROM message_blocks WHERE message_id = ? ORDER BY created_at",
                (message_id,)
            )
            block_ids = [block_row[0] for block_row in block_cursor.fetchall()]
            
            # 获取引用
            citation_cursor = conn.execute("SELECT * FROM citations WHERE message_id = ?", (message_id,))
            citations = []
            for citation_row in citation_cursor.fetchall():
                citation = Citation(
                    id=citation_row['id'],
                    title=citation_row['title'] or "",
                    content=citation_row['content'] or "",
                    source=citation_row['source'] or "",
                    url=citation_row['url'],
                    score=citation_row['score'] or 0.0
                )
                citations.append(citation)
            
            # 构建Usage对象
            usage = None
            if row['usage_total_tokens']:
                usage = Usage(
                    prompt_tokens=row['usage_prompt_tokens'] or 0,
                    completion_tokens=row['usage_completion_tokens'] or 0,
                    total_tokens=row['usage_total_tokens'] or 0
                )
            
            return Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=MessageRole(row['role']),
                status=MessageStatus(row['status']),
                blocks=block_ids,
                citations=citations,
                usage=usage,
                model_id=row['model_id'],
                temperature=row['temperature'],
                max_tokens=row['max_tokens'],
                metadata=json.loads(row['metadata'] or '{}'),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
    
    def get_conversation_messages(self, conversation_id: str) -> List[Message]:
        """获取对话的所有消息"""
        messages = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conversation_id,)
            )
            
            for row in cursor.fetchall():
                message = self.get_message(row['id'])
                if message:
                    messages.append(message)
        
        return messages

    def update_message(self, message: Message):
        """更新消息"""
        message.updated_at = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            usage_data = message.usage
            conn.execute("""
                UPDATE messages
                SET status = ?, model_id = ?, temperature = ?, max_tokens = ?,
                    usage_prompt_tokens = ?, usage_completion_tokens = ?, usage_total_tokens = ?,
                    metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                message.status.value, message.model_id, message.temperature, message.max_tokens,
                usage_data.prompt_tokens if usage_data else None,
                usage_data.completion_tokens if usage_data else None,
                usage_data.total_tokens if usage_data else None,
                json.dumps(message.metadata), message.updated_at.isoformat(),
                message.id
            ))

    # 消息块管理
    def add_message_block(self, block: MessageBlock) -> MessageBlock:
        """添加消息块"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO message_blocks
                (id, message_id, type, status, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block.id, block.message_id, block.type.value, block.status.value,
                block.content, json.dumps(block.metadata),
                block.created_at.isoformat(), block.updated_at.isoformat()
            ))

        return block

    def get_message_block(self, block_id: str) -> Optional[MessageBlock]:
        """获取消息块"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM message_blocks WHERE id = ?", (block_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return MessageBlock(
                id=row['id'],
                message_id=row['message_id'],
                type=BlockType(row['type']),
                status=BlockStatus(row['status']),
                content=row['content'] or "",
                metadata=json.loads(row['metadata'] or '{}'),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )

    def get_message_blocks(self, message_id: str) -> List[MessageBlock]:
        """获取消息的所有块"""
        blocks = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM message_blocks WHERE message_id = ? ORDER BY created_at",
                (message_id,)
            )

            for row in cursor.fetchall():
                block = MessageBlock(
                    id=row['id'],
                    message_id=row['message_id'],
                    type=BlockType(row['type']),
                    status=BlockStatus(row['status']),
                    content=row['content'] or "",
                    metadata=json.loads(row['metadata'] or '{}'),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                blocks.append(block)

        return blocks

    def update_message_block(self, block: MessageBlock):
        """更新消息块"""
        block.updated_at = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE message_blocks
                SET status = ?, content = ?, metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                block.status.value, block.content, json.dumps(block.metadata),
                block.updated_at.isoformat(), block.id
            ))

    def get_message_text_content(self, message: Message) -> str:
        """获取消息的文本内容"""
        blocks = self.get_message_blocks(message.id)
        text_blocks = [block for block in blocks if block.type == BlockType.TEXT]
        return "\n".join([block.content for block in text_blocks])

    # 搜索功能
    def search_messages(self, query: str, conversation_id: Optional[str] = None, limit: int = 50) -> List[Message]:
        """搜索消息"""
        messages = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 构建SQL查询
            sql = """
                SELECT DISTINCT m.id
                FROM messages m
                JOIN message_blocks mb ON m.id = mb.message_id
                WHERE mb.content LIKE ?
            """
            params = [f"%{query}%"]

            if conversation_id:
                sql += " AND m.conversation_id = ?"
                params.append(conversation_id)

            sql += " ORDER BY m.created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)

            for row in cursor.fetchall():
                message = self.get_message(row['id'])
                if message:
                    messages.append(message)

        return messages

    # 导出功能
    def export_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """导出对话"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return {}

        messages_data = []
        for message in self.get_conversation_messages(conversation_id):
            blocks_data = []
            for block in self.get_message_blocks(message.id):
                blocks_data.append(block.to_dict())

            message_data = message.to_dict()
            message_data['blocks_data'] = blocks_data
            messages_data.append(message_data)

        return {
            "conversation": conversation.to_dict(),
            "messages": messages_data,
            "exported_at": datetime.now().isoformat()
        }

    # 清理功能
    def clear_conversation(self, conversation_id: str):
        """清空对话消息"""
        with sqlite3.connect(self.db_path) as conn:
            # 删除相关的引用
            conn.execute("DELETE FROM citations WHERE message_id IN (SELECT id FROM messages WHERE conversation_id = ?)", (conversation_id,))
            # 删除相关的消息块
            conn.execute("DELETE FROM message_blocks WHERE message_id IN (SELECT id FROM messages WHERE conversation_id = ?)", (conversation_id,))
            # 删除相关的消息
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))

            # 更新对话的更新时间
            conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (datetime.now().isoformat(), conversation_id))


# 工厂函数
def create_message_manager(db_path: str) -> MessageManager:
    """创建消息管理器"""
    return MessageManager(db_path)
