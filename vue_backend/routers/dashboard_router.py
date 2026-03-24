"""
数据面板 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from database import get_db
from models import (
    QARecord, UserAccessLog, IPStatistics,
    RealTimeQuestion, User, KnowledgeGraph
)

router = APIRouter(prefix="/api/dashboard", tags=["数据面板"])

# ==================== 获取总体统计 ====================
@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_db)):
    """获取仪表板总体统计信息"""
    
    # 总用户数
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # 总问答数
    total_qa = db.query(func.count(QARecord.id)).scalar() or 0
    
    # 已完成问答数
    completed_qa = db.query(func.count(QARecord.id)).filter(
        QARecord.status == "completed"
    ).scalar() or 0
    
    # 知识图谱数
    total_graphs = db.query(func.count(KnowledgeGraph.id)).scalar() or 0
    
    # 活跃图谱数
    active_graphs = db.query(func.count(KnowledgeGraph.id)).filter(
        KnowledgeGraph.status == "active"
    ).scalar() or 0
    
    # 总访问次数
    total_visits = db.query(func.count(UserAccessLog.id)).scalar() or 0
    
    # 唯一IP数
    unique_ips = db.query(func.count(func.distinct(UserAccessLog.ip_address))).scalar() or 0
    
    return {
        "total_users": total_users,
        "total_qa": total_qa,
        "completed_qa": completed_qa,
        "total_graphs": total_graphs,
        "active_graphs": active_graphs,
        "total_visits": total_visits,
        "unique_ips": unique_ips
    }

# ==================== 获取今日统计 ====================
@router.get("/today-stats")
def get_today_stats(db: Session = Depends(get_db)):
    """获取今日统计信息"""
    today = datetime.utcnow().date()
    
    # 今日问答数
    today_qa = db.query(func.count(QARecord.id)).filter(
        func.date(QARecord.created_at) == today
    ).scalar() or 0
    
    # 今日访问数
    today_visits = db.query(func.count(UserAccessLog.id)).filter(
        func.date(UserAccessLog.access_time) == today
    ).scalar() or 0
    
    # 今日新用户
    today_users = db.query(func.count(User.id)).filter(
        func.date(User.created_at) == today
    ).scalar() or 0
    
    # 今日唯一IP
    today_unique_ips = db.query(func.count(func.distinct(UserAccessLog.ip_address))).filter(
        func.date(UserAccessLog.access_time) == today
    ).scalar() or 0
    
    return {
        "date": str(today),
        "today_qa": today_qa,
        "today_visits": today_visits,
        "today_users": today_users,
        "today_unique_ips": today_unique_ips
    }

# ==================== 获取最近7天访问趋势 ====================
@router.get("/visit-trend")
def get_visit_trend(db: Session = Depends(get_db)):
    """获取最近7天的访问趋势"""
    trend_data = []
    
    for i in range(6, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        
        visits = db.query(func.count(UserAccessLog.id)).filter(
            func.date(UserAccessLog.access_time) == date
        ).scalar() or 0
        
        qa_count = db.query(func.count(QARecord.id)).filter(
            func.date(QARecord.created_at) == date
        ).scalar() or 0
        
        trend_data.append({
            "date": str(date),
            "visits": visits,
            "qa_count": qa_count
        })
    
    return {"trend": trend_data}

# ==================== 获取热门IP ====================
@router.get("/top-ips")
def get_top_ips(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取访问次数最多的IP地址"""
    top_ips = db.query(
        IPStatistics.ip_address,
        IPStatistics.visit_count,
        IPStatistics.device_info,
        IPStatistics.last_access_time
    ).order_by(desc(IPStatistics.visit_count)).limit(limit).all()
    
    return {
        "total": len(top_ips),
        "data": [
            {
                "ip_address": ip[0],
                "visit_count": ip[1],
                "device_info": ip[2],
                "last_access_time": ip[3]
            }
            for ip in top_ips
        ]
    }

# ==================== 获取最近问题 ====================
@router.get("/recent-questions")
def get_recent_questions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取最近提出的问题（实时更新）"""
    questions = db.query(
        RealTimeQuestion.id,
        RealTimeQuestion.question,
        RealTimeQuestion.ip_address,
        RealTimeQuestion.created_at,
        User.username
    ).outerjoin(User, RealTimeQuestion.user_id == User.id).order_by(
        desc(RealTimeQuestion.created_at)
    ).limit(limit).all()
    
    return {
        "total": len(questions),
        "data": [
            {
                "id": q[0],
                "question": q[1],
                "ip_address": q[2],
                "created_at": q[3],
                "username": q[4]
            }
            for q in questions
        ]
    }

# ==================== 获取问答完成率 ====================
@router.get("/qa-completion-rate")
def get_qa_completion_rate(db: Session = Depends(get_db)):
    """获取问答完成率"""
    total_qa = db.query(func.count(QARecord.id)).scalar() or 0
    
    if total_qa == 0:
        return {
            "total_qa": 0,
            "completed": 0,
            "pending": 0,
            "error": 0,
            "completion_rate": 0.0
        }
    
    completed = db.query(func.count(QARecord.id)).filter(
        QARecord.status == "completed"
    ).scalar() or 0
    
    pending = db.query(func.count(QARecord.id)).filter(
        QARecord.status == "pending"
    ).scalar() or 0
    
    error = db.query(func.count(QARecord.id)).filter(
        QARecord.status == "error"
    ).scalar() or 0
    
    completion_rate = (completed / total_qa * 100) if total_qa > 0 else 0
    
    return {
        "total_qa": total_qa,
        "completed": completed,
        "pending": pending,
        "error": error,
        "completion_rate": round(completion_rate, 2)
    }

# ==================== 获取平均响应时间 ====================
@router.get("/avg-response-time")
def get_avg_response_time(db: Session = Depends(get_db)):
    """获取平均响应时间"""
    avg_time = db.query(func.avg(QARecord.response_time)).filter(
        QARecord.response_time.isnot(None)
    ).scalar() or 0
    
    # 最快响应
    min_time = db.query(func.min(QARecord.response_time)).filter(
        QARecord.response_time.isnot(None)
    ).scalar() or 0
    
    # 最慢响应
    max_time = db.query(func.max(QARecord.response_time)).filter(
        QARecord.response_time.isnot(None)
    ).scalar() or 0
    
    return {
        "avg_response_time": round(avg_time, 2),
        "min_response_time": min_time,
        "max_response_time": max_time
    }

# ==================== 获取用户活跃度 ====================
@router.get("/user-activity")
def get_user_activity(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取最活跃的用户"""
    active_users = db.query(
        User.id,
        User.username,
        func.count(QARecord.id).label('qa_count')
    ).outerjoin(QARecord, User.id == QARecord.user_id).group_by(
        User.id, User.username
    ).order_by(desc('qa_count')).limit(limit).all()
    
    return {
        "total": len(active_users),
        "data": [
            {
                "user_id": u[0],
                "username": u[1],
                "qa_count": u[2] or 0
            }
            for u in active_users
        ]
    }

# ==================== 获取图谱使用统计 ====================
@router.get("/graph-usage")
def get_graph_usage(db: Session = Depends(get_db)):
    """获取知识图谱使用统计"""
    graphs = db.query(
        KnowledgeGraph.id,
        KnowledgeGraph.name,
        KnowledgeGraph.status,
        func.count(QARecord.id).label('usage_count')
    ).outerjoin(QARecord, KnowledgeGraph.id == QARecord.graph_id).group_by(
        KnowledgeGraph.id, KnowledgeGraph.name, KnowledgeGraph.status
    ).order_by(desc('usage_count')).all()
    
    return {
        "total": len(graphs),
        "data": [
            {
                "graph_id": g[0],
                "name": g[1],
                "status": g[2],
                "usage_count": g[3] or 0
            }
            for g in graphs
        ]
    }

# ==================== 获取访问地域分布（基于IP） ====================
@router.get("/geo-distribution")
def get_geo_distribution(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取访问地域分布（基于IP统计）"""
    ip_stats = db.query(
        IPStatistics.ip_address,
        IPStatistics.visit_count,
        IPStatistics.device_info
    ).order_by(desc(IPStatistics.visit_count)).limit(limit).all()
    
    return {
        "total": len(ip_stats),
        "data": [
            {
                "ip_address": ip[0],
                "visit_count": ip[1],
                "device_info": ip[2]
            }
            for ip in ip_stats
        ]
    }

# ==================== 获取时间段统计 ====================
@router.get("/time-period-stats")
def get_time_period_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """获取不同时间段的访问和问答统计"""
    try:
        from sqlalchemy import text
        from datetime import datetime, timedelta
        
        # 从 qa_records 和 user_access_logs 表查询最近N天的数据，按时间段统计
        # MySQL 不支持 FULL OUTER JOIN，使用 UNION 替代
        query_sql = text("""
            SELECT 
                DATE(created_at) as date,
                HOUR(created_at) as hour,
                SUM(qa_count) as qa_count,
                SUM(visit_count) as visit_count
            FROM (
                -- 问答记录统计
                SELECT 
                    DATE(created_at) as created_at,
                    HOUR(created_at) as hour,
                    COUNT(*) as qa_count,
                    0 as visit_count
                FROM qa_records
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
                GROUP BY DATE(created_at), HOUR(created_at)
                
                UNION ALL
                
                -- 访问日志统计
                SELECT 
                    DATE(access_time) as created_at,
                    HOUR(access_time) as hour,
                    0 as qa_count,
                    COUNT(*) as visit_count
                FROM user_access_logs
                WHERE access_time >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
                GROUP BY DATE(access_time), HOUR(access_time)
            ) combined
            GROUP BY DATE(created_at), HOUR(created_at)
            ORDER BY date DESC, hour ASC
        """)
        
        results = db.execute(query_sql, {"days": days}).fetchall()
        
        # 按日期和时间段组织数据
        data_by_date = {}
        for row in results:
            date = str(row[0])
            hour = row[1]
            qa_count = row[2] if row[2] else 0
            visit_count = row[3] if row[3] else 0
            
            # 将小时转换为时间段标签
            if hour < 6:
                period = "00-06"
                period_label = "00:00-05:59"
            elif hour < 12:
                period = "06-12"
                period_label = "06:00-11:59"
            elif hour < 18:
                period = "12-18"
                period_label = "12:00-17:59"
            else:
                period = "18-24"
                period_label = "18:00-23:59"
            
            if date not in data_by_date:
                data_by_date[date] = {}
            
            # 累加同一时间段的问答数和访问数
            if period not in data_by_date[date]:
                data_by_date[date][period] = {
                    "period": period,
                    "period_label": period_label,
                    "visit_count": 0,
                    "qa_count": 0
                }
            
            data_by_date[date][period]["qa_count"] += qa_count
            data_by_date[date][period]["visit_count"] += visit_count
        
        # 转换为列表格式并填充空时间段
        formatted_data = {}
        for date, periods in data_by_date.items():
            formatted_data[date] = list(periods.values())
        
        data_by_date = formatted_data
        
        # 如果没有数据，生成默认数据
        if not data_by_date:
            from datetime import datetime, timedelta
            today = datetime.utcnow().date()
            
            # 生成今天的默认数据
            default_periods = [
                {"period": "00-06", "period_label": "00:00-5:59"},
                {"period": "06-12", "period_label": "6:00-11:59"},
                {"period": "12-18", "period_label": "12:00-17:59"},
                {"period": "18-24", "period_label": "18:00-23:59"}
            ]
            
            data_by_date[str(today)] = default_periods
        
        return {
            "days": days,
            "data": data_by_date
        }
    except Exception as e:
        print(f"❌ 获取时间段统计失败: {e}")
        import traceback
        print(traceback.format_exc())
        
        # 返回默认数据
        from datetime import datetime
        today = datetime.utcnow().date()
        
        default_periods = [
            {"period": "00-06", "period_label": "00:00-5:59", "visit_count": 0, "qa_count": 0},
            {"period": "06-12", "period_label": "6:00-11:59", "visit_count": 0, "qa_count": 0},
            {"period": "12-18", "period_label": "12:00-17:59", "visit_count": 0, "qa_count": 0},
            {"period": "18-24", "period_label": "18:00-23:59", "visit_count": 0, "qa_count": 0}
        ]
        
        return {
            "days": days,
            "data": {str(today): default_periods},
            "error": str(e)
        }
