@echo off
echo ========================================
echo 启动评估 RAG 系统
echo ========================================
echo.

echo [1/2] 启动后端服务...
start "Backend Server" cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo 服务启动完成!
echo ========================================
echo 后端: http://localhost:8000
echo 前端: http://localhost:3000
echo.
echo 按任意键退出此窗口...
pause >nul
