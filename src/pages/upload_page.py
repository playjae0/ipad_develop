"""Upload page UI for Step 4.

This page handles:
- drag-and-drop upload
- folder selection upload (period/line two-level)
- upload validation
- filename parsing
- image_map construction
- master dataframe construction
- missing count summary
- dataframe preview
- session state save + move to labeling page
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from config import ALLOWED_EXTENSIONS, IMAGE_ROOT_PATH
from src.atis_loader import merge_atis_to_master
from src.constants import COL_CELL_ID, KEY_SELECTED_FOLDER_INFO, PAGE_LABELING, POSITION_COLUMNS
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
from utils.naming_utils import sanitize_token
from utils.path_utils import collect_files_with_extensions, ensure_directory, list_subdirectories


def render_upload_page() -> None:
    """Render upload page and process uploaded images."""
    initialize_session_state()

    st.title("이미지 업로드")
    st.caption("이미지를 업로드한 뒤, cell_id 기준 master dataframe을 생성합니다.")

    upload_source = st.radio(
        "업로드 방식 선택",
        options=["드래그 업로드", "폴더 선택 업로드"],
        horizontal=True,
    )

    if upload_source == "드래그 업로드":
        uploaded_files = st.file_uploader(
            "이미지 파일을 업로드하세요 (jpg, jpeg, png)",
            type=list(ALLOWED_EXTENSIONS),
            accept_multiple_files=True,
        )

        if not uploaded_files:
            st.info("업로드할 이미지를 선택해주세요.")
            return

        st.session_state[KEY_SELECTED_FOLDER_INFO] = ""
        _render_uploaded_files_save_section(uploaded_files)
        _render_validation_result(uploaded_files)
        return

    folder_files, folder_info = _render_folder_selector()
    if folder_files is None:
        return

    st.session_state[KEY_SELECTED_FOLDER_INFO] = folder_info
    _render_validation_result(folder_files)


def _render_uploaded_files_save_section(uploaded_files: list[Any]) -> None:
    """Optionally save drag-uploaded original files under IMAGE_ROOT_PATH."""
    st.subheader("업로드 원본 저장")
    st.caption(f"기본 저장 경로: {IMAGE_ROOT_PATH}")

    subfolder_name = st.text_input(
        "하위 저장 폴더명 (비우면 루트에 저장)",
        value="",
        help="입력 시 IMAGE_ROOT_PATH 하위에 폴더를 생성하여 저장합니다.",
    )

    if st.button("업로드한 원본 이미지 저장"):
        try:
            save_root = ensure_directory(IMAGE_ROOT_PATH)
            if subfolder_name.strip():
                safe_subfolder = sanitize_token(subfolder_name.strip(), fallback="uploaded")
                save_root = ensure_directory(save_root / safe_subfolder)

            saved_count = 0
            for uploaded_file in uploaded_files:
                output_path = save_root / Path(str(uploaded_file.name)).name
                output_path.write_bytes(uploaded_file.getvalue())
                saved_count += 1

            st.success(f"원본 이미지 저장 완료: {saved_count}개 ({save_root})")
        except Exception as error:  # pragma: no cover - UI safety fallback
            st.error(f"원본 저장 중 오류가 발생했습니다: {error}")


def _render_folder_selector() -> tuple[list[Path] | None, str]:
    """Render two-level folder selector and return collected image file paths."""
    st.subheader("폴더 선택 업로드")
    st.caption(f"루트 폴더: {IMAGE_ROOT_PATH}")

    periods = list_subdirectories(IMAGE_ROOT_PATH)
    if not periods:
        st.warning("루트 폴더에 기간 하위 폴더가 없습니다.")
        return None, ""

    selected_period = st.selectbox("1단계: 기간", options=periods)
    period_path = IMAGE_ROOT_PATH / selected_period

    lines = list_subdirectories(period_path)
    if not lines:
        st.warning("선택한 기간 폴더에 라인 하위 폴더가 없습니다.")
        return None, ""

    selected_line = st.selectbox("2단계: 라인", options=lines)
    line_path = period_path / selected_line

    collected_files = collect_files_with_extensions(line_path, ALLOWED_EXTENSIONS)
    if not collected_files:
        st.warning("선택한 라인 폴더에 업로드 가능한 이미지 파일이 없습니다.")
        return None, ""

    st.success(f"선택된 폴더에서 {len(collected_files)}개 이미지를 찾았습니다.")
    folder_info = f"{selected_period} / {selected_line}"
    return collected_files, folder_info


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

    master_df, atis_message = merge_atis_to_master(master_df)
    st.info(atis_message)

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
