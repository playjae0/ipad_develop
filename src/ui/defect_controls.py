"""Defect controls for each position image block."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import DEFAULT_DEFECT_LIST


def render_defect_buttons(
    *,
    df: pd.DataFrame,
    row_index: int,
    defect_column: str,
    widget_key_prefix: str,
) -> tuple[str, bool]:
    """Render per-defect buttons and return (selected_value, changed)."""
    current_value = str(df.at[row_index, defect_column] or "")
    options = ["", *DEFAULT_DEFECT_LIST]

    if current_value not in options:
        options.append(current_value)

    st.caption(f"현재 라벨: {current_value if current_value else '-'}")

    changed = False
    selected_value = current_value

    button_labels = ["미선택", *DEFAULT_DEFECT_LIST]
    button_values = ["", *DEFAULT_DEFECT_LIST]

    for start in range(0, len(button_labels), 4):
        cols = st.columns(4)
        for idx, label in enumerate(button_labels[start : start + 4]):
            value = button_values[start + idx]
            key = f"{widget_key_prefix}_{value or 'empty'}"
            if cols[idx].button(label, key=key, use_container_width=True):
                selected_value = value
                changed = selected_value != current_value

    return selected_value, changed
