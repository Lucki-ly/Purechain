from fastapi import APIRouter, UploadFile, File
from ..models import AnalysisRequest, AnalysisResponse, UploadResponse, ChatRequest, ChatResponse
from ..utils.data_processor import process_uploaded_files
from ..agents.compile_agent import pureclaw_graph
import pandas as pd
import logging
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..config import settings

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)
chat_llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.3,
    timeout=settings.OLLAMA_TIMEOUT,
)


@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)):
    files_content = {}
    for file in files:
        files_content[file.filename] = await file.read()

    df = process_uploaded_files(files_content)
    return UploadResponse(
        message="上传成功",
        columns=list(df.columns),
        df_shape=df.shape,
        preview=df.head(50).to_dict(orient="records")
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    df = pd.DataFrame(request.df_data)
    state = {
        "query": request.query,
        "df": df,
        "messages": [],
        "code": "",
        "result": None,
        "insights": "",
        "echarts_options": []
    }

    try:
        logger.info("Analyze started. query=%s rows=%s", request.query, len(request.df_data))
        result_state = pureclaw_graph.invoke(state)
        logger.info("Analyze completed successfully.")
        return AnalysisResponse(
            insights=result_state.get("insights") or "",
            result=result_state.get("result"),
            charts=result_state.get("echarts_options") or [],
            code=result_state.get("code") or "",
        )
    except Exception as e:
        logger.exception("Analyze failed.")
        return AnalysisResponse(
            insights="分析失败，请查看 error 信息与日志。",
            result=None,
            charts=[],
            code="",
            error=str(e),
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # 有数据就走分析流；无数据走纯对话
        if request.df_data and len(request.df_data) > 0:
            df = pd.DataFrame(request.df_data)
            state = {
                "query": request.query,
                "df": df,
                "messages": [],
                "code": "",
                "result": None,
                "insights": "",
                "echarts_options": [],
            }
            result_state = pureclaw_graph.invoke(state)
            return ChatResponse(
                answer=result_state.get("insights") or "分析完成。",
                charts=result_state.get("echarts_options") or [],
                error=None,
            )

        history = [SystemMessage(content="你是 Pureclaw 企业数据分析助手。语气简洁、专业、友好。")]
        for msg in request.messages[-8:]:
            role = (msg.role or "").lower()
            if role == "assistant":
                history.append(AIMessage(content=msg.content))
            elif role == "user":
                history.append(HumanMessage(content=msg.content))
        history.append(HumanMessage(content=request.query))

        response = chat_llm.invoke(history)
        answer = (response.content or "").strip()
        if not answer:
            return ChatResponse(answer="", charts=[], error="模型未返回内容，请检查 Ollama 服务或模型状态。")
        return ChatResponse(answer=answer, charts=[], error=None)
    except Exception as e:
        logger.exception("Chat failed.")
        return ChatResponse(answer="", charts=[], error=str(e))