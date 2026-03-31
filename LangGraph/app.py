"""
LangGraph多智能体深度研究系统
Streamlit Web界面
"""
import streamlit as st
from src.graph.workflow import stream_research, create_research_workflow
import time


def main():
    """主应用程序"""
    
    # 页面配置
    st.set_page_config(
        page_title="LangGraph深度研究系统",
        page_icon="🔬",
        layout="wide"
    )
    
    # 标题
    st.title("🔬 LangGraph多智能体深度研究系统")
    st.markdown("---")
    
    # 侧边栏 - 系统架构说明
    with st.sidebar:
        st.header("📊 系统架构")
        st.markdown("""
        **多智能体协作架构**
        
        1. 🎯 **Supervisor Agent**
           - 任务分析与计划制定
        
        2. 🔍 **Search Agent**
           - 网络搜索与信息收集
        
        3. 🧠 **Research Agent**
           - 深度分析与思考
        
        4. 📝 **Writer Agent**
           - 报告生成与整合
        
        **技术栈**
        - LangGraph (工作流编排)
        - Azure OpenAI GPT-4o
        - Tavily Search API
        - Streamlit (界面)
        """)
        
        st.markdown("---")
        st.markdown("### 💡 示例查询")
        example_queries = [
            "分析2024年人工智能的最新发展趋势",
            "比较LangChain和LangGraph的技术差异",
            "研究大语言模型在企业中的应用场景",
            "探讨Agent技术的未来发展方向"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{query}", use_container_width=True):
                st.session_state.query = query
    
    # 主界面 - 查询输入
    st.header("📝 输入研究查询")
    
    # 从session state获取查询（用于示例按钮）
    default_query = st.session_state.get('query', '')
    
    query = st.text_area(
        "请输入您想要深入研究的问题：",
        value=default_query,
        height=100,
        placeholder="例如：分析2024年人工智能的最新发展趋势"
    )
    
    # 迭代轮数设置
    st.markdown("### ⚙️ 研究参数")
    col_a, col_b = st.columns(2)
    with col_a:
        max_iterations = st.slider(
            "最大迭代轮数",
            min_value=1,
            max_value=5,
            value=2,
            help="系统将进行多轮搜索和分析，每一轮都会识别信息缺口并进行更深入的研究"
        )
    with col_b:
        st.info(f"🔄 将进行最多 **{max_iterations}** 轮迭代分析")
    
    # 开始研究按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_research = st.button("🚀 开始深度研究", use_container_width=True, type="primary")
    
    if start_research and query:
        # 清除之前的session state
        if 'research_complete' in st.session_state:
            del st.session_state['research_complete']
        
        st.markdown("---")
        st.header("🔄 研究过程")
        
        # 创建进度容器
        progress_container = st.container()
        
        # 创建各Agent的输出容器
        supervisor_container = st.expander("🎯 Supervisor Agent - 研究计划", expanded=True)
        search_container = st.expander("🔍 Search Agent - 搜索结果", expanded=True)
        research_container = st.expander("🧠 Research Agent - 深度分析", expanded=True)
        writer_container = st.expander("📝 Writer Agent - 报告生成", expanded=False)
        
        # 最终报告容器
        report_container = st.container()
        
        # 运行工作流
        try:
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            # 流式执行
            final_state = None
            step_count = 0
            iteration_info = st.empty()
            
            for state_update in stream_research(query, max_iterations):
                step_count += 1
                
                # 获取当前节点和状态
                node_name = list(state_update.keys())[0]
                state = state_update[node_name]
                
                # 更新迭代信息
                current_iteration = state.get("iteration_count", 0)
                need_more = state.get("need_more_research", False)
                additional_questions = state.get("additional_questions", [])
                
                with progress_container:
                    if current_iteration > 0:
                        iteration_info.info(f"🔄 当前迭代: 第 {current_iteration} / {max_iterations} 轮")
                
                # 计算进度
                base_progress = (current_iteration - 1) / max_iterations if current_iteration > 0 else 0
                node_progress = 0.25 / max_iterations  # 每个节点在当前迭代的进度
                
                if node_name == "supervisor":
                    progress = 0.1
                elif node_name == "search":
                    progress = base_progress + 0.3 * node_progress
                elif node_name == "research":
                    progress = base_progress + 0.6 * node_progress
                elif node_name == "writer":
                    progress = 0.95
                else:
                    progress = base_progress
                
                # 更新进度
                with progress_container:
                    progress_bar.progress(min(progress, 0.99))
                
                # 更新状态文本
                current_step = state.get("current_step", "")
                with progress_container:
                    status_text.info(f"**当前状态:** {current_step}")
                
                # 显示各Agent的输出
                if node_name == "supervisor":
                    with supervisor_container:
                        st.markdown("### 📋 研究计划")
                        research_plan = state.get("research_plan", [])
                        for i, topic in enumerate(research_plan, 1):
                            st.markdown(f"{i}. {topic}")
                
                elif node_name == "search":
                    with search_container:
                        st.markdown("### 🔍 搜索结果")
                        search_results = state.get("search_results", [])
                        
                        # 按主题分组显示
                        topics = {}
                        for result in search_results:
                            topic = result.get("search_topic", "未分类")
                            if topic not in topics:
                                topics[topic] = []
                            topics[topic].append(result)
                        
                        for topic, results in topics.items():
                            st.markdown(f"**主题: {topic}**")
                            for i, result in enumerate(results, 1):
                                with st.container():
                                    st.markdown(f"**{i}. [{result['title']}]({result['url']})**")
                                    st.caption(result['content'][:200] + "...")
                            st.markdown("---")
                
                elif node_name == "research":
                    iteration = state.get("iteration_count", 0)
                    with research_container:
                        st.markdown(f"### 🧠 深度分析 (第{iteration}轮)")
                        analysis = state.get("analysis", [])
                        for analysis_text in analysis:
                            st.markdown(analysis_text)
                        
                        # 显示补充问题
                        if state.get("need_more_research"):
                            st.markdown("#### 💡 发现信息缺口，需要进一步研究：")
                            additional_q = state.get("additional_questions", [])
                            for i, q in enumerate(additional_q, 1):
                                st.markdown(f"{i}. {q}")
                
                elif node_name == "writer":
                    final_state = state
                
                # 显示消息日志
                messages = state.get("messages", [])
                if messages:
                    with progress_container:
                        for msg in messages:
                            st.text(msg)
            
            # 显示最终报告
            if final_state and final_state.get("final_report"):
                with progress_container:
                    progress_bar.progress(1.0)
                    status_text.success("✅ 研究完成！")
                
                st.markdown("---")
                with report_container:
                    st.header("📊 最终研究报告")
                    st.markdown(final_state["final_report"])
                
                # 下载按钮
                st.download_button(
                    label="📥 下载报告 (Markdown)",
                    data=final_state["final_report"],
                    file_name=f"research_report_{int(time.time())}.md",
                    mime="text/markdown"
                )
                
                # 保存到session state
                st.session_state['research_complete'] = True
                st.session_state['final_report'] = final_state["final_report"]
        
        except Exception as e:
            st.error(f"❌ 研究过程中出现错误: {str(e)}")
            st.exception(e)
    
    elif start_research and not query:
        st.warning("⚠️ 请先输入研究查询")
    
    # 显示工作流图
    st.markdown("---")
    st.header("🗺️ LangGraph工作流图")
    
    with st.expander("查看工作流结构", expanded=False):
        try:
            # 创建工作流
            app = create_research_workflow()
            
            # 尝试获取图的图表表示
            st.markdown("""
            ```mermaid
            graph TB
                START([开始]) --> Supervisor[🎯 Supervisor Agent<br/>制定研究计划]
                Supervisor --> Search[🔍 Search Agent<br/>网络搜索]
                Search --> Research[🧠 Research Agent<br/>深度分析]
                Research -->|"needMoreResearch=true"| Search
                Research -->|"needMoreResearch=false"| Writer[📝 Writer Agent<br/>生成报告]
                Writer --> END([结束])
                
                style START fill:#90EE90
                style END fill:#FFB6C1
                style Supervisor fill:#87CEEB
                style Search fill:#DDA0DD
                style Research fill:#F0E68C
                style Writer fill:#FFA07A
            ```
            """)
            
            st.info("🔄 工作流说明：用户查询 → 制定计划 → 搜索信息 → 深度分析 → [循环或生成报告]")
        
        except Exception as e:
            st.warning(f"无法显示工作流图: {str(e)}")


if __name__ == "__main__":
    main()
