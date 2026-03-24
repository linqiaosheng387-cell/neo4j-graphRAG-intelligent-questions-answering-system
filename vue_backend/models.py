"""
SQLAlchemy ORM 模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
import enum

# ==================== 枚举类型 ====================
class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"

class QAStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    error = "error"

class GraphStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    processing = "processing"
    failed = "failed"

class DataUploadStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class LogLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ==================== 用户表 ====================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # 关系
    qa_records = relationship("QARecord", back_populates="user", cascade="all, delete-orphan")
    knowledge_graphs = relationship("KnowledgeGraph", back_populates="creator", cascade="all, delete-orphan")
    data_uploads = relationship("DataUpload", back_populates="user", cascade="all, delete-orphan")
    system_logs = relationship("SystemLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

# ==================== 问答记录表 ====================
class QARecord(Base):
    __tablename__ = "qa_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(String(1000), nullable=False)
    answer = Column(Text, nullable=True)
    graph_id = Column(Integer, ForeignKey("knowledge_graphs.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Enum(QAStatus), default=QAStatus.pending, index=True)
    response_time = Column(Integer, nullable=True)  # 毫秒
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="qa_records")
    graph = relationship("KnowledgeGraph", back_populates="qa_records")

    def __repr__(self):
        return f"<QARecord(id={self.id}, user_id={self.user_id}, status={self.status})>"

# ==================== 知识图谱表 ====================
class KnowledgeGraph(Base):
    __tablename__ = "knowledge_graphs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Enum(GraphStatus), default=GraphStatus.inactive, index=True)
    entity_count = Column(Integer, default=0)
    relation_count = Column(Integer, default=0)
    neo4j_db_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    creator = relationship("User", back_populates="knowledge_graphs")
    qa_records = relationship("QARecord", back_populates="graph", cascade="all, delete-orphan")
    data_uploads = relationship("DataUpload", back_populates="graph", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeGraph(id={self.id}, name={self.name}, status={self.status})>"

# ==================== 数据上传记录表 ====================
class DataUpload(Base):
    __tablename__ = "data_uploads"

    id = Column(Integer, primary_key=True, index=True)
    upload_name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_id = Column(Integer, ForeignKey("knowledge_graphs.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Enum(DataUploadStatus), default=DataUploadStatus.pending, index=True)
    entities_file = Column(String(500), nullable=True)
    relationships_file = Column(String(500), nullable=True)
    text_units_file = Column(String(500), nullable=True)
    communities_file = Column(String(500), nullable=True)
    community_reports_file = Column(String(500), nullable=True)
    documents_file = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="data_uploads")
    graph = relationship("KnowledgeGraph", back_populates="data_uploads")

    def __repr__(self):
        return f"<DataUpload(id={self.id}, upload_name={self.upload_name}, status={self.status})>"

# ==================== 系统日志表 ====================
class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_level = Column(Enum(LogLevel), default=LogLevel.INFO, index=True)
    module = Column(String(100), nullable=True, index=True)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = relationship("User", back_populates="system_logs")

    def __repr__(self):
        return f"<SystemLog(id={self.id}, log_level={self.log_level})>"

# ==================== 用户访问日志表 ====================
class UserAccessLog(Base):
    __tablename__ = "user_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), nullable=False, index=True)
    port = Column(Integer, nullable=True)
    domain = Column(String(255), nullable=True)
    device_info = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # 毫秒
    access_time = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<UserAccessLog(id={self.id}, ip_address={self.ip_address})>"

# ==================== IP访问统计表 ====================
class IPStatistics(Base):
    __tablename__ = "ip_statistics"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), unique=True, nullable=False, index=True)
    visit_count = Column(Integer, default=0, index=True)
    device_info = Column(String(500), nullable=True)
    first_access_time = Column(DateTime, nullable=True)
    last_access_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<IPStatistics(ip_address={self.ip_address}, visit_count={self.visit_count})>"

# ==================== 实时问题表 ====================
class RealTimeQuestion(Base):
    __tablename__ = "real_time_questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    question = Column(String(1000), nullable=False)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = relationship("User", back_populates="real_time_questions")

    def __repr__(self):
        return f"<RealTimeQuestion(id={self.id}, question={self.question})>"
