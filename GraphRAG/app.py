"""GraphRAG 本地知识图谱 RAG Demo - Streamlit Web 应用"""
import streamlit as st
from pathlib import Path
import sys
import os
import json
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.api.azure_llm_adapter import AzureLLMAdapter
from src.api.azure_embedding_adapter import AzureEmbeddingAdapter
from src.document.processor import DocumentProcessor
# 使用简化版 RAG 系统（真实可用）
from src.graphrag.simple_indexer import SimpleRAGIndexer
from src.graphrag.simple_query import SimpleRAGQuery

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO")

# 页面配置
st.set_page_config(
    page_title="GraphRAG 知识图谱 Demo",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(120deg, #2196F3, #00BCD4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """初始化 session state"""
    if 'llm_adapter' not in st.session_state:
        st.session_state.llm_adapter = None
    if 'embedding_adapter' not in st.session_state:
        st.session_state.embedding_adapter = None
    if 'document_processor' not in st.session_state:
        st.session_state.document_processor = DocumentProcessor()
    if 'indexer' not in st.session_state:
        st.session_state.indexer = None
    if 'query_engine' not in st.session_state:
        st.session_state.query_engine = None
    if 'documents' not in st.session_state:
        st.session_state.documents = []
    if 'index_built' not in st.session_state:
        st.session_state.index_built = False
    # 添加模式选择
    if 'rag_mode' not in st.session_state:
        st.session_state.rag_mode = "simple"  # "simple" 或 "graphrag"


def check_api_configuration():
    """检查 API 配置"""
    is_valid, error_msg = settings.validate()
    
    if not is_valid:
        st.error(f"⚠️ 配置错误: {error_msg}")
        st.info("请确保 .env 文件已正确配置。参考 .env.example 文件。")
        return False
    
    return True


def initialize_adapters():
    """初始化 API 适配器"""
    if st.session_state.llm_adapter is None:
        st.session_state.llm_adapter = AzureLLMAdapter(
            endpoint=settings.llm_endpoint,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    
    if st.session_state.embedding_adapter is None:
        st.session_state.embedding_adapter = AzureEmbeddingAdapter(
            endpoint=settings.embedding_endpoint,
            api_key=settings.embedding_api_key,
            model=settings.embedding_model,
        )
    
    # 根据模式选择不同的实现
    if st.session_state.rag_mode == "graphrag":
        # 完整 GraphRAG
        from src.graphrag.full_indexer import FullGraphRAGIndexer
        from src.graphrag.full_query import FullGraphRAGQuery
        
        if st.session_state.indexer is None:
            st.session_state.indexer = FullGraphRAGIndexer(
                input_dir=settings.data_input_dir,
                output_dir=settings.data_output_dir,
                llm_adapter=st.session_state.llm_adapter,
                embedding_adapter=st.session_state.embedding_adapter,
            )
        
        st.session_state.query_engine = FullGraphRAGQuery(
            index_dir=settings.data_output_dir,
            llm_adapter=st.session_state.llm_adapter,
            embedding_adapter=st.session_state.embedding_adapter,
        )
    else:
        # 简化版 RAG
        if st.session_state.indexer is None:
            st.session_state.indexer = SimpleRAGIndexer(
                input_dir=settings.data_input_dir,
                output_dir=settings.data_output_dir,
                llm_adapter=st.session_state.llm_adapter,
                embedding_adapter=st.session_state.embedding_adapter,
            )
        
        st.session_state.query_engine = SimpleRAGQuery(
            index_dir=settings.data_output_dir,
            llm_adapter=st.session_state.llm_adapter,
            embedding_adapter=st.session_state.embedding_adapter,
        )


def sidebar():
    """侧边栏"""
    with st.sidebar:
        st.markdown("### 🔗 GraphRAG Demo")
        st.markdown("---")
        
        # RAG模式选择
        st.markdown("#### 🎛️ RAG 模式")
        mode_options = {
            "simple": "🚀 简化版RAG（快速）",
            "graphrag": "🧠 完整GraphRAG（知识图谱）"
        }
        
        selected_mode = st.radio(
            "选择模式",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x],
            index=0 if st.session_state.rag_mode == "simple" else 1,
            help="简化版：向量检索，快速低成本\nGraphRAG：知识图谱，深度分析",
            label_visibility="collapsed"
        )
        
        # 如果模式改变，清空索引并更新
        if selected_mode != st.session_state.rag_mode:
            st.session_state.rag_mode = selected_mode
            st.session_state.indexer = None
            st.session_state.query_engine = None
            st.session_state.index_built = False
            st.rerun()
        
        # 显示当前模式说明
        if st.session_state.rag_mode == "simple":
            st.info("📝 简化版：基于向量相似度的快速检索")
        else:
            st.success("🔬 GraphRAG：完整知识图谱，包含实体、关系和社区")
        
        st.markdown("---")
        
        # 系统状态
        st.markdown("#### 📊 系统状态")
        
        # 检查配置
        if check_api_configuration():
            st.success("✅ 配置正常")
            
            # 测试连接按钮
            if st.button("🔌 测试 API 连接", use_container_width=True):
                with st.spinner("测试中..."):
                    test_api_connection()
        else:
            st.error("❌ 配置错误")
        
        st.markdown("---")
        
        # 文档统计
        st.markdown("#### 📁 文档统计")
        st.metric("已上传文档", len(st.session_state.documents))
        
        # 索引状态
        index_status = st.session_state.indexer.get_index_status() if st.session_state.indexer else None
        if index_status:
            st.metric("索引状态", "✅ 已构建")
            st.metric("处理文档数", index_status.get("documents_processed", 0))
        else:
            st.metric("索引状态", "❌ 未构建")
        
        st.markdown("---")
        
        # 清空数据
        if st.button("🗑️ 清空所有数据", use_container_width=True, type="secondary"):
            if st.session_state.indexer:
                st.session_state.indexer.clear_index()
            st.session_state.documents = []
            st.session_state.index_built = False
            st.success("已清空所有数据")
            st.rerun()


def test_api_connection():
    """测试 API 连接"""
    # 测试 LLM
    st.write("**测试 LLM API...**")
    llm_success, llm_msg = st.session_state.llm_adapter.test_connection()
    if llm_success:
        st.success(f"✅ LLM: {llm_msg}")
    else:
        st.error(f"❌ LLM: {llm_msg}")
    
    # 测试 Embedding
    st.write("**测试 Embedding API...**")
    emb_success, emb_msg = st.session_state.embedding_adapter.test_connection()
    if emb_success:
        st.success(f"✅ Embedding: {emb_msg}")
    else:
        st.error(f"❌ Embedding: {emb_msg}")


def page_document_management():
    """页面1: 文档管理"""
    st.markdown('<h1 class="main-header">📁 文档管理</h1>', unsafe_allow_html=True)
    
    # 文件上传
    st.markdown("### 上传文档")
    uploaded_files = st.file_uploader(
        "选择文档文件",
        type=['txt', 'md', 'docx', 'pdf'],
        accept_multiple_files=True,
        help="支持 txt、md、docx、pdf 格式",
    )
    
    if uploaded_files:
        if st.button("📥 处理上传的文件", type="primary"):
            with st.spinner("处理中..."):
                try:
                    documents = st.session_state.document_processor.process_uploaded_files(
                        uploaded_files,
                        settings.data_input_dir
                    )
                    st.session_state.documents.extend(documents)
                    st.success(f"✅ 成功处理 {len(documents)} 个文件")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 处理文件失败: {str(e)}")
    
    # 显示已上传文档
    st.markdown("---")
    st.markdown("### 已上传的文档")
    
    if st.session_state.documents:
        for idx, doc in enumerate(st.session_state.documents):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{doc['filename']}**")
            with col2:
                st.write(f"{doc['extension']}")
            with col3:
                st.write(f"{doc['size']:,} 字符")
            with col4:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.documents.pop(idx)
                    st.rerun()
    else:
        st.info("📋 还没有上传任何文档")


def page_index_building():
    """页面2: 知识图谱构建"""
    st.markdown('<h1 class="main-header">🔗 知识图谱构建</h1>', unsafe_allow_html=True)
    
    if not st.session_state.documents:
        st.warning("⚠️ 请先在【文档管理】页面上传文档")
        return
    
    st.markdown("### 📊 构建参数配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chunk_size = st.slider(
            "文本分块大小 (Chunk Size)",
            min_value=100,
            max_value=1000,
            value=settings.default_chunk_size,
            step=50,
            help="将文档分成多大的文本块进行处理"
        )
        
        llm_temperature = st.slider(
            "LLM 温度 (Temperature)",
            min_value=0.0,
            max_value=1.0,
            value=settings.default_llm_temperature,
            step=0.1,
            help="控制 LLM 生成的随机性，0 表示确定性，1 表示高随机性"
        )
    
    with col2:
        chunk_overlap = st.slider(
            "分块重叠 (Chunk Overlap)",
            min_value=0,
            max_value=200,
            value=settings.default_chunk_overlap,
            step=10,
            help="相邻文本块之间的重叠字符数"
        )
        
        max_cluster_size = st.slider(
            "最大簇大小 (Max Cluster Size)",
            min_value=5,
            max_value=50,
            value=settings.default_max_cluster_size,
            step=5,
            help="社区检测的最大簇大小"
        )
    
    st.markdown("---")
    
    # 构建按钮
    if st.button("🚀 开始构建知识图谱", type="primary", use_container_width=True):
        with st.spinner("正在构建知识图谱，这可能需要几分钟..."):
            try:
                # 准备文档
                st.session_state.indexer.prepare_documents(st.session_state.documents)
                
                # 构建索引
                result = st.session_state.indexer.build_index(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    llm_temperature=llm_temperature,
                    max_cluster_size=max_cluster_size,
                )
                
                st.session_state.index_built = True
                st.success("✅ 索引构建完成！")
                
                # 显示统计信息
                st.markdown("### 📈 构建结果")
                
                if st.session_state.rag_mode == "graphrag":
                    # GraphRAG 模式 - 显示实体和社区
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("文档数", result.get("documents_processed", 0))
                    with col2:
                        st.metric("实体数", result.get("entities_extracted", 0))
                    with col3:
                        st.metric("关系数", result.get("relationships_extracted", 0))
                    with col4:
                        st.metric("社区数", result.get("communities_detected", 0))
                    
                    # 显示图统计
                    if "graph_stats" in result:
                        with st.expander("📊 查看图统计信息"):
                            stats = result["graph_stats"]
                            st.write(f"- 节点数: {stats.get('num_nodes', 0)}")
                            st.write(f"- 边数: {stats.get('num_edges', 0)}")
                            st.write(f"- 图密度: {stats.get('density', 0):.4f}")
                            
                            if "entity_types" in stats:
                                st.write("**实体类型分布:**")
                                for etype, count in stats["entity_types"].items():
                                    st.write(f"  - {etype}: {count}")
                else:
                    # 简化版 - 显示文本块
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("处理文档数", result.get("documents_processed", 0))
                    with col2:
                        st.metric("文本块数量", result.get("chunks_created", 0))
                    with col3:
                        st.metric("索引类型", result.get("index_type", "simple_rag"))
                
            except Exception as e:
                st.error(f"❌ 构建失败: {str(e)}")
                logger.exception("索引构建失败")


def page_query():
    """页面3: RAG 检索"""
    st.markdown('<h1 class="main-header">💬 RAG 检索</h1>', unsafe_allow_html=True)
    
    # 检查索引状态
    index_status = st.session_state.indexer.get_index_status() if st.session_state.indexer else None
    
    if not index_status:
        st.warning("⚠️ 请先在【知识图谱构建】页面构建索引")
        return
    
    # 查询输入
    st.markdown("### 🔍 输入查询")
    query = st.text_area(
        "请输入您的问题",
        height=100,
        placeholder="例如：文档的主要内容是什么？"
    )
    
    # 检索参数
    st.markdown("### ⚙️ 检索参数")
    
    # GraphRAG 模式有本地/全局两种检索
    if st.session_state.rag_mode == "graphrag":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_type = st.selectbox(
                "检索类型",
                options=["local", "global"],
                format_func=lambda x: "🎯 本地检索（实体级）" if x == "local" else "🌍 全局检索（社区级）",
                help="本地：基于实体和关系的精确问答\n全局：基于社区摘要的整体理解"
            )
        
        with col2:
            top_k = st.slider(
                "返回结果数 (Top-K)",
                min_value=1,
                max_value=10,
                value=5,
                help="返回最相关的 K 个结果"
            )
        
        with col3:
            temperature = st.slider(
                "LLM 温度",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                help="控制回答的随机性"
            )
    else:
        # 简化版只有向量检索
        col1, col2 = st.columns(2)
        
        with col1:
            top_k = st.slider(
                "返回结果数 (Top-K)",
                min_value=1,
                max_value=10,
                value=5,
                help="返回最相关的 K 个文档片段"
            )
        
        with col2:
            temperature = st.slider(
                "LLM 温度",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                help="控制回答的随机性"
            )
    
    # 执行查询
    if st.button("🔎 执行查询", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("⚠️ 请输入查询内容")
            return
        
        with st.spinner("查询中..."):
            try:
                # 根据模式执行不同的检索
                if st.session_state.rag_mode == "graphrag":
                    # GraphRAG 模式
                    if search_type == "local":
                        result = st.session_state.query_engine.local_search(
                            query=query,
                            top_k=top_k,
                            temperature=temperature,
                        )
                    else:
                        result = st.session_state.query_engine.global_search(
                            query=query,
                            top_k=top_k,
                            temperature=temperature,
                        )
                else:
                    # 简化版
                    result = st.session_state.query_engine.search(
                        query=query,
                        top_k=top_k,
                        temperature=temperature,
                    )
                
                # 显示结果
                st.markdown("---")
                st.markdown("### 📝 查询结果")
                
                # 显示检索到的信息（根据模式不同）
                if st.session_state.rag_mode == "graphrag":
                    if result.get("search_type") == "local":
                        # 本地检索 - 显示实体和关系
                        if "entities" in result and result["entities"]:
                            st.markdown("#### 🔗 检索到的实体")
                            for entity in result["entities"]:
                                with st.expander(f"📌 {entity.get('name', 'Unknown')} ({entity.get('type', 'OTHER')})"):
                                    st.write(entity.get('description', '无描述'))
                        
                        if "relationships" in result and result["relationships"]:
                            st.markdown("#### 🔀 相关关系")
                            for rel in result["relationships"]:
                                st.write(f"- {rel['source']} --[{rel.get('type', 'RELATED_TO')}]--> {rel['target']}")
                    else:
                        # 全局检索 - 显示社区
                        if "communities" in result and result["communities"]:
                            st.markdown("#### 🌐 相关知识社区")
                            for i, comm in enumerate(result["communities"], 1):
                                with st.expander(f"📊 社区 {i} ({comm.get('size', 0)} 个实体, 相似度: {comm.get('similarity', 0):.3f})"):
                                    st.write(comm.get('summary', '无摘要'))
                else:
                    # 简化版 - 显示文档片段
                    if "chunks" in result and result["chunks"]:
                        st.markdown("#### 📄 检索到的文档片段")
                        st.info(f"从文档中检索到 {len(result['chunks'])} 个最相关的片段")
                        
                        for i, chunk in enumerate(result["chunks"], 1):
                            with st.expander(f"📌 片段 {i} - {chunk.get('source', '未知')} (相似度: {chunk.get('similarity', 0):.3f})"):
                                st.text(chunk.get('text', ''))
                
                # 显示最终答案
                st.markdown("---")
                st.markdown("#### 💡 AI 生成的最终答案")
                st.markdown(f'<div class="success-box">{result["answer"]}</div>', unsafe_allow_html=True)
                
                # 完整上下文（可选查看）
                with st.expander("🔍 查看完整上下文（用于生成答案）"):
                    st.text(result.get("context_used", ""))
                
            except Exception as e:
                st.error(f"❌ 查询失败: {str(e)}")
                logger.exception("查询失败")


def main():
    """主函数"""
    # 初始化
    initialize_session_state()
    
    # 检查配置
    if not check_api_configuration():
        st.stop()
    
    # 初始化适配器
    initialize_adapters()
    
    # 侧边栏
    sidebar()
    
    # 主页面导航
    st.markdown("---")
    page = st.radio(
        "选择功能",
        options=["📁 文档管理", "🔗 知识图谱构建", "💬 RAG 检索"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # 根据选择显示页面
    if page == "📁 文档管理":
        page_document_management()
    elif page == "🔗 知识图谱构建":
        page_index_building()
    elif page == "💬 RAG 检索":
        page_query()


if __name__ == "__main__":
    main()
