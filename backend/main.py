"""
中央苏区史 GraphRAG 问答系统 - 后端API
GraphRAG 负责检索，Neo4j 负责图谱可视化
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
import json
import asyncio
import pandas as pd
import time
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
print(f"✅ 环境变量已加载")
print(f"   - LLM_PROVIDER: {os.getenv('LLM_PROVIDER', '未设置')}")
print(f"   - DASHSCOPE_API_KEY: {'已设置' if os.getenv('DASHSCOPE_API_KEY') else '未设置'}")

from graphrag_service import GraphRAGService
from db_logger import log_question, log_access, init_db

# 初始化数据库
init_db()

# 创建 FastAPI 应用
app = FastAPI(
    title="中央苏区史问答系统",
    description="基于 GraphRAG + Neo4j 的智能问答API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 访问日志中间件
@app.middleware("http")
async def log_access_middleware(request: Request, call_next):
    """记录所有HTTP访问"""
    start_time = time.time()
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 获取User-Agent
    user_agent = request.headers.get("user-agent", "")
    
    # 调用下一个中间件/路由
    response = await call_next(request)
    
    # 计算响应时间
    process_time = (time.time() - start_time) * 1000  # 转换为毫秒
    
    # 记录访问日志（仅记录API端点）
    if request.url.path.startswith("/api/"):
        try:
            log_access(
                ip_address=client_ip,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time=process_time,
                user_agent=user_agent
            )
        except Exception as e:
            print(f"[中间件] ❌ 记录访问日志失败: {e}")
            import traceback
            print(traceback.format_exc())
    
    return response

# 初始化 GraphRAG 服务
print("正在初始化服务...")
try:
    # 获取 GraphRAG 数据路径（从环境变量或使用默认值）
    data_path = os.getenv("GRAPHRAG_DATA_PATH", "..")
    print(f"   - 数据路径: {os.path.abspath(data_path)}")
    
    graphrag_service = GraphRAGService(
        # data_path=data_path,
        neo4j_uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "12345678")
        # LLM配置现在从 .env 文件自动读取
    )
    print("✅ GraphRAG 服务初始化成功")
except Exception as e:
    print(f"❌ GraphRAG 服务初始化失败: {str(e)}")
    print(f"   请检查数据路径和配置是否正确")
    import traceback
    traceback.print_exc()
    # 创建一个空的服务对象，避免应用崩溃
    graphrag_service = None

# ========== 请求/响应模型 ==========

class QueryRequest(BaseModel):
    question: str
    mode: str = "global"
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    mode: str
    source: Optional[str] = None
    graph_data: Optional[Dict[str, Any]] = None
    confidence: float = 0.0

# ========== API 路由 ==========

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "message": "中央苏区史问答系统API运行中",
        "version": "1.0.0",
        "graphrag_service": "已初始化" if graphrag_service else "未初始化"
    }

@app.get("/api/health")
async def health_check():
    """详细健康检查"""
    return {
        "status": "healthy" if graphrag_service else "degraded",
        "graphrag_service": graphrag_service is not None,
        "endpoints": [
            "GET /",
            "GET /api/health",
            "POST /api/query",
            "POST /api/query/stream",
            "GET /api/graph/{entity_titles}",
            "GET /api/recommend",
            "GET /api/stats"
        ]
    }

@app.post("/api/query/stream")
async def query_stream(request: QueryRequest, req: Request = None):
    """
    流式问答接口 - 使用LLM真正的流式输出
    """
    # 检查服务是否初始化
    if graphrag_service is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"error": "GraphRAG 服务未初始化，请检查服务器日志"}
        )

    # 提前获取客户端IP（在生成器外部访问 req 对象）
    client_ip = req.client.host if (req and req.client) else "unknown"

    async def generate():
        try:
            start_time = time.time()
            print("=" * 80)
            print(f"[API] ========== 收到流式查询请求 ==========")
            print(f"[API] 问题: {request.question}")
            print(f"[API] 模式: {request.mode}")
            print("=" * 80)

            # 记录实时问题
            try:
                from db_logger import log_real_time_question
                log_real_time_question(
                    question=request.question,
                    ip_address=client_ip
                )
            except Exception as e:
                print(f"[API] 记录实时问题失败: {e}")
            
            # 先获取检索结果（不生成答案）
            if request.mode == "global":
                # 执行全局搜索的检索部分
                keywords = graphrag_service._extract_keywords_from_question(request.question)
                scored_reports = []
                
                for idx, report in graphrag_service.community_reports.iterrows():
                    title = graphrag_service._safe_get_value(report.get('title', ''), "")
                    summary = graphrag_service._safe_get_value(report.get('summary', ''), "")
                    full_content = graphrag_service._safe_get_value(report.get('full_content', ''), "")

                    score = 0
                    for kw in keywords:
                        if kw:
                            if kw in title:
                                score += 3
                            if kw in summary:
                                score += 2
                            if kw in full_content:
                                score += 1

                    if score > 0:
                        scored_reports.append({
                            'report': report,
                            'score': score,
                            'confidence': min(score / 10.0, 1.0)
                        })

                if not scored_reports:
                    print("[API] 未找到得分报告，尝试宽松匹配...")
                    for idx, report in graphrag_service.community_reports.iterrows():
                        title = graphrag_service._safe_get_value(report.get('title', ''), "")
                        summary = graphrag_service._safe_get_value(report.get('summary', ''), "")
                        for kw in keywords:
                            if kw and len(kw) > 1:
                                if kw.lower() in title.lower() or kw.lower() in summary.lower():
                                    scored_reports.append({
                                        'report': report,
                                        'score': 0.5,
                                        'confidence': 0.05
                                    })
                                    break

                if not scored_reports:
                    print("[API] 仍未找到相关报告，尝试顶层社区报告...")
                    try:
                        if 'level' in graphrag_service.communities.columns:
                            top_level = graphrag_service.communities[
                                graphrag_service.communities['level'] == 0
                            ]
                        else:
                            top_level = pd.DataFrame()
                    except Exception:
                        top_level = pd.DataFrame()

                    if len(top_level) > 0:
                        for _, community in top_level.iterrows():
                            cid = graphrag_service._safe_get_value(community.get('id', ''), "")
                            if not cid:
                                continue
                            matched = graphrag_service.community_reports[
                                graphrag_service.community_reports['id'] == cid
                            ]
                            if len(matched) > 0:
                                report = matched.iloc[0]
                                scored_reports.append({
                                    'report': report,
                                    'score': 0.1,
                                    'confidence': 0.05
                                })
                                if len(scored_reports) >= 3:
                                    break

                if not scored_reports:
                    print("[API] 使用兜底随机报告...")
                    for _, report in graphrag_service.community_reports.head(5).iterrows():
                        scored_reports.append({
                            'report': report,
                            'score': 0.05,
                            'confidence': 0.02
                        })

                scored_reports.sort(key=lambda x: x['score'], reverse=True)
                top_reports = scored_reports[:5]

                print(f"[API] 最终选取 {len(top_reports)} 个社区报告")

                # 为报告分配编号
                for i, item in enumerate(top_reports, 1):
                    item['report_number'] = i

                # 构建LLM prompt
                context = ""
                for item in top_reports[:5]:
                    report = item['report']
                    title = graphrag_service._safe_get_value(report.get('title', ''), "")
                    summary = graphrag_service._safe_get_value(report.get('summary', ''), "")
                    full_content = graphrag_service._safe_get_value(report.get('full_content', ''), "")
                    context += "\n\n### 报告 {num}: {title}\n".format(num=item['report_number'], title=title or "未命名报告")
                    if summary:
                        context += f"{summary}\n"
                    if full_content:
                        context += f"{full_content[:500]}"

                if not context.strip():
                    print("[API] 构建的社区报告上下文为空，返回兜底提示")
                    fallback_message = (
                        "抱歉，目前未能检索到与该问题直接相关的社区报告。如果您希望基于具体报告回答，"
                        "请补充更多线索或尝试更换提问方式。"
                    )
                    data = {'type': 'text', 'content': fallback_message}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    final_data = {
                        'type': 'done',
                        'graph_data': None,
                        'sources': [],
                        'mode': 'global',
                        'confidence': 0.0
                    }
                    yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                    return

                prompt = f"""问题：{request.question}

社区报告内容：
{context}

请基于以上社区报告内容，用自然、准确、流畅的中文回答问题。如果报告中有直接答案，请明确指出；如果没有直接答案，请根据相关信息进行合理推断。如果确实没有相关信息，请诚实说明。"""
                
                # 使用LLM流式生成答案
                print(f"[API] 开始LLM流式生成...")
                full_answer = ''
                for chunk in graphrag_service._call_llm_api_stream(prompt, max_tokens=2000):
                    full_answer += chunk
                    data = {
                        'type': 'text',
                        'content': chunk
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.01)  # 小延迟，避免过快

                # 获取图谱数据
                all_entity_titles = []
                for item in top_reports[:3]:
                    report = item['report']
                    try:
                        report_id = graphrag_service._safe_get_value(report.get('id', ''), "")
                        community_match = graphrag_service.communities[
                            graphrag_service.communities['id'] == report_id
                        ]
                        if len(community_match) > 0:
                            entity_ids_val = community_match.iloc[0].get('entity_ids', [])
                            try:
                                if isinstance(entity_ids_val, str):
                                    entity_ids = json.loads(entity_ids_val)
                                elif isinstance(entity_ids_val, (list, tuple)):
                                    entity_ids = list(entity_ids_val)
                                else:
                                    entity_ids = []
                                
                                if entity_ids:
                                    entity_ids = entity_ids[:10]
                                    entity_mask = graphrag_service.entities['id'].isin(entity_ids)
                                    community_entities = graphrag_service.entities[entity_mask]
                                    for idx, entity in community_entities.iterrows():
                                        title = graphrag_service._safe_get_value(entity.get('title', ''), "")
                                        if title:
                                            all_entity_titles.append(title)
                            except:
                                pass
                    except:
                        continue
                
                graph_data = graphrag_service.get_graph_data(all_entity_titles[:15]) if top_reports else None
                sources = [graphrag_service._safe_get_value(item['report'].get('title', ''), "") for item in top_reports]

                # 发送完成信号
                final_data = {
                    'type': 'done',
                    'graph_data': graph_data,
                    'sources': sources,
                    'mode': 'global',
                    'confidence': top_reports[0]['confidence'] if top_reports else 0.0
                }
                yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                
                # 记录问答到数据库
                elapsed_time = time.time() - start_time
                log_question(
                    question=request.question,
                    answer=full_answer,
                    mode='global',
                    response_time=elapsed_time * 1000,
                    confidence=top_reports[0]['confidence'] if top_reports else 0.0
                )
            else:
                # 本地搜索 - 使用 LLM 流式生成答案
                print(f"[API] 本地搜索模式")
                
                # 获取本地搜索的检索结果
                result = graphrag_service.query(request.question, request.mode, request.conversation_id)
                
                # 如果检索失败，直接返回
                if not result or not result.get('answer'):
                    error_msg = result.get('answer', '未找到相关信息') if result else '未找到相关信息'
                    data = {'type': 'text', 'content': error_msg}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    
                    final_data = {
                        'type': 'done',
                        'graph_data': result.get('graph_data') if result else None,
                        'sources': [],
                        'mode': 'local',
                        'confidence': result.get('confidence', 0.0) if result else 0.0
                    }
                    yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                else:
                    # 构建 LLM prompt（使用本地搜索的检索结果）
                    context = result.get('answer', '')
                    
                    prompt = f"""问题：{request.question}

检索到的相关信息：
{context}

请基于以上信息，用自然、准确、流畅的中文回答问题。如果信息中有直接答案，请明确指出；如果没有直接答案，请根据相关信息进行合理推断。如果确实没有相关信息，请诚实说明。"""
                    
                    # 使用 LLM 流式生成答案
                    print(f"[API] 开始本地搜索 LLM 流式生成...")
                    full_answer = ''
                    for chunk in graphrag_service._call_llm_api_stream(prompt, max_tokens=2000):
                        full_answer += chunk
                        data = {
                            'type': 'text',
                            'content': chunk
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.01)  # 小延迟，避免过快
                    
                    # 获取图谱数据
                    graph_data = result.get('graph_data')
                    
                    # 发送完成信号
                    final_data = {
                        'type': 'done',
                        'graph_data': graph_data,
                        'sources': result.get('sources', []),
                        'mode': result.get('mode', 'local'),
                        'confidence': result.get('confidence', 0.0)
                    }
                    yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                    
                    # 记录问答到数据库
                    elapsed_time = time.time() - start_time
                    log_question(
                        question=request.question,
                        answer=full_answer,
                        mode=result.get('mode', 'local'),
                        response_time=elapsed_time * 1000,
                        confidence=result.get('confidence', 0.0)
                    )
            
            print("[API] ========== 流式输出完成 ==========")
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] 流式查询错误: {e}")
            print(f"[ERROR] 错误堆栈:\n{error_trace}")
            
            # 记录错误到数据库
            try:
                from db_logger import log_error
                log_error(
                    ip_address=client_ip,
                    endpoint="/api/query/stream",
                    error_message=str(e),
                    error_trace=error_trace,
                    question=request.question
                )
            except Exception as log_err:
                print(f"[ERROR] 记录错误失败: {log_err}")
            
            error_data = {
                'type': 'error',
                'content': str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, req: Request = None):
    """
    问答接口（非流式）
    """
    # 检查服务是否初始化
    if graphrag_service is None:
        return {
            "answer": "抱歉，GraphRAG 服务未初始化，请检查服务器配置和日志",
            "mode": request.mode,
            "source": None,
            "graph_data": None,
            "confidence": 0.0
        }
    
    start_time = time.time()
    
    try:
        print("=" * 80)
        print(f"[API] ========== 收到查询请求 ==========")
        print(f"[API] 问题: {request.question}")
        print(f"[API] 模式: {request.mode}")
        print(f"[API] 会话ID: {request.conversation_id}")
        print(f"[API] 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        result = graphrag_service.query(
            question=request.question,
            mode=request.mode,
            conversation_id=request.conversation_id
        )
        
        elapsed_time = time.time() - start_time
        print("=" * 80)
        print(f"[API] ========== 查询完成 ==========")
        print(f"[API] 模式: {result.get('mode')}")
        print(f"[API] 置信度: {result.get('confidence')}")
        print(f"[API] 答案长度: {len(result.get('answer', ''))} 字符")
        print(f"[API] 耗时: {elapsed_time:.2f} 秒")
        print(f"[API] 答案预览: {result.get('answer', '')[:200]}...")
        
        # 打印图谱数据（用于调试）
        graph_data = result.get('graph_data', {})
        if graph_data and graph_data.get('nodes'):
            print(f"[API] 图谱节点数: {len(graph_data['nodes'])} 个")
            if len(graph_data['nodes']) > 0:
                sample = graph_data['nodes'][0]
                print(f"[API] 样本节点: {sample.get('label', '')}")
                print(f"[API]   - 有description: {'是' if sample.get('description') else '否'}")
                if sample.get('description'):
                    print(f"[API]   - description长度: {len(sample.get('description', ''))}")
        
        print("=" * 80)
        
        # 记录问答到数据库
        log_question(
            question=request.question,
            answer=result.get('answer', ''),
            mode=result.get('mode', 'global'),
            response_time=elapsed_time * 1000,  # 转换为毫秒
            confidence=result.get('confidence', 0.0)
        )
        
        return result
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        elapsed_time = time.time() - start_time
        
        print("=" * 80)
        print(f"[API ERROR] ========== 查询失败 ==========")
        print(f"[API ERROR] 错误: {str(e)}")
        print(f"[API ERROR] 耗时: {elapsed_time:.2f} 秒")
        print(f"[API ERROR] 错误堆栈:\n{error_trace}")
        print("=" * 80)
        
        # 记录失败的问答
        log_question(
            question=request.question,
            answer=f"错误: {str(e)}",
            mode=request.mode,
            response_time=elapsed_time * 1000,
            confidence=0.0
        )
        
        # 返回错误信息，而不是抛出异常，这样前端可以显示错误
        return {
            "answer": f"抱歉，检索时出现错误：{str(e)}",
            "mode": request.mode,
            "source": None,
            "graph_data": None,
            "confidence": 0.0
        }

@app.get("/api/graph/{entity_titles}")
async def get_graph(entity_titles: str):
    """
    获取图谱数据
    """
    if graphrag_service is None:
        raise HTTPException(status_code=503, detail="GraphRAG 服务未初始化")
    try:
        titles = entity_titles.split(",")
        graph_data = graphrag_service.get_graph_data(titles)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图谱失败: {str(e)}")

@app.get("/api/recommend")
async def get_recommendations():
    """
    获取常见问题推荐
    """
    try:
        recommendations = graphrag_service.get_common_questions()
        return {"questions": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """
    获取知识库统计信息
    """
    try:
        stats = graphrag_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

# ========== 启动服务器 ==========

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("📋 已注册的API端点:")
    print("=" * 80)
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods:15} {route.path}")
    print("=" * 80)
    print(f"🚀 启动服务器: http://0.0.0.0:8084")
    print("=" * 80 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8084,
        reload=True
    )

