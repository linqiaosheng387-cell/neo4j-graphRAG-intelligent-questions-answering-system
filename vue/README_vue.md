# GraphRAG 后台管理系统 - 前端界面

## 📋 项目概述

这是 GraphRAG 后台管理系统的前端界面，基于 Vue 3 + TypeScript + Vite 构建。提供数据面板、问答管理、用户日志、图谱管理等功能。

**核心特性**：
- 🎨 **现代化 UI** - 基于 Element Plus 的美观界面
- 🌓 **明暗主题** - 支持浅色和深色主题切换
- 📱 **响应式设计** - 完美适配桌面和移动设备
- 📊 **数据可视化** - 使用 ECharts 展示各类统计图表
- 🔐 **权限管理** - 基于用户角色的权限控制
- ⚡ **高性能** - Vite 构建，快速加载和响应

---

## 📁 项目结构

```
vue/
├── src/
│   ├── api/                 # API 请求模块
│   │   ├── dashboard.ts     # 数据面板 API
│   │   ├── qa.ts            # 问答管理 API
│   │   ├── graph.ts         # 图谱管理 API
│   │   ├── logs.ts          # 日志 API
│   │   └── data.ts          # 数据上传 API
│   ├── components/          # 可复用组件
│   │   ├── common/          # 通用组件
│   │   │   ├── StatCard.vue # 统计卡片
│   │   │   ├── Card.vue     # 卡片容器
│   │   │   └── Table.vue    # 表格组件
│   │   └── layout/          # 布局组件
│   │       ├── Header.vue   # 顶部导航
│   │       └── Sidebar.vue  # 侧边栏
│   ├── views/               # 页面组件
│   │   ├── Dashboard.vue    # 数据面板
│   │   ├── QAManagement.vue # 问答管理
│   │   ├── GraphManagement.vue # 图谱管理
│   │   ├── DataManagement.vue  # 数据管理
│   │   ├── UserAccessLogs.vue  # 用户日志
│   │   └── OperationMonitoring.vue # 运维监控
│   ├── stores/              # Pinia 状态管理
│   │   ├── auth.ts          # 认证状态
│   │   └── app.ts           # 应用状态
│   ├── router/              # 路由配置
│   │   └── index.ts         # 路由定义
│   ├── styles/              # 全局样式
│   │   └── main.scss        # 主样式文件
│   ├── App.vue              # 根组件
│   └── main.ts              # 应用入口
├── public/                  # 静态资源
├── index.html               # HTML 模板
├── vite.config.ts           # Vite 配置
├── tsconfig.json            # TypeScript 配置
├── package.json             # 项目依赖
└── README.md                # 本文档
```

---

## 🔧 核心模块说明

### 1. **API 模块** (`src/api/`)

负责与后端 API 通信。

**主要文件**：
- `dashboard.ts` - 数据面板 API（概览、趋势、统计等）
- `qa.ts` - 问答管理 API（CRUD 操作）
- `graph.ts` - 图谱管理 API
- `logs.ts` - 日志查询 API
- `data.ts` - 数据上传 API

**使用示例**：
```typescript
import { dashboardAPI } from '@/api/dashboard'

// 获取概览数据
const overview = await dashboardAPI.getOverview()

// 获取访问趋势
const trend = await dashboardAPI.getVisitTrend()
```

---

### 2. **组件模块** (`src/components/`)

可复用的 UI 组件。

**通用组件**：
- `StatCard.vue` - 统计卡片（显示数值和趋势）
- `Card.vue` - 卡片容器（带标题和内容）
- `Table.vue` - 表格组件（支持排序、分页）

**布局组件**：
- `Header.vue` - 顶部导航栏
- `Sidebar.vue` - 侧边栏菜单

---

### 3. **页面组件** (`src/views/`)

各个功能页面。

**主要页面**：

#### Dashboard.vue - 数据面板
- 统计卡片：总用户数、总问答数、知识图谱数、访问次数
- 访问趋势图：最近 7 天的访问和问答数据
- 时间段统计：不同时间段的访问和问答对比
- 热门 IP 排名：访问最频繁的 IP 地址
- 最近问题：最新提交的问题列表

#### QAManagement.vue - 问答管理
- 问答列表：显示所有问答记录
- 搜索和筛选：按问题内容和状态筛选
- 新建问答：添加新的问答记录
- 编辑和删除：修改或删除现有记录

#### GraphManagement.vue - 图谱管理
- 图谱列表：显示所有知识图谱
- 图谱详情：查看图谱的实体数和关系数
- 图谱操作：激活、停用、删除图谱

#### DataManagement.vue - 数据管理
- 数据上传：上传 Parquet 文件
- 上传记录：查看上传历史
- 导入状态：显示 Neo4j 导入进度

#### UserAccessLogs.vue - 用户日志
- 访问日志：显示所有 API 访问记录
- 统计信息：访问次数、唯一 IP 数等
- IP 统计：按 IP 地址统计访问情况

#### OperationMonitoring.vue - 运维监控
- 系统日志：显示系统运行日志
- 日志级别：INFO、WARNING、ERROR、CRITICAL
- 日志搜索：按模块和时间搜索

---

### 4. **状态管理** (`src/stores/`)

使用 Pinia 进行状态管理。

**主要 Store**：
- `auth.ts` - 认证状态（用户信息、权限等）
- `app.ts` - 应用状态（主题、语言等）

---

### 5. **路由配置** (`src/router/`)

定义应用的路由和导航。

**主要路由**：
```typescript
/dashboard          # 数据面板
/qa-management      # 问答管理
/graph-management   # 图谱管理
/data-management    # 数据管理
/user-logs          # 用户日志
/operation-monitor  # 运维监控
```

---

## ⚙️ 环境配置

### .env.example

```env
VITE_API_URL=http://localhost:8000
```

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_API_URL` | 后端 API 地址 | http://localhost:8000 |

---

## 🚀 启动和运行

### 1. 安装依赖
```bash
npm install
```

### 2. 开发环境
```bash
npm run dev
```

访问 `http://localhost:5173`

### 3. 生产构建
```bash
npm run build
```

### 4. 预览构建结果
```bash
npm run preview
```

---

## 📦 依赖说明

| 包名 | 版本 | 说明 |
|------|------|------|
| vue | ^3.3.4 | Vue 框架 |
| vue-router | ^4.2.5 | 路由管理 |
| pinia | ^2.1.6 | 状态管理 |
| axios | ^1.6.2 | HTTP 客户端 |
| element-plus | ^2.4.2 | UI 组件库 |
| echarts | ^5.4.3 | 数据可视化 |
| dayjs | ^1.11.10 | 日期处理 |
| @vueuse/core | ^10.7.0 | Vue 组合式 API 工具 |

---

## 🎨 主题和样式

### 主题切换
在 Header 组件中点击主题按钮切换浅色/深色主题。

### 样式文件
- `src/styles/main.scss` - 全局样式
- 各组件的 `<style scoped>` - 组件样式

### Tailwind CSS
使用 Tailwind CSS 进行样式设计。

---

## 📡 API 集成

### 数据面板 API

```typescript
// 获取概览数据
dashboardAPI.getOverview()

// 获取访问趋势
dashboardAPI.getVisitTrend()

// 获取时间段统计
dashboardAPI.getTimePeriodStats(days: number)

// 获取热门 IP
dashboardAPI.getTopIPs(limit: number)

// 获取最近问题
dashboardAPI.getRecentQuestions(limit: number)
```

### 问答管理 API

```typescript
// 获取问答列表
qaAPI.getRecords(page, pageSize, search, status)

// 创建问答
qaAPI.createQARecord(data)

// 更新问答
qaAPI.updateQARecord(id, data)

// 删除问答
qaAPI.deleteQARecord(id)
```

---

## 🔄 与其他组件的集成

### 后端 API（vue_backend）
- 地址：`http://localhost:8000`
- 提供所有数据和操作接口

### 问答系统（backend）
- 地址：`http://localhost:8085`
- 前端不直接调用，通过后台管理后端转发

### 前端代理（frontnew）
- 地址：`http://localhost:5000`
- 独立的问答界面

---

## 🔍 调试和故障排除

### 常见问题

**问题 1：API 连接失败**
- 检查 `VITE_API_URL` 配置
- 确保后端服务运行在正确的端口
- 检查 CORS 配置

**问题 2：页面加载缓慢**
- 检查网络连接
- 使用浏览器开发者工具分析性能
- 考虑启用代码分割和懒加载

**问题 3：样式显示不正确**
- 清除浏览器缓存
- 重新构建项目
- 检查 Tailwind CSS 配置

### 调试模式

启用 Vue DevTools 浏览器扩展进行调试。

---

## 📝 开发指南

### 添加新页面

1. 在 `src/views/` 创建新的 `.vue` 文件
2. 在 `src/router/index.ts` 添加路由
3. 在 `src/components/layout/Sidebar.vue` 添加菜单项

### 添加新 API

1. 在 `src/api/` 创建新的 `.ts` 文件
2. 定义 API 函数
3. 在组件中导入和使用

### 添加新组件

1. 在 `src/components/` 创建新的 `.vue` 文件
2. 定义组件逻辑和样式
3. 在其他组件中导入和使用

---

## 🚀 性能优化

### 代码分割
使用动态导入实现路由级别的代码分割：
```typescript
const Dashboard = () => import('@/views/Dashboard.vue')
```

### 图片优化
- 使用 WebP 格式
- 压缩图片大小
- 使用 CDN 加速

### 缓存策略
- 利用浏览器缓存
- 使用 Service Worker
- 实现数据缓存

---

## 📚 相关文档

- [Vue 3 官方文档](https://vuejs.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Element Plus 文档](https://element-plus.org/)
- [ECharts 文档](https://echarts.apache.org/)
- [TypeScript 文档](https://www.typescriptlang.org/)

---

## 📞 支持和反馈

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新**：2025-11-22
**版本**：1.0.0
