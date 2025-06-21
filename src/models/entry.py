import dataclasses
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

@dataclasses.dataclass
class Entry:
    """代表一个内容条目的数据模型"""
    uuid: str
    title: str
    content: str
    tags: List[str] = dataclasses.field(default_factory=list)
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)
    attachments: List[Dict[str, str]] = dataclasses.field(default_factory=list)
    version: int = 1

    def __post_init__(self):
        """初始化后处理，确保元数据完整"""
        if not self.metadata:
            current_time = datetime.now(timezone.utc).isoformat()
            self.metadata = {
                "created_at": current_time,
                "updated_at": current_time,
                "word_count": self._calculate_word_count(self.content)
            }
        elif "word_count" not in self.metadata:
            self.metadata["word_count"] = self._calculate_word_count(self.content)

    @classmethod
    def create_new(cls, title: str, content: str = "", tags: Optional[List[str]] = None) -> "Entry":
        """创建一个新的条目实例"""
        current_time = datetime.now(timezone.utc).isoformat()
        return cls(
            uuid=str(uuid.uuid4()),
            title=title,
            content=content,
            tags=tags or [],
            metadata={
                "created_at": current_time,
                "updated_at": current_time,
                "word_count": cls._calculate_word_count(content)
            },
            attachments=[],
            version=1
        )

    def update_content(self, title: Optional[str] = None, content: Optional[str] = None,
                      tags: Optional[List[str]] = None):
        """更新条目内容并自动更新元数据"""
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
            self.metadata["word_count"] = self._calculate_word_count(content)
        if tags is not None:
            self.tags = tags

        self.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """将Entry对象转换为字典，用于JSON序列化"""
        return {
            "uuid": self.uuid,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "metadata": self.metadata,
            "attachments": self.attachments,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entry":
        """从字典创建Entry对象，用于JSON反序列化"""
        return cls(
            uuid=data.get("uuid", str(uuid.uuid4())),
            title=data.get("title", "无标题"),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            attachments=data.get("attachments", []),
            version=data.get("version", 1)
        )

    def to_json(self) -> str:
        """将Entry对象转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Entry":
        """从JSON字符串创建Entry对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_word_count(self) -> int:
        """获取内容字数"""
        return self.metadata.get("word_count", 0)

    def get_created_at(self) -> str:
        """获取创建时间"""
        return self.metadata.get("created_at", "")

    def get_updated_at(self) -> str:
        """获取更新时间"""
        return self.metadata.get("updated_at", "")

    @staticmethod
    def _calculate_word_count(content: str) -> int:
        """计算字数。
        对于中文环境，直接计算字符总数通常更符合用户对“字数”的预期。
        这个实现简单、高效且准确。
        """
        return len(content)