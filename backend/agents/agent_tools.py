from langchain_core.tools import tool
import pandas as pd
import json
from typing import Dict, Any

@tool
def execution_tool(code: str, df: pd.DataFrame) -> Dict[str, Any]:
    """执行 Agent 生成的代码，支持返回 Echarts JSON"""
    local_env = {"pd": pd, "df": df, "json": json}
    safe_builtins = {
        "__import__": __import__,
        "len": len,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "range": range,
        "sorted": sorted,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "float": float,
        "int": int,
        "str": str,
    }
    try:
        exec(code, {"__builtins__": safe_builtins}, local_env)
        result = local_env.get("result", {})
        return {
            "success": True,
            "result": result.get("data") if isinstance(result, dict) else result,
            "echarts_option": result.get("echarts_option") if isinstance(result, dict) else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def get_data_summary(df: pd.DataFrame) -> str:
    """返回数据集概要"""
    return f"Shape: {df.shape}\nColumns: {list(df.columns)}\nSample:\n{df.head(3).to_string()}"