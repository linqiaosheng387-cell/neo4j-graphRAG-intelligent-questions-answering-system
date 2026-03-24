"""
数据管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import os
import sys
import pandas as pd
from database import get_db
from models import DataUpload, User, KnowledgeGraph
from schemas import DataUploadCreate, DataUploadUpdate, DataUploadResponse, DataUploadListResponse
from neo4j import GraphDatabase
import threading

router = APIRouter(prefix="/api/data", tags=["数据管理"])

# 上传文件保存目录
UPLOAD_DIR = "uploads/data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
BATCH_SIZE = 500

# ==================== Neo4j 导入辅助函数 ====================

def _safe_convert_to_string(value):
    """安全地将值转换为字符串，处理数组/列表"""
    try:
        if value is None:
            return '[]'
        if isinstance(value, (list, tuple)):
            return str(list(value))
        if hasattr(value, '__iter__') and not isinstance(value, str):
            return str(list(value))
        if isinstance(value, pd.Series):
            return str(value.tolist())
        return str(value)
    except Exception as e:
        print(f"[警告] 转换值时出错: {e}")
        return '[]'

def _check_and_trigger_import(upload_id: int, db: Session):
    """检查是否所有文件都已上传，如果是则触发异步导入"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        return
    
    # 检查所有文件是否都已上传
    all_files_uploaded = (
        upload.entities_file and
        upload.relationships_file and
        upload.text_units_file and
        upload.communities_file and
        upload.community_reports_file and
        upload.documents_file
    )
    
    if all_files_uploaded and upload.status == "pending":
        print(f"[触发器] 所有文件已上传，开始异步导入到 Neo4j (upload_id={upload_id})")
        # 启动后台线程进行导入
        thread = threading.Thread(
            target=import_to_neo4j_async,
            args=(upload_id, upload, db),
            daemon=True
        )
        thread.start()

def import_to_neo4j_async(upload_id: int, upload_record: DataUpload, db: Session):
    """异步导入数据到 Neo4j"""
    try:
        print(f"\n[后台任务] 开始导入数据到 Neo4j (upload_id={upload_id})...")
        
        # 连接 Neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver.session() as session:
            # 1. 导入实体
            if upload_record.entities_file:
                print(f"[后台任务] 导入实体...")
                entities_df = pd.read_parquet(upload_record.entities_file)
                
                entities_data = []
                for idx, row in entities_df.iterrows():
                    entities_data.append({
                        'id': row['id'],
                        'title': str(row['title']) if pd.notna(row['title']) else '',
                        'type': str(row['type']) if pd.notna(row['type']) else '',
                        'description': str(row['description'])[:500] if pd.notna(row['description']) else '',
                        'degree': int(row['degree']) if pd.notna(row['degree']) else 0
                    })
                
                query = """
                UNWIND $batch AS entity
                CREATE (e:Entity {
                    id: entity.id,
                    title: entity.title,
                    type: entity.type,
                    description: entity.description,
                    degree: entity.degree
                })
                """
                
                for i in range(0, len(entities_data), BATCH_SIZE):
                    batch = entities_data[i:i+BATCH_SIZE]
                    session.run(query, batch=batch)
                
                print(f"[后台任务] ✅ 导入 {len(entities_df)} 个实体")
            
            # 2. 导入关系
            if upload_record.relationships_file:
                print(f"[后台任务] 导入关系...")
                relationships_df = pd.read_parquet(upload_record.relationships_file)
                
                relationships_data = []
                for idx, row in relationships_df.iterrows():
                    relationships_data.append({
                        'id': row['id'],
                        'source': str(row['source']) if pd.notna(row['source']) else '',
                        'target': str(row['target']) if pd.notna(row['target']) else '',
                        'description': str(row['description'])[:500] if pd.notna(row['description']) else '',
                        'weight': float(row['weight']) if pd.notna(row['weight']) else 1.0
                    })
                
                query = """
                UNWIND $batch AS rel
                MATCH (e1:Entity {title: rel.source}), (e2:Entity {title: rel.target})
                CREATE (e1)-[r:RELATED_TO {
                    id: rel.id,
                    description: rel.description,
                    weight: rel.weight
                }]->(e2)
                """
                
                for i in range(0, len(relationships_data), BATCH_SIZE):
                    batch = relationships_data[i:i+BATCH_SIZE]
                    session.run(query, batch=batch)
                
                print(f"[后台任务] ✅ 导入 {len(relationships_df)} 条关系")
            
            # 3. 导入文本单元
            if upload_record.text_units_file:
                print(f"[后台任务] 导入文本单元...")
                text_units_df = pd.read_parquet(upload_record.text_units_file)
                
                text_units_data = []
                for idx, row in text_units_df.iterrows():
                    text_units_data.append({
                        'id': row['id'],
                        'text': str(row['text'])[:5000] if pd.notna(row['text']) else '',
                        'document_ids': _safe_convert_to_string(row['document_ids'])
                    })
                
                query = """
                UNWIND $batch AS text_unit
                CREATE (t:TextUnit {
                    id: text_unit.id,
                    text: text_unit.text,
                    document_ids: text_unit.document_ids
                })
                """
                
                for i in range(0, len(text_units_data), BATCH_SIZE):
                    batch = text_units_data[i:i+BATCH_SIZE]
                    session.run(query, batch=batch)
                
                print(f"[后台任务] ✅ 导入 {len(text_units_df)} 个文本单元")
            
            # 4. 导入社区
            if upload_record.communities_file:
                print(f"[后台任务] 导入社区...")
                communities_df = pd.read_parquet(upload_record.communities_file)
                
                communities_data = []
                for idx, row in communities_df.iterrows():
                    communities_data.append({
                        'id': row['id'],
                        'level': int(row['level']) if pd.notna(row['level']) else 0,
                        'title': str(row['title']) if pd.notna(row['title']) else '',
                        'entity_ids': _safe_convert_to_string(row['entity_ids'])
                    })
                
                query = """
                UNWIND $batch AS community
                CREATE (c:Community {
                    id: community.id,
                    level: community.level,
                    title: community.title,
                    entity_ids: community.entity_ids
                })
                """
                
                for i in range(0, len(communities_data), BATCH_SIZE):
                    batch = communities_data[i:i+BATCH_SIZE]
                    session.run(query, batch=batch)
                
                print(f"[后台任务] ✅ 导入 {len(communities_df)} 个社区")
            
            # 5. 导入社区报告
            if upload_record.community_reports_file:
                print(f"[后台任务] 导入社区报告...")
                reports_df = pd.read_parquet(upload_record.community_reports_file)
                
                reports_data = []
                for idx, row in reports_df.iterrows():
                    title = str(row['title']) if 'title' in row and pd.notna(row['title']) else ''
                    summary = ''
                    if 'summary' in row and pd.notna(row['summary']):
                        summary = str(row['summary'])[:2000]
                    
                    full_content = ''
                    if 'full_content' in row and pd.notna(row['full_content']):
                        full_content = str(row['full_content'])[:5000]
                    
                    reports_data.append({
                        'id': row['id'],
                        'title': title,
                        'summary': summary,
                        'full_content': full_content
                    })
                
                query = """
                UNWIND $batch AS report
                CREATE (r:Report {
                    id: report.id,
                    title: report.title,
                    summary: report.summary,
                    full_content: report.full_content
                })
                """
                
                for i in range(0, len(reports_data), BATCH_SIZE):
                    batch = reports_data[i:i+BATCH_SIZE]
                    session.run(query, batch=batch)
                
                print(f"[后台任务] ✅ 导入 {len(reports_df)} 个社区报告")
            
            # 6. 导入文档
            if upload_record.documents_file:
                print(f"[后台任务] 导入文档...")
                documents_df = pd.read_parquet(upload_record.documents_file)
                
                documents_data = []
                for idx, row in documents_df.iterrows():
                    content = ''
                    for field in ['raw_content', 'content', 'text', 'body']:
                        if field in row and pd.notna(row[field]):
                            content = str(row[field])[:5000]
                            break
                    
                    documents_data.append({
                        'id': row['id'],
                        'title': str(row['title']) if pd.notna(row['title']) else '',
                        'raw_content': content
                    })
                
                query = """
                UNWIND $batch AS document
                CREATE (d:Document {
                    id: document.id,
                    title: document.title,
                    raw_content: document.raw_content
                })
                """
                
                for i in range(0, len(documents_data), BATCH_SIZE):
                    batch = documents_data[i:i+BATCH_SIZE]
                    session.run(query, batch=batch)
                
                print(f"[后台任务] ✅ 导入 {len(documents_df)} 个文档")
        
        driver.close()
        
        # 更新上传记录状态
        upload_record.status = "completed"
        db.commit()
        print(f"[后台任务] ✅ 数据导入完成 (upload_id={upload_id})")
        
    except Exception as e:
        print(f"[后台任务] ❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 更新上传记录状态
        upload_record.status = "failed"
        upload_record.error_message = str(e)
        db.commit()

# ==================== 创建数据上传记录 ====================
@router.post("/uploads", response_model=DataUploadResponse)
def create_data_upload(
    upload_data: DataUploadCreate,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """创建新的数据上传记录"""
    # 验证用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证图谱是否存在（如果指定了）
    if upload_data.graph_id:
        graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == upload_data.graph_id).first()
        if not graph:
            raise HTTPException(status_code=404, detail="知识图谱不存在")
    
    # 创建上传记录
    db_upload = DataUpload(
        upload_name=upload_data.upload_name,
        user_id=user_id,
        graph_id=upload_data.graph_id,
        status="pending"
    )
    db.add(db_upload)
    db.commit()
    db.refresh(db_upload)
    return db_upload

# ==================== 获取数据上传列表 ====================
@router.get("/uploads", response_model=DataUploadListResponse)
def get_data_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """获取数据上传列表（支持分页和筛选）"""
    query = db.query(DataUpload)
    
    # 筛选条件
    if user_id:
        query = query.filter(DataUpload.user_id == user_id)
    if status:
        query = query.filter(DataUpload.status == status)
    
    # 总数
    total = query.count()
    
    # 分页
    uploads = query.order_by(desc(DataUpload.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": uploads
    }

# ==================== 获取单个上传记录 ====================
@router.get("/uploads/{upload_id}", response_model=DataUploadResponse)
def get_data_upload(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """获取单个数据上传记录详情"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    return upload

# ==================== 更新上传记录 ====================
@router.put("/uploads/{upload_id}", response_model=DataUploadResponse)
def update_data_upload(
    upload_id: int,
    upload_data: DataUploadUpdate,
    db: Session = Depends(get_db)
):
    """更新数据上传记录"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    # 更新字段
    if upload_data.status is not None:
        upload.status = upload_data.status
    if upload_data.error_message is not None:
        upload.error_message = upload_data.error_message
    
    upload.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(upload)
    return upload

# ==================== 删除上传记录 ====================
@router.delete("/uploads/{upload_id}")
def delete_data_upload(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """删除数据上传记录"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    db.delete(upload)
    db.commit()
    return {"message": "删除成功"}

# ==================== 上传 entities 文件 ====================
@router.post("/uploads/{upload_id}/entities")
async def upload_entities_file(
    upload_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传 entities.parquet 文件"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"upload_{upload_id}_entities.parquet")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    upload.entities_file = file_path
    upload.updated_at = datetime.utcnow()
    db.commit()
    
    # 检查是否所有文件都已上传，如果是则触发导入
    _check_and_trigger_import(upload_id, db)
    
    return {"message": "entities 文件上传成功", "file_path": file_path}

# ==================== 上传 relationships 文件 ====================
@router.post("/uploads/{upload_id}/relationships")
async def upload_relationships_file(
    upload_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传 relationships.parquet 文件"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"upload_{upload_id}_relationships.parquet")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    upload.relationships_file = file_path
    upload.updated_at = datetime.utcnow()
    db.commit()
    
    # 检查是否所有文件都已上传，如果是则触发导入
    _check_and_trigger_import(upload_id, db)
    
    return {"message": "relationships 文件上传成功", "file_path": file_path}

# ==================== 上传 text_units 文件 ====================
@router.post("/uploads/{upload_id}/text-units")
async def upload_text_units_file(
    upload_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传 text_units.parquet 文件"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"upload_{upload_id}_text_units.parquet")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    upload.text_units_file = file_path
    upload.updated_at = datetime.utcnow()
    db.commit()
    
    # 检查是否所有文件都已上传，如果是则触发导入
    _check_and_trigger_import(upload_id, db)
    
    return {"message": "text_units 文件上传成功", "file_path": file_path}

# ==================== 上传 communities 文件 ====================
@router.post("/uploads/{upload_id}/communities")
async def upload_communities_file(
    upload_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传 communities.parquet 文件"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"upload_{upload_id}_communities.parquet")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    upload.communities_file = file_path
    upload.updated_at = datetime.utcnow()
    db.commit()
    
    # 检查是否所有文件都已上传，如果是则触发导入
    _check_and_trigger_import(upload_id, db)
    
    return {"message": "communities 文件上传成功", "file_path": file_path}

# ==================== 上传 community_reports 文件 ====================
@router.post("/uploads/{upload_id}/community-reports")
async def upload_community_reports_file(
    upload_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传 community_reports.parquet 文件"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"upload_{upload_id}_community_reports.parquet")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    upload.community_reports_file = file_path
    upload.updated_at = datetime.utcnow()
    db.commit()
    
    # 检查是否所有文件都已上传，如果是则触发导入
    _check_and_trigger_import(upload_id, db)
    
    return {"message": "community_reports 文件上传成功", "file_path": file_path}

# ==================== 上传 documents 文件 ====================
@router.post("/uploads/{upload_id}/documents")
async def upload_documents_file(
    upload_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传 documents.parquet 文件"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"upload_{upload_id}_documents.parquet")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    upload.documents_file = file_path
    upload.updated_at = datetime.utcnow()
    db.commit()
    
    # 检查是否所有文件都已上传，如果是则触发导入
    _check_and_trigger_import(upload_id, db)
    
    return {"message": "documents 文件上传成功", "file_path": file_path}

# ==================== 检查上传完整性 ====================
@router.get("/uploads/{upload_id}/status")
def check_upload_status(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """检查数据上传是否完整"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    
    files_uploaded = {
        "entities": upload.entities_file is not None,
        "relationships": upload.relationships_file is not None,
        "text_units": upload.text_units_file is not None,
        "communities": upload.communities_file is not None,
        "community_reports": upload.community_reports_file is not None,
        "documents": upload.documents_file is not None
    }
    
    all_uploaded = all(files_uploaded.values())
    
    return {
        "upload_id": upload_id,
        "files_uploaded": files_uploaded,
        "all_uploaded": all_uploaded,
        "status": upload.status
    }
