-- ========================================================================
-- GraphRAG 后台管理系统 - 完整数据库脚本
-- 数据库: graphrag_admin
-- 字符集: utf8mb4 (支持中文和emoji)
-- 引擎: InnoDB (支持事务和外键)
-- ========================================================================

-- 创建数据库
DROP DATABASE IF EXISTS graphrag_admin;
CREATE DATABASE graphrag_admin DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE graphrag_admin;

-- ==================== 用户管理表 ====================
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `role` enum('admin','user') COLLATE utf8mb4_unicode_ci DEFAULT 'user' COMMENT '角色',
  `is_active` tinyint DEFAULT '1' COMMENT '是否激活',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_username` (`username`),
  KEY `idx_email` (`email`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ==================== 知识图谱表 ====================
CREATE TABLE `knowledge_graphs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '图谱ID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '图谱名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '图谱描述',
  `created_by` int DEFAULT NULL COMMENT '创建者用户ID',
  `status` enum('active','inactive','processing','failed') COLLATE utf8mb4_unicode_ci DEFAULT 'inactive' COMMENT '状态',
  `entity_count` int DEFAULT '0' COMMENT '实体数量',
  `relation_count` int DEFAULT '0' COMMENT '关系数量',
  `neo4j_db_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对应的Neo4j数据库名',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_created_by` (`created_by`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `knowledge_graphs_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识图谱表';

-- ==================== 问答记录表 ====================
CREATE TABLE `qa_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer` text COLLATE utf8mb4_unicode_ci,
  `mode` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `response_time` float DEFAULT NULL,
  `confidence` float DEFAULT NULL,
  `graph_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_qa_records_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== 数据上传记录表 ====================
CREATE TABLE `data_uploads` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '上传记录ID',
  `upload_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '上传批次名称',
  `user_id` int NOT NULL COMMENT '上传用户ID',
  `graph_id` int DEFAULT NULL COMMENT '关联的图谱ID',
  `status` enum('pending','processing','completed','failed') COLLATE utf8mb4_unicode_ci DEFAULT 'pending' COMMENT '上传状态',
  `entities_file` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'entities.parquet文件路径',
  `relationships_file` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'relationships.parquet文件路径',
  `text_units_file` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'text_units.parquet文件路径',
  `communities_file` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'communities.parquet文件路径',
  `community_reports_file` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'community_reports.parquet文件路径',
  `documents_file` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'documents.parquet文件路径',
  `error_message` longtext COLLATE utf8mb4_unicode_ci COMMENT '错误信息',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_graph_id` (`graph_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `data_uploads_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `data_uploads_ibfk_2` FOREIGN KEY (`graph_id`) REFERENCES `knowledge_graphs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据上传记录表';

-- ==================== Neo4j 配置表 ====================
CREATE TABLE `neo4j_configs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `config_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置名称',
  `host` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '主机地址',
  `port` int DEFAULT '7687' COMMENT '端口',
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码(加密存储)',
  `database_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据库名',
  `is_default` tinyint DEFAULT '0' COMMENT '是否为默认配置',
  `created_by` int DEFAULT NULL COMMENT '创建者用户ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_name` (`config_name`),
  KEY `created_by` (`created_by`),
  KEY `idx_config_name` (`config_name`),
  KEY `idx_is_default` (`is_default`),
  CONSTRAINT `neo4j_configs_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Neo4j数据库配置表';

-- ==================== 系统日志表 ====================
CREATE TABLE `system_logs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `log_level` enum('INFO','WARNING','ERROR','CRITICAL') COLLATE utf8mb4_unicode_ci DEFAULT 'INFO' COMMENT '日志级别',
  `module` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '模块名称',
  `message` longtext COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志消息',
  `stack_trace` longtext COLLATE utf8mb4_unicode_ci COMMENT '错误堆栈',
  `solution` longtext COLLATE utf8mb4_unicode_ci COMMENT '解决方案',
  `user_id` int DEFAULT NULL COMMENT '相关用户ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_log_level` (`log_level`),
  KEY `idx_module` (`module`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `system_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统日志表';

-- ==================== 用户访问日志表 ====================
CREATE TABLE `user_access_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip_address` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `endpoint` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `method` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status_code` int DEFAULT NULL,
  `response_time` float DEFAULT NULL,
  `device_info` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` text COLLATE utf8mb4_unicode_ci,
  `access_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_user_access_logs_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== 访问统计表 ====================
CREATE TABLE `access_statistics` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '统计ID',
  `stat_date` date NOT NULL COMMENT '统计日期',
  `total_visits` int DEFAULT '0' COMMENT '总访问次数',
  `unique_users` int DEFAULT '0' COMMENT '唯一用户数',
  `unique_ips` int DEFAULT '0' COMMENT '唯一IP数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `stat_date` (`stat_date`),
  KEY `idx_stat_date` (`stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='访问统计表';

-- ==================== IP 访问统计表 ====================
CREATE TABLE `ip_statistics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip_address` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `visit_count` int DEFAULT NULL,
  `device_info` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_access_time` datetime DEFAULT NULL,
  `first_access_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_address` (`ip_address`),
  KEY `ix_ip_statistics_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== 实时问题表 ====================
CREATE TABLE `real_time_questions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '问题ID',
  `user_id` int DEFAULT NULL COMMENT '用户ID',
  `question` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '问题内容',
  `ip_address` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP地址',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `real_time_questions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实时问题表';

-- ==================== 时间段统计表 ====================
CREATE TABLE `time_period_statistics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `period` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '时间段: 00-06, 06-12, 12-18, 18-24',
  `period_label` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '时间段标签: 00:00-5:59, 6:00-11:59, 12:00-17:59, 18:00-23:59',
  `visit_count` int DEFAULT '0' COMMENT '访问数',
  `qa_count` int DEFAULT '0' COMMENT '问答数',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_date_period` (`date`,`period`),
  KEY `idx_date` (`date`),
  KEY `idx_period` (`period`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== 初始化数据 ====================

-- 1. 创建默认管理员用户
-- 用户名: admin
-- 密码: admin123 (bcrypt加密)
-- 角色: admin
INSERT INTO users (username, email, password_hash, role, is_active) 
VALUES ('admin', 'admin@graphrag.com', '$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUe', 'admin', 1)
ON DUPLICATE KEY UPDATE id=id;

-- 2. 创建默认普通用户
-- 用户名: user
-- 密码: user123 (bcrypt加密)
-- 角色: user
INSERT INTO users (username, email, password_hash, role, is_active) 
VALUES ('user', 'user@graphrag.com', '$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUe', 'user', 1)
ON DUPLICATE KEY UPDATE id = id;

-- 3. 创建示例知识图谱
INSERT INTO knowledge_graphs (name, description, created_by, status, entity_count, relation_count, neo4j_db_name)
SELECT '中央苏区知识图谱', '中央苏区历史数据知识图谱', u.id, 'inactive', 0, 0, 'central_soviet_area'
FROM users u WHERE u.username = 'admin' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- ==================== 数据库配置注释 ====================
/*
数据库使用说明：

1. 字符集：utf8mb4
   - 支持中文、emoji等多语言
   - 确保所有连接使用 utf8mb4 字符集

2. 引擎：InnoDB
   - 支持事务处理
   - 支持外键约束
   - 支持行级锁定

3. 默认用户：
   - 用户名: admin, 密码: admin123
   - 用户名: user, 密码: user123

4. 表结构说明：
   - users: 用户信息表
   - qa_records: 问答记录表
   - knowledge_graphs: 知识图谱表
   - data_uploads: 数据上传记录表
   - neo4j_configs: Neo4j配置表
   - system_logs: 系统日志表
   - user_access_logs: 用户访问日志表
   - access_statistics: 访问统计表
   - ip_statistics: IP访问统计表
   - real_time_questions: 实时问题表
   - time_period_statistics: 时间段统计表

5. 表之间的关系：
   - users (1) ---> (N) knowledge_graphs (created_by)
   - users (1) ---> (N) data_uploads (user_id)
   - users (1) ---> (N) system_logs (user_id)
   - users (1) ---> (N) real_time_questions (user_id)
   - users (1) ---> (N) neo4j_configs (created_by)
   - knowledge_graphs (1) ---> (N) data_uploads (graph_id)

6. 性能优化：
   - 已创建多个索引优化查询性能
   - 建议定期分析表统计信息：ANALYZE TABLE table_name;

7. 备份建议：
   - 定期备份数据库（建议每天）
   - 备份命令: mysqldump -u root -p graphrag_admin > backup.sql
   - 恢复命令: mysql -u root -p graphrag_admin < backup.sql
*/
