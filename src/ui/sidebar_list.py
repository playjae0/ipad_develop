"""Sidebar cell list UI for labeling page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.constants import COL_CELL_ID, DEFECT_COLUMNS


def render_sidebar_cell_list(df: pd.DataFrame, selected_cell_id: str) -> str:
    """Render sorted cell list in sidebar using selected_cell_id as the source of truth.

    Returns updated selected cell_id.
    """
    st.sidebar.subheader("Cell List")

    sorted_df = df.sort_values(COL_CELL_ID, ascending=False).reset_index(drop=True)
    options = [str(value) for value in sorted_df[COL_CELL_ID].tolist()]
    if not options:
        return ""

    safe_cell_id = selected_cell_id if selected_cell_id in options else options[0]
    force_sync = bool(st.session_state.get("sidebar_force_sync", False))
    if force_sync and st.session_state.get("sidebar_cell_id") != safe_cell_id:
        st.session_state["sidebar_cell_id"] = safe_cell_id
    st.session_state["sidebar_force_sync"] = False

    selected_cell_id = st.sidebar.radio(
        "cell_id 목록",
        options=options,
        key="sidebar_cell_id",
        format_func=lambda cell_id: _build_cell_summary_by_cell_id(sorted_df, cell_id),
    )

    return str(selected_cell_id)


def _build_cell_summary_by_cell_id(df: pd.DataFrame, cell_id: str) -> str:
    """Build display text with cell_id + 4 defect values (no column names)."""
    matched = df[df[COL_CELL_ID].astype(str) == str(cell_id)]
    if matched.empty:
        return str(cell_id)

    row = matched.iloc[0]
    values = [str(row[col]).strip() for col in DEFECT_COLUMNS]
    normalized = [value if value else "-" for value in values]
    return f"{row[COL_CELL_ID]} | {' / '.join(normalized)}"
