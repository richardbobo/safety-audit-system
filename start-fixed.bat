@echo off
chcp 65001 >nul
echo ========================================
echo 启动安全智能审核系统 - 修复版
echo ========================================
echo.

echo 1. 设置环境变量...
set DEEPSEEK_API_KEY=sk-b263c6b8ee8341ba8e2863f4f91aa492
set PYTHONPATH=%cd%\backend

echo 2. 检查端口占用...
netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo   端口8000已被占用，跳过主后端启动
) else (
    echo   启动主后端服务 (端口 8000)...
    start "主后端服务" cmd /k "cd /d %cd% && uvicorn backend.main_fixed:app --host 0.0.0.0 --port 8000 --reload"
    timeout /t 3 /nobreak >nul
)

netstat -ano | findstr :8002 >nul
if %errorlevel% equ 0 (
    echo   端口8002已被占用，跳过AI审核API启动
) else (
    echo   启动AI审核API服务 (端口 8002)...
    start "AI审核API" cmd /k "cd /d %cd% && python backend/ai_audit_api_fixed.py"
    timeout /t 3 /nobreak >nul
)

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo 访问地址：
echo 1. 主后端服务: http://localhost:8000
echo 2. 修复版整合应用: http://localhost:8000/static/safety-audit-app-fixed.html
echo 3. 调试页面: http://localhost:8000/static/debug-audit-result.html
echo 4. AI审核API: http://localhost:8002/health
echo.
echo 按任意键退出...
pause >nul