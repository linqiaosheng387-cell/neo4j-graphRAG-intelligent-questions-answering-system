"""
图谱管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from database import get_db
from models import KnowledgeGraph, User
from schemas import KnowledgeGraphCreate, KnowledgeGraphUpdate, KnowledgeGraphResponse, KnowledgeGraphListResponse

router = APIRouter(prefix="/api/graphs", tags=["图谱管理"])

# ==================== 获取图谱统计概览（必须在通用路由之前）====================
@router.get("/stats/overview")
def get_graph_overview(
    db: Session = Depends(get_db)
):
    """获取图谱统计概览"""
    graphs = db.query(KnowledgeGraph).all()
    
    total_graphs = len(graphs)
    active_graphs = len([g for g in graphs if g.status == "active"])
    total_entities = sum([g.entity_count for g in graphs])
    total_relations = sum([g.relation_count for g in graphs])
    
    return {
        "total_graphs": total_graphs,
        "active_graphs": active_graphs,
        "total_entities": total_entities,
        "total_relations": total_relations
    }

# ==================== 获取活跃的图谱（必须在通用路由之前）====================
@router.get("/active/list", response_model=KnowledgeGraphListResponse)
def get_active_graphs(
    db: Session = Depends(get_db)
):
    """获取所有活跃的知识图谱"""
    graphs = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.status == "active"
    ).order_by(desc(KnowledgeGraph.created_at)).all()
    
    return {
        "total": len(graphs),
        "page": 1,
        "page_size": len(graphs),
        "data": graphs
    }

# ==================== 创建知识图谱 ====================
@router.post("", response_model=KnowledgeGraphResponse)
def create_knowledge_graph(
    graph_data: KnowledgeGraphCreate,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """创建新的知识图谱"""
    # 验证用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 创建图谱
    db_graph = KnowledgeGraph(
        name=graph_data.name,
        description=graph_data.description,
        created_by=user_id,
        neo4j_db_name=graph_data.neo4j_db_name,
        status="inactive"
    )
    db.add(db_graph)
    db.commit()
    db.refresh(db_graph)
    return db_graph

# ==================== 获取图谱列表 ====================
@router.get("", response_model=KnowledgeGraphListResponse)
def get_knowledge_graphs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """获取知识图谱列表（支持分页和筛选）"""
    query = db.query(KnowledgeGraph)
    
    # 筛选条件
    if status:
        query = query.filter(KnowledgeGraph.status == status)
    
    # 总数
    total = query.count()
    
    # 分页
    graphs = query.order_by(desc(KnowledgeGraph.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": graphs
    }

# ==================== 获取单个图谱 ====================
@router.get("/{graph_id}", response_model=KnowledgeGraphResponse)
def get_knowledge_graph(
    graph_id: int,
    db: Session = Depends(get_db)
):
    """获取单个知识图谱详情"""
    graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == graph_id).first()
    if not graph:
        raise HTTPException(status_code=404, detail="知识图谱不存在")
    return graph

# ==================== 更新图谱 ====================
@router.put("/{graph_id}", response_model=KnowledgeGraphResponse)
def update_knowledge_graph(
    graph_id: int,
    graph_data: KnowledgeGraphUpdate,
    db: Session = Depends(get_db)
):
    """更新知识图谱"""
    graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == graph_id).first()
    if not graph:
        raise HTTPException(status_code=404, detail="知识图谱不存在")
    
    # 更新字段
    if graph_data.name is not None:
        graph.name = graph_data.name
    if graph_data.description is not None:
        graph.description = graph_data.description
    if graph_data.status is not None:
        graph.status = graph_data.status
    if graph_data.entity_count is not None:
        graph.entity_count = graph_data.entity_count
    if graph_data.relation_count is not None:
        graph.relation_count = graph_data.relation_count
    if graph_data.neo4j_db_name is not None:
        graph.neo4j_db_name = graph_data.neo4j_db_name
    
    graph.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(graph)
    return graph

# ==================== 删除图谱 ====================
@router.delete("/{graph_id}")
def delete_knowledge_graph(
    graph_id: int,
    db: Session = Depends(get_db)
):
    """删除知识图谱"""
    graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == graph_id).first()
    if not graph:
        raise HTTPException(status_code=404, detail="知识图谱不存在")
    
    db.delete(graph)
    db.commit()
    return {"message": "删除成功"}
