# Neo4j GraphRAG 中央苏区史智能问答系统

> 基于 Microsoft GraphRAG + Neo4j 图数据库 + 大语言模型（LLM）的领域专业知识问答系统，以中央苏区革命历史为知识库，支持流式输出、知识图谱可视化与后台数据管理。

---

## 目录

- [系统截图](#系统截图)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [依赖说明](#依赖说明)
- [API 文档](#api-文档)
- [配置说明](#配置说明)

---

## 系统截图

### 问答聊天界面

<table>
  <tr>
    <td><img src="docs/images/问答前端/chat-ui-1.png" alt="问答界面 1" width="100%"/></td>
    <td><img src="docs/images/问答前端/chat-ui-2.jpg" alt="问答界面 2" width="100%"/></td>
  </tr>
</table>

### 后台管理系统

<table>
  <tr>
    <td><img src="docs/images/后台前端/admin-1.jpg" alt="后台管理 Dashboard" width="100%"/></td>
    <td><img src="docs/images/后台前端/admin-2.jpg" alt="后台管理 问答记录" width="100%"/></td>
  </tr>
  <tr>
    <td><img src="docs/images/后台前端/admin-3.jpg" alt="后台管理 知识图谱" width="100%"/></td>
    <td><img src="docs/images/后台前端/admin-4.jpg" alt="后台管理 访问日志" width="100%"/></td>
  </tr>
  <tr>
    <td colspan="2"><img src="docs/images/后台前端/admin-5.jpg" alt="后台管理 数据管理" width="50%"/></td>
  </tr>
</table>

### Neo4j 知识图谱数据库

<img src="docs/images/neo4j数据库/neo4j.jpg" alt="Neo4j 图数据库可视化" width="80%"/>

---

## 系统架构

```
用户浏览器
    │
    ├─── 聊天界面 (frontnew/index_updated.html)
    │         │ HTTP fetch (SSE 流式)
    │         ▼
    │    问答后端 FastAPI :8084
    │    ├── GraphRAG 检索引擎 (Parquet)
    │    ├── Neo4j 图谱查询 (可视化)
    │    ├── LLM 流式生成 (DashScope / DeepSeek 等)
    │    └── MySQL 问答记录写入
    │
    └─── 后台管理界面 Vue3 :5173
              │ axios (proxy → :8000)
              ▼
         后台管理后端 FastAPI :8000
         ├── 问答记录查询
         ├── 访问日志统计
         ├── 知识图谱管理
         └── Parquet 数据上传 → Neo4j 导入

依赖服务：MySQL :3306 │ Neo4j :7687
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 问答后端 | Python · FastAPI · GraphRAG (Parquet) · SSE 流式输出 |
| 图数据库 | Neo4j Community Edition |
| 关系数据库 | MySQL 8.x |
| LLM 接入 | 阿里云通义千问 (DashScope) · DeepSeek · SiliconFlow · Groq · 智谱 |
| 后台管理后端 | Python · FastAPI · SQLAlchemy |
| 后台管理前端 | Vue 3 · TypeScript · Vite · Element Plus · ECharts |
| 聊天前端 | 原生 HTML/JS · Tailwind CSS · D3.js · Marked.js |

---

## 项目结构

```
output/
├── backend/                  # 问答系统后端（端口 8084）
│   ├── main.py               # FastAPI 主入口，SSE 流式问答
│   ├── graphrag_service.py   # GraphRAG 检索核心逻辑
│   ├── llm_client.py         # 多 LLM 提供商统一客户端
│   ├── db_logger.py          # MySQL 日志写入
│   ├── import_to_neo4j.py    # Parquet → Neo4j 数据导入工具
│   ├── verify_neo4j.py       # Neo4j 连接与数据验证工具
│   ├── check_server.py       # 后端健康检查脚本
│   └── requirements.txt
│
├── vue_backend/              # 后台管理后端（端口 8000）
│   ├── app.py                # FastAPI 主入口
│   ├── models.py             # SQLAlchemy ORM 模型
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── database.py           # 数据库连接管理
│   ├── init_graph_data.py    # 启动时同步图谱统计数据
│   ├── routers/
│   │   ├── qa_router.py      # 问答记录 CRUD
│   │   ├── graph_router.py   # 知识图谱管理
│   │   ├── data_router.py    # Parquet 文件上传 & Neo4j 导入
│   │   ├── dashboard_router.py # 统计面板数据
│   │   └── logs_router.py    # 访问日志 & 错误日志
│   └── requirements.txt
│
├── vue/                      # 后台管理前端（端口 5173）
│   ├── src/
│   │   ├── views/            # 页面：Dashboard / QA管理 / 图谱 / 日志 / 数据
│   │   ├── api/              # axios 封装
│   │   └── components/       # 公共组件
│   ├── vite.config.ts        # 开发代理 → :8000
│   └── package.json
│
├── frontnew/                 # 独立聊天界面
│   ├── index_updated.html    # 主聊天页（直接用浏览器打开即可）
│   └── app_new.py            # 可选：Flask 托管服务（端口 5000）
│
├── database/
│   └── graphrag_admin_complete.sql  # MySQL 完整建表语句
│
├── 启动说明.md               # 完整启动指南
└── LLM_CHANGE_GUIDE.md       # 切换 LLM 提供商说明
```

---

## 环境要求

| 软件 | 版本要求 |
|------|---------|
| Python | 3.9 + |
| Node.js | 18 + |
| MySQL | 8.x |
| Neo4j | Community 5.x |

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/linqiaosheng387-cell/neo4j-graphRAG-intelligent-questions-answering-system.git
cd neo4j-graphRAG-intelligent-questions-answering-system
```

### 2. 创建 MySQL 数据库

```sql
CREATE DATABASE IF NOT EXISTS graphrag_admin2 CHARACTER SET utf8mb4;
```

也可以直接导入完整表结构：

```bash
mysql -u root -p graphrag_admin2 < database/graphrag_admin_complete.sql
```

### 3. 配置环境变量

**`backend/.env`**

```env
# LLM 配置（选一个填写）
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=你的通义千问 API Key
DASHSCOPE_MODEL=qwen-plus

# 或使用 DeepSeek
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=你的 DeepSeek API Key

# MySQL
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2

# Neo4j
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678

# GraphRAG Parquet 数据路径（相对于 backend/ 目录）
GRAPHRAG_DATA_PATH=..
```

**`vue_backend/.env`**

```env
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2
QA_SYSTEM_URL=http://localhost:8084
```

### 4. 安装依赖

```bash
# 问答后端
cd backend && pip install -r requirements.txt

# 后台管理后端
cd ../vue_backend && pip install -r requirements.txt

# 后台管理前端
cd ../vue && npm install
```

### 5. 启动服务（需开 3 个终端）

```bash
# 终端 1 — 问答后端
cd backend && python main.py
# 启动成功：🚀 http://0.0.0.0:8084

# 终端 2 — 后台管理后端
cd vue_backend && python app.py
# 启动成功：API 文档 http://localhost:8000/api/docs

# 终端 3 — 后台管理前端
cd vue && npm run dev
# 启动成功：http://localhost:5173
```

### 6. 访问系统

| 功能 | 地址 |
|------|------|
| **聊天界面**（双击直接打开） | `frontnew/index_updated.html` |
| **后台管理系统** | http://localhost:5173 |
| 问答系统 API 文档 | http://localhost:8084/docs |
| 后台管理 API 文档 | http://localhost:8000/api/docs |

---

## 依赖说明

### `backend/requirements.txt` — 问答系统后端

```
fastapi==0.104.1          # Web 框架
uvicorn==0.24.0           # ASGI 服务器
pandas==2.1.3             # Parquet 数据处理
pyarrow==13.0.0           # Parquet 文件读取
neo4j==5.15.0             # Neo4j 图数据库驱动
sqlalchemy==2.0.23        # ORM（写 MySQL 日志）
pymysql==1.1.0            # MySQL 驱动
requests==2.31.0          # HTTP 客户端
openai==1.3.8             # DashScope / OpenAI 兼容 SDK（LLM 调用）
python-dotenv==1.0.0      # 加载 .env 配置文件
tqdm==4.66.1              # 进度条（Neo4j 数据导入）
aiofiles==23.2.1          # 异步文件操作
httpx==0.25.1             # 异步 HTTP 客户端
```

### `vue_backend/requirements.txt` — 后台管理后端

```
fastapi==0.104.1          # Web 框架
uvicorn[standard]==0.24.0 # ASGI 服务器（含 websockets）
sqlalchemy==2.0.23        # ORM
pymysql==1.1.0            # MySQL 驱动
cryptography==41.0.7      # 数据库连接加密支持
pydantic==2.5.0           # 数据验证
pydantic-settings==2.1.0  # 环境变量配置
email-validator==2.1.0    # 邮箱格式验证
python-dotenv==1.0.0      # 加载 .env 配置文件
python-multipart==0.0.6   # 文件上传支持（Parquet 导入）
```

### `frontnew/requirements.txt` — 聊天前端（可选，Flask 托管）

```
Flask==2.3.3              # Web 框架（托管 index_updated.html）
requests==2.31.0          # 向问答后端转发请求
gunicorn==21.2.0          # 生产环境 WSGI 服务器
python-dotenv==1.0.0      # 加载 .env 配置文件
```

> **说明**：聊天前端 `index_updated.html` 可以**直接双击用浏览器打开**，无需启动 Flask，`frontnew/requirements.txt` 中的依赖仅在使用 `app_new.py` 托管时需要安装。

### `vue/package.json` — 后台管理前端（Node.js）

```
vue ^3.3.4                # 前端框架
vue-router ^4.2.5         # 路由管理
pinia ^2.1.6              # 状态管理
axios ^1.6.2              # HTTP 请求
element-plus ^2.4.2       # UI 组件库
echarts ^5.4.3            # 数据可视化图表
@vueuse/core ^10.7.0      # Vue 组合式工具函数
dayjs ^1.11.10            # 日期处理
```

---

## API 文档

启动服务后访问交互式 Swagger 文档：

- **问答系统**：http://localhost:8084/docs
- **后台管理**：http://localhost:8000/api/docs

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/query/stream` | 流式问答（SSE） |
| `POST` | `/api/query` | 非流式问答 |
| `GET` | `/api/stats` | 知识库统计信息 |
| `GET` | `/api/graph/{entity_titles}` | 获取实体图谱数据 |
| `GET` | `/api/recommend` | 获取推荐问题 |
| `GET` | `/api/health` | 健康检查 |

---

## 配置说明

### 切换 LLM 提供商

修改 `backend/.env` 中的 `LLM_PROVIDER`，重启后端即可：

| 提供商 | `LLM_PROVIDER` 值 | 所需 API Key 变量 |
|--------|-------------------|-----------------|
| 阿里云通义千问 | `dashscope` | `DASHSCOPE_API_KEY` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` |
| SiliconFlow | `siliconflow` | `SILICONFLOW_API_KEY` |
| Groq | `groq` | `GROQ_API_KEY` |
| 智谱 AI | `zhipu` | `ZHIPU_API_KEY` |

详细说明见 [LLM_CHANGE_GUIDE.md](./LLM_CHANGE_GUIDE.md)

### Neo4j 数据导入

如需将 Parquet 数据导入 Neo4j 以启用图谱可视化：

```bash
cd backend
python import_to_neo4j.py
```

> Neo4j 不是必需的。未连接时问答功能正常，仅图谱可视化不可用。
