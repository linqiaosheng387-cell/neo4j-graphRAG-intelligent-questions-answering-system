"""
新前端服务器 - 对接现有的FastAPI后端
"""
from flask import Flask, render_template_string, send_from_directory
import os

app = Flask(__name__)

# 读取HTML文件
html_path = os.path.join(os.path.dirname(__file__), 'index_updated.html')
with open(html_path, 'r', encoding='utf-8') as f:
    HTML_TEMPLATE = f.read()

@app.route('/')
def index():
    """主页"""
    return HTML_TEMPLATE

@app.route('/test')
def test():
    """测试页面"""
    test_html_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'test_endpoint.html')
    if os.path.exists(test_html_path):
        with open(test_html_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "测试页面未找到", 404

@app.route('/favicon.ico')
def favicon():
    """图标"""
    return '', 204

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 中央苏区史智能问答系统 - 前端服务")
    print("=" * 80)
    print("📍 前端地址: http://localhost:5000")
    print("📍 后端API: http://localhost:8084")
    print("=" * 80)
    print("⚠️  请确保后端服务已启动！")
    print("   在另一个终端窗口运行:")
    print("   cd backend")
    print("   python main.py")
    print("=" * 80)
    print("✅ 前端服务器正在启动...")
    print("   访问: http://localhost:5000")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
