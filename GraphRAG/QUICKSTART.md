# 快速配置指南

## 🔧 配置步骤

### 1. 编辑 .env 文件

项目已自动创建 `.env` 文件，请按照以下说明填写：

```env
# ========== LLM 配置 ==========
# 将 curl 命令中的 endpoint 复制到这里
LLM_ENDPOINT=https://fxiaoke-azureopenai-02.openai.azure.com/openai/responses?api-version=2025-04-01-preview

# 模型名称
LLM_MODEL=azure02-gpt-5

# 将 curl 命令中 Bearer 后面的值复制到这里
LLM_API_KEY=7215c7fa8f0f4a4eb56ad02f066cc7a6

# ========== Embedding 配置 ==========
# Embedding endpoint
EMBEDDING_ENDPOINT=https://fxiaoke-azureopenai-01.openai.azure.com/openai/deployments/FXIAOKE-MODEL-text-embedding-ada-002/embeddings?api-version=2023-07-01-preview

# Embedding 模型名称
EMBEDDING_MODEL=FXIAOKE-MODEL-text-embedding-ada-002

# Embedding API key（注意这里是 api-key 认证）
EMBEDDING_API_KEY=8934d2ca8da74a2392cee6e8803a2f39
```

### 2. 测试 API 连接

```bash
python tests/test_api.py
```

**预期结果**：
```
✅ 配置验证通过

====================================
测试 LLM API
====================================

测试 1: 基本文本生成
✅ 成功!
响应: [LLM 的响应内容]

测试 2: 对话生成
✅ 成功!
响应: [LLM 的响应内容]

====================================
测试 Embedding API
====================================

测试 1: 单个文本 Embedding
✅ 成功!
Embedding 维度: 1536
前 5 个值: [0.123, -0.456, ...]

测试 2: 批量 Embedding
✅ 成功!
生成了 3 个 embeddings
每个维度: 1536

====================================
测试总结
====================================
LLM API: ✅ 通过
Embedding API: ✅ 通过

🎉 所有测试通过! 可以开始使用 GraphRAG 了。
```

### 3. 启动应用

**方式 1: 使用启动脚本（推荐）**
```bash
# Windows
start.bat
```

**方式 2: 手动启动**
```bash
streamlit run app.py
```

### 4. 开始使用

1. 浏览器自动打开 `http://localhost:8501`
2. 在 **📁 文档管理** 页面上传文档
3. 在 **🔗 知识图谱构建** 页面构建索引
4. 在 **💬 RAG 检索** 页面进行查询

## 📋 常见问题

### Q: 如何确认配置是否正确？

A: 在侧边栏点击 "🔌 测试 API 连接" 按钮，如果都显示绿色✅则配置正确。

### Q: 构建索引需要多长时间？

A: 取决于文档数量和大小。示例文档（2个小文档）大约需要 5-10 分钟。

### Q: API 调用会产生费用吗？

A: 是的，GraphRAG 会调用大量 API。建议先用少量文档测试。

### Q: 可以使用其他 LLM 吗？

A: 理论上可以，但需要修改适配器代码以支持不同的 API 格式。

## 🎯 快速测试流程

1. **上传示例文档**
   - `data/input/example_ai.md`
   - `data/input/example_kg.md`
   - 或者自己准备的文档

2. **使用默认参数构建**
   - Chunk Size: 300
   - Chunk Overlap: 50
   - Temperature: 0.0
   - Max Cluster Size: 10

3. **测试查询**
   - "人工智能有哪些应用领域？"
   - "什么是 GraphRAG？"
   - "知识图谱有什么挑战？"

---

配置完成后，享受使用 GraphRAG！🎉
