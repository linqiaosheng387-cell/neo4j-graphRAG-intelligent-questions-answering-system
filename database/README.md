# GraphRAG 数据库 - 完整配置指南

## 📋 项目概述

这是 GraphRAG 系统的数据库配置和初始化模块。包含完整的 MySQL 数据库 schema、初始化脚本和数据导出工具。

**核心功能**：
- 📊 **数据库 Schema** - 完整的表结构定义
- 🔧 **初始化工具** - 自动化数据库初始化
- 📤 **数据导出** - 导出现有数据库结构
- 📝 **文档** - 详细的配置和使用说明

---

## 📁 文件结构

```
database/
├── graphrag_admin_complete.sql    # 完整的数据库 SQL 脚本
├── show_schema.py                 # 显示数据库结构的 Python 脚本
├── export_schema.py               # 导出数据库结构的 Python 脚本
└── README.md                      # 本文档
```

---

## 🔧 核心文件说明

### 1. **graphrag_admin_complete.sql** - 完整数据库脚本

这是一个完整的 MySQL 数据库初始化脚本，包含：

**数据库创建**：
```sql
DROP DATABASE IF EXISTS graphrag_admin;
CREATE DATABASE graphrag_admin DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE graphrag_admin;
```

**11 个数据表**：
1. `users` - 用户表
2. `knowledge_graphs` - 知识图谱表
3. `qa_records` - 问答记录表
4. `data_uploads` - 数据上传记录表
5. `neo4j_configs` - Neo4j 配置表
6. `system_logs` - 系统日志表
7. `user_access_logs` - 用户访问日志表
8. `access_statistics` - 访问统计表
9. `ip_statistics` - IP 统计表
10. `real_time_questions` - 实时问题表
11. `time_period_statistics` - 时间段统计表

**初始化数据**：
- 默认管理员用户：`admin` / `admin123`
- 默认普通用户：`user` / `user123`
- 示例知识图谱：中央苏区知识图谱

**使用方法**：

#### 方式 1：MySQL 命令行（推荐，无需 GUI 工具）

**Windows 系统**：
```bash
# 进入 database 目录
cd e:\graphRAG\output\database

# 运行 SQL 脚本
mysql -u root -p < graphrag_admin_complete.sql

# 或者指定密码（不推荐，密码会显示在命令行）
mysql -u root -proot < graphrag_admin_complete.sql

# 或者使用完整路径
mysql -u root -p < "e:\graphRAG\output\database\graphrag_admin_complete.sql"
```

**Linux/Mac 系统**：
```bash
# 进入 database 目录
cd /path/to/graphrag/database

# 运行 SQL 脚本
mysql -u root -p < graphrag_admin_complete.sql
```

**详细步骤**：
1. 打开 PowerShell 或 CMD
2. 进入 database 文件夹：`cd e:\graphRAG\output\database`
3. 运行命令：`mysql -u root -p < graphrag_admin_complete.sql`
4. 输入 MySQL 密码（默认为 `root`）
5. 等待脚本执行完成

**验证是否成功**：
```bash
# 连接到 MySQL
mysql -u root -p

# 在 MySQL 命令行中执行
SHOW DATABASES;

# 应该能看到 graphrag_admin 数据库
```

---

#### 方式 2：Navicat（GUI 工具）

# 1. 打开 Navicat
# 2. 右键数据库 → 新建查询
# 3. 打开 graphrag_admin_complete.sql
# 4. 点击运行

---

#### 方式 3：MySQL Workbench（GUI 工具）

# 1. 打开 MySQL Workbench
# 2. File → Open SQL Script
# 3. 选择 graphrag_admin_complete.sql
# 4. 点击执行

---

#### 方式 4：直接在 MySQL 命令行中执行（适合小脚本）

```bash
# 连接到 MySQL
mysql -u root -p

# 在 MySQL 命令行中执行
source e:\graphRAG\output\database\graphrag_admin_complete.sql;

# 或者（Linux/Mac）
source /path/to/graphrag/database/graphrag_admin_complete.sql;
```

---

#### 方式 5：使用 Python 脚本初始化（推荐）

```bash
# 如果有 init_database.py 脚本，可以使用 Python 初始化
python database/init_database.py

# 或指定参数
python database/init_database.py -H localhost -u root -p root
```
```

---

### 2. **show_schema.py** - 显示数据库结构

这个 Python 脚本可以连接到 MySQL 数据库并显示完整的数据库结构。

**功能**：
- 显示所有表的信息
- 显示每个表的字段、类型、约束
- 显示索引和外键信息
- 显示视图、存储过程、触发器

**使用方法**：
```bash
python show_schema.py
```

**输出示例**：
```
================================================================================
📊 数据库: graphrag_admin
================================================================================

📋 找到 11 个表:

====================================================================================================
表名: users
====================================================================================================

【创建语句】:
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  ...
)

【字段信息】(9 个字段):
字段名                  类型                             Null   Key    默认值                  额外
...

【索引信息】(6 个):
...

【外键信息】(0 个):
...
```

---

### 3. **export_schema.py** - 导出数据库结构

这个 Python 脚本可以导出现有数据库的完整结构为 SQL 和 JSON 格式。

**功能**：
- 导出所有表的创建语句
- 导出视图、存储过程、触发器
- 生成 SQL 脚本文件
- 生成 JSON schema 文件

**使用方法**：
```bash
python export_schema.py
```

**输出文件**：
- `graphrag_admin_schema_export.sql` - SQL 脚本
- `graphrag_admin_schema_export.json` - JSON schema

---

## 📊 数据库表详解

### users - 用户表
```sql
CREATE TABLE `users` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `username` varchar(50) UNIQUE NOT NULL,
  `email` varchar(100) UNIQUE NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','user') DEFAULT 'user',
  `is_active` tinyint DEFAULT 1,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_login` datetime
)
```

**用途**：存储系统用户信息

---

### qa_records - 问答记录表
```sql
CREATE TABLE `qa_records` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int,
  `question` text NOT NULL,
  `answer` text,
  `mode` varchar(50),
  `status` varchar(50),
  `response_time` float,
  `confidence` float,
  `graph_id` int,
  `created_at` datetime,
  `updated_at` datetime
)
```

**用途**：存储所有问答记录

---

### user_access_logs - 访问日志表
```sql
CREATE TABLE `user_access_logs` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `ip_address` varchar(50) NOT NULL,
  `endpoint` varchar(255) NOT NULL,
  `method` varchar(10) NOT NULL,
  `status_code` int,
  `response_time` float,
  `device_info` varchar(255),
  `user_agent` text,
  `access_time` datetime
)
```

**用途**：记录所有 API 访问日志

---

### knowledge_graphs - 知识图谱表
```sql
CREATE TABLE `knowledge_graphs` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `created_by` int,
  `status` enum('active','inactive','processing','failed'),
  `entity_count` int DEFAULT 0,
  `relation_count` int DEFAULT 0,
  `neo4j_db_name` varchar(100),
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

**用途**：管理知识图谱元数据

---

### data_uploads - 数据上传记录表
```sql
CREATE TABLE `data_uploads` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `upload_name` varchar(100) NOT NULL,
  `user_id` int NOT NULL,
  `graph_id` int,
  `status` enum('pending','processing','completed','failed'),
  `entities_file` varchar(500),
  `relationships_file` varchar(500),
  `text_units_file` varchar(500),
  `communities_file` varchar(500),
  `community_reports_file` varchar(500),
  `documents_file` varchar(500),
  `error_message` longtext,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

**用途**：记录 Parquet 文件上传和 Neo4j 导入状态

---

## 🔄 修改数据库配置指南

### 场景：将数据库从 `graphrag_admin` 改为 `graphrag_admin2`

需要修改以下 **5 个文件** 中的数据库名字：

---

### 1. **backend/.env** - 问答系统环境配置

**文件位置**：`e:\graphRAG\output\backend\.env`

**修改内容**：
```env
# 原配置
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin

# 改为
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2
```

**说明**：
- 这是问答系统的数据库连接字符串
- 用于记录问答和访问日志
- 格式：`mysql+pymysql://用户名:密码@主机:端口/数据库名`

---

### 2. **backend/db_logger.py** - 问答系统日志模块

**文件位置**：`e:\graphRAG\output\backend\db_logger.py`

**修改内容**（第 17-20 行）：
```python
# 原配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/graphrag_admin"
)

# 改为
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/graphrag_admin2"
)
```

**说明**：
- 这是 `db_logger.py` 的默认数据库连接
- 用于记录问答和访问日志
- 如果环境变量中有 `DATABASE_URL`，会使用环境变量的值

---

### 3. **vue_backend/routers/qa_router.py** - 后台管理系统问答路由

**文件位置**：`e:\graphRAG\output\vue_backend\routers\qa_router.py`

**修改内容**（第 22-26 行）：
```python
# 原配置
QA_DATABASE_URL = os.getenv(
    "QA_DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/graphrag_admin"
)

# 改为
QA_DATABASE_URL = os.getenv(
    "QA_DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/graphrag_admin2"
)
```

**说明**：
- 这是后台管理系统读取问答数据的数据库连接
- 用于在后台管理界面显示问答记录
- 如果环境变量中有 `QA_DATABASE_URL`，会使用环境变量的值

---

### 4. **vue_backend/config.py** - 后台管理系统配置

**文件位置**：`e:\graphRAG\output\vue_backend\config.py`

**修改内容**（第 10-13 行）：
```python
# 原配置
SQLALCHEMY_DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/graphrag_admin'
)

# 改为
SQLALCHEMY_DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/graphrag_admin2'
)
```

**说明**：
- 这是后台管理系统的主数据库连接
- 用于存储用户、问答、日志等数据
- 如果环境变量中有 `DATABASE_URL`，会使用环境变量的值

---

### 5. **vue_backend/.env** - 后台管理系统环境配置

**文件位置**：`e:\graphRAG\output\vue_backend\.env`

**修改内容**（第 1-7 行）：
```env
# 原配置
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin
QA_DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin

# 改为
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2
QA_DATABASE_URL=mysql+pymysql://root:root@localhost:3306/graphrag_admin2
```

**说明**：
- `DATABASE_URL` - 后台管理系统的主数据库连接
- `QA_DATABASE_URL` - 读取问答数据的数据库连接
- 这里的配置会覆盖代码中的默认值

---

## 📋 修改数据库配置的完整步骤

### 步骤 1：创建新数据库
```bash
# 在 MySQL 中创建新数据库
mysql -u root -p
CREATE DATABASE graphrag_admin2 DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 步骤 2：导入 SQL 脚本
```bash
# 将 schema 导入到新数据库
mysql -u root -p graphrag_admin2 < database/graphrag_admin_complete.sql
```

### 步骤 3：修改 5 个配置文件

按照上面的说明，修改以下文件中的数据库名：

| 文件 | 行号 | 修改内容 |
|------|------|--------|
| `backend/.env` | 3 | `graphrag_admin` → `graphrag_admin2` |
| `backend/db_logger.py` | 19 | `graphrag_admin` → `graphrag_admin2` |
| `vue_backend/routers/qa_router.py` | 25 | `graphrag_admin` → `graphrag_admin2` |
| `vue_backend/config.py` | 12 | `graphrag_admin` → `graphrag_admin2` |
| `vue_backend/.env` | 4,7 | `graphrag_admin` → `graphrag_admin2` |

### 步骤 4：重启所有服务
```bash
# 重启问答系统
cd backend
python main.py

# 重启后台管理后端
cd vue_backend
python app.py

# 重启前端（如果需要）
cd vue
npm run dev
```

### 步骤 5：验证连接
```bash
# 检查后端是否正常运行
curl http://localhost:8085/health

# 检查后台管理后端是否正常运行
curl http://localhost:8000/api/docs
```

---

## 🔍 修改数据库配置的常见错误

### 错误 1：只修改了部分文件
**症状**：某些功能正常，某些功能报错
**原因**：没有修改所有 5 个文件
**解决**：确保修改了所有 5 个文件

### 错误 2：修改了错误的数据库名
**症状**：连接失败
**原因**：数据库名拼写错误或数据库不存在
**解决**：
- 检查数据库名拼写
- 确保数据库已创建
- 运行 `SHOW DATABASES;` 验证

### 错误 3：没有重启服务
**症状**：修改后仍然使用旧数据库
**原因**：服务缓存了旧配置
**解决**：重启所有相关服务

### 错误 4：权限不足
**症状**：连接成功但无法操作
**原因**：用户权限不足
**解决**：
```sql
GRANT ALL PRIVILEGES ON graphrag_admin2.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

---

## 📊 数据库配置总结表

| 组件 | 文件 | 环境变量 | 默认值 |
|------|------|--------|--------|
| 问答系统 | `backend/.env` | `DATABASE_URL` | graphrag_admin |
| 问答系统日志 | `backend/db_logger.py` | `DATABASE_URL` | graphrag_admin |
| 后台管理后端 | `vue_backend/.env` | `DATABASE_URL` | graphrag_admin |
| 后台管理后端 | `vue_backend/.env` | `QA_DATABASE_URL` | graphrag_admin |
| 后台管理配置 | `vue_backend/config.py` | `DATABASE_URL` | graphrag_admin |
| 后台管理问答路由 | `vue_backend/routers/qa_router.py` | `QA_DATABASE_URL` | graphrag_admin |

---

## 🚀 快速修改脚本

如果要批量修改数据库名，可以使用以下脚本：

```bash
#!/bin/bash
# 修改数据库配置脚本

OLD_DB="graphrag_admin"
NEW_DB="graphrag_admin2"

# 修改 backend/.env
sed -i "s/$OLD_DB/$NEW_DB/g" backend/.env

# 修改 backend/db_logger.py
sed -i "s/$OLD_DB/$NEW_DB/g" backend/db_logger.py

# 修改 vue_backend/.env
sed -i "s/$OLD_DB/$NEW_DB/g" vue_backend/.env

# 修改 vue_backend/config.py
sed -i "s/$OLD_DB/$NEW_DB/g" vue_backend/config.py

# 修改 vue_backend/routers/qa_router.py
sed -i "s/$OLD_DB/$NEW_DB/g" vue_backend/routers/qa_router.py

echo "✅ 数据库配置已修改为: $NEW_DB"
```

---

## 📚 相关文档

- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [PyMySQL 文档](https://pymysql.readthedocs.io/)

---

## � 终端运行常见问题

### 问题 1：找不到 mysql 命令
**症状**：`'mysql' 不是内部或外部命令`
**原因**：MySQL 没有添加到系统 PATH
**解决方案**：
```bash
# 方式 1：使用完整路径
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql" -u root -p < graphrag_admin_complete.sql

# 方式 2：添加 MySQL 到 PATH（永久解决）
# Windows: 系统设置 → 环境变量 → 添加 C:\Program Files\MySQL\MySQL Server 8.0\bin
# 然后重启 PowerShell/CMD

# 方式 3：使用 MySQL 自带的命令行工具
# 打开 MySQL Command Line Client（从开始菜单）
```

---

### 问题 2：密码错误
**症状**：`ERROR 1045 (28000): Access denied for user 'root'@'localhost'`
**原因**：输入的密码不正确
**解决方案**：
```bash
# 确认你的 MySQL 密码，然后运行
mysql -u root -p < graphrag_admin_complete.sql

# 输入正确的密码（默认为 root）
```

---

### 问题 3：文件路径错误
**症状**：`No such file or directory`
**原因**：SQL 文件路径不正确
**解决方案**：
```bash
# 确保在正确的目录
cd e:\graphRAG\output\database

# 或使用完整路径
mysql -u root -p < "e:\graphRAG\output\database\graphrag_admin_complete.sql"

# 或使用正斜杠（Windows 也支持）
mysql -u root -p < "e:/graphRAG/output/database/graphrag_admin_complete.sql"
```

---

### 问题 4：脚本执行中断
**症状**：脚本执行到一半停止
**原因**：可能是权限问题或语法错误
**解决方案**：
```bash
# 查看错误信息，重新运行脚本
mysql -u root -p < graphrag_admin_complete.sql 2>&1 | tee output.log

# 检查 output.log 文件查看详细错误
```

---

### 问题 5：Windows PowerShell 重定向问题
**症状**：PowerShell 中 `<` 重定向不工作
**原因**：PowerShell 的重定向语法不同
**解决方案**：
```powershell
# 方式 1：使用 cmd.exe
cmd /c "mysql -u root -p < graphrag_admin_complete.sql"

# 方式 2：使用 Get-Content
Get-Content graphrag_admin_complete.sql | mysql -u root -p

# 方式 3：使用 PowerShell 的重定向
mysql -u root -p @'
$(Get-Content graphrag_admin_complete.sql)
'@
```

---

### 问题 6：验证数据库是否创建成功
**症状**：不确定脚本是否执行成功
**解决方案**：
```bash
# 连接到 MySQL
mysql -u root -p

# 在 MySQL 命令行中执行以下命令
SHOW DATABASES;                    # 查看所有数据库
USE graphrag_admin;                # 切换到 graphrag_admin 数据库
SHOW TABLES;                       # 查看所有表
SELECT COUNT(*) FROM users;        # 查看 users 表的记录数
SELECT * FROM users;               # 查看用户数据
```

---

## �📞 支持和反馈

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新**：2025-11-22
**版本**：1.0.0
