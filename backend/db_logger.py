"""
数据库日志记录模块
记录问答系统的所有访问、问题和答案到后台管理系统的数据库
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 使用后台管理系统的数据库
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/graphrag_admin2"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class QuestionRecord(Base):
    """问答记录模型"""
    __tablename__ = "qa_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    mode = Column(String(50), default="global")
    status = Column(String(50), default="completed")
    response_time = Column(Float, nullable=True)  # 响应时间（毫秒）
    confidence = Column(Float, default=0.0)
    graph_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccessLog(Base):
    """访问日志模型"""
    __tablename__ = "user_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), nullable=False)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)  # 响应时间（毫秒）
    device_info = Column(String(255), nullable=True)
    user_agent = Column(Text, nullable=True)
    access_time = Column(DateTime, default=datetime.utcnow)


class IPStatistic(Base):
    """IP 统计模型"""
    __tablename__ = "ip_statistics"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), unique=True, nullable=False)
    visit_count = Column(Integer, default=1)
    device_info = Column(String(255), nullable=True)
    last_access_time = Column(DateTime, default=datetime.utcnow)
    first_access_time = Column(DateTime, default=datetime.utcnow)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_question(
    question: str,
    answer: str,
    mode: str = "global",
    response_time: float = 0.0,
    confidence: float = 0.0,
    user_id: Optional[int] = None,
    graph_id: Optional[int] = None
) -> Optional[int]:
    """
    记录问答到数据库
    
    Args:
        question: 问题内容
        answer: 答案内容
        mode: 查询模式（global/local）
        response_time: 响应时间（毫秒）
        confidence: 置信度
        user_id: 用户ID
        graph_id: 图谱ID
    
    Returns:
        问答记录ID
    """
    try:
        print(f"[DB] 正在保存问答记录...")
        print(f"[DB] 问题: {question[:50]}...")
        print(f"[DB] 答案长度: {len(answer)} 字符")
        print(f"[DB] 模式: {mode}, 响应时间: {response_time}ms, 置信度: {confidence}")
        
        db = SessionLocal()
        # 使用本地时间（UTC+8）而不是 UTC 时间
        local_time = datetime.utcnow() + timedelta(hours=8)
        record = QuestionRecord(
            user_id=user_id,
            question=question,
            answer=answer,
            mode=mode,
            status="completed",
            response_time=response_time,
            confidence=confidence,
            graph_id=graph_id,
            created_at=local_time,
            updated_at=local_time
        )
        db.add(record)
        db.commit()
        record_id = record.id
        db.close()
        print(f"✅ 问答记录已保存: ID={record_id}")
        return record_id
    except Exception as e:
        import traceback
        print(f"❌ 保存问答记录失败: {str(e)}")
        print(f"[DB] 错误堆栈:\n{traceback.format_exc()}")
        return None


def log_access(
    ip_address: str,
    endpoint: str,
    method: str = "GET",
    status_code: int = 200,
    response_time: float = 0.0,
    device_info: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[int]:
    """
    记录访问日志到数据库
    
    Args:
        ip_address: IP地址
        endpoint: 访问端点
        method: HTTP方法
        status_code: 状态码
        response_time: 响应时间（毫秒）
        device_info: 设备信息
        user_agent: User-Agent
    
    Returns:
        访问日志ID
    """
    try:
        db = SessionLocal()
        
        # 使用本地时间（UTC+8）而不是 UTC 时间
        local_time = datetime.utcnow() + timedelta(hours=8)
        
        # 记录访问日志
        log = AccessLog(
            ip_address=ip_address,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            device_info=device_info,
            user_agent=user_agent,
            access_time=local_time
        )
        db.add(log)
        
        # 更新或创建 IP 统计
        ip_stat = db.query(IPStatistic).filter(
            IPStatistic.ip_address == ip_address
        ).first()
        
        if ip_stat:
            ip_stat.visit_count += 1
            ip_stat.last_access_time = local_time
            if device_info:
                ip_stat.device_info = device_info
        else:
            ip_stat = IPStatistic(
                ip_address=ip_address,
                visit_count=1,
                device_info=device_info,
                first_access_time=local_time,
                last_access_time=local_time
            )
            db.add(ip_stat)
        
        db.commit()
        log_id = log.id
        db.close()
        print(f"[DB] ✅ 访问日志已保存: IP={ip_address}, 端点={endpoint}, ID={log_id}")
        return log_id
    except Exception as e:
        print(f"[DB] ❌ 保存访问日志失败: {str(e)}")
        import traceback
        print(f"[DB] 错误堆栈:\n{traceback.format_exc()}")
        return None


def log_real_time_question(
    question: str,
    ip_address: str = "unknown",
    user_id: Optional[int] = None
) -> Optional[int]:
    """
    记录实时问题到数据库
    
    Args:
        question: 问题内容
        ip_address: 客户端IP
        user_id: 用户ID（可选）
    
    Returns:
        实时问题记录ID
    """
    try:
        print(f"[DB] 正在保存实时问题...")
        print(f"[DB] 问题: {question[:50]}...")
        print(f"[DB] IP: {ip_address}")
        
        db = SessionLocal()
        
        # 使用原生 SQL 插入实时问题
        from sqlalchemy import text
        
        insert_sql = text("""
            INSERT INTO real_time_questions (question, ip_address, user_id, created_at)
            VALUES (:question, :ip_address, :user_id, :created_at)
        """)
        
        result = db.execute(insert_sql, {
            "question": question,
            "ip_address": ip_address,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        
        db.commit()
        record_id = result.lastrowid
        db.close()
        
        print(f"✅ 实时问题已保存: ID={record_id}")
        return record_id
    except Exception as e:
        import traceback
        print(f"❌ 保存实时问题失败: {str(e)}")
        print(f"[DB] 错误堆栈:\n{traceback.format_exc()}")
        return None


def log_error(
    ip_address: str,
    endpoint: str,
    error_message: str,
    error_trace: str = "",
    question: str = "",
    module: str = "query"
) -> Optional[int]:
    """
    记录错误到数据库
    
    Args:
        ip_address: 客户端IP
        endpoint: API端点
        error_message: 错误信息
        error_trace: 错误堆栈
        question: 问题内容（如果有）
        module: 模块名称
    
    Returns:
        错误记录ID
    """
    try:
        print(f"[DB] 正在保存错误记录...")
        print(f"[DB] IP: {ip_address}, 端点: {endpoint}")
        print(f"[DB] 错误: {error_message[:100]}...")
        
        db = SessionLocal()
        
        # 使用原生 SQL 插入错误记录，避免模型依赖
        from sqlalchemy import text
        
        message = f"[{ip_address}] {endpoint}: {error_message}"
        solution = f"问题: {question[:100]}" if question else None
        
        insert_sql = text("""
            INSERT INTO system_logs (log_level, module, message, stack_trace, solution, created_at)
            VALUES (:log_level, :module, :message, :stack_trace, :solution, :created_at)
        """)
        
        result = db.execute(insert_sql, {
            "log_level": "ERROR",
            "module": module,
            "message": message,
            "stack_trace": error_trace,
            "solution": solution,
            "created_at": datetime.utcnow()
        })
        
        db.commit()
        record_id = result.lastrowid
        db.close()
        
        print(f"✅ 错误记录已保存: ID={record_id}")
        return record_id
    except Exception as e:
        import traceback
        print(f"❌ 保存错误记录失败: {str(e)}")
        print(f"[DB] 错误堆栈:\n{traceback.format_exc()}")
        return None


def init_db():
    """初始化数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表已初始化")
    except Exception as e:
        print(f"❌ 初始化数据库失败: {str(e)}")


if __name__ == "__main__":
    init_db()
