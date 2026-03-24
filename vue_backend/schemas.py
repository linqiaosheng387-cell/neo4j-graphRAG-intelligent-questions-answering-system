"""
Pydantic 数据验证模型 (请求/响应模式)
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

# ==================== 枚举 ====================
class QAStatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"
    error = "error"

class GraphStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    processing = "processing"
    failed = "failed"

class DataUploadStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class LogLevelEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ==================== 问答记录相关 ====================
class QARecordCreate(BaseModel):
    user_id: int
    question: str
    graph_id: Optional[int] = None

class QARecordUpdate(BaseModel):
    answer: Optional[str] = None
    status: Optional[QAStatusEnum] = None
    response_time: Optional[int] = None
    error_message: Optional[str] = None

class QARecordResponse(BaseModel):
    id: int
    user_id: int
    question: str
    answer: Optional[str]
    graph_id: Optional[int]
    status: QAStatusEnum
    response_time: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QARecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[QARecordResponse]

# ==================== 知识图谱相关 ====================
class KnowledgeGraphCreate(BaseModel):
    name: str
    description: Optional[str] = None
    neo4j_db_name: Optional[str] = None

class KnowledgeGraphUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GraphStatusEnum] = None
    entity_count: Optional[int] = None
    relation_count: Optional[int] = None
    neo4j_db_name: Optional[str] = None

class KnowledgeGraphResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: Optional[int]
    status: GraphStatusEnum
    entity_count: int
    relation_count: int
    neo4j_db_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KnowledgeGraphListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[KnowledgeGraphResponse]

# ==================== 数据上传相关 ====================
class DataUploadCreate(BaseModel):
    upload_name: str
    graph_id: Optional[int] = None

class DataUploadUpdate(BaseModel):
    status: Optional[DataUploadStatusEnum] = None
    error_message: Optional[str] = None

class DataUploadResponse(BaseModel):
    id: int
    upload_name: str
    user_id: int
    graph_id: Optional[int]
    status: DataUploadStatusEnum
    entities_file: Optional[str]
    relationships_file: Optional[str]
    text_units_file: Optional[str]
    communities_file: Optional[str]
    community_reports_file: Optional[str]
    documents_file: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DataUploadListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[DataUploadResponse]

# ==================== 系统日志相关 ====================
class SystemLogResponse(BaseModel):
    id: int
    log_level: LogLevelEnum
    module: Optional[str]
    message: str
    stack_trace: Optional[str]
    solution: Optional[str]
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class SystemLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[SystemLogResponse]

# ==================== IP统计相关 ====================
class IPStatisticsResponse(BaseModel):
    id: int
    ip_address: str
    visit_count: int
    device_info: Optional[str]
    first_access_time: Optional[datetime]
    last_access_time: datetime

    class Config:
        from_attributes = True


# ==================== 枚举 ====================
class UserRoleEnum(str, Enum):
    admin = "admin"
    user = "user"

class QAStatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"
    error = "error"

class GraphStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    processing = "processing"
    failed = "failed"

class DataUploadStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class LogLevelEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ==================== 用户相关 ====================
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRoleEnum = UserRoleEnum.user

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRoleEnum
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

# ==================== 问答记录相关 ====================
class QARecordCreate(BaseModel):
    user_id: int
    question: str = Field(..., min_length=1, max_length=1000)
    graph_id: Optional[int] = None

class QARecordUpdate(BaseModel):
    answer: Optional[str] = None
    status: Optional[QAStatusEnum] = None
    response_time: Optional[int] = None
    error_message: Optional[str] = None

class QARecordResponse(BaseModel):
    id: int
    user_id: int
    question: str
    answer: Optional[str]
    graph_id: Optional[int]
    status: QAStatusEnum
    response_time: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QARecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[QARecordResponse]

# ==================== 知识图谱相关 ====================
class KnowledgeGraphCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    neo4j_db_name: Optional[str] = None

class KnowledgeGraphUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[GraphStatusEnum] = None
    entity_count: Optional[int] = None
    relation_count: Optional[int] = None
    neo4j_db_name: Optional[str] = None

class KnowledgeGraphResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: Optional[int]
    status: GraphStatusEnum
    entity_count: int
    relation_count: int
    neo4j_db_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KnowledgeGraphListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[KnowledgeGraphResponse]

# ==================== 数据上传相关 ====================
class DataUploadCreate(BaseModel):
    upload_name: str = Field(..., min_length=1, max_length=100)
    graph_id: Optional[int] = None

class DataUploadUpdate(BaseModel):
    status: Optional[DataUploadStatusEnum] = None
    error_message: Optional[str] = None

class DataUploadResponse(BaseModel):
    id: int
    upload_name: str
    user_id: int
    graph_id: Optional[int]
    status: DataUploadStatusEnum
    entities_file: Optional[str]
    relationships_file: Optional[str]
    text_units_file: Optional[str]
    communities_file: Optional[str]
    community_reports_file: Optional[str]
    documents_file: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DataUploadListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[DataUploadResponse]

# ==================== Neo4j配置相关 ====================
class Neo4jConfigCreate(BaseModel):
    config_name: str = Field(..., min_length=1, max_length=100)
    host: str = Field(..., min_length=1, max_length=100)
    port: int = Field(default=7687, ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=255)
    database_name: str = Field(..., min_length=1, max_length=100)
    is_default: bool = False

class Neo4jConfigUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: Optional[str] = None
    is_default: Optional[bool] = None

class Neo4jConfigResponse(BaseModel):
    id: int
    config_name: str
    host: str
    port: int
    username: str
    database_name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Neo4jConfigListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[Neo4jConfigResponse]

# ==================== 系统日志相关 ====================
class SystemLogCreate(BaseModel):
    log_level: LogLevelEnum = LogLevelEnum.INFO
    module: Optional[str] = None
    message: str = Field(..., min_length=1)
    stack_trace: Optional[str] = None
    solution: Optional[str] = None
    user_id: Optional[int] = None

class SystemLogResponse(BaseModel):
    id: int
    log_level: LogLevelEnum
    module: Optional[str]
    message: str
    stack_trace: Optional[str]
    solution: Optional[str]
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class SystemLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[SystemLogResponse]

# ==================== 用户访问日志相关 ====================
class UserAccessLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    ip_address: str
    port: Optional[int]
    domain: Optional[str]
    device_info: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    response_time: Optional[int]
    access_time: datetime

    class Config:
        from_attributes = True

class UserAccessLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[UserAccessLogResponse]

# ==================== 访问统计相关 ====================
class AccessStatisticsResponse(BaseModel):
    id: int
    stat_date: str
    total_visits: int
    unique_users: int
    unique_ips: int
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== IP统计相关 ====================
class IPStatisticsResponse(BaseModel):
    id: int
    ip_address: str
    visit_count: int
    device_info: Optional[str]
    first_access_time: Optional[datetime]
    last_access_time: datetime

    class Config:
        from_attributes = True

class IPStatisticsListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[IPStatisticsResponse]

# ==================== 实时问题相关 ====================
class RealTimeQuestionResponse(BaseModel):
    id: int
    user_id: Optional[int]
    question: str
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class RealTimeQuestionListResponse(BaseModel):
    total: int
    data: List[RealTimeQuestionResponse]

# ==================== 通用响应 ====================
class SuccessResponse(BaseModel):
    code: int = 200
    message: str = "Success"
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    code: int = 400
    message: str = "Error"
    error: Optional[str] = None
