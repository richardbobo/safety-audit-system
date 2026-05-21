@echo off
chcp 65001 >nul
echo ========================================
echo Safety Audit System - Clean Version
echo ========================================
echo.

echo 1. Starting main backend service (port: 8000)
echo   Creating necessary directory structure...
if not exist "data\uploads" mkdir "data\uploads"
start cmd /k "cd /d %~dp0 && py backend/main_fixed.py"

timeout /t 3 /nobreak >nul

echo.
echo 2. Starting AI audit service (port: 8002) - Optional
echo   For AI audit function, please start manually:
echo   cd /d %~dp0
echo   py backend/ai_audit_api_deterministic.py
echo.

echo 3. System access addresses:
echo   Main service: http://localhost:8000
echo   API docs: http://localhost:8000/docs
echo   Frontend: http://localhost:8000/static/dashboard.html
echo.

echo 4. Core function pages:
echo   - Dashboard: http://localhost:8000/static/dashboard.html
echo   - SOP Management: http://localhost:8000/static/sops.html
echo   - Standards Library: http://localhost:8000/static/standards.html
echo   - Department Management: http://localhost:8000/static/departments.html
echo   - Category Management: http://localhost:8000/static/categories.html
echo.

echo 5. Notes:
echo   - Ensure Python 3.7+ is installed
echo   - First run may require dependencies: pip install -r requirements.txt
echo   - AI audit requires DeepSeek API key configuration
echo   - Default login: admin / admin123
echo.

pause