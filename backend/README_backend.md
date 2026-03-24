# GraphRAG 问答系统 - 后端 API 文档

## 📋 项目概述

这是中央苏区史 GraphRAG 问答系统的后端 API，基于 FastAPI 框架构建。系统集成了 GraphRAG 检索引擎和 Neo4j 图数据库，提供智能问答、图谱可视化等功能。

**核心特性**：
- 🔍 **GraphRAG 检索** - 基于向量和关键词的混合检索
- 🗂️ **Neo4j 图谱** - 知识图谱可视化和关系查询
- 📊 **访问日志** - 自动记录所有 API 访问和问答数据
- 🚀 **流式响应** - 支持问答流式输出
- 🔐 **CORS 配置** - 支持前端跨域请求

---

## 📁 文件结构

```
backend/
├── main.py                      # FastAPI 应用入口，定义所有 API 端点
├── graphrag_service.py          # GraphRAG 核心服务类，处理检索和搜索逻辑
├── graphrag_service_neo4j.py    # Neo4j 版本的 GraphRAG 服务（可选）
├── db_logger.py                 # 数据库日志记录模块，记录访问和问答数据
├── llm_client.py                # LLM 客户端，支持多个 LLM 提供商
├── import_to_neo4j.py           # Neo4j 数据导入脚本
├── check_server.py              # 服务器健康检查工具
├── verify_neo4j.py              # Neo4j 连接验证工具
├── .env                         # 环境变量配置文件
└── README.md                    # 本文档
```

---

## 🔧 核心模块说明

### 1. **main.py** - FastAPI 应用入口
主要职责：
- 初始化 FastAPI 应用和 CORS 中间件
- 定义所有 API 路由和端点
- 配置访问日志中间件
- 启动 GraphRAG 服务

**关键端点**：
```
POST   /api/query              # 问答查询（支持全局和本地搜索）
GET    /api/query/stream       # 流式问答查询
GET    /api/graph/{entities}   # 获取知识图谱数据
GET    /api/stats              # 获取统计信息
GET    /health                 # 健康检查
GET    /api/docs               # API 文档（Swagger UI）
```

**启动命令**：
```bash
python main.py
# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8085 --reload
```

---

### 2. **graphrag_service.py** - GraphRAG 核心服务
主要职责：
- 加载 Parquet 数据文件（entities、relationships、text_units 等）
- 实现全局搜索和本地搜索算法
- 与 Neo4j 交互获取图谱数据
- 调用 LLM 生成答案

**主要方法**：
```python
# 查询问答
query(question, mode='global')

# 全局搜索（基于社区报告）
_global_search(question)

# 本地搜索（基于实体和关系）
_local_search(question)

# 获取知识图谱数据
_get_graph_from_neo4j(entity_titles)

# 获取统计信息
get_statistics()
```

**数据源**：
- 6 个 Parquet 文件：entities、relationships、text_units、communities、community_reports、documents
- Neo4j 图数据库（用于图谱可视化）

---

### 3. **db_logger.py** - 数据库日志记录
主要职责：
- 记录所有问答记录到 MySQL 数据库
- 记录所有访问日志和 IP 统计
- 管理数据库连接和会话

**主要函数**：
```python
# 记录问答
log_question(question, answer, mode, response_time, confidence)

# 记录访问
log_access(ip_address, endpoint, method, status_code, response_time)

# 记录实时问题
log_real_time_question(question, ip_address)

# 初始化数据库
init_db()
```

**数据库表**：
- `qa_records` - 问答记录
- `user_access_logs` - 访问日志
- `ip_statistics` - IP 统计
- `real_time_questions` - 实时问题

---

### 4. **llm_client.py** - LLM 客户端
主要职责：
- 支持多个 LLM 提供商（DashScope、OpenAI 等）
- 处理 API 密钥和模型选择
- 提供常规和流式聊天接口

**支持的 LLM**：
- DashScope（阿里云通义千问）
- OpenAI
- 其他兼容 OpenAI API 的服务

---

### 5. **import_to_neo4j.py** - Neo4j 数据导入
主要职责：
- 从 Parquet 文件读取数据
- 导入节点到 Neo4j（Entity、TextUnit、Community、Report、Document）
- 创建节点间的关系

**使用方法**：
```bash
python import_to_neo4j.py
```

---

## ⚙️ 环境配置

### .env 文件配置

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2

# LLM 配置
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_MODEL=qwen-plus

# Neo4j 配置
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678

# GraphRAG 数据路径
GRAPHRAG_DATA_PATH=..
```

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | MySQL 数据库连接字符串 | 必须设置 |
| `LLM_PROVIDER` | LLM 提供商 | dashscope |
| `DASHSCOPE_API_KEY` | DashScope API 密钥 | 必须设置 |
| `DASHSCOPE_MODEL` | DashScope 模型名称 | qwen-plus |
| `NEO4J_URI` | Neo4j 连接地址 | neo4j://localhost:7687 |
| `NEO4J_USER` | Neo4j 用户名 | neo4j |
| `NEO4J_PASSWORD` | Neo4j 密码 | 12345678 |
| `GRAPHRAG_DATA_PATH` | GraphRAG 数据文件路径 | .. |

---

## 🚀 启动和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
编辑 `.env` 文件，设置数据库、LLM 和 Neo4j 的连接信息。

### 3. 启动后端服务
```bash
# 方式 1：直接运行
python main.py

# 方式 2：使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8085 --reload
```

### 4. 验证服务
```bash
# 健康检查
curl http://localhost:8085/health

# 查看 API 文档
http://localhost:8085/api/docs
```

---

## 📡 API 端点详解

### 1. 问答查询
**请求**：
```bash
POST /api/query
Content-Type: application/json

{
  "question": "中央苏区的历史背景是什么？",
  "mode": "global"  # 或 "local"
}
```

**响应**：
```json
{
  "answer": "中央苏区是...",
  "mode": "global",
  "source": ["entity1", "entity2"],
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  },
  "confidence": 0.95
}
```

### 2. 流式问答
**请求**：
```bash
GET /api/query/stream?question=...&mode=global
```

**响应**：
流式返回答案文本，支持实时显示。

### 3. 获取知识图谱
**请求**：
```bash
GET /api/graph/entity1,entity2,entity3
```

**响应**：
```json
{
  "nodes": [
    {"id": "entity1", "label": "...", "type": "..."}
  ],
  "edges": [
    {"source": "entity1", "target": "entity2", "label": "..."}
  ]
}
```

### 4. 统计信息
**请求**：
```bash
GET /api/stats
```

**响应**：
```json
{
  "total_entities": 20690,
  "total_relationships": 38558,
  "total_documents": 1,
  "total_communities": 100
}
```

---

## 🔍 调试和故障排除

### 1. 检查服务器状态
```bash
python check_server.py
```

### 2. 验证 Neo4j 连接
```bash
python verify_neo4j.py
```

### 3. 查看日志
后端会在控制台输出详细的日志信息，包括：
- 服务初始化状态
- 数据库连接状态
- 每个请求的处理过程
- 错误信息和堆栈跟踪

### 常见问题

**问题 1：Neo4j 连接失败**
- 检查 Neo4j 服务是否运行
- 验证 `NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD` 配置
- 运行 `python verify_neo4j.py` 诊断

**问题 2：数据库连接失败**
- 检查 MySQL 服务是否运行
- 验证 `DATABASE_URL` 配置
- 确保数据库 `graphrag_admin2` 已创建

**问题 3：LLM API 调用失败**
- 检查 `DASHSCOPE_API_KEY` 是否正确
- 确保 API 密钥有效且有足够的额度
- 检查网络连接

---

## 📊 数据流

```
用户请求
  ↓
FastAPI 路由处理
  ↓
访问日志中间件记录
  ↓
GraphRAG 服务检索
  ├─ 加载 Parquet 数据
  ├─ 执行搜索算法
  └─ 调用 LLM 生成答案
  ↓
Neo4j 获取图谱数据
  ↓
数据库记录问答和访问日志
  ↓
返回响应给客户端
```

---

## 🔄 与其他组件的集成

### 前端（Vue 3）
- 地址：`http://localhost:5173`
- 调用后端 API 获取问答结果和图谱数据

### 后台管理系统
- 地址：`http://localhost:8000`
- 查询访问日志、问答记录、统计信息

### 数据库
- MySQL：`localhost:3306/graphrag_admin2`
- Neo4j：`localhost:7687`

---

## 📝 开发指南

### 添加新的 API 端点
```python
@app.post("/api/new-endpoint")
async def new_endpoint(request: YourModel):
    """新端点说明"""
    try:
        # 处理逻辑
        result = ...
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 修改搜索算法
编辑 `graphrag_service.py` 中的 `_global_search()` 或 `_local_search()` 方法。

### 支持新的 LLM 提供商
在 `llm_client.py` 中添加新的 LLM 类。

---

## 📚 相关文档

- [GraphRAG 官方文档](https://microsoft.github.io/graphrag/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Neo4j 文档](https://neo4j.com/docs/)
- [DashScope API 文档](https://help.aliyun.com/zh/dashscope/)

---

## 📞 支持和反馈

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新**：2025-11-22
**版本**：1.0.0
