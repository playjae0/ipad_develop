"""ATIS data loading and merge utilities for upload step."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import ATIS_COLUMN_MAPPING, ATIS_FILE_PATH
from src.constants import COL_CELL_ID


def merge_atis_to_master(master_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Merge ATIS data into master dataframe using left join on cell_id.

    Behavior:
    - If ATIS file is missing, return original dataframe unchanged.
    - If mapping is empty, return original dataframe unchanged.
    - Keeps master dataframe row unit as one row per cell_id.
    """
    atis_path = Path(ATIS_FILE_PATH)
    if not atis_path.exists():
        return master_df, "ATIS 파일이 없어 병합 없이 진행합니다."

    if not ATIS_COLUMN_MAPPING:
        return master_df, "ATIS 컬럼 매핑이 비어 있어 병합 없이 진행합니다."

    required_source_columns = [COL_CELL_ID, *ATIS_COLUMN_MAPPING.values()]
    atis_df = pd.read_excel(atis_path, usecols=lambda c: c in required_source_columns)

    if COL_CELL_ID not in atis_df.columns:
        return master_df, "ATIS 파일에 cell_id 컬럼이 없어 병합 없이 진행합니다."

    rename_map = {source: target for target, source in ATIS_COLUMN_MAPPING.items()}
    atis_df = atis_df.rename(columns=rename_map)

    target_columns = [COL_CELL_ID, *ATIS_COLUMN_MAPPING.keys()]
    atis_df = atis_df[[col for col in target_columns if col in atis_df.columns]]
    atis_df = atis_df.drop_duplicates(subset=[COL_CELL_ID])

    merged_df = master_df.merge(atis_df, on=COL_CELL_ID, how="left")
    return merged_df, "ATIS 데이터를 병합했습니다."
