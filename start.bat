@echo off
echo ========================================
echo 安全智能审核系统 - 纯净版
echo ========================================
echo.

echo 1. 启动主后端服务 (端口: 8000)
echo   正在创建必要的目录结构...
if not exist "data\uploads" mkdir "data\uploads"
start cmd /k "cd /d %~dp0 && python backend/main_fixed.py"

timeout /t 3 /nobreak >nul

echo.
echo 2. 启动AI审核服务 (端口: 8002) - 可选
echo   如需AI审核功能，请手动启动:
echo   cd /d %~dp0
echo   python backend/ai_audit_api_deterministic.py
echo.

echo 3. 系统访问地址:
echo   主服务: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo   前端页面: http://localhost:8000/static/dashboard.html
echo.

echo 4. 核心功能页面:
echo   - 仪表板: http://localhost:8000/static/dashboard.html
echo   - SOP管理: http://localhost:8000/static/sops.html
echo   - 标准库: http://localhost:8000/static/standards.html
echo   - 部门管理: http://localhost:8000/static/departments.html
echo   - 分类管理: http://localhost:8000/static/categories.html
echo.

echo 5. 注意事项:
echo   - 确保已安装Python 3.7+
echo   - 首次运行可能需要安装依赖: pip install fastapi uvicorn sqlite3
echo   - AI审核需要配置DeepSeek API密钥
echo.

pause