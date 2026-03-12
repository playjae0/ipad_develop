"""Defect controls for each position image block."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import DEFAULT_DEFECT_LIST


def render_defect_selector(
    *,
    df: pd.DataFrame,
    row_index: int,
    defect_column: str,
    widget_key: str,
) -> str:
    """Render a selectbox for defect selection and return selected value."""
    current_value = str(df.at[row_index, defect_column] or "")
    options = ["", *DEFAULT_DEFECT_LIST]

    if current_value not in options:
        options.append(current_value)

    selected = st.selectbox(
        "Defect",
        options=options,
        index=options.index(current_value),
        key=widget_key,
    )
    return selected
