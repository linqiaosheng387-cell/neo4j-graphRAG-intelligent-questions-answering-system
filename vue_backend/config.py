"""
数据库配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MySQL数据库配置
SQLALCHEMY_DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/graphrag_admin2'
)

# SQLAlchemy配置
SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', 10))
SQLALCHEMY_POOL_RECYCLE = int(os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600))

# 应用配置
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
