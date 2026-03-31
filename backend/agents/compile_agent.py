from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import pandas as pd
from typing import Any
import operator
import logging
from .agent_tools import execution_tool, get_data_summary
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from backend.config import settings

class AgentState(TypedDict):
    query: str
    df: pd.DataFrame
    messages: Annotated[list, operator.add]
    code: str
    result: Any
    insights: str
    echarts_options: list

logger = logging.getLogger(__name__)

llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.3,
    timeout=settings.OLLAMA_TIMEOUT,
)

def classifier_node(state: AgentState):
    prompt = f"判断用户查询是否需要生成代码和图表: {state['query']}"
    response = llm.invoke([HumanMessage(content=prompt)])
    if not getattr(response, "content", "").strip():
        raise RuntimeError("Ollama 返回空内容（classifier 阶段）")
    return {"messages": [response]}

def code_generator_node(state: AgentState):
    prompt = f"""
你是企业财务/运营数据分析师。
用户查询: {state['query']}
数据集列: {list(state['df'].columns)}
请生成 pandas 代码，变量名为 'result'。
无论是否需要图表，都必须把输出写到变量 result：
1) 仅分析/统计：result 必须是可 JSON 化的 dict，形如：{{'data': <jsonable>}}
2) 需要图表：result 形如 {{'data': <jsonable>, 'echarts_option': <echarts option>}}
如果无法计算，也请把 result 设置为 {{'data': [], 'echarts_option': None}} 并确保代码可执行。
只返回可执行代码，不要解释。
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    code = (response.content or "").strip().strip("```python").strip("```").strip()
    if not code:
        raise RuntimeError("Ollama 未返回可执行代码（code_generator 阶段）")
    return {"code": code}

def execute_node(state: AgentState):
    exec_result = execution_tool.invoke({"code": state["code"], "df": state["df"]})

    if not exec_result.get("success", False):
        # 兼容：执行失败时 tool 可能不返回 result 字段
        err_msg = exec_result.get("error") or "代码执行失败（未返回错误信息）"
        return {
            "result": {"error": err_msg},
            "echarts_options": [],
        }

    # tool 在成功时返回：{success: True, result: ..., echarts_option: ...}
    echarts_option = exec_result.get("echarts_option")
    return {
        "result": exec_result.get("result"),
        "echarts_options": [echarts_option] if echarts_option else [],
    }

def insight_node(state: AgentState):
    if isinstance(state["result"], dict) and state["result"].get("error"):
        # 执行失败时直接把错误透传为洞察，避免再次调用模型
        return {"insights": f"执行失败：{state['result']['error']}"}

    prompt = f"基于以下结果，给出企业运营/财务洞察（趋势、异常、建议）：\n{state['result']}"
    response = llm.invoke([HumanMessage(content=prompt)])
    insights = (response.content or "").strip()
    if not insights:
        logger.warning("Ollama returned empty insights")
        insights = "模型未返回洞察内容，请检查 Ollama 服务状态与模型加载情况。"
    return {"insights": insights}

workflow = StateGraph(AgentState)
workflow.add_node("classifier", classifier_node)
workflow.add_node("code_generator", code_generator_node)
workflow.add_node("execute", execute_node)
workflow.add_node("insight", insight_node)

workflow.set_entry_point("classifier")
workflow.add_edge("classifier", "code_generator")
workflow.add_edge("code_generator", "execute")
workflow.add_edge("execute", "insight")
workflow.add_edge("insight", END)

pureclaw_graph = workflow.compile()