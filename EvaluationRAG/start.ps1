Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动评估 RAG 系统" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] 启动后端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py"
Start-Sleep -Seconds 3

Write-Host "[2/2] 启动前端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "服务启动完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "后端: http://localhost:8000" -ForegroundColor White
Write-Host "前端: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "提示: 两个新窗口已打开,关闭窗口即可停止对应服务" -ForegroundColor Gray
