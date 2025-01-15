import os
from dotenv import load_dotenv
from pathlib import Path

# 加载.env文件
load_dotenv()

# 数据库配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME', 'autotask')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')

# Git镜像配置
GIT_MIRROR_BASE_PATH = os.getenv('GIT_MIRROR_BASE_PATH', 'G:/temp/git_mirrors')
GIT_DAEMON_PORT = int(os.getenv('GIT_DAEMON_PORT', 9418))

# 构建数据库URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"

