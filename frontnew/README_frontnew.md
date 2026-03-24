# 中央苏区史问答系统 - 前端代理服务

## 📋 项目概述

这是一个基于 Flask 的前端代理服务，作为 GraphRAG 问答系统的中间层，负责：
- 提供用户交互界面
- 转发前端请求到后端 API
- 处理错误和异常情况
- 支持流式和非流式问答

**核心特性**：
- 🎨 **现代化 UI** - 使用 Tailwind CSS 和现代 Web 技术
- 🔄 **代理转发** - 安全地转发请求到后端 API
- 📱 **响应式设计** - 支持桌面和移动设备
- 💬 **实时问答** - 支持流式和非流式问答
- 📊 **知识图谱展示** - 可视化问答相关的知识图谱

---

## 📁 文件结构

```
frontnew/
├── app3_updated.py          # Flask 应用主文件（推荐使用）
├── app3.py                  # Flask 应用备份版本
├── app_new.py               # 新版本应用（实验性）
├── index_updated.html       # 更新后的前端页面（推荐使用）
├── index.html               # 原始前端页面
└── README.md                # 本文档
```

---

## 🔧 核心文件说明

### 1. **app3_updated.py** - Flask 应用主文件（推荐）

主要职责：
- 初始化 Flask 应用
- 定义所有路由和 API 端点
- 转发请求到后端 API
- 处理错误和异常

**关键配置**：
```python
# 后端 API 地址
BACKEND_API_URL = "http://localhost:8084"

# 预设问题列表
PRESET_QUESTIONS = [
    "中央苏区的历史意义",
    "中央苏区主要领导人物",
    # ...
]
```

**主要路由**：
```
GET  /                    # 首页
POST /api/query           # 问答查询
GET  /api/graph/<entities> # 获取知识图谱
```

**启动命令**：
```bash
python app3_updated.py
# 或使用 gunicorn（生产环境）
gunicorn -w 4 -b 0.0.0.0:5000 app3_updated.py
```

---

### 2. **index_updated.html** - 前端页面（推荐）

主要功能：
- 提供用户交互界面
- 显示预设问题
- 实时显示问答结果
- 可视化知识图谱

**主要组件**：
- **问题输入区** - 用户输入问题的文本框
- **预设问题** - 快速选择常见问题
- **答案显示区** - 显示 AI 生成的答案
- **知识图谱** - 可视化相关实体和关系
- **模式选择** - 全局搜索 vs 本地搜索

**技术栈**：
- HTML5
- Tailwind CSS（样式）
- JavaScript（交互）
- ECharts（图谱可视化）

---

## ⚙️ 环境配置

### 后端 API 地址配置

编辑 `app3_updated.py` 第 18 行：
```python
BACKEND_API_URL = "http://localhost:8084"  # 改为实际的后端地址
```

### 依赖安装

```bash
pip install flask requests
```

---

## 🚀 启动和运行

### 1. 安装依赖
```bash
pip install flask requests
```

### 2. 配置后端地址
编辑 `app3_updated.py`，确保 `BACKEND_API_URL` 指向正确的后端地址。

### 3. 启动服务
```bash
# 开发环境
python app3_updated.py

# 生产环境（使用 gunicorn）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app3_updated.py
```

### 4. 访问应用
打开浏览器访问：`http://localhost:5000`

---

## 📡 API 端点

### 1. 首页
**请求**：
```
GET /
```

**响应**：
返回 HTML 页面，包含预设问题列表。

---

### 2. 问答查询
**请求**：
```bash
POST /api/query
Content-Type: application/json

{
  "question": "中央苏区的历史意义",
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

**错误处理**：
- 连接错误：返回 "无法连接到后端服务"
- 超时错误：返回 "后端服务响应超时"
- 其他错误：返回具体错误信息

---

### 3. 知识图谱
**请求**：
```
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

---

## 🎨 前端功能说明

### 问题输入
- 用户可以在文本框中输入任意问题
- 支持中文和英文输入
- 按 Enter 或点击搜索按钮提交

### 预设问题
- 显示 6 个常见问题
- 点击快速提交问题
- 可在 `app3_updated.py` 中修改预设问题列表

### 搜索模式
- **全局搜索**（Global）：基于社区报告的全局搜索
- **本地搜索**（Local）：基于实体和关系的本地搜索

### 答案显示
- 实时显示 AI 生成的答案
- 显示置信度分数
- 显示答案来源

### 知识图谱
- 可视化问答相关的实体和关系
- 支持交互（拖动、缩放、点击）
- 显示实体类型和关系标签

---

## 🔄 与其他组件的集成

### 后端 API（backend）
- 地址：`http://localhost:8084`（可配置）
- 转发所有问答请求到后端
- 接收问答结果和图谱数据

### 后台管理系统（vue_backend）
- 地址：`http://localhost:8000`
- 独立运行，不与前端代理直接通信

### 前端管理界面（vue）
- 地址：`http://localhost:5173`
- 独立的后台管理界面

---

## 🔍 调试和故障排除

### 常见问题

**问题 1：无法连接到后端服务**
- 检查后端服务是否运行
- 验证 `BACKEND_API_URL` 配置是否正确
- 检查防火墙设置

**问题 2：页面加载缓慢**
- 检查网络连接
- 检查后端服务性能
- 增加超时时间（在 `app3_updated.py` 中修改 `timeout=30`）

**问题 3：知识图谱不显示**
- 检查浏览器控制台是否有错误
- 确保后端返回了 `graph_data`
- 检查 ECharts 库是否正确加载

### 调试模式

启用 Flask 调试模式：
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 📝 开发指南

### 修改预设问题
编辑 `app3_updated.py` 中的 `PRESET_QUESTIONS` 列表：
```python
PRESET_QUESTIONS = [
    "你的问题1",
    "你的问题2",
    # ...
]
```

### 修改后端地址
编辑 `app3_updated.py` 第 18 行：
```python
BACKEND_API_URL = "http://your-backend-address:port"
```

### 自定义样式
编辑 `index_updated.html` 中的 Tailwind CSS 类。

### 添加新功能
在 `app3_updated.py` 中添加新的路由：
```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    # 你的逻辑
    pass
```

---

## 📊 数据流

```
用户输入问题
  ↓
前端页面提交请求
  ↓
Flask 应用接收请求
  ↓
转发到后端 API
  ↓
后端处理并返回结果
  ↓
Flask 应用返回给前端
  ↓
前端显示答案和图谱
```

---

## 🚀 性能优化

### 缓存
- 考虑缓存常见问题的答案
- 使用 Redis 或内存缓存

### 并发
- 使用 gunicorn 的多个 worker 进程
- 配置合适的超时时间

### 压缩
- 启用 gzip 压缩
- 压缩静态资源

---

## 📚 相关文档

- [Flask 官方文档](https://flask.palletsprojects.com/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [ECharts 文档](https://echarts.apache.org/)

---

## 📞 支持和反馈

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新**：2025-11-22
**版本**：1.0.0
