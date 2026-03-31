from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class UploadResponse(BaseModel):
    message: str
    columns: List[str]
    df_shape: tuple
    preview: List[Dict]

class AnalysisRequest(BaseModel):
    query: str
    df_data: List[Dict]  # 前端传 JSON 化的 DataFrame

class AnalysisResponse(BaseModel):
    insights: str
    result: Any
    charts: List[Dict]  # Echarts option
    code: str
    error: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    messages: List[ChatMessage] = []
    df_data: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    answer: str
    charts: List[Dict] = []
    error: Optional[str] = None