"""
问答管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from schemas import QARecordCreate, QARecordUpdate, QARecordResponse

# 加载环境变量（从当前目录的 .env 文件）
env_path = Path(__file__).parent.parent / '.env'
print(f"[QA Router] 加载环境变量: {env_path}")
load_dotenv(env_path)

# 连接问答系统的数据库（graphrag_admin2）
QA_DATABASE_URL = os.getenv(
    "QA_DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/graphrag_admin2"
)

print(f"[QA Router] 问答系统数据库 URL: {QA_DATABASE_URL}")

# 创建问答系统数据库的引擎和会话
try:
    qa_engine = create_engine(QA_DATABASE_URL, pool_pre_ping=True)
    QASessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=qa_engine)
    QABase = declarative_base()
    print(f"[QA Router] ✅ 问答系统数据库连接已初始化")
except Exception as e:
    print(f"[QA Router] ❌ 问答系统数据库连接失败: {e}")
    QASessionLocal = None
    QABase = declarative_base()

# 定义问答系统的 QARecord 模型（映射到 graphrag_admin.qa_records）
class QASystemRecord(QABase):
    __tablename__ = "qa_records"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    mode = Column(String(50), default="global")
    status = Column(String(50), default="completed")
    response_time = Column(Float, nullable=True)
    confidence = Column(Float, default=0.0)
    graph_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

def get_qa_db():
    """获取问答系统数据库会话"""
    if QASessionLocal is None:
        raise HTTPException(status_code=500, detail="问答系统数据库连接失败")
    
    db = QASessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/api/qa", tags=["问答管理"])

# ==================== 创建问答记录 ====================
@router.post("/records", response_model=QARecordResponse)
def create_qa_record(
    qa_data: QARecordCreate,
    db: Session = Depends(get_qa_db)
):
    """创建新的问答记录"""
    # 验证用户是否存在
    user = db.query(QASystemRecord).filter(QASystemRecord.id == qa_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 创建问答记录
    db_qa = QASystemRecord(
        user_id=qa_data.user_id,
        question=qa_data.question,
        graph_id=qa_data.graph_id,
        status="pending"
    )
    db.add(db_qa)
    db.commit()
    db.refresh(db_qa)
    return db_qa

# ==================== 获取问答记录列表 ====================
@router.get("/records")
def get_qa_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_qa_db)
):
    """获取问答记录列表（从问答系统数据库读取）"""
    try:
        print(f"[QA API] 获取问答记录 - page={page}, page_size={page_size}")
        
        query = db.query(QASystemRecord)
        
        # 筛选条件
        if user_id:
            query = query.filter(QASystemRecord.user_id == user_id)
        if status:
            query = query.filter(QASystemRecord.status == status)
        
        # 总数
        total = query.count()
        print(f"[QA API] 总记录数: {total}")
        
        # 分页
        records = query.order_by(desc(QASystemRecord.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        print(f"[QA API] 当前页记录数: {len(records)}")
        
        # 转换为响应格式
        data = []
        for record in records:
            data.append({
                "id": record.id,
                "user_id": record.user_id,
                "question": record.question,
                "answer": record.answer,
                "graph_id": record.graph_id,
                "status": record.status,
                "response_time": record.response_time,
                "error_message": None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            })
        
        result = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": data
        }
        print(f"[QA API] ✅ 返回成功")
        return result
        
    except Exception as e:
        print(f"[QA API] ❌ 获取问答记录失败: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取问答记录失败: {str(e)}")

# ==================== 获取单个问答记录 ====================
@router.get("/records/{record_id}", response_model=QARecordResponse)
def get_qa_record(
    record_id: int,
    db: Session = Depends(get_qa_db)
):
    """获取单个问答记录详情"""
    record = db.query(QASystemRecord).filter(QASystemRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="问答记录不存在")
    return record

# ==================== 更新问答记录 ====================
@router.put("/records/{record_id}", response_model=QARecordResponse)
def update_qa_record(
    record_id: int,
    qa_data: QARecordUpdate,
    db: Session = Depends(get_qa_db)
):
    """更新问答记录（用于存储答案和状态）"""
    record = db.query(QASystemRecord).filter(QASystemRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="问答记录不存在")

    # 更新字段
    if qa_data.answer is not None:
        record.answer = qa_data.answer
    if qa_data.status is not None:
        record.status = qa_data.status
    if qa_data.response_time is not None:
        record.response_time = qa_data.response_time

    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record

# ==================== 删除问答记录 ====================
@router.delete("/records/{record_id}")
def delete_qa_record(
    record_id: int,
    db: Session = Depends(get_qa_db)
):
    """删除问答记录"""
    record = db.query(QASystemRecord).filter(QASystemRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="问答记录不存在")

    db.delete(record)
    db.commit()
    return {"message": "删除成功"}

# ==================== 获取用户问答统计 ====================
@router.get("/users/{user_id}/stats")
def get_user_qa_stats(
    user_id: int,
    db: Session = Depends(get_qa_db)
):
    """获取用户的问答统计信息"""
    records = db.query(QASystemRecord).filter(QASystemRecord.user_id == user_id).all()

    total_questions = len(records)
    completed = len([r for r in records if r.status == "completed"])
    pending = len([r for r in records if r.status == "pending"])
    errors = len([r for r in records if r.status == "error"])
    avg_response_time = sum([r.response_time for r in records if r.response_time]) / len([r for r in records if r.response_time]) if [r for r in records if r.response_time] else 0

    return {
        "user_id": user_id,
        "total_questions": total_questions,
        "completed": completed,
        "pending": pending,
        "errors": errors,
        "avg_response_time": round(avg_response_time, 2)
    }

# ==================== 获取最近的问答记录 ====================
@router.get("/recent")
def get_recent_qa_records(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_qa_db)
):
    """获取最近的问答记录（从问答系统数据库读取）"""
    try:
        print(f"[QA API] 获取最近问答记录 - limit={limit}")
        
        records = db.query(QASystemRecord).order_by(desc(QASystemRecord.created_at)).limit(limit).all()
        
        print(f"[QA API] 找到 {len(records)} 条最近记录")
        
        # 转换为响应格式
        data = []
        for record in records:
            data.append({
                "id": record.id,
                "user_id": record.user_id,
                "question": record.question,
                "answer": record.answer,
                "graph_id": record.graph_id,
                "status": record.status,
                "response_time": record.response_time,
                "error_message": None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            })
        
        result = {
            "total": len(records),
            "page": 1,
            "page_size": limit,
            "data": data
        }
        print(f"[QA API] ✅ 返回成功")
        return result
        
    except Exception as e:
        print(f"[QA API] ❌ 获取最近问答记录失败: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取最近问答记录失败: {str(e)}")
