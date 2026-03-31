from typing import TypedDict, Annotated, Sequence, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from .llm import get_llm
from .tools import get_tavily_search_tool, web_fetch
from .rag import retrieve_documents
import json

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

SYSTEM_PROMPT = """你是一个智能助手。请根据用户的提问，结合搜索结果或文档内容回答问题。
回答要求：
1. 结构清晰，尽量使用有序列表（1. 2. 3.）来组织内容。
2. 必须在回答中包含引用来源。使用 [1], [2] 等形式标注。
3. 在回答的最后，列出所有参考文献，格式如下：
### 参考文献
[1] 文档: <文档名称>
[2] 网页: <Title> - <URL>

如果信息来自上传的文档，请注明文档名称。
如果信息来自网络搜索，请注明网页标题和链接。
"""

@tool
def retrieve_knowledge(query: str) -> str:
    """
    Search local knowledge base (uploaded documents) for relevant information.
    Use this when the user asks questions about specific documents they provided.
    """
    docs = retrieve_documents(query)
    return "\n\n".join([f"Source: {d.metadata['source']}\nContent: {d.page_content}" for d in docs])

def get_agent_graph():
    tools = [get_tavily_search_tool(), web_fetch, retrieve_knowledge]
    llm = get_llm()
    model = llm.bind_tools(tools)

    def agent(state):
        messages = state['messages']
        # Prepend system prompt
        prompt_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = model.invoke(prompt_messages)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.set_entry_point("agent")
    
    def should_continue(state):
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END
    
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
