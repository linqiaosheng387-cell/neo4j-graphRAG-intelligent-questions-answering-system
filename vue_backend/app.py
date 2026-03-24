"""
FastAPI 主应用程序
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from database import Base, engine
from routers import qa_router, graph_router, data_router, dashboard_router, logs_router
from init_graph_data import init_graph_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# ==================== lifespan 管理启动/关闭事件 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    logger.info("=" * 50)
    logger.info("GraphRAG 后台管理系统 API 启动")
    logger.info("=" * 50)
    logger.info("API 文档: http://localhost:8000/api/docs")
    logger.info("健康检查: http://localhost:8000/health")

    try:
        init_graph_data()
    except Exception as e:
        logger.error(f"初始化图谱数据失败: {e}")

    yield

    # 关闭
    logger.info("=" * 50)
    logger.info("GraphRAG 后台管理系统 API 已关闭")
    logger.info("=" * 50)

# 创建 FastAPI 应用
app = FastAPI(
    title="GraphRAG 后台管理系统 API",
    description="基于 GraphRAG + Neo4j 的后台管理系统 API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# ==================== 中间件配置 ====================
# 信任主机中间件（先添加）
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# CORS 中间件（后添加，这样会首先执行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 路由注册 ====================
app.include_router(qa_router.router)
app.include_router(graph_router.router)
app.include_router(data_router.router)
app.include_router(dashboard_router.router)
app.include_router(logs_router.router)

# ==================== 健康检查 ====================
@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "GraphRAG Admin Backend"
    }

# ==================== 根路由 ====================
@app.get("/")
def root():
    """根路由"""
    return {
        "message": "欢迎使用 GraphRAG 后台管理系统 API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
