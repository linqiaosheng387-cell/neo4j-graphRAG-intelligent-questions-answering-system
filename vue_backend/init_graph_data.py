"""
初始化图谱数据 - 从问答系统同步到后台管理系统数据库
"""
import os
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import SessionLocal
from models import KnowledgeGraph

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

QA_SYSTEM_URL = os.getenv('QA_SYSTEM_URL', 'http://localhost:8084')

def init_graph_data():
    """初始化图谱数据"""
    db = SessionLocal()
    try:
        print("\n" + "=" * 80)
        print("📊 初始化图谱数据")
        print("=" * 80)
        
        # 检查是否已有图谱
        existing_graphs = db.query(KnowledgeGraph).all()
        print(f"📋 数据库中已有 {len(existing_graphs)} 个图谱")
        
        if existing_graphs:
            print("\n📊 现有图谱信息:")
            for graph in existing_graphs:
                print(f"   - {graph.name}")
                print(f"     实体数: {graph.entity_count}")
                print(f"     关系数: {graph.relation_count}")
            
            # 检查是否需要更新数据
            if existing_graphs[0].entity_count == 0 and existing_graphs[0].relation_count == 0:
                print("\n⚠️  图谱数据为空，正在更新...")
            else:
                print("\n✅ 图谱数据已存在，跳过初始化")
                print("=" * 80 + "\n")
                return
        
        # 从问答系统获取统计数据
        print(f"\n🔄 从问答系统获取统计数据: {QA_SYSTEM_URL}/api/stats")
        try:
            response = requests.get(
                f"{QA_SYSTEM_URL}/api/stats",
                timeout=10
            )
            response.raise_for_status()
            stats = response.json()
            
            # 注意：问答系统返回的是 entities_count 和 relationships_count
            entity_count = stats.get('entities_count', 0)
            relation_count = stats.get('relationships_count', 0)
            
            print(f"✅ 获取成功")
            print(f"   - 实体数: {entity_count}")
            print(f"   - 关系数: {relation_count}")
            
        except Exception as e:
            print(f"❌ 获取失败: {e}")
            print("   将创建空图谱")
            entity_count = 0
            relation_count = 0
        
        # 如果已有图谱但数据为空，则更新
        if existing_graphs and existing_graphs[0].entity_count == 0:
            print(f"\n📝 更新现有图谱...")
            graph = existing_graphs[0]
            graph.entity_count = entity_count
            graph.relation_count = relation_count
            db.commit()
            db.refresh(graph)
            
            print(f"✅ 图谱更新成功")
            print(f"   - ID: {graph.id}")
            print(f"   - 名称: {graph.name}")
            print(f"   - 实体数: {graph.entity_count}")
            print(f"   - 关系数: {graph.relation_count}")
        else:
            # 创建默认图谱
            print(f"\n📝 创建默认图谱...")
            default_graph = KnowledgeGraph(
                name="中央苏区史知识图谱",
                description="从问答系统同步的知识图谱",
                status="active",
                entity_count=entity_count,
                relation_count=relation_count,
                neo4j_db_name="default"
            )
            db.add(default_graph)
            db.commit()
            db.refresh(default_graph)
            
            print(f"✅ 图谱创建成功")
            print(f"   - ID: {default_graph.id}")
            print(f"   - 名称: {default_graph.name}")
            print(f"   - 实体数: {default_graph.entity_count}")
            print(f"   - 关系数: {default_graph.relation_count}")
        
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        print(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_graph_data()
