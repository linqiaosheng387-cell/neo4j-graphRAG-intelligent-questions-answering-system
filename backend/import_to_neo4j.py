"""
将 GraphRAG 数据导入 Neo4j 图数据库
保留原有的 GraphRAG 检索逻辑，Neo4j 仅用于图谱存储和可视化
"""

import pandas as pd
from neo4j import GraphDatabase
import sys
from tqdm import tqdm

# ==================== 配置部分 ====================

# Neo4j 连接配置
NEO4J_URI = "neo4j://localhost:7687"  # Neo4j 地址
NEO4J_USER = "neo4j"                 # 用户名
NEO4J_PASSWORD = "12345678"     # 密码（请修改为您的实际密码）

# 数据文件路径
DATA_PATH = ".."  # 上级目录（output文件夹）

# 批量导入大小（如果导入失败，可以尝试减小这个值）
BATCH_SIZE = 500  # 从 1000 改为 500，更稳定

# ==================== 导入脚本 ====================

class Neo4jImporter:
    def __init__(self, uri, user, password):
        """初始化 Neo4j 连接"""
        print(f"正在连接 Neo4j: {uri}")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Neo4j 连接成功！")
        except Exception as e:
            print(f"❌ Neo4j 连接失败: {e}")
            print("\n请检查：")
            print("1. Neo4j 是否已启动")
            print("2. 地址、用户名、密码是否正确")
            print("3. 端口 7687 是否开放")
            sys.exit(1)
    
    def close(self):
        """关闭连接"""
        self.driver.close()
    
    def _safe_convert_to_string(self, value):
        """安全地将值转换为字符串，处理数组/列表"""
        try:
            if value is None:
                return '[]'
            # 检查是否是数组/列表类型
            if isinstance(value, (list, tuple)):
                return str(list(value))
            # 检查是否是 numpy 数组
            if hasattr(value, '__iter__') and not isinstance(value, str):
                return str(list(value))
            # 检查是否是 pandas Series
            if isinstance(value, pd.Series):
                return str(value.tolist())
            # 普通值直接转换
            return str(value)
        except Exception as e:
            print(f"[警告] 转换值时出错: {e}")
            return '[]'
    
    def clear_database(self):
        """清空数据库（可选）"""
        print("\n⚠️  清空现有数据...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ 数据库已清空")
    
    def create_indexes(self):
        """创建索引以提高查询性能"""
        print("\n📊 创建索引...")
        with self.driver.session() as session:
            # 实体索引
            session.run("CREATE INDEX entity_title IF NOT EXISTS FOR (e:Entity) ON (e.title)")
            session.run("CREATE INDEX entity_id IF NOT EXISTS FOR (e:Entity) ON (e.id)")
            session.run("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)")
            
            # 文本单元索引
            session.run("CREATE INDEX textunit_id IF NOT EXISTS FOR (t:TextUnit) ON (t.id)")
            
            # 社区索引
            session.run("CREATE INDEX community_id IF NOT EXISTS FOR (c:Community) ON (c.id)")
            session.run("CREATE INDEX community_level IF NOT EXISTS FOR (c:Community) ON (c.level)")
            
            # 社区报告索引
            session.run("CREATE INDEX report_id IF NOT EXISTS FOR (r:Report) ON (r.id)")
            
            # 文档索引
            session.run("CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.id)")
        print("✅ 索引创建完成")
    
    def import_entities(self, entities_df):
        """导入实体节点"""
        print(f"\n📥 导入实体节点（共 {len(entities_df)} 个）...")
        
        # 准备数据
        entities_data = []
        for idx, row in entities_df.iterrows():
            entities_data.append({
                'id': row['id'],
                'title': row['title'],
                'type': row['type'] if pd.notna(row['type']) else 'UNKNOWN',
                'description': row['description'] if pd.notna(row['description']) else '',
                'degree': int(row['degree']) if pd.notna(row['degree']) else 0
            })
        
        # 批量导入
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
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(entities_data), BATCH_SIZE), desc="导入实体"):
                batch = entities_data[i:i+BATCH_SIZE]
                session.run(query, batch=batch)
        
        print(f"✅ 成功导入 {len(entities_df)} 个实体节点")

    def import_relationships(self, relationships_df):
        """导入关系边"""
        print(f"\n📥 导入关系边（共 {len(relationships_df)} 条）...")
        
        print("⚠️  检测到关系使用实体名称（title）而非ID")
        print("   将通过实体名称进行匹配...")
        
        # 准备数据
        relationships_data = []
        for idx, row in relationships_df.iterrows():
            relationships_data.append({
                'id': row['id'],
                'source': row['source'],  # 这是实体的 title
                'target': row['target'],  # 这也是实体的 title
                'description': row['description'] if pd.notna(row['description']) else '',
                'weight': float(row['weight']) if pd.notna(row['weight']) else 1.0
            })
        
        # 批量导入 - 通过 title 匹配实体（而不是 id）
        query = """
        UNWIND $batch AS rel
        MATCH (source:Entity {title: rel.source})
        MATCH (target:Entity {title: rel.target})
        CREATE (source)-[r:RELATED_TO {
            id: rel.id,
            description: rel.description,
            weight: rel.weight
        }]->(target)
        RETURN count(r) as created
        """
        
        total_created = 0
        failed_batches = 0
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(relationships_data), BATCH_SIZE), desc="导入关系"):
                batch = relationships_data[i:i+BATCH_SIZE]
                try:
                    result = session.run(query, batch=batch)
                    record = result.single()
                    if record:
                        total_created += record['created']
                except Exception as e:
                    failed_batches += 1
                    print(f"\n⚠️  批次 {i//BATCH_SIZE + 1} 导入失败: {e}")
                    
                    # 尝试单条导入看具体问题
                    if i == 0:  # 只在第一个批次失败时详细检查
                        print("\n🔍 检查前5条关系的实体是否存在...")
                        for j, rel in enumerate(batch[:5]):
                            source_exists = session.run(
                                "MATCH (e:Entity {title: $title}) RETURN count(e) as count", 
                                title=rel['source']
                            ).single()['count']
                            target_exists = session.run(
                                "MATCH (e:Entity {title: $title}) RETURN count(e) as count", 
                                title=rel['target']
                            ).single()['count']
                            
                            print(f"  关系 {j+1}: source={rel['source'][:20]} (存在:{source_exists}) → "
                                  f"target={rel['target'][:20]} (存在:{target_exists})")
                    continue
        
        print(f"\n✅ 实际成功导入 {total_created} 条关系边")
        if failed_batches > 0:
            print(f"⚠️  {failed_batches} 个批次失败")
        if total_created == 0:
            print("\n❌ 没有关系被导入！可能的原因：")
            print("   1. 实体ID格式不匹配")
            print("   2. 关系中的 source/target 找不到对应的实体")
            print("   3. 建议运行诊断脚本检查")
    
    def import_text_units(self, text_units_df):
        """导入文本单元节点"""
        print(f"\n📥 导入文本单元节点（共 {len(text_units_df)} 个）...")
        
        # 准备数据
        text_units_data = []
        for idx, row in text_units_df.iterrows():
            text_units_data.append({
                'id': row['id'],
                'text': str(row['text'])[:5000] if pd.notna(row['text']) else '',  # 限制长度
                'document_ids': self._safe_convert_to_string(row['document_ids'])
            })
        
        # 批量导入
        query = """
        UNWIND $batch AS text_unit
        CREATE (t:TextUnit {
            id: text_unit.id,
            text: text_unit.text,
            document_ids: text_unit.document_ids
        })
        """
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(text_units_data), BATCH_SIZE), desc="导入文本单元"):
                batch = text_units_data[i:i+BATCH_SIZE]
                session.run(query, batch=batch)
        
        print(f"✅ 成功导入 {len(text_units_df)} 个文本单元节点")
    
    def import_communities(self, communities_df):
        """导入社区节点"""
        print(f"\n📥 导入社区节点（共 {len(communities_df)} 个）...")
        
        # 准备数据
        communities_data = []
        for idx, row in communities_df.iterrows():
            communities_data.append({
                'id': row['id'],
                'level': int(row['level']) if pd.notna(row['level']) else 0,
                'title': str(row['title']) if pd.notna(row['title']) else '',
                'entity_ids': self._safe_convert_to_string(row['entity_ids'])
            })
        
        # 批量导入
        query = """
        UNWIND $batch AS community
        CREATE (c:Community {
            id: community.id,
            level: community.level,
            title: community.title,
            entity_ids: community.entity_ids
        })
        """
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(communities_data), BATCH_SIZE), desc="导入社区"):
                batch = communities_data[i:i+BATCH_SIZE]
                session.run(query, batch=batch)
        
        print(f"✅ 成功导入 {len(communities_df)} 个社区节点")
    
    def import_community_reports(self, community_reports_df):
        """导入社区报告节点"""
        print(f"\n📥 导入社区报告节点（共 {len(community_reports_df)} 个）...")
        
        # 检查可用的字段
        print(f"[DEBUG] 社区报告表的列名: {community_reports_df.columns.tolist()}")
        
        # 准备数据
        reports_data = []
        for idx, row in community_reports_df.iterrows():
            # 安全地获取字段值
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
                'summary': summary,  # 限制长度
                'full_content': full_content  # 限制长度
            })
        
        # 批量导入
        query = """
        UNWIND $batch AS report
        CREATE (r:Report {
            id: report.id,
            title: report.title,
            summary: report.summary,
            full_content: report.full_content
        })
        """
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(reports_data), BATCH_SIZE), desc="导入社区报告"):
                batch = reports_data[i:i+BATCH_SIZE]
                session.run(query, batch=batch)
        
        print(f"✅ 成功导入 {len(community_reports_df)} 个社区报告节点")
    
    def import_documents(self, documents_df):
        """导入文档节点"""
        print(f"\n📥 导入文档节点（共 {len(documents_df)} 个）...")
        
        # 检查可用的字段
        print(f"[DEBUG] 文档表的列名: {documents_df.columns.tolist()}")
        
        # 确定内容字段名（可能是 raw_content 或其他名称）
        content_field = None
        for field in ['raw_content', 'content', 'text', 'body']:
            if field in documents_df.columns:
                content_field = field
                print(f"[DEBUG] 使用内容字段: {content_field}")
                break
        
        if content_field is None:
            print(f"[警告] 未找到内容字段，将使用空内容")
        
        # 准备数据
        documents_data = []
        for idx, row in documents_df.iterrows():
            content = ''
            if content_field and content_field in row:
                content = str(row[content_field])[:5000] if pd.notna(row[content_field]) else ''
            
            documents_data.append({
                'id': row['id'],
                'title': str(row['title']) if pd.notna(row['title']) else '',
                'raw_content': content  # 限制长度
            })
        
        # 批量导入
        query = """
        UNWIND $batch AS document
        CREATE (d:Document {
            id: document.id,
            title: document.title,
            raw_content: document.raw_content
        })
        """
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(documents_data), BATCH_SIZE), desc="导入文档"):
                batch = documents_data[i:i+BATCH_SIZE]
                session.run(query, batch=batch)
        
        print(f"✅ 成功导入 {len(documents_df)} 个文档节点")
    
    def create_relationships(self):
        """创建节点间的关系"""
        print("\n🔗 创建节点间的关系...")
        
        with self.driver.session() as session:
            # 1. 文本单元 -> 文档 的关系
            print("   创建 TextUnit -> Document 关系...")
            session.run("""
                MATCH (t:TextUnit), (d:Document)
                WHERE t.document_ids CONTAINS d.id
                CREATE (t)-[:BELONGS_TO]->(d)
            """)
            
            # 2. 社区 -> 实体 的关系
            print("   创建 Community -> Entity 关系...")
            session.run("""
                MATCH (c:Community), (e:Entity)
                WHERE c.entity_ids CONTAINS e.id
                CREATE (c)-[:CONTAINS]->(e)
            """)
            
            # 3. 社区 -> 报告 的关系
            print("   创建 Community -> Report 关系...")
            session.run("""
                MATCH (c:Community), (r:Report)
                WHERE c.id = r.id
                CREATE (c)-[:HAS_REPORT]->(r)
            """)
        
        print("✅ 关系创建完成")
    
    def get_statistics(self):
        """获取导入统计"""
        print("\n📊 数据库统计信息：")
        with self.driver.session() as session:
            # 各类型节点数量
            result = session.run("MATCH (e:Entity) RETURN count(e) as count")
            entity_count = result.single()['count']
            print(f"   - 实体节点: {entity_count:,}")
            
            result = session.run("MATCH (t:TextUnit) RETURN count(t) as count")
            textunit_count = result.single()['count']
            print(f"   - 文本单元: {textunit_count:,}")
            
            result = session.run("MATCH (c:Community) RETURN count(c) as count")
            community_count = result.single()['count']
            print(f"   - 社区: {community_count:,}")
            
            result = session.run("MATCH (r:Report) RETURN count(r) as count")
            report_count = result.single()['count']
            print(f"   - 社区报告: {report_count:,}")
            
            result = session.run("MATCH (d:Document) RETURN count(d) as count")
            document_count = result.single()['count']
            print(f"   - 文档: {document_count:,}")
            
            # 关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            print(f"   - 关系边: {rel_count:,}")
            
            # 实体类型分布
            result = session.run("""
                MATCH (e:Entity) 
                RETURN e.type as type, count(e) as count 
                ORDER BY count DESC 
                LIMIT 10
            """)
            print("\n   实体类型 TOP 10:")
            for record in result:
                print(f"      {record['type']}: {record['count']:,}")

def main():
    """主函数"""
    print("=" * 80)
    print("  GraphRAG 数据导入 Neo4j 工具（完整版 - 导入所有6个Parquet文件）")
    print("=" * 80)
    
    # 提示用户确认密码
    print(f"\n当前配置：")
    print(f"  - URI: {NEO4J_URI}")
    print(f"  - 用户名: {NEO4J_USER}")
    print(f"  - 密码: {'*' * len(NEO4J_PASSWORD)}")
    
    if NEO4J_PASSWORD == "your_password":
        print("\n⚠️  请先在脚本中修改 Neo4j 密码！")
        sys.exit(1)
    
    # 1. 加载所有数据
    print("\n📂 加载 GraphRAG 数据（6个文件）...")
    try:
        entities_df = pd.read_parquet(f"{DATA_PATH}/entities.parquet")
        relationships_df = pd.read_parquet(f"{DATA_PATH}/relationships.parquet")
        text_units_df = pd.read_parquet(f"{DATA_PATH}/text_units.parquet")
        communities_df = pd.read_parquet(f"{DATA_PATH}/communities.parquet")
        community_reports_df = pd.read_parquet(f"{DATA_PATH}/community_reports.parquet")
        documents_df = pd.read_parquet(f"{DATA_PATH}/documents.parquet")
        
        print(f"✅ 数据加载成功")
        print(f"   - 实体: {len(entities_df):,}")
        print(f"   - 关系: {len(relationships_df):,}")
        print(f"   - 文本单元: {len(text_units_df):,}")
        print(f"   - 社区: {len(communities_df):,}")
        print(f"   - 社区报告: {len(community_reports_df):,}")
        print(f"   - 文档: {len(documents_df):,}")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        sys.exit(1)
    
    # 2. 连接 Neo4j
    importer = Neo4jImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    # 3. 询问是否清空现有数据
    response = input("\n是否清空现有数据？(yes/no，默认no): ").lower()
    if response in ['yes', 'y']:
        importer.clear_database()
    
    # 4. 创建索引
    importer.create_indexes()
    
    # 5. 导入所有节点
    importer.import_entities(entities_df)
    importer.import_text_units(text_units_df)
    importer.import_communities(communities_df)
    importer.import_community_reports(community_reports_df)
    importer.import_documents(documents_df)
    
    # 6. 导入关系
    importer.import_relationships(relationships_df)
    
    # 7. 创建节点间的关系
    importer.create_relationships()
    
    # 8. 统计信息
    importer.get_statistics()
    
    # 9. 关闭连接
    importer.close()
    
    print("\n" + "=" * 80)
    print("  ✅ 导入完成！")
    print("=" * 80)
    print("\n📊 导入的数据结构：")
    print("  ├─ Entity (实体节点)")
    print("  ├─ TextUnit (文本单元)")
    print("  ├─ Community (社区)")
    print("  ├─ Report (社区报告)")
    print("  ├─ Document (文档)")
    print("  └─ 关系:")
    print("     ├─ Entity -[RELATED_TO]-> Entity")
    print("     ├─ TextUnit -[BELONGS_TO]-> Document")
    print("     ├─ Community -[CONTAINS]-> Entity")
    print("     └─ Community -[HAS_REPORT]-> Report")
    print("\n下一步：")
    print("1. 打开 Neo4j Browser: http://localhost:7474")
    print("2. 尝试查询:")
    print("   - MATCH (e:Entity) RETURN e LIMIT 25")
    print("   - MATCH (c:Community)-[r:CONTAINS]->(e:Entity) RETURN c, r, e LIMIT 10")
    print("   - MATCH (t:TextUnit)-[r:BELONGS_TO]->(d:Document) RETURN t, r, d LIMIT 10")
    print()

if __name__ == "__main__":
    main()

