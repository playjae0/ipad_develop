"""Upload page UI for Step 3.

This page handles:
- drag-and-drop upload
- upload validation
- filename parsing
- image_map construction
- master dataframe construction
- missing count summary
- dataframe preview
- session state save + move to labeling page
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from config import ALLOWED_EXTENSIONS
from src.constants import COL_CELL_ID, PAGE_LABELING, POSITION_COLUMNS
from src.dataframe_builder import build_master_dataframe
from src.image_registry import build_image_map
from src.state_manager import (
    initialize_session_state,
    set_current_cell_index,
    set_image_map,
    set_master_dataframe,
    set_upload_completed,
)
from src.validation import (
    extract_parse_failures,
    parse_files_with_results,
    validate_file_count,
    validate_file_extensions,
)


def render_upload_page() -> None:
    """Render upload page and process uploaded images."""
    initialize_session_state()

    st.title("이미지 업로드")
    st.caption("이미지를 업로드한 뒤, cell_id 기준 master dataframe을 생성합니다.")

    uploaded_files = st.file_uploader(
        "이미지 파일을 업로드하세요 (jpg, jpeg, png)",
        type=list(ALLOWED_EXTENSIONS),
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("업로드할 이미지를 선택해주세요.")
        return

    _render_validation_result(uploaded_files)


def _render_validation_result(uploaded_files: list[Any]) -> None:
    """Validate uploads, build artifacts, and expose save/navigation actions."""
    count_error = validate_file_count(uploaded_files)
    if count_error:
        st.error(count_error)
        return

    invalid_extensions = validate_file_extensions(uploaded_files)
    if invalid_extensions:
        st.error("지원하지 않는 확장자가 포함되어 있습니다.")
        st.write(invalid_extensions)
        return

    parsed_pairs = parse_files_with_results(uploaded_files)
    parse_failures = extract_parse_failures(parsed_pairs)
    if parse_failures:
        st.warning("일부 파일은 파싱에 실패하여 제외됩니다.")
        st.dataframe(parse_failures, use_container_width=True)

    image_map = build_image_map(parsed_pairs)
    master_df = build_master_dataframe(image_map)

    if master_df.empty:
        st.error("유효한 파일이 없어 master dataframe을 생성할 수 없습니다.")
        return

    _render_missing_counts(master_df)

    st.subheader("Master DataFrame Preview")
    st.dataframe(master_df, use_container_width=True)

    if st.button("업로드 결과 저장 후 라벨링 페이지로 이동", type="primary"):
        set_master_dataframe(master_df)
        set_image_map(image_map)
        set_current_cell_index(0)
        set_upload_completed(True)
        st.session_state["current_page"] = PAGE_LABELING
        st.success("세션 상태 저장 완료. 라벨링 페이지로 이동합니다.")
        st.rerun()


def _render_missing_counts(master_df: Any) -> None:
    """Show missing image counts by position.

    Missing count = number of cells where position column value is 0.
    """
    st.subheader("위치별 누락 수량")
    columns = st.columns(len(POSITION_COLUMNS))

    for idx, position in enumerate(POSITION_COLUMNS):
        missing_count = int((master_df[position] == 0).sum())
        columns[idx].metric(label=position, value=f"{missing_count} cells")

    st.caption(f"전체 cell 수: {master_df[COL_CELL_ID].nunique()}")
