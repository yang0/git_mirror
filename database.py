from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from databaseConfig import DATABASE_URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
import shortuuid
import logging
import traceback

logger = logging.getLogger(__name__)

# 优化连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 自动检测断开的连接
    pool_size=20,  # 增加连接池大小
    max_overflow=30,  # 增加最大溢出连接数
    pool_recycle=3600,  # 连接回收时间
    pool_timeout=30,  # 连接超时时间
    echo=False  # 不输出SQL语句
)

# 使用连接池创建会话
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 提交后不过期对象
)

class BaseModel:
    id = Column(String(22), primary_key=True, default=lambda: shortuuid.uuid(), index=True)
    
    def to_dict(self):
        """将模型转换为字典，并处理datetime类型"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    @staticmethod
    def serialize_dict(obj):
        """递归序列化字典中的datetime对象"""
        if isinstance(obj, dict):
            return {key: BaseModel.serialize_dict(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [BaseModel.serialize_dict(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj

Base = declarative_base(cls=BaseModel)

# 优化获取数据库连接的函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        import traceback
        logger.error(f"数据库会话异常: {str(e)}", exc_info=True)
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    finally:
        db.close()