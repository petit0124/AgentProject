# GraphRAG 本地知识图谱 RAG Demo

一个基于 Microsoft GraphRAG 的本地知识图谱 RAG 演示项目，支持多种文档格式，提供友好的 Web 界面。

## ✨ 功能特性

- 📁 **多格式文档支持**: txt、markdown、docx、pdf
- 🔗 **知识图谱构建**: 自动从文档中提取实体、关系和社区结构
- 💬 **双模式检索**: 
  - 本地检索 (Local Search): 基于实体和关系的精准检索
  - 全局检索 (Global Search): 基于社区摘要的宏观问答
- ⚙️ **灵活参数配置**: 可自定义分块大小、LLM 参数、聚类参数等
- 🎨 **友好的 Web 界面**: 基于 Streamlit 的现代化界面

## 📋 系统要求

- Python 3.9+
- Azure OpenAI API 访问权限

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入您的 API 配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 Azure OpenAI 配置:

```env
# LLM 配置
LLM_ENDPOINT=https://your-endpoint.openai.azure.com/...
LLM_MODEL=your-model-name
LLM_API_KEY=your-api-key

# Embedding 配置
EMBEDDING_ENDPOINT=https://your-endpoint.openai.azure.com/...
EMBEDDING_MODEL=your-embedding-model
EMBEDDING_API_KEY=your-embedding-api-key
```

### 3. 测试 API 连接

```bash
python tests/test_api.py
```

如果看到 "🎉 所有测试通过!"，说明配置正确。

### 4. 启动 Web 应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开（默认地址: http://localhost:8501）

## 📖 使用指南

### 步骤 1: 上传文档

1. 进入 **📁 文档管理** 页面
2. 点击文件上传按钮，选择一个或多个文档
3. 点击 **📥 处理上传的文件**
4. 查看已上传的文档列表

### 步骤 2: 构建知识图谱

1. 进入 **🔗 知识图谱构建** 页面
2. 根据需要调整参数：
   - **文本分块大小**: 控制每个文本块的大小（默认 300）
   - **分块重叠**: 相邻块之间的重叠字符数（默认 50）
   - **LLM 温度**: 控制生成的随机性（默认 0.0）
   - **最大簇大小**: 社区检测的簇大小（默认 10）
3. 点击 **🚀 开始构建知识图谱**
4. 等待构建完成（可能需要几分钟，取决于文档数量和大小）

### 步骤 3: 执行查询

1. 进入 **💬 RAG 检索** 页面
2. 在文本框中输入您的问题
3. 选择检索模式：
   - **本地检索**: 适合回答关于特定实体和关系的问题
   - **全局检索**: 适合回答需要综合理解的宏观问题
4. 调整检索参数（Top-K、温度等）
5. 点击 **🔎 执行查询**
6. 查看答案和相关上下文

## 🏗️ 项目结构

```
graphrag/
├── app.py                      # Streamlit 主应用
├── requirements.txt            # 项目依赖
├── .env.example               # 环境变量模板
├── README.md                  # 项目说明
├── src/
│   ├── api/                   # API 适配器
│   │   ├── azure_llm_adapter.py
│   │   └── azure_embedding_adapter.py
│   ├── document/              # 文档处理
│   │   └── processor.py
│   ├── graphrag/              # GraphRAG 集成
│   │   ├── indexer.py
│   │   └── query.py
│   └── config/                # 配置管理
│       └── settings.py
├── data/
│   ├── input/                 # 上传的文档
│   └── output/                # GraphRAG 索引输出
└── tests/
    └── test_api.py            # API 测试工具
```

## ⚙️ 参数说明

### 知识图谱构建参数

- **Chunk Size (文本分块大小)**: 
  - 范围: 100-1000
  - 推荐值: 300
  - 说明: 较小的值会产生更细粒度的知识，但会增加 API 调用次数

- **Chunk Overlap (分块重叠)**:
  - 范围: 0-200
  - 推荐值: 50
  - 说明: 避免重要信息在分块边界处丢失

- **LLM Temperature (温度)**:
  - 范围: 0.0-1.0
  - 推荐值: 0.0 (确定性输出)
  - 说明: 较高的值会产生更多样化但可能不太准确的结果

- **Max Cluster Size (最大簇大小)**:
  - 范围: 5-50
  - 推荐值: 10
  - 说明: 控制社区检测的粒度

### 检索参数

- **Search Type (检索类型)**:
  - Local: 基于文档中的具体实体和关系
  - Global: 基于整体理解和社区摘要

- **Top-K**: 返回最相关的 K 个结果

## 🔧 故障排除

### API 连接失败

1. 检查 `.env` 文件中的 endpoint 和 API key 是否正确
2. 确认网络可以访问 Azure OpenAI 服务
3. 运行 `python tests/test_api.py` 诊断问题

### 文档处理失败

1. 确认文件格式在支持的范围内（txt, md, docx, pdf）
2. 对于 PDF 文件，确保已安装 `pdfplumber` 或 `PyPDF2`
3. 对于 Word 文档，确保已安装 `python-docx`

### 索引构建失败

1. 检查是否有足够的 API 配额
2. 查看错误日志了解具体问题
3. 尝试减少文档数量或文档大小进行测试

## 📝 注意事项

⚠️ **API 成本**: GraphRAG 会调用大量 LLM API 来提取实体和生成摘要，请注意控制成本。建议先用少量小文档测试。

⚠️ **处理时间**: 索引构建时间取决于文档数量和大小，可能需要几分钟到几小时不等。

✅ **本地存储**: 构建好的知识图谱会保存在 `data/output/` 目录，无需重复构建。

## 🤝 技术栈

- **GraphRAG**: Microsoft GraphRAG 库
- **Web 框架**: Streamlit
- **文档处理**: python-docx, pdfplumber
- **API**: Azure OpenAI

## 📄 许可证

MIT License

## 👨‍💻 支持

如有问题，请查看日志文件或联系开发者。
