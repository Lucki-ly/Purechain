import pandas as pd
from typing import Dict, List


def process_uploaded_files(files_content: Dict[str, bytes]) -> pd.DataFrame:
    dfs = {}
    for filename, content in files_content.items():
        if filename.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(content))
        else:
            excel_file = pd.ExcelFile(pd.io.common.BytesIO(content))
            for sheet_name in excel_file.sheet_names:
                key = f"{filename}_{sheet_name}" if len(excel_file.sheet_names) > 1 else filename
                dfs[key] = excel_file.parse(sheet_name)

    if not dfs:
        raise ValueError("No data loaded")

    # 多表自动合并（可后续优化为用户指定 join keys）
    if len(dfs) > 1:
        main_df = pd.concat(dfs.values(), ignore_index=True)
    else:
        main_df = list(dfs.values())[0]

    # 自动清洗
    main_df = main_df.dropna(thresh=len(main_df.columns) * 0.5)
    numeric_cols = main_df.select_dtypes(include=['number']).columns
    main_df[numeric_cols] = main_df[numeric_cols].fillna(main_df[numeric_cols].median())
    main_df = main_df.fillna("未知")

    return main_df