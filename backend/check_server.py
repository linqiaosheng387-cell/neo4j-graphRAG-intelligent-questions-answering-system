"""
后端服务器诊断工具
用于检查服务器是否正常运行以及所有端点是否可访问
"""
import requests
import sys

def check_endpoint(url, method="GET", data=None):
    """检查端点是否可访问"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        return {
            "status": "✅ 成功",
            "status_code": response.status_code,
            "accessible": True
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "❌ 连接失败 - 服务器未运行",
            "status_code": None,
            "accessible": False
        }
    except requests.exceptions.Timeout:
        return {
            "status": "⏱️ 超时",
            "status_code": None,
            "accessible": False
        }
    except Exception as e:
        return {
            "status": f"❌ 错误: {str(e)}",
            "status_code": None,
            "accessible": False
        }

def main():
    print("=" * 80)
    print("🔍 中央苏区史问答系统 - 后端服务器诊断")
    print("=" * 80)
    print()
    
    base_url = "http://localhost:8084"
    
    # 检查端点列表
    endpoints = [
        ("根路径", f"{base_url}/", "GET", None),
        ("流式查询", f"{base_url}/api/query/stream", "POST", {"question": "测试", "mode": "global"}),
        ("普通查询", f"{base_url}/api/query", "POST", {"question": "测试", "mode": "global"}),
        ("统计信息", f"{base_url}/api/stats", "GET", None),
    ]
    
    all_ok = True
    
    for name, url, method, data in endpoints:
        print(f"检查 [{name}]")
        print(f"  URL: {method} {url}")
        result = check_endpoint(url, method, data)
        print(f"  状态: {result['status']}")
        if result['status_code']:
            print(f"  HTTP状态码: {result['status_code']}")
        print()
        
        if not result['accessible']:
            all_ok = False
    
    print("=" * 80)
    
    if not all_ok:
        print("❌ 发现问题！")
        print()
        print("可能的原因：")
        print("1. 后端服务器未启动")
        print("   解决方法: cd backend && python main.py")
        print()
        print("2. 服务器启动时出错")
        print("   检查: 查看运行 python main.py 时的错误信息")
        print()
        print("3. 端口被占用")
        print("   检查: netstat -ano | findstr :8084")
        print()
        print("4. 服务初始化失败")
        print("   检查: .env 文件是否配置正确")
        print("   检查: GraphRAG 数据文件是否存在")
        print()
    else:
        print("✅ 所有端点正常！")
    
    print("=" * 80)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

