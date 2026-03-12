"""Status panel UI for labeling progress and navigation position."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.constants import DEFECT_COLUMNS


def render_status_panel(df: pd.DataFrame, current_index: int) -> None:
    """Render total count, current index, and labeling progress."""
    total_cells = len(df)
    current_display = current_index + 1 if total_cells > 0 else 0

    total_slots = total_cells * len(DEFECT_COLUMNS)
    labeled_slots = int((df[DEFECT_COLUMNS].replace("", pd.NA).notna()).sum().sum()) if total_slots > 0 else 0
    progress_pct = (labeled_slots / total_slots * 100.0) if total_slots > 0 else 0.0

    cols = st.columns(3)
    cols[0].metric("전체 cell 수", total_cells)
    cols[1].metric("현재 index", f"{current_display} / {total_cells}")
    cols[2].metric("라벨링 진행", f"{labeled_slots}/{total_slots} ({progress_pct:.1f}%)")
