@echo off
chcp 65001 >nul
echo ====================================
echo GraphRAG 本地知识图谱 RAG Demo
echo ====================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或未添加到 PATH
    echo 请安装 Python 3.9+ 并添加到系统 PATH
    pause
    exit /b 1
)

echo [1/4] 检查虚拟环境...
if exist ".venv\Scripts\activate.bat" (
    echo [✓] 发现虚拟环境，正在激活...
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [错误] 虚拟环境激活失败
        pause
        exit /b 1
    )
    echo [✓] 虚拟环境已激活
) else (
    echo [信息] 未发现虚拟环境，使用全局 Python 环境
)

echo [2/4] 检查配置文件...
if not exist ".env" (
    echo [警告] .env 文件不存在，从 .env.example 复制...
    copy .env.example .env >nul
    echo.
    echo ====================================
    echo [重要] 请编辑 .env 文件
    echo ====================================
    echo 请填入您的 Azure OpenAI API 配置，然后重新运行此脚本
    echo 配置文件位置: %CD%\.env
    echo.
    pause
    exit /b 0
)
echo [✓] 配置文件存在

echo [3/4] 检查依赖包...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [信息] Streamlit 未安装，正在安装依赖包...
    echo 这可能需要几分钟，请耐心等待...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        echo 请检查网络连接和 pip 配置
        pause
        exit /b 1
    )
    echo [✓] 依赖包安装完成
) else (
    echo [✓] 依赖包已安装
)

echo [4/4] 启动应用...
echo.
echo ====================================
echo 正在启动 Streamlit 应用...
echo 浏览器将自动打开 http://localhost:8501
echo.
echo 提示：
echo - 如需停止应用，请按 Ctrl+C
echo - 如窗口关闭，请在浏览器中手动访问上述地址
echo ====================================
echo.

REM 使用 python -m 方式运行，更可靠
python -m streamlit run app.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请尝试手动运行：
    echo    python -m streamlit run app.py
    echo.
    pause
)

