"""Image grid UI for labeling page (2x2 fixed layout)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config import ATIS_TOP_LEVELS
from src.ui.defect_controls import render_defect_selector


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

    st.markdown("### CA Set")
    ca_cols = st.columns([1, 1], gap="large")
    changed = _render_single_position(ca_cols[0], df, image_map, row_index, "CA(TOP)", cell_id) or changed
    changed = _render_single_position(ca_cols[1], df, image_map, row_index, "CA(BOT)", cell_id) or changed

    st.divider()

    st.markdown("### AN Set")
    an_cols = st.columns([1, 1], gap="large")
    changed = _render_single_position(an_cols[0], df, image_map, row_index, "AN(TOP)", cell_id) or changed
    changed = _render_single_position(an_cols[1], df, image_map, row_index, "AN(BOT)", cell_id) or changed

    return changed


def _render_single_position(
    container: Any,
    df: pd.DataFrame,
    image_map: dict[str, dict[str, Any]],
    row_index: int,
    position: str,
    cell_id: str,
) -> bool:
    """Render one position panel including image and defect buttons."""
    defect_col = POSITION_TO_DEFECT_COLUMN[position]
    atis_col = f"ATIS_{position}"
    changed = False

    with container:
        current_top = _get_atis_value(df, row_index, position)
        raw_atis = _get_raw_atis_text(df, row_index, position)
        title = f"{position} - {raw_atis}" if raw_atis else f"{position} - {current_top}"
        st.markdown(f"**{title}**")
        image_ref = image_map.get(cell_id, {}).get(position)

        if image_ref is None:
            st.info("No image")
        else:
            try:
                st.image(_to_image_source(image_ref), use_container_width=True)
            except Exception as error:  # pragma: no cover - UI safety fallback
                st.warning(f"이미지 표시 실패: {error}")

        current_sub = str(df.at[row_index, defect_col] or "").strip()
        selected_top, selected_sub, selector_changed = render_defect_selector(
            current_top=current_top,
            current_sub=current_sub,
            widget_key_prefix=f"defect_{cell_id}_{position}",
        )

        if selector_changed:
            if selected_top != current_top:
                _apply_atis_override(df, row_index, atis_col, selected_top)
                selected_sub = ""
            df.at[row_index, defect_col] = selected_sub
            changed = True

    return changed


def _get_atis_value(df: pd.DataFrame, row_index: int, position: str) -> str:
    """Return ATIS top-level value for a position, normalizing NaN/blank to OK."""
    raw_text = _get_raw_atis_text(df, row_index, position)
    if not raw_text:
        return "OK"

    if "/" in raw_text:
        _, new_value = _split_atis_override(raw_text)
        return _normalize_top_level(new_value)
    return _normalize_top_level(raw_text)


def _get_raw_atis_text(df: pd.DataFrame, row_index: int, position: str) -> str:
    """Return raw ATIS text for a position when column exists."""
    atis_col = f"ATIS_{position}"
    if atis_col not in df.columns:
        return ""

    value = str(df.at[row_index, atis_col] or "").strip()
    if not value or value.lower() == "nan":
        return "OK"
    return value


def _split_atis_override(text: str) -> tuple[str, str]:
    """Split `Original/New` formatted ATIS text."""
    if "/" not in text:
        normalized = _normalize_top_level(text.strip() or "OK")
        return normalized, normalized

    original, new = text.split("/", 1)
    original_text = _normalize_top_level(original.strip() or "OK")
    new_text = _normalize_top_level(new.strip() or original_text)
    return original_text, new_text


def _normalize_top_level(value: str) -> str:
    """Normalize top-level to configured categories; unknown values become OK."""
    if value in ATIS_TOP_LEVELS:
        return value
    return "OK"


def _apply_atis_override(df: pd.DataFrame, row_index: int, atis_col: str, selected_top: str) -> None:
    """Apply ATIS override using `Original/New` format when top-level changes."""
    if atis_col not in df.columns:
        return

    raw_text = str(df.at[row_index, atis_col] or "").strip()
    if not raw_text or raw_text.lower() == "nan":
        raw_text = "OK"

    original, current = _split_atis_override(raw_text)
    if selected_top == current:
        return

    if selected_top == original:
        df.at[row_index, atis_col] = original
        return

    df.at[row_index, atis_col] = f"{original}/{selected_top}"


def _to_image_source(image_ref: Any) -> Any:
    """Normalize image source for streamlit display."""
    if isinstance(image_ref, Path):
        return str(image_ref)
    return image_ref
