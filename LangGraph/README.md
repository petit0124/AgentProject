# LangGraph多智能体深度研究系统

一个基于LangGraph的多智能体协作系统，能够进行深度网络研究、分析思考，并生成结构化的中文研究报告。

## ✨ 功能特性

- 🤖 **多智能体协作**: 四个专业Agent协同工作
  - Supervisor Agent: 任务分析与研究计划
  - Search Agent: 网络信息搜索
  - Research Agent: 深度分析思考
  - Writer Agent: 报告生成整合

- � **多轮迭代分析**: 智能识别信息缺口，自动进行深度研究
  - 可配置迭代轮数（1-5轮）
  - Research Agent自动评估信息完整性
  - 发现信息缺口时触发补充搜索
  - 每一轮分析都更加深入和全面

- �🔍 **深度研究能力**: 使用GPT-4o进行深入分析
- 🌐 **网络搜索**: 集成Tavily API获取最新信息
- 📊 **实时进度**: Streamlit界面展示研究过程
- 📝 **结构化报告**: Markdown格式，包含完整参考来源
- 🎨 **工作流可视化**: LangGraph图结构展示

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
AZURE_OPENAI_ENDPOINT=你的Azure OpenAI端点
AZURE_OPENAI_API_KEY=你的API密钥
MODEL_NAME=gpt-4o
TAVILY_API_KEY=你的Tavily API密钥
```

### 3. 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址：`http://localhost:8501`

## 📖 使用方法

1. **输入查询**: 在文本框中输入你想要研究的问题
2. **设置轮数**: 使用滑块选择最大迭代轮数（1-5轮）
   - 轮数越多，研究越深入
   - 系统会自动识别信息缺口并进行补充研究
3. **开始研究**: 点击"开始深度研究"按钮
4. **查看过程**: 实时查看各个Agent的工作进展
   - 研究计划制定
   - 网络搜索结果
   - 深度分析内容（包含迭代信息）
   - 补充问题识别
   - 报告生成过程
5. **获取报告**: 查看完整的研究报告并可下载

## 🏗️ 系统架构

```
用户查询
    ↓
Supervisor Agent (制定研究计划)
    ↓
┌───Search Agent (执行网络搜索)
│   ↓
│   Research Agent (深度分析)
│   ↓
│   [评估信息完整性]
│   ├── 需要更多信息 ─┘ (循环)
│   └── 信息充分
│       ↓
└───→ Writer Agent (生成报告)
    ↓
最终报告
```

## 📁 项目结构

```
LangGraph/
├── src/
│   ├── agents/          # Agent实现
│   │   ├── supervisor.py
│   │   ├── search_agent.py
│   │   ├── research_agent.py
│   │   └── writer_agent.py
│   ├── graph/           # LangGraph工作流
│   │   ├── state.py
│   │   └── workflow.py
│   ├── tools/           # 工具集成
│   │   └── tavily_search.py
│   └── config/          # 配置
│       └── llm_config.py
├── app.py              # Streamlit主应用
├── requirements.txt    # 依赖
└── .env               # 环境变量
```

## 🛠️ 技术栈

- **LangGraph**: 多智能体工作流编排
- **LangChain**: LLM工具链
- **Azure OpenAI**: GPT-4o模型
- **Streamlit**: Web界面框架
- **Tavily**: 网络搜索API

## 📝 示例查询

- "分析2024年人工智能的最新发展趋势"
- "比较LangChain和LangGraph的技术差异"
- "研究大语言模型在企业中的应用场景"
- "探讨Agent技术的未来发展方向"

## ⚙️ 环境要求

- Python 3.8+
- Azure OpenAI API访问权限
- Tavily API密钥

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！
