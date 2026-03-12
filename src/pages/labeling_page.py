"""Labeling page implementation for Step 5."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import DEFAULT_SAVE_ROOT
from src.constants import COL_CELL_ID, KEY_SELECTED_FOLDER_INFO, PAGE_UPLOAD
from src.save_manager import build_csv_export_payload, save_defect_images
from src.state_manager import (
    get_current_cell_index,
    get_image_map,
    get_master_dataframe,
    is_upload_completed,
    set_current_cell_index,
    set_master_dataframe,
    touch_label_sync_token,
)
from src.ui.image_grid import render_image_grid
from src.ui.sidebar_list import render_sidebar_cell_list
from src.ui.status_panel import render_status_panel


def render_labeling_page() -> None:
    """Render labeling page with sidebar list, image grid, and controls."""
    st.title("라벨링 페이지")

    if not is_upload_completed():
        st.warning("업로드가 완료되지 않았습니다. 업로드 페이지에서 먼저 데이터를 준비해주세요.")
        if st.button("업로드 페이지로 이동"):
            st.session_state["current_page"] = PAGE_UPLOAD
            st.rerun()
        return

    master_df = get_master_dataframe()
    image_map = get_image_map()

    if master_df is None or master_df.empty:
        st.warning("라벨링할 데이터가 없습니다. 업로드 페이지에서 데이터를 생성해주세요.")
        if st.button("업로드 페이지로 이동"):
            st.session_state["current_page"] = PAGE_UPLOAD
            st.rerun()
        return

    _render_sidebar_source_info()

    sorted_df = master_df.sort_values(COL_CELL_ID).reset_index(drop=True)
    current_index = _safe_index(get_current_cell_index(), len(sorted_df))

    selected_index = render_sidebar_cell_list(sorted_df, current_index)
    if selected_index != current_index:
        set_current_cell_index(selected_index)
        current_index = selected_index

    render_status_panel(sorted_df, current_index)
    _render_navigation_buttons(current_index, len(sorted_df))

    changed = render_image_grid(df=sorted_df, image_map=image_map, row_index=current_index)
    if changed:
        set_master_dataframe(sorted_df)
        touch_label_sync_token()

    _render_save_section(sorted_df, image_map)


def _render_sidebar_source_info() -> None:
    """Show selected source folder information in sidebar when available."""
    folder_info = str(st.session_state.get(KEY_SELECTED_FOLDER_INFO, "") or "").strip()
    if folder_info:
        st.sidebar.caption(f"선택 폴더(상위/하위): {folder_info}")


def _render_save_section(df: pd.DataFrame, image_map: dict[str, dict[str, object]]) -> None:
    """Render CSV and image save controls."""
    st.divider()
    st.subheader("저장")

    session_name = st.text_input("이미지 저장 세션 폴더명", value="session_01")
    if st.button("이미지 저장"):
        result = save_defect_images(
            df=df,
            image_map=image_map,
            save_root=DEFAULT_SAVE_ROOT,
            session_name=session_name,
        )
        st.success(
            f"이미지 저장 완료 - saved: {result['saved']}, skipped: {result['skipped']}"
        )

    csv_base_name = st.text_input("CSV 파일명", value="labeling_result")
    csv_filename, csv_bytes = build_csv_export_payload(df, csv_base_name)
    st.download_button(
        "CSV 저장",
        data=csv_bytes,
        file_name=csv_filename,
        mime="text/csv",
    )

    st.caption("CSV 추출 대상 데이터프레임")
    st.dataframe(df, use_container_width=True)


def _render_navigation_buttons(current_index: int, total_count: int) -> None:
    """Render previous/next navigation controls."""
    col_prev, col_next = st.columns(2)

    with col_prev:
        if st.button("이전 cell", disabled=(current_index <= 0)):
            set_current_cell_index(current_index - 1)
            st.rerun()

    with col_next:
        if st.button("다음 cell", disabled=(current_index >= total_count - 1)):
            set_current_cell_index(current_index + 1)
            st.rerun()


def _safe_index(index: int, length: int) -> int:
    """Clamp index into dataframe bounds."""
    if length <= 0:
        return 0
    return min(max(index, 0), length - 1)
