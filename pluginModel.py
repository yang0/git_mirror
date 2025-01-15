from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, Text, Enum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import Dict, Any
import shortuuid
from enum import Enum as PyEnum

class PluginRepoName(Base):
    """插件仓库名称模型"""
    __tablename__ = "plugin_repo_name"
    
    plugin_repo_name = Column(String(255), primary_key=True)
    plugin_key = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('plugin_repo_name', name='uk_plugin_repo_name'),
        Index('idx_plugin_repo_name', plugin_repo_name, created_at),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_repo_name": self.plugin_repo_name,
            "plugin_key": self.plugin_key,
            "created_at": self.created_at
        }
