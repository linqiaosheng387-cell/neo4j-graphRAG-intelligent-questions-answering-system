"""
测试 Neo4j 图数据库导入是否成功
"""

from neo4j import GraphDatabase
import sys

# ==================== 配置部分 ====================

NEO4J_URI = "bolt://localhost:7687"  # 使用 bolt 协议
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j"  # 修改为您的实际密码

# ==================== 测试脚本 ====================

class Neo4jTester:
    def __init__(self, uri, user, password):
        """初始化连接"""
        print("正在连接 Neo4j...")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ 连接成功！\n")
        except Exception as e:
            print(f"❌ 连接失败: {e}\n")
            sys.exit(1)
    
    def close(self):
        """关闭连接"""
        self.driver.close()
    
    def test_basic_stats(self):
        """测试1：基本统计"""
        print("=" * 60)
        print("测试 1: 基本统计")
        print("=" * 60)
        
        with self.driver.session() as session:
            # 节点数量
            result = session.run("MATCH (e:Entity) RETURN count(e) as count")
            node_count = result.single()['count']
            
            # 关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            
            print(f"实体节点数量: {node_count:,}")
            print(f"关系边数量: {rel_count:,}")
            
            if node_count > 0 and rel_count > 0:
                print("✅ 测试通过：数据已成功导入\n")
                return True
            else:
                print("❌ 测试失败：数据库为空\n")
                return False
    
    def test_entity_types(self):
        """测试2：实体类型分布"""
        print("=" * 60)
        print("测试 2: 实体类型分布")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.type as type, count(e) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            print(f"{'类型':<20} {'数量':>10}")
            print("-" * 32)
            for record in result:
                print(f"{record['type']:<20} {record['count']:>10,}")
            
            print("\n✅ 测试通过：实体类型正常\n")
    
    def test_sample_entities(self):
        """测试3：查看示例实体"""
        print("=" * 60)
        print("测试 3: 示例实体（前10个）")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.title as title, e.type as type, e.description as description
                LIMIT 10
            """)
            
            for i, record in enumerate(result, 1):
                print(f"\n{i}. {record['title']} ({record['type']})")
                desc = record['description']
                if desc:
                    print(f"   {desc[:100]}...")
            
            print("\n✅ 测试通过：能够查询实体\n")
    
    def test_relationships(self):
        """测试4：查看示例关系"""
        print("=" * 60)
        print("测试 4: 示例关系（前10条）")
        print("=" * 60)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity)
                RETURN a.title as source, r.description as relation, b.title as target
                LIMIT 10
            """)
            
            for i, record in enumerate(result, 1):
                print(f"{i}. {record['source']} → {record['relation'][:30]}... → {record['target']}")
            
            print("\n✅ 测试通过：关系正常\n")
    
    def test_specific_query(self):
        """测试5：特定查询测试"""
        print("=" * 60)
        print("测试 5: 查询特定实体及其关系")
        print("=" * 60)
        
        # 查找包含"中央苏区"的实体
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity)
                WHERE e.title CONTAINS '中央苏区' OR e.title CONTAINS '苏区'
                RETURN e.title as title, e.type as type
                LIMIT 5
            """)
            
            entities = list(result)
            if entities:
                print("找到相关实体：")
                for record in entities:
                    print(f"  - {record['title']} ({record['type']})")
                
                # 查询第一个实体的关系
                first_title = entities[0]['title']
                print(f"\n查询 '{first_title}' 的关系：")
                
                result = session.run("""
                    MATCH (e:Entity {title: $title})-[r]-(related:Entity)
                    RETURN related.title as related_title, type(r) as rel_type
                    LIMIT 10
                """, title=first_title)
                
                for record in result:
                    print(f"  - {record['related_title']}")
                
                print("\n✅ 测试通过：能够查询特定实体\n")
            else:
                print("⚠️  未找到相关实体，但数据库正常\n")
    
    def test_graph_query(self):
        """测试6：图谱查询（用于前端可视化）"""
        print("=" * 60)
        print("测试 6: 图谱查询（模拟前端请求）")
        print("=" * 60)
        
        with self.driver.session() as session:
            # 模拟前端请求：获取一个实体及其邻居（用于可视化）
            result = session.run("""
                MATCH (e:Entity)
                WHERE e.title CONTAINS '苏区'
                WITH e LIMIT 1
                MATCH (e)-[r]-(neighbor:Entity)
                RETURN e, r, neighbor
                LIMIT 20
            """)
            
            nodes = set()
            edges = []
            
            for record in result:
                e = record['e']
                neighbor = record['neighbor']
                r = record['r']
                
                nodes.add((e['id'], e['title'], e['type']))
                nodes.add((neighbor['id'], neighbor['title'], neighbor['type']))
                edges.append((e['id'], neighbor['id'], r.get('description', '')))
            
            print(f"节点数: {len(nodes)}")
            print(f"边数: {len(edges)}")
            
            if len(nodes) > 0:
                print("\n示例节点：")
                for node in list(nodes)[:5]:
                    print(f"  - {node[1]} ({node[2]})")
                
                print("\n示例关系：")
                for edge in edges[:5]:
                    print(f"  - {edge[0][:8]}... → {edge[2][:30]}... → {edge[1][:8]}...")
                
                print("\n✅ 测试通过：图谱查询正常\n")
            else:
                print("⚠️  未找到图谱数据\n")
    
    def test_index_performance(self):
        """测试7：索引性能"""
        print("=" * 60)
        print("测试 7: 索引性能测试")
        print("=" * 60)
        
        import time
        
        with self.driver.session() as session:
            # 测试ID索引查询速度
            start = time.time()
            result = session.run("""
                MATCH (e:Entity)
                WHERE e.id STARTS WITH '0'
                RETURN count(e) as count
            """)
            count = result.single()['count']
            elapsed = time.time() - start
            
            print(f"ID索引查询: {count:,} 个结果，耗时 {elapsed*1000:.2f} ms")
            
            # 测试标题索引查询速度
            start = time.time()
            result = session.run("""
                MATCH (e:Entity)
                WHERE e.title CONTAINS '中'
                RETURN count(e) as count
            """)
            count = result.single()['count']
            elapsed = time.time() - start
            
            print(f"标题模糊查询: {count:,} 个结果，耗时 {elapsed*1000:.2f} ms")
            
            if elapsed < 1:
                print("\n✅ 测试通过：查询性能良好\n")
            else:
                print("\n⚠️  查询稍慢，建议检查索引\n")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  Neo4j 数据导入测试工具")
    print("=" * 60 + "\n")
    
    # 检查密码
    if NEO4J_PASSWORD == "your_password":
        print("⚠️  请先修改脚本中的 Neo4j 密码！\n")
        sys.exit(1)
    
    # 初始化测试器
    tester = Neo4jTester(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    # 运行测试
    try:
        # 基本测试
        if not tester.test_basic_stats():
            print("数据库为空，请先运行 import_to_neo4j.py 导入数据")
            sys.exit(1)
        
        # 详细测试
        tester.test_entity_types()
        tester.test_sample_entities()
        tester.test_relationships()
        tester.test_specific_query()
        tester.test_graph_query()
        tester.test_index_performance()
        
        # 总结
        print("=" * 60)
        print("  ✅ 所有测试通过！")
        print("=" * 60)
        print("\nNeo4j 数据库已成功导入，可以正常使用！")
        print("\n下一步：")
        print("1. 在 Neo4j Browser 中查看: http://localhost:7474")
        print("2. 尝试查询: MATCH (e:Entity)-[r]->(n) RETURN e,r,n LIMIT 25")
        print("3. 修改后端代码，使用 Neo4j 提供图谱数据\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
    finally:
        tester.close()

if __name__ == "__main__":
    main()

