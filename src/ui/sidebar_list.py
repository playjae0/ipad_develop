"""Sidebar cell list UI for labeling page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.constants import COL_CELL_ID, DEFECT_COLUMNS
from src.state_manager import get_sidebar_cell_index, set_sidebar_cell_index


def render_sidebar_cell_list(df: pd.DataFrame, current_index: int) -> int:
    """Render sorted cell list with defect summary values in sidebar.

    Returns updated selected index.
    """
    st.sidebar.subheader("Cell List")

    sorted_df = df.sort_values(COL_CELL_ID).reset_index(drop=True)
    max_index = max(len(sorted_df) - 1, 0)
    safe_index = min(max(current_index, 0), max_index)

    options = list(range(len(sorted_df)))
    widget_index = get_sidebar_cell_index(safe_index)
    if widget_index != safe_index:
        set_sidebar_cell_index(safe_index)

    selected_index = st.sidebar.radio(
        "cell_id 목록",
        options=options,
        index=safe_index,
        key="sidebar_cell_index",
        format_func=lambda idx: _build_cell_summary(sorted_df, idx),
    )

    return int(selected_index)


def _build_cell_summary(df: pd.DataFrame, index: int) -> str:
    """Build display text with cell_id + 4 defect values (no column names)."""
    row = df.iloc[index]
    values = [str(row[col]).strip() for col in DEFECT_COLUMNS]
    normalized = [value if value else "-" for value in values]
    return f"{row[COL_CELL_ID]} | {' / '.join(normalized)}"
