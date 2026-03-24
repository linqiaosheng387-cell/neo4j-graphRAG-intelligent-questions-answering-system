"""
GraphRAG 核心服务类
- GraphRAG (Parquet) 负责检索和问答
- Neo4j 负责图谱可视化
- LLM API 负责生成智能答案（支持多个免费LLM）
"""
import pandas as pd
import re
import os
import requests
import json
from typing import Dict, List, Any, Optional, Iterator
from neo4j import GraphDatabase
from llm_client import LLMClient

class GraphRAGService:
    def __init__(self, data_path: str = "..", 
                 neo4j_uri: str = "neo4j://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "12345678",
                 deepseek_api_key: Optional[str] = None):
        """
        初始化 GraphRAG 服务
        
        Args:
            data_path: 数据文件路径
            neo4j_uri: Neo4j 连接地址
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
            deepseek_api_key: DeepSeek API Key（如果为None，则从环境变量 DEEPSEEK_API_KEY 读取）
        """
        print("正在加载 GraphRAG 数据...")
        
        # 加载 Parquet 文件（用于检索）
        self.entities = pd.read_parquet(f"{data_path}/entities.parquet")
        self.relationships = pd.read_parquet(f"{data_path}/relationships.parquet")
        self.text_units = pd.read_parquet(f"{data_path}/text_units.parquet")
        self.communities = pd.read_parquet(f"{data_path}/communities.parquet")
        self.community_reports = pd.read_parquet(f"{data_path}/community_reports.parquet")
        self.documents = pd.read_parquet(f"{data_path}/documents.parquet")
        
        # 连接 Neo4j（仅用于图谱可视化）
        try:
            self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            print(f"✅ Neo4j 连接成功")
        except Exception as e:
            print(f"⚠️  Neo4j 连接失败: {e}")
            print(f"   图谱可视化功能将不可用，但问答功能正常")
            self.neo4j_driver = None
        
        # 初始化 LLM 客户端（支持多个免费LLM）
        self.llm_client = LLMClient()
        # 兼容旧的deepseek_api_key参数
        if deepseek_api_key and not self.llm_client.api_key:
            self.llm_client = LLMClient(provider="deepseek", api_key=deepseek_api_key)
        
        print(f"✅ GraphRAG 数据加载完成！")
        print(f"   - 实体数量: {len(self.entities):,}")
        print(f"   - 关系数量: {len(self.relationships):,}")
        print(f"   - 社区数量: {len(self.communities):,}")
        print(f"   - 文本单元: {len(self.text_units):,}")
        
    def query(self, question: str, mode: str = "global", 
              conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """执行问答查询"""
        if mode == "global":
            return self._global_search(question)
        else:
            return self._local_search(question)
    
    def _call_llm_api_stream(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> Iterator[str]:
        """
        流式调用 LLM API 生成答案
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_tokens: 最大token数
            
        Yields:
            生成的文本片段
        """
        return self.llm_client.chat_stream(prompt, system_prompt, max_tokens)
    
    def _call_llm_api(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> Optional[str]:
        """
        调用 LLM API 生成答案（支持多个免费LLM）
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_tokens: 最大生成token数
            
        Returns:
            生成的答案，如果失败则返回None
        """
        print(f"[DEBUG] 开始调用 {self.llm_client.provider} API...")
        
        answer = self.llm_client.chat(prompt, system_prompt, max_tokens)
        
        if answer:
            print(f"[DEBUG] LLM API 调用成功")
            print(f"[DEBUG] 生成答案长度: {len(answer)} 字符")
            print(f"[DEBUG] 生成答案预览: {answer[:200]}...")
        else:
            print(f"[DEBUG] LLM API 调用失败或未配置")
        
        return answer
    
    def _score_report_relevance(self, report: pd.Series, question: str, keywords: List[str]) -> float:
        """
        计算社区报告与问题的相关性得分（Map阶段）
        改进：使用更智能的匹配策略，优先匹配长关键词（通常是实体名称）
        """
        score = 0.0
        
        try:
            title = self._safe_get_value(report.get('title', ''), "")
            summary = self._safe_get_value(report.get('summary', ''), "")
            full_content = self._safe_get_value(report.get('full_content', ''), "")
            
            # 对关键词按长度降序排序，优先匹配长词（通常是实体名称）
            sorted_keywords = sorted(keywords, key=len, reverse=True) if keywords else []
            
            # 标题匹配得分最高
            if title:
                title_lower = title.lower()
                question_lower = question.lower()
                
                # 完整问题匹配
                if question_lower in title_lower or title_lower in question_lower:
                    score += 25.0
                
                # 关键词匹配（更宽松）
                matched_keywords = []
                for keyword in sorted_keywords:
                    if keyword and len(keyword) >= 2:
                        keyword_lower = keyword.lower()
                        if keyword_lower in title_lower:
                            # 长词匹配权重更高
                            weight = min(8.0, len(keyword) * 2.0)
                            score += weight
                            matched_keywords.append(keyword)
                            print(f"[DEBUG] 标题匹配关键词 '{keyword}', 得分+{weight:.1f}")
                
                # 多个关键词匹配额外加分
                if len(matched_keywords) >= 2:
                    score += 3.0
            
            # 摘要匹配
            if summary:
                summary_lower = summary.lower()
                question_lower = question.lower()
                
                # 完整问题匹配
                if question_lower in summary_lower or any(kw in summary_lower for kw in question_lower.split() if len(kw) >= 2):
                    score += 15.0
                
                # 关键词匹配
                matched_keywords = []
                for keyword in sorted_keywords:
                    if keyword and len(keyword) >= 2:
                        keyword_lower = keyword.lower()
                        if keyword_lower in summary_lower:
                            # 长词匹配权重更高
                            weight = min(5.0, len(keyword) * 1.2)
                            score += weight
                            matched_keywords.append(keyword)
                            print(f"[DEBUG] 摘要匹配关键词 '{keyword}', 得分+{weight:.1f}")
                
                # 多个关键词匹配额外加分
                if len(matched_keywords) >= 2:
                    score += 2.0
            
            # 完整内容匹配（权重较低，但覆盖范围广）
            if full_content:
                content_lower = full_content.lower()
                question_lower = question.lower()
                
                # 完整问题匹配
                if question_lower in content_lower:
                    score += 10.0
                
                # 关键词匹配（所有关键词）
                matched_count = 0
                for keyword in sorted_keywords:
                    if keyword and len(keyword) >= 2:
                        keyword_lower = keyword.lower()
                        if keyword_lower in content_lower:
                            score += min(2.0, len(keyword) * 0.5)
                            matched_count += 1
                
                # 多个关键词匹配额外加分
                if matched_count >= 2:
                    score += 1.0
                if matched_count >= 3:
                    score += 1.0
            
            # 如果有任何匹配，给予基础分数（确保不会完全没有结果）
            if score > 0:
                score += 1.0  # 基础分数
                
        except Exception as e:
            print(f"[DEBUG] 评分报告时出错: {e}")
            pass
        
        return score
    
    def _extract_answer_from_reports(self, question: str, keywords: List[str], 
                                    top_reports: List[Dict]) -> str:
        """
        从多个社区报告中提取并综合生成答案
        如果配置了 DeepSeek API，则使用 LLM 生成智能答案；否则使用文本拼接
        """
        # 构建上下文信息（从社区报告中提取）
        context_parts = []
        
        for item in top_reports[:5]:  # 取前5个最相关的报告
            report = item['report']
            try:
                title = self._safe_get_value(report.get('title', ''), "")
                summary = self._safe_get_value(report.get('summary', ''), "")
                full_content = self._safe_get_value(report.get('full_content', ''), "")
                
                if title:
                    context_parts.append(f"\n## {title}\n\n")
                
                # 优先使用摘要，如果没有则使用完整内容的前1000字符
                if summary:
                    context_parts.append(f"{summary}\n\n")
                elif full_content:
                    # 限制长度
                    content_short = full_content[:1000] + "..." if len(full_content) > 1000 else full_content
                    context_parts.append(f"{content_short}\n\n")
            except:
                continue
        
        context = "".join(context_parts)
        
        print(f"[DEBUG] 全局搜索 - API Key 配置: {'是' if self.llm_client.api_key else '否'}")
        print(f"[DEBUG] 全局搜索 - Context 长度: {len(context)} 字符")
        print(f"[DEBUG] 全局搜索 - Context 预览: {context[:200]}...")
        
        # 如果配置了 DeepSeek API，使用 LLM 生成答案
        if self.llm_client.api_key:
            if not context:
                # 即使没有 context，也尝试用 LLM 回答
                context = "未找到直接相关的社区报告，但请尝试根据您对中央苏区历史的了解回答问题。"
            
            prompt = f"""请根据以下关于中央苏区历史的社区报告，回答用户的问题。

用户问题：{question}

社区报告内容：
{context}

请基于以上社区报告内容，用自然、准确、流畅的中文回答问题。如果报告中有直接答案，请明确指出；如果没有直接答案，请根据相关信息进行合理推断。如果确实没有相关信息，请诚实说明。"""
            
            print(f"[DEBUG] 全局搜索 - 准备调用 DeepSeek API，Prompt 长度: {len(prompt)} 字符")
            llm_answer = self._call_llm_api(prompt, max_tokens=2000)
            if llm_answer:
                print(f"[DEBUG] 全局搜索 - LLM 生成答案成功，长度: {len(llm_answer)} 字符")
                
                # 在LLM答案末尾添加报告编号引用（显示所有报告）
                report_numbers = [str(item['report_number']) for item in top_reports[:5]]
                if report_numbers:
                    refs = ", ".join(report_numbers)
                    llm_answer += f"\n\n[Data: Reports ({refs})]"
                    print(f"[DEBUG] LLM答案 - 引用的报告编号: {refs}")
                
                return llm_answer
            else:
                print(f"[DEBUG] 全局搜索 - LLM 调用失败，降级到文本拼接")
        else:
            print(f"[DEBUG] 全局搜索 - 未配置 API Key，使用文本拼接")
        
        # 如果没有配置 API 或调用失败，使用文本拼接方式（改进版）
        print(f"[DEBUG] 使用文本拼接方式生成答案...")
        answer = ""
        
        # 分析问题类型
        is_time_question = any(w in question for w in ['时间', '时候', '何时', '成立', '建立', '创建', '开始'])
        is_location_question = any(w in question for w in ['地点', '哪里', '位置', '在', '于'])
        is_what_question = any(w in question for w in ['什么', '哪些', '是什么', '有哪些', '如何', '怎么'])
        is_who_question = any(w in question for w in ['谁', '人物', '领导', '人物'])
        is_intro_question = any(w in question for w in ['介绍', '讲讲', '说说', '是什么'])
        
        # 提取问题中的核心实体
        core_entity = None
        for keyword in keywords:
            if len(keyword) > 2:
                # 检查是否是实体名称
                try:
                    entity_match = self.entities[
                        self.entities['title'].str.contains(keyword, case=False, na=False)
                    ]
                    if len(entity_match) > 0:
                        core_entity = self._safe_get_value(entity_match.iloc[0]['title'])
                        print(f"[DEBUG] 识别到核心实体: {core_entity}")
                        break
                except:
                    pass
        
        # 根据问题类型生成答案开头
        if is_intro_question:
            if core_entity:
                answer += f"# {core_entity}\n\n根据《中央苏区史》社区报告的综合分析：\n\n"
            else:
                answer += f"根据《中央苏区史》社区报告的综合分析：\n\n"
        elif is_time_question:
            if core_entity:
                answer += f"## 关于{core_entity}的时间信息\n\n根据《中央苏区史》社区报告：\n\n"
            else:
                answer += f"## 时间信息\n\n根据《中央苏区史》社区报告：\n\n"
        elif is_location_question:
            if core_entity:
                answer += f"## 关于{core_entity}的地点信息\n\n根据《中央苏区史》社区报告：\n\n"
            else:
                answer += f"## 地点信息\n\n根据《中央苏区史》社区报告：\n\n"
        elif is_what_question or is_who_question:
            if core_entity:
                answer += f"## {core_entity}\n\n根据《中央苏区史》社区报告：\n\n"
            else:
                answer += f"根据《中央苏区史》社区报告：\n\n"
        else:
            answer += f"根据《中央苏区史》社区报告综合分析：\n\n"
        
        # 从报告中提取相关信息（改进版，更智能地提取内容，并记录来源）
        relevant_sentences = []  # 格式：(sentence, report_number)
        for item in top_reports[:5]:  # 增加到前5个报告
            report = item['report']
            report_num = item['report_number']  # 获取报告编号
            try:
                title = self._safe_get_value(report.get('title', ''), "")
                summary = self._safe_get_value(report.get('summary', ''), "")
                full_content = self._safe_get_value(report.get('full_content', ''), "")
                
                print(f"[DEBUG] 处理报告 #{report_num}: {title[:50]}...")
                
                # 优先使用摘要（通常是最精炼的内容）
                if summary and len(summary) > 20:
                    # 对于介绍类问题，直接使用完整摘要
                    if is_intro_question:
                        relevant_sentences.append((f"**{title}**\n\n{summary}", report_num))
                        print(f"[DEBUG] 添加完整摘要，长度: {len(summary)}")
                    else:
                        # 检查摘要是否包含关键词
                        if any(kw in summary for kw in keywords if kw):
                            relevant_sentences.append((summary, report_num))
                            print(f"[DEBUG] 添加相关摘要")
                
                # 对于时间类问题，从完整内容中提取包含时间的句子
                if is_time_question and full_content and len(relevant_sentences) < 3:
                    year_pattern = r'\d{4}年\d{0,2}月?\d{0,2}日?'
                    sentences = full_content.split('。')
                    for sentence in sentences:
                        if re.search(year_pattern, sentence):
                            if any(kw in sentence for kw in keywords if kw) or (core_entity and core_entity in sentence):
                                relevant_sentences.append((sentence.strip(), report_num))
                                print(f"[DEBUG] 添加时间相关句子")
                                if len(relevant_sentences) >= 5:
                                    break
                
                # 如果摘要不够，从完整内容中提取
                if len(relevant_sentences) < 3 and full_content:
                    # 分段处理（按句号或换行符）
                    sentences = re.split(r'[。\n]', full_content)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(sentence) > 15:  # 至少15个字符
                            # 检查是否包含关键词
                            if any(kw in sentence for kw in keywords if kw):
                                relevant_sentences.append((sentence, report_num))
                                print(f"[DEBUG] 添加相关句子: {sentence[:50]}...")
                                if len(relevant_sentences) >= 8:
                                    break
            except Exception as e:
                print(f"[DEBUG] 处理报告时出错: {e}")
                continue
        
        # 生成答案内容，在每个句子后面添加引用编号
        if relevant_sentences:
            # 去重并限制数量
            unique_sentences = []
            seen = set()
            for sent_tuple in relevant_sentences:
                sent, report_num = sent_tuple
                sent_key = sent[:50]  # 使用前50个字符作为唯一标识
                if sent_key not in seen:
                    seen.add(sent_key)
                    unique_sentences.append((sent, report_num))
                    if len(unique_sentences) >= 5:
                        break
            
            # 在每个句子后面添加引用编号（同一报告只标注一次）
            cited_reports = set()  # 记录已经引用过的报告
            used_report_numbers = []  # 记录使用过的报告编号
            
            for sent, report_num in unique_sentences[:5]:
                # 确保句子以句号结尾
                if not sent.endswith('。'):
                    sent = sent + '。'
                
                # 只有第一次引用该报告时才添加标注
                if report_num not in cited_reports:
                    answer += f"{sent} [Data: Reports ({report_num})]\n\n"
                    cited_reports.add(report_num)
                    used_report_numbers.append(report_num)
                else:
                    answer += f"{sent}\n\n"
            
            # 在答案末尾添加汇总引用（显示所有使用的报告编号）
            if used_report_numbers:
                refs = ", ".join(map(str, used_report_numbers))
                answer += f"\n[Data: Reports ({refs})]\n"
                print(f"[DEBUG] 本次查询引用的报告编号: {refs}")
        else:
            # 如果没有提取到特定句子，使用报告的摘要
            for item in top_reports[:2]:
                report = item['report']
                report_num = item['report_number']
                try:
                    summary = self._safe_get_value(report.get('summary', ''), "")
                    if summary:
                        answer += f"{summary} [Data: Reports ({report_num})]\n\n"
                        break
                except:
                    continue
        
        return answer
    
    def _global_search(self, question: str) -> Dict[str, Any]:
        """
        全局检索：通过map-reduce方式搜索所有AI生成的社区报告来生成答案
        参考: https://microsoft.github.io/graphrag/query/local_search/
        
        这是一种资源密集型方法，但通常可以对需要了解整个数据集的问题给出很好的答案
        """
        try:
            print(f"\n{'='*80}")
            print(f"[全局搜索] 开始处理问题")
            print(f"{'='*80}")
            print(f"[DEBUG] 问题: {question}")
            print(f"[DEBUG] 问题长度: {len(question)} 字符")
            
            # 提取关键词（去除疑问词）
            print(f"\n[步骤1] 提取关键词...")
            keywords = self._extract_keywords_from_question(question)
            print(f"[DEBUG] 提取到 {len(keywords)} 个关键词: {keywords}")
            print(f"{'='*80}\n")
            
            # Map阶段：为每个社区报告计算相关性得分
            print(f"[步骤2] Map阶段 - 评分社区报告...")
            print(f"[DEBUG] 共有 {len(self.community_reports)} 个社区报告需要评分")
            scored_reports = []
            report_count = 0
            for idx, report in self.community_reports.iterrows():
                try:
                    score = self._score_report_relevance(report, question, keywords)
                    if score > 0:
                        scored_reports.append({
                            'report': report,
                            'score': score,
                            'idx': idx
                        })
                    report_count += 1
                    if report_count % 100 == 0:
                        print(f"[DEBUG] 已评分 {report_count}/{len(self.community_reports)} 个报告，找到 {len(scored_reports)} 个相关报告")
                except Exception as e:
                    print(f"[DEBUG] 评分报告 {idx} 时出错: {e}")
                    continue
            
            print(f"[DEBUG] Map阶段完成，共找到 {len(scored_reports)} 个相关报告")
            print(f"{'='*80}\n")
            
            # 如果没找到相关报告，尝试更宽松的匹配
            if len(scored_reports) == 0:
                print(f"[DEBUG] 未找到相关报告，尝试更宽松的匹配...")
                for idx, report in self.community_reports.iterrows():
                    try:
                        title = self._safe_get_value(report.get('title', ''), "")
                        summary = self._safe_get_value(report.get('summary', ''), "")
                        # 只要标题或摘要包含任何一个关键词就加入
                        for keyword in keywords:
                            if keyword and len(keyword) > 1:
                                if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
                                    scored_reports.append({
                                        'report': report,
                                        'score': 0.5,
                                        'idx': idx
                                    })
                                    break
                    except:
                        continue
            
            # 如果还是没找到，尝试查找顶层社区报告（包含最广泛的信息）
            if len(scored_reports) == 0:
                print(f"[DEBUG] 仍未找到，使用顶层社区报告...")
                try:
                    # 尝试获取所有顶层社区报告
                    top_level_communities = self.communities[self.communities['level'] == 0]
                    if len(top_level_communities) > 0:
                        for idx, community in top_level_communities.iterrows():
                            community_id = self._safe_get_value(community.get('id', ''), "")
                            if community_id:
                                matched_reports = self.community_reports[
                                    self.community_reports['id'] == community_id
                                ]
                                if len(matched_reports) > 0:
                                    report = matched_reports.iloc[0]
                                    scored_reports.append({
                                        'report': report,
                                        'score': 0.1,
                                        'idx': matched_reports.index[0]
                                    })
                                    if len(scored_reports) >= 3:  # 至少获取3个顶层报告
                                        break
                except Exception as e:
                    print(f"[DEBUG] 获取顶层社区报告出错: {e}")
            
            # 如果还是没有报告，随机选择一些报告（兜底策略）
            if len(scored_reports) == 0:
                print(f"[DEBUG] 使用随机报告作为兜底...")
                try:
                    # 随机选择前5个报告
                    for idx, report in self.community_reports.head(5).iterrows():
                        scored_reports.append({
                            'report': report,
                            'score': 0.05,
                            'idx': idx
                        })
                except Exception as e:
                    print(f"[DEBUG] 获取随机报告出错: {e}")
            
            # 如果配置了LLM，即使没有完美匹配也尝试生成答案
            if len(scored_reports) == 0:
                if self.llm_client.api_key:
                    print(f"[DEBUG] 没有找到报告，但尝试用LLM直接回答...")
                    prompt = f"""请回答以下关于中央苏区历史的问题：

用户问题：{question}

请基于你对中央苏区历史的了解，用自然、准确、流畅的中文回答问题。如果你不确定答案，请诚实说明。"""
                    
                    llm_answer = self._call_llm_api(prompt, max_tokens=2000)
                    if llm_answer:
                        return {
                            "answer": llm_answer,
                            "mode": "global",
                            "source": "DeepSeek LLM 直接回答",
                            "graph_data": None,
                            "confidence": 0.3
                        }
                
                # 如果LLM也失败了，返回友好的错误信息
                return {
                    "answer": "抱歉，未找到相关信息。建议：\n1. 尝试使用更具体的关键词\n2. 切换到本地检索模式\n3. 查看推荐问题获取灵感",
                    "mode": "global",
                    "confidence": 0.0
                }
            
            # Reduce阶段：按得分排序，选择最相关的报告
            scored_reports.sort(key=lambda x: x['score'], reverse=True)
            top_reports = scored_reports[:5]  # 取前5个最相关的报告
            
            print(f"[DEBUG] 找到 {len(scored_reports)} 个相关报告，选择前 {len(top_reports)} 个")
            
            # 为报告分配数字序号（从1开始）
            print(f"[DEBUG] 为 {len(top_reports)} 个报告分配编号:")
            for i, item in enumerate(top_reports, 1):
                item['report_number'] = i
                report_title = self._safe_get_value(item['report'].get('title', ''), "未知标题")
                print(f"[DEBUG]   报告 #{i}: {report_title[:50]}...")
            
            # 生成综合答案
            answer = self._extract_answer_from_reports(question, keywords, top_reports)
            
            # 获取相关实体用于图谱展示
            all_entity_titles = []
            for item in top_reports[:3]:  # 只取前3个报告的实体
                report = item['report']
                try:
                    report_id = self._safe_get_value(report.get('id', ''), "")
                    if report_id:
                        community = self.communities[self.communities['id'] == report_id]
                        if len(community) > 0:
                            community_row = community.iloc[0]
                            entity_ids_val = community_row.get('entity_ids', [])
                            
                            # 安全地解析 entity_ids
                            try:
                                if isinstance(entity_ids_val, str):
                                    entity_ids = json.loads(entity_ids_val)
                                elif isinstance(entity_ids_val, (list, tuple)):
                                    entity_ids = list(entity_ids_val)
                                else:
                                    entity_ids = []
                                
                                if entity_ids:
                                    entity_ids = entity_ids[:10]
                                    entity_mask = self.entities['id'].isin(entity_ids)
                                    community_entities = self.entities[entity_mask]
                                    for idx, entity in community_entities.iterrows():
                                        title = self._safe_get_value(entity.get('title', ''), "")
                                        if title:
                                            all_entity_titles.append(title)
                            except:
                                pass
                except:
                    continue
            
            # 去重
            all_entity_titles = list(dict.fromkeys(all_entity_titles))[:15]
            
            # 从 Neo4j 生成图谱数据
            graph_data = self._get_graph_from_neo4j(all_entity_titles)
            
            # 提取来源信息
            sources = []
            for item in top_reports[:6]:  # 最多显示6个来源
                report = item['report']
                try:
                    title = self._safe_get_value(report.get('title', ''), "")
                    if title:
                        sources.append(title)
                except:
                    pass
            
            return {
                "answer": answer,
                "mode": "global",
                "source": f"《中央苏区史》- {len(top_reports)}个社区报告",
                "sources": sources,  # 新增：来源列表
                "graph_data": graph_data,
                "confidence": min(0.95, 0.7 + len(top_reports) * 0.05)
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] 全局检索错误: {e}")
            print(f"[ERROR] 错误堆栈:\n{error_trace}")
            return {
                "answer": f"抱歉，检索时出现错误：{str(e)}",
                "mode": "global",
                "confidence": 0.0
            }
    
    def _safe_get_value(self, val, default=""):
        """安全地获取值，处理可能的 Series"""
        if val is None:
            return default
        try:
            # 首先检查是否是 pandas Series
            if isinstance(val, pd.Series):
                if len(val) > 0:
                    return str(val.iloc[0])
                return default
            # 检查是否是其他可迭代对象（但不是字符串）
            if hasattr(val, '__iter__') and not isinstance(val, (str, bytes)):
                # 可能是其他类型的数组或列表
                if hasattr(val, 'iloc'):  # 可能是其他 pandas 类型
                    return default
                return default
            # 安全地检查 NaN - 只对数值类型检查
            try:
                if isinstance(val, (float, int)) and pd.isna(val):
                    return default
            except:
                pass
            # 转换为字符串
            return str(val)
        except Exception as e:
            # 如果所有方法都失败，尝试直接转换
            try:
                if val is not None:
                    return str(val)
            except:
                pass
            return default
    
    def _extract_keywords_from_question(self, question: str) -> List[str]:
        """从问题中提取关键词，保留重要实体名称"""
        import re
        
        # 移除疑问词和常见助词（扩展版）
        stop_words = {
            '什么', '什么时候', '何时', '哪里', '哪个', '哪些', '怎么', '如何', '为什么', 
            '是', '的', '了', '吗', '呢', '？', '?', '，', '。', '、', '时间', '成立', '建立', '创建',
            '介绍', '一下', '讲讲', '说说', '告诉', '我', '请', '能', '可以', '帮', '帮忙',
            '关于', '有关', '相关', '方面', '情况', '内容', '信息', '资料', '详细', '具体'
        }
        
        keywords = []
        
        # 策略1: 先尝试匹配已知实体（最精确）
        # 优化：使用高效的字符串匹配，检查所有实体，优先匹配长词
        try:
            print(f"[DEBUG] 策略1: 从 {len(self.entities)} 个实体中查找匹配...")
            # 提取问题中可能的实体名称（2-10字的中文词组）
            potential_entities = re.findall(r'[\u4e00-\u9fa5]{2,10}', question)
            # 按长度降序排序，优先匹配长实体名
            potential_entities = sorted(set(potential_entities), key=len, reverse=True)
            print(f"[DEBUG] 策略1: 候选实体片段: {potential_entities}")
            
            for potential in potential_entities:
                # 跳过常见停用词
                if potential in stop_words:
                    continue
                    
                # 使用pandas的向量化操作快速查找
                matches = self.entities[
                    self.entities['title'].str.contains(potential, case=False, na=False)
                ]
                
                if len(matches) > 0:
                    print(f"[DEBUG] 策略1: '{potential}' 匹配到 {len(matches)} 个实体")
                
                for idx, entity in matches.iterrows():
                    entity_title = self._safe_get_value(entity.get('title', ''), "")
                    if entity_title and entity_title not in keywords:
                        keywords.append(entity_title)
                        print(f"[DEBUG] 策略1: 从实体库匹配到 '{entity_title}'")
                        if len(keywords) >= 5:  # 增加到5个，确保不会过早停止
                            break
                
                if len(keywords) >= 5:
                    break
        except Exception as e:
            print(f"[DEBUG] 策略1执行出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 策略2: 提取连续的中文词（2-8字），过滤停用词
        # 这可以捕获"中央苏区"、"第一次全国代表大会"等实体
        chinese_phrases = re.findall(r'[\u4e00-\u9fa5]{2,8}', question)
        for phrase in chinese_phrases:
            # 检查是否是停用词或已存在
            if phrase not in stop_words and phrase not in keywords:
                # 检查是否包含停用词
                has_stop_word = False
                for stop_word in stop_words:
                    if stop_word in phrase and len(stop_word) >= 2:
                        has_stop_word = True
                        break
                
                if not has_stop_word:
                    keywords.append(phrase)
                    print(f"[DEBUG] 策略2: 提取中文短语 '{phrase}'")
        
        # 策略3: 如果关键词太少，尝试分词提取
        if len(keywords) < 2:
            # 移除常见疑问句式
            cleaned = question
            for pattern in ['介绍一下', '讲一讲', '说一说', '告诉我', '是什么时候', '什么时候', 
                          '是什么', '有哪些', '在哪里', '哪里', '成立时间', '建立时间', '创建时间',
                          '关于', '有关', '的信息', '的情况', '的内容']:
                cleaned = cleaned.replace(pattern, ' ')
            
            # 清理标点
            cleaned = re.sub(r'[？?，。、！!；;：:\s]+', ' ', cleaned)
            
            # 提取所有非空词
            words = [w.strip() for w in cleaned.split() if w.strip() and len(w.strip()) >= 2]
            
            for word in words:
                if word not in stop_words and word not in keywords:
                    keywords.append(word)
                    print(f"[DEBUG] 策略3: 分词提取 '{word}'")
        
        # 策略4: 如果还是没有关键词，提取所有2-6字的中文词
        if len(keywords) == 0:
            all_chinese = re.findall(r'[\u4e00-\u9fa5]{2,6}', question)
            for word in all_chinese:
                if word not in keywords:
                    keywords.append(word)
                    print(f"[DEBUG] 策略4: 提取所有中文词 '{word}'")
                    if len(keywords) >= 5:
                        break
        
        # 策略5: 最后的兜底策略 - 使用原问题
        if len(keywords) == 0:
            # 清理标点后的完整问题
            cleaned_question = re.sub(r'[？?，。、！!；;：:\s]', '', question)
            if len(cleaned_question) >= 2:
                keywords.append(cleaned_question[:10])
                print(f"[DEBUG] 策略5: 使用原问题 '{cleaned_question[:10]}'")
        
        # 去重并按长度排序（长词优先）
        keywords = list(dict.fromkeys(keywords))  # 去重但保持顺序
        keywords.sort(key=len, reverse=True)  # 按长度降序排序
        
        print(f"[DEBUG] 最终提取的关键词: {keywords[:5]}")
        return keywords[:5] if keywords else [question]
    
    def _find_entities_by_query(self, question: str, keywords: List[str]) -> pd.DataFrame:
        """
        根据查询找到语义相关的实体（Entity-based Reasoning）
        参考: https://microsoft.github.io/graphrag/query/local_search/
        改进：使用更智能的匹配策略，优先匹配长词（通常是实体名称）
        """
        related_entities = pd.DataFrame()
        entities_list = []
        
        # 策略1: 完整问题匹配实体标题（最高优先级）
        try:
            mask = self.entities['title'].str.contains(question, case=False, na=False)
            found = self.entities[mask]
            if len(found) > 0:
                entities_list.append(found)
                print(f"[DEBUG] 策略1: 完整问题匹配找到 {len(found)} 个实体")
        except Exception as e:
            print(f"[DEBUG] 策略1执行出错: {e}")
        
        # 策略2: 按关键词长度排序，优先匹配长词（通常是实体名称）
        # 对关键词按长度降序排序
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        
        for keyword in sorted_keywords:
            if len(keyword) >= 2:  # 至少2个字符
                try:
                    # 优先匹配标题（完全匹配或包含）
                    title_mask = self.entities['title'].str.contains(keyword, case=False, na=False)
                    # 其次匹配描述
                    desc_mask = self.entities['description'].str.contains(keyword, case=False, na=False)
                    # 合并结果，标题匹配优先
                    mask = title_mask | desc_mask
                    found = self.entities[mask]
                    if len(found) > 0:
                        # 将标题完全匹配的实体排在前面
                        title_exact = found[found['title'].str.contains(keyword, case=False, na=False)]
                        if len(title_exact) > 0:
                            entities_list.append(title_exact)
                        # 添加其他匹配的实体
                        other = found[~found['title'].str.contains(keyword, case=False, na=False)]
                        if len(other) > 0:
                            entities_list.append(other)
                        print(f"[DEBUG] 策略2: 关键词 '{keyword}' 匹配找到 {len(found)} 个实体")
                        if sum(len(df) for df in entities_list) >= 15:
                            break
                except Exception as e:
                    print(f"[DEBUG] 关键词 '{keyword}' 匹配出错: {e}")
                    continue
        
        # 策略3: 如果还是没找到，尝试从问题中提取可能的实体名称
        if len(entities_list) == 0:
            import re
            # 提取2-6字的中文词作为可能的实体名称
            possible_entities = re.findall(r'[\u4e00-\u9fa5]{2,6}', question)
            for entity_name in possible_entities:
                if len(entity_name) >= 2:
                    try:
                        mask = (
                            self.entities['title'].str.contains(entity_name, case=False, na=False) |
                            self.entities['description'].str.contains(entity_name, case=False, na=False)
                        )
                        found = self.entities[mask]
                        if len(found) > 0:
                            entities_list.append(found)
                            print(f"[DEBUG] 策略3: 提取实体名称 '{entity_name}' 匹配找到 {len(found)} 个实体")
                            if sum(len(df) for df in entities_list) >= 10:
                                break
                    except:
                        continue
        
        # 合并所有找到的实体
        if entities_list:
            try:
                related_entities = pd.concat(entities_list, ignore_index=True)
                if 'id' in related_entities.columns:
                    related_entities = related_entities.drop_duplicates(subset=['id'])
                else:
                    related_entities = related_entities.drop_duplicates()
                print(f"[DEBUG] 总共找到 {len(related_entities)} 个相关实体")
            except Exception as e:
                print(f"[DEBUG] 合并实体列表时出错: {e}")
                related_entities = pd.DataFrame()
        
        return related_entities
    
    def _get_entity_text_units(self, entity_ids: List[str]) -> pd.DataFrame:
        """
        Entity-Text Unit Mapping: 根据实体ID找到相关的文本单元
        参考: https://microsoft.github.io/graphrag/query/local_search/
        """
        matched_texts_list = []
        
        try:
            # 检查 text_units 是否有 entity_ids 字段
            if 'entity_ids' in self.text_units.columns:
                for entity_id in entity_ids[:10]:  # 限制检查的实体数量
                    try:
                        # 安全地查找包含该实体ID的文本单元
                        def check_entity_in_list(x):
                            try:
                                if pd.isna(x):
                                    return False
                                if isinstance(x, str):
                                    # 尝试解析字符串（可能是列表的字符串表示）
                                    try:
                                        x = json.loads(x)
                                    except:
                                        pass
                                if isinstance(x, (list, tuple)):
                                    return entity_id in x
                                return str(x) == str(entity_id)
                            except:
                                return False
                        
                        mask = self.text_units['entity_ids'].apply(check_entity_in_list)
                        found = self.text_units[mask]
                        if len(found) > 0:
                            matched_texts_list.append(found)
                            if sum(len(df) for df in matched_texts_list) >= 10:
                                break
                    except Exception as e:
                        print(f"[DEBUG] 检查实体ID {entity_id} 时出错: {e}")
                        continue
                
                # 合并所有找到的文本单元
                if matched_texts_list:
                    matched_texts = pd.concat(matched_texts_list, ignore_index=True)
                    if 'id' in matched_texts.columns:
                        matched_texts = matched_texts.drop_duplicates(subset=['id'])
                    else:
                        matched_texts = matched_texts.drop_duplicates()
                else:
                    matched_texts = pd.DataFrame()
            else:
                # 如果没有 entity_ids 字段，通过实体名称匹配文本内容
                entity_titles = []
                for entity_id in entity_ids[:10]:
                    try:
                        entity_mask = self.entities['id'] == entity_id
                        entity = self.entities[entity_mask]
                        if len(entity) > 0:
                            title = self._safe_get_value(entity.iloc[0]['title'])
                            if title:
                                entity_titles.append(title)
                    except:
                        continue
                
                # 通过实体名称在文本中查找
                for entity_title in entity_titles[:5]:
                    try:
                        text_mask = self.text_units['text'].str.contains(str(entity_title), case=False, na=False)
                        found = self.text_units[text_mask]
                        if len(found) > 0:
                            matched_texts_list.append(found)
                            if sum(len(df) for df in matched_texts_list) >= 10:
                                break
                    except:
                        continue
                
                # 合并所有找到的文本单元
                if matched_texts_list:
                    matched_texts = pd.concat(matched_texts_list, ignore_index=True)
                    if 'id' in matched_texts.columns:
                        matched_texts = matched_texts.drop_duplicates(subset=['id'])
                    else:
                        matched_texts = matched_texts.drop_duplicates()
                else:
                    matched_texts = pd.DataFrame()
        except Exception as e:
            print(f"[DEBUG] 获取实体文本单元时出错: {e}")
            matched_texts = pd.DataFrame()
        
        return matched_texts.head(10)  # 限制返回数量
    
    def _get_entity_relationships(self, entity_ids: List[str]) -> pd.DataFrame:
        """
        Entity-Entity Relationships: 获取实体的关系
        参考: https://microsoft.github.io/graphrag/query/local_search/
        """
        related_relationships_list = []
        
        try:
            for entity_id in entity_ids[:10]:
                try:
                    # 安全地查找以该实体为源或目标的关系
                    source_mask = self.relationships['source'] == entity_id
                    target_mask = self.relationships['target'] == entity_id
                    # 使用 | 运算符组合两个布尔 Series
                    combined_mask = source_mask | target_mask
                    found = self.relationships[combined_mask]
                    if len(found) > 0:
                        related_relationships_list.append(found)
                        if sum(len(df) for df in related_relationships_list) >= 20:
                            break
                except Exception as e:
                    print(f"[DEBUG] 检查实体 {entity_id} 的关系时出错: {e}")
                    continue
            
            # 合并所有找到的关系
            if related_relationships_list:
                related_relationships = pd.concat(related_relationships_list, ignore_index=True)
                if 'id' in related_relationships.columns:
                    related_relationships = related_relationships.drop_duplicates(subset=['id'])
                else:
                    related_relationships = related_relationships.drop_duplicates()
            else:
                related_relationships = pd.DataFrame()
        except Exception as e:
            print(f"[DEBUG] 获取实体关系时出错: {e}")
            related_relationships = pd.DataFrame()
        
        return related_relationships.head(20)
    
    def _get_entity_community_reports(self, entity_ids: List[str]) -> pd.DataFrame:
        """
        Entity-Report Mapping: 根据实体找到相关的社区报告
        参考: https://microsoft.github.io/graphrag/query/local_search/
        """
        matched_reports_list = []
        
        try:
            # 通过实体所属的社区找到报告
            for entity_id in entity_ids[:10]:
                try:
                    # 安全地查找包含该实体的社区
                    def check_entity_in_community(x):
                        try:
                            if pd.isna(x):
                                return False
                            if isinstance(x, str):
                                try:
                                    x = json.loads(x)
                                except:
                                    pass
                            if isinstance(x, (list, tuple)):
                                return entity_id in x
                            return str(x) == str(entity_id)
                        except:
                            return False
                    
                    mask = self.communities['entity_ids'].apply(check_entity_in_community)
                    communities_with_entity = self.communities[mask]
                    
                    if len(communities_with_entity) > 0:
                        # 获取这些社区的ID
                        try:
                            community_ids = communities_with_entity['id'].tolist()
                            # 查找对应的报告
                            reports_mask = self.community_reports['id'].isin(community_ids)
                            reports = self.community_reports[reports_mask]
                            if len(reports) > 0:
                                matched_reports_list.append(reports)
                                if sum(len(df) for df in matched_reports_list) >= 5:
                                    break
                        except:
                            continue
                except Exception as e:
                    print(f"[DEBUG] 检查实体 {entity_id} 的社区时出错: {e}")
                    continue
            
            # 合并所有找到的报告
            if matched_reports_list:
                matched_reports = pd.concat(matched_reports_list, ignore_index=True)
                if 'id' in matched_reports.columns:
                    matched_reports = matched_reports.drop_duplicates(subset=['id'])
                else:
                    matched_reports = matched_reports.drop_duplicates()
            else:
                matched_reports = pd.DataFrame()
        except Exception as e:
            print(f"[DEBUG] 获取实体社区报告时出错: {e}")
            matched_reports = pd.DataFrame()
        
        return matched_reports.head(5)
    
    def _local_search(self, question: str) -> Dict[str, Any]:
        """
        本地检索：按照 Microsoft GraphRAG 官方文档实现
        参考: https://microsoft.github.io/graphrag/query/local_search/
        
        流程：
        1. Entity-based Reasoning: 找到语义相关的实体
        2. Entity-Text Unit Mapping: 找到实体相关的文本单元
        3. Entity-Report Mapping: 找到实体相关的社区报告
        4. Entity-Entity Relationships: 找到相关实体和关系
        5. Ranking + Filtering: 排序和过滤
        6. Generate Response: 生成答案
        """
        try:
            # 提取关键词
            keywords = self._extract_keywords_from_question(question)
            print(f"[DEBUG] 本地搜索 - 问题: {question}, 关键词: {keywords}")
            
            # 步骤1: Entity-based Reasoning - 找到语义相关的实体
            related_entities = self._find_entities_by_query(question, keywords)
            
            if len(related_entities) == 0:
                return {
                    "answer": "抱歉，未找到相关信息。请尝试其他关键词或使用全局检索模式。",
                    "mode": "local",
                    "confidence": 0.0
                }
            
            # 限制实体数量并获取实体ID列表
            related_entities = related_entities.head(10)
            entity_ids = []
            entity_titles = []
            try:
                for idx, row in related_entities.iterrows():
                    try:
                        entity_id = self._safe_get_value(row.get('id', ''))
                        entity_title = self._safe_get_value(row.get('title', ''))
                        if entity_id and entity_title:
                            entity_ids.append(entity_id)
                            entity_titles.append(entity_title)
                    except:
                        continue
            except:
                pass
            
            if not entity_ids:
                return {
                    "answer": "抱歉，未找到相关信息。请尝试其他关键词或使用全局检索模式。",
                    "mode": "local",
                    "confidence": 0.0
                }
            
            # 步骤2: Entity-Text Unit Mapping - 找到实体相关的文本单元
            matched_texts = self._get_entity_text_units(entity_ids)
            
            # 步骤3: Entity-Report Mapping - 找到实体相关的社区报告
            matched_reports = self._get_entity_community_reports(entity_ids)
            
            # 步骤4: Entity-Entity Relationships - 找到相关关系
            related_relationships = self._get_entity_relationships(entity_ids)
            
            # 步骤5 & 6: 生成答案 - 结合所有信息
            answer = self._generate_local_answer(
                question=question,
                entities=related_entities,
                text_units=matched_texts,
                reports=matched_reports,
                relationships=related_relationships
            )
            
            # 从 Neo4j 生成图谱数据
            graph_data = self._get_graph_from_neo4j(entity_titles[:10] if entity_titles else [])
            
            return {
                "answer": answer,
                "mode": "local",
                "source": "《中央苏区史》相关章节",
                "graph_data": graph_data,
                "confidence": 0.80 if len(matched_texts) > 0 else 0.60
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] 本地检索错误: {e}")
            print(f"[ERROR] 错误堆栈:\n{error_trace}")
            return {
                "answer": f"抱歉，检索时出现错误：{str(e)}",
                "mode": "local",
                "confidence": 0.0
            }
    
    def _generate_local_answer(self, question: str, entities: pd.DataFrame, 
                              text_units: pd.DataFrame, reports: pd.DataFrame,
                              relationships: pd.DataFrame) -> str:
        """
        生成本地搜索答案，结合实体、文本单元、报告和关系信息
        如果配置了 DeepSeek API，则使用 LLM 生成智能答案；否则使用文本拼接
        """
        # 构建上下文信息
        context_parts = []
        
        # 1. 实体信息
        if len(entities) > 0:
            context_parts.append("## 相关实体信息：\n")
            for idx, entity in entities.head(5).iterrows():
                try:
                    title = self._safe_get_value(entity.get('title', ''), "")
                    description = self._safe_get_value(entity.get('description', ''), "")
                    if title:
                        entity_info = f"- **{title}**"
                        if description:
                            entity_info += f": {description[:200]}"
                        context_parts.append(entity_info + "\n")
                except:
                    continue
        
        # 2. 文本单元（原始文档片段）
        if len(text_units) > 0:
            context_parts.append("\n## 相关文档片段：\n")
            for idx, text_unit in text_units.head(5).iterrows():
                try:
                    text_content = self._safe_get_value(text_unit.get('text', ''), "")
                    if text_content:
                        # 限制长度
                        if len(text_content) > 500:
                            text_content = text_content[:500] + "..."
                        context_parts.append(f"- {text_content}\n\n")
                except:
                    continue
        
        # 3. 社区报告摘要
        if len(reports) > 0:
            context_parts.append("\n## 相关主题报告：\n")
            for idx, report in reports.head(3).iterrows():
                try:
                    title = self._safe_get_value(report.get('title', ''), "")
                    summary = self._safe_get_value(report.get('summary', ''), "")
                    if title:
                        context_parts.append(f"- **{title}**")
                        if summary:
                            summary_short = summary[:200] + "..." if len(summary) > 200 else summary
                            context_parts.append(f": {summary_short}")
                        context_parts.append("\n")
                except:
                    continue
        
        # 4. 关系信息
        if len(relationships) > 0:
            context_parts.append("\n## 相关关系：\n")
            for idx, rel in relationships.head(5).iterrows():
                try:
                    source = self._safe_get_value(rel.get('source', ''), "")
                    target = self._safe_get_value(rel.get('target', ''), "")
                    relation_type = self._safe_get_value(rel.get('relationship', ''), "")
                    
                    # 获取实体名称
                    source_entity = self.entities[self.entities['id'] == source]
                    target_entity = self.entities[self.entities['id'] == target]
                    
                    source_name = self._safe_get_value(source_entity.iloc[0]['title'], "") if len(source_entity) > 0 else source
                    target_name = self._safe_get_value(target_entity.iloc[0]['title'], "") if len(target_entity) > 0 else target
                    
                    if relation_type:
                        context_parts.append(f"- {source_name} {relation_type} {target_name}\n")
                except:
                    continue
        
        context = "".join(context_parts)
        
        print(f"[DEBUG] 本地搜索 - API Key 配置: {'是' if self.llm_client.api_key else '否'}")
        print(f"[DEBUG] 本地搜索 - Context 长度: {len(context)} 字符")
        print(f"[DEBUG] 本地搜索 - Context 预览: {context[:200]}...")
        
        # 如果配置了 DeepSeek API，使用 LLM 生成答案
        if self.llm_client.api_key:
            if not context:
                # 即使没有 context，也尝试用 LLM 回答（基于问题本身）
                context = "未找到直接相关的上下文信息，但请尝试根据您对中央苏区历史的了解回答问题。"
            
            prompt = f"""请根据以下关于中央苏区历史的上下文信息，回答用户的问题。

用户问题：{question}

上下文信息：
{context}

请基于以上上下文信息，用自然、准确、流畅的中文回答问题。如果上下文中没有直接答案，请根据相关信息进行合理推断。如果确实没有相关信息，请诚实说明。"""
            
            print(f"[DEBUG] 本地搜索 - 准备调用 DeepSeek API，Prompt 长度: {len(prompt)} 字符")
            llm_answer = self._call_llm_api(prompt, max_tokens=1500)
            if llm_answer:
                print(f"[DEBUG] 本地搜索 - LLM 生成答案成功，长度: {len(llm_answer)} 字符")
                return llm_answer
            else:
                print(f"[DEBUG] 本地搜索 - LLM 调用失败，降级到文本拼接")
        else:
            print(f"[DEBUG] 本地搜索 - 未配置 API Key，使用文本拼接")
        
        # 如果没有配置 API 或调用失败，使用文本拼接方式
        answer = "## 本地检索结果\n\n"
        
        if len(entities) > 0:
            main_entity = entities.iloc[0]
            entity_title = self._safe_get_value(main_entity.get('title', ''), "")
            entity_desc = self._safe_get_value(main_entity.get('description', ''), "")
            
            if entity_title:
                answer += f"根据《中央苏区史》的记载，关于**{entity_title}**的信息：\n\n"
                if entity_desc:
                    answer += f"{entity_desc}\n\n"
        
        if len(text_units) > 0:
            answer += "**相关信息：**\n\n"
            for idx, text_unit in text_units.head(3).iterrows():
                try:
                    text_content = self._safe_get_value(text_unit.get('text', ''), "")
                    if text_content:
                        if len(text_content) > 400:
                            text_content = text_content[:400] + "..."
                        answer += f"> {text_content}\n\n"
                except:
                    continue
        
        answer += "\n---\n*以上内容来自《中央苏区史》*"
        return answer
    
    def _get_graph_from_neo4j(self, entity_titles: List[str]) -> Dict[str, Any]:
        """从 Neo4j 获取图谱可视化数据（增强版：包含邻居节点）"""
        if not self.neo4j_driver or not entity_titles:
            return {"nodes": [], "edges": []}
        
        try:
            with self.neo4j_driver.session() as session:
                # 步骤1: 获取核心实体
                core_query = """
                MATCH (e:Entity)
                WHERE e.title IN $titles
                RETURN e.id as id, e.title as title, e.type as type, 
                       e.description as description
                LIMIT 15
                """
                
                core_result = session.run(core_query, titles=entity_titles[:15])
                nodes_dict = {}
                
                for record in core_result:
                    node_id = record['id']
                    if node_id:
                        desc = record['description']
                        title = record['title']
                        print(f"[DEBUG] Neo4j返回节点: {title}, description={'有' if desc else '无'}, 长度={len(desc) if desc else 0}")
                        nodes_dict[node_id] = {
                            "id": node_id,
                            "label": title or '',
                            "type": (record['type'] or 'unknown').lower(),
                            "description": desc or ''
                        }
                
                if not nodes_dict:
                    return {"nodes": [], "edges": []}
                
                core_ids = list(nodes_dict.keys())
                print(f"[DEBUG] 核心实体: {len(core_ids)} 个")
                
                # 步骤2: 获取1-hop邻居
                neighbor_query = """
                MATCH (core:Entity)-[r:RELATED_TO]-(neighbor:Entity)
                WHERE core.id IN $core_ids
                RETURN DISTINCT neighbor.id as id, neighbor.title as title, 
                       neighbor.type as type, neighbor.description as description
                LIMIT 20
                """
                
                neighbor_result = session.run(neighbor_query, core_ids=core_ids)
                
                for record in neighbor_result:
                    node_id = record['id']
                    if node_id and node_id not in nodes_dict:
                        nodes_dict[node_id] = {
                            "id": node_id,
                            "label": record['title'] or '',
                            "type": (record['type'] or 'unknown').lower(),
                            "description": record['description'] or ''
                        }
                
                print(f"[DEBUG] 总节点数（含邻居）: {len(nodes_dict)} 个")
                
                # 步骤3: 获取所有节点间的关系
                all_node_ids = list(nodes_dict.keys())
                edges_query = """
                MATCH (e1:Entity)-[r:RELATED_TO]-(e2:Entity)
                WHERE e1.id IN $node_ids AND e2.id IN $node_ids
                AND e1.id < e2.id
                RETURN DISTINCT e1.id as from_id, e2.id as to_id, 
                       r.description as label
                LIMIT 50
                """
                
                edges_result = session.run(edges_query, node_ids=all_node_ids)
                edges = []
                
                for record in edges_result:
                    if record['from_id'] and record['to_id']:
                        edges.append({
                            "from": record['from_id'],
                            "to": record['to_id'],
                            "label": (record['label'] or '相关')[:15]
                        })
                
                print(f"[DEBUG] 图谱数据: {len(nodes_dict)} 个节点, {len(edges)} 条边")
                
                # 打印样本节点的description（用于前端调试）
                sample_nodes = list(nodes_dict.values())[:3]
                print(f"[DEBUG] === 返回给前端的数据样本 ===")
                for node in sample_nodes:
                    desc = node.get('description', '')
                    print(f"[DEBUG] 节点: {node['label']}")
                    print(f"[DEBUG]   - description字段存在: {'是' if 'description' in node else '否'}")
                    print(f"[DEBUG]   - description值: {desc[:100] if desc else '空字符串'}...")
                    print(f"[DEBUG]   - description长度: {len(desc)}")
                
                return {
                    "nodes": list(nodes_dict.values()),
                    "edges": edges
                }
        
        except Exception as e:
            print(f"从 Neo4j 获取图谱数据错误: {e}")
            import traceback
            traceback.print_exc()
            return {"nodes": [], "edges": []}
    
    def get_graph_data(self, entity_titles: List[str]) -> Dict[str, Any]:
        """获取指定实体的图谱数据"""
        return self._get_graph_from_neo4j(entity_titles)
    
    def get_common_questions(self) -> List[str]:
        """获取常见问题推荐"""
        return [
            "中央苏区成立时间",
            "中华苏维埃第一次全国代表大会召开地点",
            "中央苏区的主要领导人物有哪些？",
            "苏区土地改革政策的主要内容",
            "中央苏区的历史意义"
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return {
            "entities_count": len(self.entities),
            "relationships_count": len(self.relationships),
            "communities_count": len(self.communities),
            "text_units_count": len(self.text_units),
            "documents_count": len(self.documents)
        }
    
    def close(self):
        """关闭连接"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

