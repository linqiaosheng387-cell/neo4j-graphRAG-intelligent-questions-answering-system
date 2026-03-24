"""
日志管理 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from database import get_db
from models import UserAccessLog, SystemLog, IPStatistics

router = APIRouter(prefix="/api/logs", tags=["日志管理"])

# ==================== 获取访问日志 ====================
@router.get("/access")
def get_access_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    ip_address: str = Query(""),
    endpoint: str = Query(""),
    db: Session = Depends(get_db)
):
    """获取用户访问日志"""
    try:
        print(f"[日志API] 查询参数: page={page}, page_size={page_size}, ip_address={ip_address}, endpoint={endpoint}")
        
        # 使用原生 SQL 查询，避免 SQLAlchemy 缓存问题
        from sqlalchemy import text
        
        # 构建 WHERE 条件
        where_conditions = []
        params = {}
        
        if ip_address and ip_address.strip():
            where_conditions.append("ip_address LIKE :ip_address")
            params['ip_address'] = f"%{ip_address}%"
            print(f"[日志API] 按 IP 筛选: {ip_address}")
        
        if endpoint and endpoint.strip():
            where_conditions.append("endpoint LIKE :endpoint")
            params['endpoint'] = f"%{endpoint}%"
            print(f"[日志API] 按端点筛选: {endpoint}")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # 查询总数
        count_sql = text(f"SELECT COUNT(*) FROM user_access_logs WHERE {where_clause}")
        total = db.execute(count_sql, params).scalar()
        print(f"[日志API] 查询结果总数: {total}")
        
        # 查询分页数据
        offset = (page - 1) * page_size
        query_sql = text(f"""
            SELECT id, ip_address, endpoint, method, status_code, response_time, device_info, user_agent, access_time
            FROM user_access_logs
            WHERE {where_clause}
            ORDER BY access_time DESC
            LIMIT :limit OFFSET :offset
        """)
        params['limit'] = page_size
        params['offset'] = offset
        
        result = db.execute(query_sql, params)
        logs = result.fetchall()
        print(f"[日志API] 当前页记录数: {len(logs)}")
        
        # 转换为字典列表
        logs_data = [
            {
                "id": log[0],
                "ip_address": log[1],
                "endpoint": log[2],
                "method": log[3],
                "status_code": log[4],
                "response_time": log[5],
                "device_info": log[6],
                "user_agent": log[7],
                "access_time": log[8].isoformat() if log[8] else None
            }
            for log in logs
        ]
        
        print(f"[日志API] ✅ 成功返回 {len(logs_data)} 条记录")
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": logs_data
        }
    except Exception as e:
        print(f"[日志API] ❌ 获取访问日志失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "data": [],
            "error": str(e)
        }

# ==================== 获取访问统计 ====================
@router.get("/access/stats")
def get_access_stats(db: Session = Depends(get_db)):
    """获取访问统计信息"""
    try:
        # 总访问次数
        total_visits = db.query(func.count(UserAccessLog.id)).scalar() or 0
        
        # 唯一 IP 数
        unique_ips = db.query(func.count(func.distinct(UserAccessLog.ip_address))).scalar() or 0
        
        return {
            "total_visits": total_visits,
            "unique_ips": unique_ips
        }
    except Exception as e:
        print(f"❌ 获取访问统计失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "total_visits": 0,
            "unique_ips": 0,
            "error": str(e)
        }

# ==================== 获取热门 IP ====================
@router.get("/access/top-ips")
def get_top_ips(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取热门 IP 排名"""
    try:
        top_ips = db.query(IPStatistics).order_by(
            desc(IPStatistics.visit_count)
        ).limit(limit).all()
        
        # 转换为字典列表
        ips_data = [
            {
                "id": ip.id,
                "ip_address": ip.ip_address,
                "visit_count": ip.visit_count,
                "device_info": ip.device_info,
                "first_access_time": ip.first_access_time.isoformat() if ip.first_access_time else None,
                "last_access_time": ip.last_access_time.isoformat() if ip.last_access_time else None
            }
            for ip in top_ips
        ]
        
        return {
            "total": len(ips_data),
            "data": ips_data
        }
    except Exception as e:
        print(f"❌ 获取热门 IP 失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "total": 0,
            "data": [],
            "error": str(e)
        }

# ==================== 获取 IP 统计 ====================
@router.get("/access/ip-stats/{ip_address}")
def get_ip_stats(
    ip_address: str,
    db: Session = Depends(get_db)
):
    """获取特定 IP 的统计信息"""
    ip_stat = db.query(IPStatistics).filter(
        IPStatistics.ip_address == ip_address
    ).first()
    
    if not ip_stat:
        return {
            "ip_address": ip_address,
            "visit_count": 0,
            "device_info": None,
            "first_access_time": None,
            "last_access_time": None
        }
    
    return ip_stat

# ==================== 获取系统日志 ====================
@router.get("/system")
def get_system_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    log_level: str = Query(""),
    module: str = Query(""),
    db: Session = Depends(get_db)
):
    """获取系统日志"""
    try:
        query = db.query(SystemLog)
        
        # 筛选条件
        if log_level and log_level.strip():
            query = query.filter(SystemLog.log_level == log_level)
        if module and module.strip():
            query = query.filter(SystemLog.module.contains(module))
        
        # 总数
        total = query.count()
        
        # 分页
        logs = query.order_by(desc(SystemLog.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": logs
        }
    except Exception as e:
        print(f"❌ 获取系统日志失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "data": [],
            "error": str(e)
        }

# ==================== 清空日志 ====================
@router.delete("/{log_type}")
def clear_logs(
    log_type: str,
    db: Session = Depends(get_db)
):
    """清空日志（system 或 access）"""
    try:
        if log_type == "system":
            db.query(SystemLog).delete()
        elif log_type == "access":
            db.query(UserAccessLog).delete()
            db.query(IPStatistics).delete()
        else:
            return {"error": "Invalid log type"}
        
        db.commit()
        return {"message": f"{log_type} logs cleared"}
    except Exception as e:
        print(f"❌ 清空日志失败: {e}")
        import traceback
        print(traceback.format_exc())
        db.rollback()
        return {"error": str(e)}

# ==================== 获取错误日志（运维监控） ====================
@router.get("/errors")
def get_error_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    log_level: str = Query(""),
    module: str = Query(""),
    db: Session = Depends(get_db)
):
    """获取系统错误日志"""
    try:
        print(f"[错误日志API] 查询参数: page={page}, page_size={page_size}, log_level={log_level}, module={module}")
        
        # 使用原生 SQL 查询
        from sqlalchemy import text
        
        # 构建 WHERE 条件
        where_conditions = ["log_level = 'ERROR'"]  # 只查询ERROR级别的日志
        params = {}
        
        if module and module.strip():
            where_conditions.append("module LIKE :module")
            params['module'] = f"%{module}%"
            print(f"[错误日志API] 按模块筛选: {module}")
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询总数
        count_sql = text(f"SELECT COUNT(*) FROM system_logs WHERE {where_clause}")
        total = db.execute(count_sql, params).scalar()
        print(f"[错误日志API] 查询结果总数: {total}")
        
        # 查询分页数据
        offset = (page - 1) * page_size
        query_sql = text(f"""
            SELECT id, log_level, module, message, stack_trace, solution, created_at
            FROM system_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        params['limit'] = page_size
        params['offset'] = offset
        
        result = db.execute(query_sql, params)
        logs = result.fetchall()
        print(f"[错误日志API] 当前页记录数: {len(logs)}")
        
        # 转换为字典列表
        logs_data = [
            {
                "id": log[0],
                "log_level": log[1],
                "module": log[2],
                "message": log[3],
                "stack_trace": log[4],
                "solution": log[5],
                "created_at": log[6].isoformat() if log[6] else None
            }
            for log in logs
        ]
        
        print(f"[错误日志API] ✅ 成功返回 {len(logs_data)} 条记录")
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": logs_data
        }
    except Exception as e:
        print(f"[错误日志API] ❌ 获取错误日志失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "data": [],
            "error": str(e)
        }

# ==================== 获取错误统计 ====================
@router.get("/errors/stats")
def get_error_stats(db: Session = Depends(get_db)):
    """获取错误统计信息"""
    try:
        from sqlalchemy import text
        
        # 查询总错误数
        total_sql = text("SELECT COUNT(*) FROM system_logs WHERE log_level = 'ERROR'")
        total_errors = db.execute(total_sql).scalar()
        
        # 查询今天的错误数
        today_sql = text("""
            SELECT COUNT(*) FROM system_logs 
            WHERE log_level = 'ERROR' AND DATE(created_at) = CURDATE()
        """)
        today_errors = db.execute(today_sql).scalar()
        
        # 查询按模块分类的错误数
        module_sql = text("""
            SELECT module, COUNT(*) as count 
            FROM system_logs 
            WHERE log_level = 'ERROR'
            GROUP BY module
            ORDER BY count DESC
            LIMIT 5
        """)
        module_results = db.execute(module_sql).fetchall()
        
        module_stats = [
            {"module": row[0] or "unknown", "count": row[1]}
            for row in module_results
        ]
        
        # 查询最近的错误
        recent_sql = text("""
            SELECT message, created_at 
            FROM system_logs 
            WHERE log_level = 'ERROR'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_results = db.execute(recent_sql).fetchall()
        
        recent_errors = [
            {"message": row[0], "time": row[1].isoformat() if row[1] else None}
            for row in recent_results
        ]
        
        return {
            "total_errors": total_errors,
            "today_errors": today_errors,
            "module_stats": module_stats,
            "recent_errors": recent_errors
        }
    except Exception as e:
        print(f"❌ 获取错误统计失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "total_errors": 0,
            "today_errors": 0,
            "module_stats": [],
            "recent_errors": [],
            "error": str(e)
        }
