@echo off
chcp 65001 >nul
echo ========================================
echo 安全智能审核系统 - 安全启动脚本
echo ========================================
echo.
echo 重要提示：
echo 1. 请先设置DEEPSEEK_API_KEY环境变量
echo 2. 不要在脚本中硬编码API密钥
echo 3. 建议使用.env文件管理敏感信息
echo.

echo 检查环境变量...
if "%DEEPSEEK_API_KEY%"=="" (
    echo   警告：DEEPSEEK_API_KEY环境变量未设置
    echo   请先设置环境变量：
    echo   set DEEPSEEK_API_KEY=your_api_key_here
    echo   或者创建.env文件
    echo.
)

echo 设置Python路径...
set PYTHONPATH=%cd%\backend

echo 检查端口占用...
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
    start "AI审核API" cmd /k "cd /d %cd% && python backend/ai_audit_api_deterministic.py"
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