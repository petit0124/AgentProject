# 启动问题排查指南

如果双击 `start.bat` 后窗口立即关闭，请按照以下步骤排查：

## 方法 1: 使用 Python 启动脚本（推荐）

```bash
python run.py
```

或者双击 `run.py` 文件（如果已关联 Python）

## 方法 2: 手动启动（最可靠）

### 步骤 1: 打开命令提示符
在项目目录右键，选择"在终端中打开"

### 步骤 2: 激活虚拟环境（如果有）
```bash
.venv\Scripts\activate
```

### 步骤 3: 直接运行
```bash
python -m streamlit run app.py
```

## 方法 3: 修复后的批处理脚本

已更新 `start.bat`，现在会：
1. 自动检测并激活虚拟环境
2. 检查依赖包
3. 使用更可靠的 `python -m streamlit` 方式启动

再次双击 `start.bat` 试试。

## 常见问题

### Q: streamlit 命令未找到
**原因**: streamlit 安装在虚拟环境中，但未激活虚拟环境

**解决方案**:
```bash
# 激活虚拟环境后再运行
.venv\Scripts\activate
python -m streamlit run app.py
```

### Q: 窗口闪退
**原因**: 可能是配置文件缺失或脚本执行出错

**解决方案**:
1. 使用 `python run.py` 替代 `start.bat`
2. 在命令提示符中手动运行，查看错误信息

### Q: 端口被占用
**错误信息**: `Address already in use`

**解决方案**:
```bash
# 使用其他端口
python -m streamlit run app.py --server.port 8502
```

### Q: 依赖安装失败
**解决方案**:
```bash
# 手动安装依赖
pip install -r requirements.txt

# 如果网络问题，使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 代理连接错误
**错误信息**: `ProxyError('Unable to connect to proxy', RemoteDisconnected('Remote end closed connection without response'))`

**原因**: 系统配置了代理服务器，但代理无法正常工作或连接失败

**解决方案**:

1. **禁用代理**（如果不需要代理）:
   ```bash
   # Windows PowerShell
   $env:NO_PROXY="1"
   # 或者
   $env:DISABLE_PROXY="1"
   
   # Windows CMD
   set NO_PROXY=1
   set DISABLE_PROXY=1
   
   # Linux/Mac
   export NO_PROXY=1
   export DISABLE_PROXY=1
   ```

2. **配置正确的代理**（如果需要代理）:
   ```bash
   # Windows PowerShell
   $env:HTTP_PROXY="http://proxy.example.com:8080"
   $env:HTTPS_PROXY="http://proxy.example.com:8080"
   
   # Windows CMD
   set HTTP_PROXY=http://proxy.example.com:8080
   set HTTPS_PROXY=http://proxy.example.com:8080
   
   # Linux/Mac
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080
   ```

3. **在代码中配置**（永久设置）:
   创建或编辑 `.env` 文件，添加：
   ```
   NO_PROXY=1
   # 或者
   HTTP_PROXY=http://proxy.example.com:8080
   HTTPS_PROXY=http://proxy.example.com:8080
   ```

4. **检查网络连接**:
   - 确认可以访问 Azure OpenAI 端点
   - 检查防火墙设置
   - 验证代理服务器是否正常运行

**注意**: 代码已实现自动重试机制（最多3次），如果代理问题持续存在，请按照上述方法配置。

## 测试是否正常

启动成功的标志：
- 终端显示 "You can now view your Streamlit app in your browser."
- 浏览器自动打开 http://localhost:8501
- 看到 GraphRAG 应用界面

## 仍然无法解决？

请尝试完全重新安装：

```bash
# 1. 删除虚拟环境（如果有）
rmdir /s .venv

# 2. 创建新的虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
.venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动应用
python -m streamlit run app.py
```
