# GraphRAG 后台管理系统 - 后端 API

## 📋 项目概述

这是 GraphRAG 后台管理系统的后端 API，基于 FastAPI 框架构建。负责管理问答记录、访问日志、知识图谱、数据上传等功能。

**核心特性**：
- 📊 **数据管理** - 问答记录、访问日志、知识图谱管理
- 📈 **统计分析** - 访问趋势、时间段统计、热门 IP 等
- 📤 **数据上传** - 支持 Parquet 文件上传和 Neo4j 导入
- 🔐 **权限管理** - 基于用户角色的权限控制
- 📝 **日志记录** - 详细的操作日志和错误追踪

---

## 📁 项目结构

```
vue_backend/
├── routers/                 # API 路由模块
│   ├── qa_router.py        # 问答管理路由
│   ├── graph_router.py      # 图谱管理路由
│   ├── data_router.py       # 数据上传路由
│   ├── dashboard_router.py  # 数据面板路由
│   └── logs_router.py       # 日志查询路由
├── app.py                   # FastAPI 应用入口
├── config.py                # 配置文件
├── database.py              # 数据库连接
├── models.py                # 数据库模型
├── schemas.py               # 数据验证模式
├── init_graph_data.py       # 图谱数据初始化
├── .env                     # 环境变量配置
├── requirements.txt         # 项目依赖
├── uploads/                 # 上传文件目录
└── README.md                # 本文档
```

---

## 🔧 核心模块说明

### 1. **app.py** - FastAPI 应用入口

主要职责：
- 初始化 FastAPI 应用
- 配置中间件（CORS、日志等）
- 注册所有路由
- 初始化数据库和图谱数据

**启动命令**：
```bash
python app.py
# 或使用 uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

### 2. **routers/** - API 路由模块

#### qa_router.py - 问答管理
```
GET    /api/qa/records              # 获取问答列表
POST   /api/qa/records              # 创建问答
PUT    /api/qa/records/{id}         # 更新问答
DELETE /api/qa/records/{id}         # 删除问答
```

**主要功能**：
- 查询问答记录（支持分页、搜索、筛选）
- 创建新的问答记录
- 更新现有问答记录
- 删除问答记录

#### graph_router.py - 图谱管理
```
GET    /api/graphs                  # 获取图谱列表
POST   /api/graphs                  # 创建图谱
PUT    /api/graphs/{id}             # 更新图谱
DELETE /api/graphs/{id}             # 删除图谱
GET    /api/graphs/{id}/stats       # 获取图谱统计
```

**主要功能**：
- 管理知识图谱
- 查看图谱统计信息
- 激活/停用图谱

#### data_router.py - 数据上传
```
POST   /api/uploads                 # 创建上传记录
POST   /api/uploads/{id}/entities   # 上传 entities 文件
POST   /api/uploads/{id}/relationships # 上传 relationships 文件
POST   /api/uploads/{id}/text-units # 上传 text_units 文件
POST   /api/uploads/{id}/communities # 上传 communities 文件
POST   /api/uploads/{id}/community-reports # 上传 community_reports 文件
POST   /api/uploads/{id}/documents  # 上传 documents 文件
GET    /api/uploads/{id}/status     # 查询上传状态
```

**主要功能**：
- 创建上传批次
- 上传 Parquet 文件
- 自动触发 Neo4j 导入
- 查询导入状态

#### dashboard_router.py - 数据面板
```
GET    /api/dashboard/overview      # 获取概览数据
GET    /api/dashboard/visit-trend   # 获取访问趋势
GET    /api/dashboard/time-period-stats # 获取时间段统计
GET    /api/dashboard/top-ips       # 获取热门 IP
GET    /api/dashboard/recent-questions # 获取最近问题
```

**主要功能**：
- 统计用户、问答、图谱数据
- 分析访问趋势
- 统计不同时间段的访问和问答
- 识别热门 IP 地址

#### logs_router.py - 日志查询
```
GET    /api/logs/access             # 获取访问日志
GET    /api/logs/access/stats       # 获取访问统计
GET    /api/logs/access/top-ips     # 获取热门 IP
GET    /api/logs/system             # 获取系统日志
```

**主要功能**：
- 查询访问日志
- 统计访问信息
- 分析 IP 访问情况
- 查看系统日志

---

### 3. **models.py** - 数据库模型

定义所有数据库表的 ORM 模型：
- `User` - 用户表
- `QARecord` - 问答记录表
- `KnowledgeGraph` - 知识图谱表
- `DataUpload` - 数据上传记录表
- `SystemLog` - 系统日志表
- `UserAccessLog` - 用户访问日志表
- `AccessStatistics` - 访问统计表
- `IPStatistics` - IP 统计表
- `RealTimeQuestion` - 实时问题表

---

### 4. **schemas.py** - 数据验证模式

定义 API 请求和响应的数据模式：
- `QARecordCreate` - 创建问答的请求模式
- `QARecordUpdate` - 更新问答的请求模式
- `QARecordResponse` - 问答响应模式
- `GraphResponse` - 图谱响应模式
- `AccessLogResponse` - 访问日志响应模式
- 等等

---

### 5. **database.py** - 数据库连接

```python
from database import get_db, SessionLocal, engine

# 获取数据库会话
def my_route(db: Session = Depends(get_db)):
    # 使用 db 进行数据库操作
    pass
```

---

### 6. **config.py** - 配置文件

```python
# MySQL 数据库配置
SQLALCHEMY_DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/graphrag_admin'
)

# SQLAlchemy 配置
SQLALCHEMY_ECHO = False
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_POOL_RECYCLE = 3600
```

---

### 7. **init_graph_data.py** - 图谱数据初始化

主要职责：
- 从问答系统获取统计信息
- 初始化知识图谱数据
- 应用启动时自动执行

---

## ⚙️ 环境配置

### .env 文件配置

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2

# 问答系统数据库配置（用于读取问答记录）
QA_DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2

# SQLAlchemy 配置
SQLALCHEMY_ECHO=False
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_POOL_RECYCLE=3600

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=False
```

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | MySQL 数据库连接字符串 | 必须设置 |
| `QA_DATABASE_URL` | 问答系统数据库连接字符串 | 同 DATABASE_URL |
| `SQLALCHEMY_ECHO` | 是否输出 SQL 语句 | False |
| `SQLALCHEMY_POOL_SIZE` | 数据库连接池大小 | 10 |
| `SQLALCHEMY_POOL_RECYCLE` | 连接回收时间（秒） | 3600 |
| `SECRET_KEY` | JWT 密钥 | 必须设置 |
| `DEBUG` | 调试模式 | False |

---

## 🚀 启动和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
编辑 `.env` 文件，设置数据库连接信息。

### 3. 启动服务
```bash
# 开发环境
python app.py

# 或使用 uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 生产环境（使用 gunicorn）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 4. 验证服务
```bash
# 健康检查
curl http://localhost:8000/health

# 查看 API 文档
http://localhost:8000/api/docs
```

---

## 📡 API 端点详解

### 问答管理 API

**获取问答列表**：
```bash
GET /api/qa/records?page=1&page_size=10&status=completed
```

**创建问答**：
```bash
POST /api/qa/records
Content-Type: application/json

{
  "question": "...",
  "answer": "...",
  "status": "completed",
  "user_id": 1
}
```

---

### 数据面板 API

**获取概览数据**：
```bash
GET /api/dashboard/overview
```

**获取访问趋势**：
```bash
GET /api/dashboard/visit-trend
```

**获取时间段统计**：
```bash
GET /api/dashboard/time-period-stats?days=7
```

---

### 数据上传 API

**创建上传记录**：
```bash
POST /api/uploads
Content-Type: application/json

{
  "upload_name": "batch_001",
  "user_id": 1,
  "graph_id": 1
}
```

**上传文件**：
```bash
POST /api/uploads/{upload_id}/entities
Content-Type: multipart/form-data

file: <entities.parquet>
```

**查询上传状态**：
```bash
GET /api/uploads/{upload_id}/status
```

---

## 🔄 与其他组件的集成

### 前端（vue）
- 地址：`http://localhost:5173`
- 调用后端 API 获取数据和执行操作

### 问答系统（backend）
- 地址：`http://localhost:8085`
- 读取问答系统的数据库
- 初始化图谱数据

### 数据库
- MySQL：`localhost:3306/graphrag_admin2`
- 存储所有管理系统的数据

---

## 🔍 调试和故障排除

### 常见问题

**问题 1：数据库连接失败**
- 检查 MySQL 服务是否运行
- 验证 `DATABASE_URL` 配置
- 确保数据库 `graphrag_admin2` 已创建

**问题 2：API 返回 404**
- 检查路由是否正确注册
- 验证请求路径和方法
- 查看 API 文档

**问题 3：文件上传失败**
- 检查 `uploads/` 目录权限
- 验证文件格式是否正确
- 检查磁盘空间

### 调试模式

启用调试模式查看详细日志：
```python
# 在 app.py 中
app.debug = True
```

---

## 📝 开发指南

### 添加新的 API 端点

1. 在 `routers/` 创建新的路由文件
2. 定义路由函数
3. 在 `app.py` 中注册路由

```python
# routers/new_router.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/new", tags=["new"])

@router.get("/endpoint")
def new_endpoint():
    return {"message": "Hello"}
```

```python
# app.py
from routers import new_router
app.include_router(new_router.router)
```

### 添加新的数据库模型

1. 在 `models.py` 定义模型
2. 创建对应的 Schema
3. 创建路由处理

---

## 🚀 性能优化

### 数据库优化
- 使用索引加速查询
- 实现查询缓存
- 使用连接池

### API 优化
- 实现分页
- 使用异步操作
- 压缩响应数据

### 监控和日志
- 记录详细的操作日志
- 监控 API 性能
- 设置告警机制

---

## 📚 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)

---

## 📞 支持和反馈

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新**：2025-11-22
**版本**：1.0.0
