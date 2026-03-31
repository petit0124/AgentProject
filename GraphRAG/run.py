# GraphRAG 启动脚本
# 使用方法: python run.py

import sys
import subprocess
import os
from pathlib import Path

def check_environment():
    """检查环境配置"""
    print("=" * 60)
    print("GraphRAG 本地知识图谱 RAG Demo - 启动检查")
    print("=" * 60)
    print()
    
    # 检查 Python 版本
    print("[1/4] 检查 Python 版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 版本过低: {version.major}.{version.minor}")
        print("需要 Python 3.9 或更高版本")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    print()
    
    # 检查配置文件
    print("[2/4] 检查配置文件...")
    if not Path(".env").exists():
        print("⚠️  .env 文件不存在，从模板创建...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print()
            print("=" * 60)
            print("⚠️  重要提示")
            print("=" * 60)
            print("请编辑 .env 文件，填入您的 Azure OpenAI API 配置")
            print(f"文件位置: {Path('.env').absolute()}")
            print()
            input("配置完成后，按 Enter 继续...")
        else:
            print("❌ .env.example 文件不存在")
            return False
    print("✅ 配置文件存在")
    print()
    
    # 检查依赖
    print("[3/4] 检查依赖包...")
    try:
        import streamlit
        print("✅ Streamlit 已安装")
    except ImportError:
        print("⚠️  Streamlit 未安装，正在安装依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ 依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败")
            print("请手动运行: pip install -r requirements.txt")
            return False
    print()
    
    # 检查应用文件
    print("[4/4] 检查应用文件...")
    if not Path("app.py").exists():
        print("❌ app.py 文件不存在")
        return False
    print("✅ 应用文件存在")
    print()
    
    return True

def start_app():
    """启动应用"""
    print("=" * 60)
    print("正在启动 Streamlit 应用...")
    print()
    print("浏览器将自动打开: http://localhost:8501")
    print()
    print("提示:")
    print("  - 按 Ctrl+C 停止应用")
    print("  - 如需手动打开，请访问上述地址")
    print("=" * 60)
    print()
    
    try:
        # 使用 python -m streamlit 方式启动
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n\n应用已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n请尝试手动运行:")
        print(f"  {sys.executable} -m streamlit run app.py")
        return False
    
    return True

def main():
    """主函数"""
    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)
    
    # 检查环境
    if not check_environment():
        print("\n环境检查失败，无法启动应用")
        input("\n按 Enter 退出...")
        return
    
    # 启动应用
    start_app()

if __name__ == "__main__":
    main()
