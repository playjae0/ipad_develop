"""Image grid UI for labeling page (2x2 fixed layout)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.ui.defect_controls import render_defect_selector


POSITION_LAYOUT: list[str] = ["CA(TOP)", "CA(BOT)", "AN(TOP)", "AN(BOT)"]
POSITION_TO_DEFECT_COLUMN = {
    "CA(TOP)": "Defect_CA(TOP)",
    "CA(BOT)": "Defect_CA(BOT)",
    "AN(TOP)": "Defect_AN(TOP)",
    "AN(BOT)": "Defect_AN(BOT)",
}


def render_image_grid(
    *,
    df: pd.DataFrame,
    image_map: dict[str, dict[str, Any]],
    row_index: int,
) -> bool:
    """Render 2x2 image grid and defect controls.

    Returns True when any defect value was changed.
    """
    row = df.iloc[row_index]
    cell_id = str(row["cell_id"])

    st.subheader(f"Cell: {cell_id}")
    changed = False

    top_cols = st.columns(2)
    changed = _render_single_position(top_cols[0], df, image_map, row_index, "CA(TOP)", cell_id) or changed
    changed = _render_single_position(top_cols[1], df, image_map, row_index, "CA(BOT)", cell_id) or changed

    bottom_cols = st.columns(2)
    changed = _render_single_position(bottom_cols[0], df, image_map, row_index, "AN(TOP)", cell_id) or changed
    changed = _render_single_position(bottom_cols[1], df, image_map, row_index, "AN(BOT)", cell_id) or changed

    return changed


def _render_single_position(
    container: Any,
    df: pd.DataFrame,
    image_map: dict[str, dict[str, Any]],
    row_index: int,
    position: str,
    cell_id: str,
) -> bool:
    """Render one position panel including image and defect selector."""
    defect_col = POSITION_TO_DEFECT_COLUMN[position]
    changed = False

    with container:
        st.markdown(f"**{position}**")
        image_ref = image_map.get(cell_id, {}).get(position)

        if image_ref is None:
            st.info("No image")
        else:
            try:
                st.image(_to_image_source(image_ref), use_container_width=True)
            except Exception as error:  # pragma: no cover - UI safety fallback
                st.warning(f"이미지 표시 실패: {error}")

        selected = render_defect_selector(
            df=df,
            row_index=row_index,
            defect_column=defect_col,
            widget_key=f"defect_{cell_id}_{position}",
        )

        existing = str(df.at[row_index, defect_col] or "")
        if selected != existing:
            df.at[row_index, defect_col] = selected
            changed = True

    return changed


def _to_image_source(image_ref: Any) -> Any:
    """Normalize image source for streamlit display."""
    if isinstance(image_ref, Path):
        return str(image_ref)
    return image_ref
