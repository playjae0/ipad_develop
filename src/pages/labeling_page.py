"""Labeling page implementation for Step 5."""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st

from config import CSV_OUTPUT_ROOT_DIR, IMAGE_EXPORT_ROOT_DIR
from src.constants import (
    COL_CELL_ID,
    KEY_SELECTED_FOLDER_INFO,
    KEY_SELECTED_IMAGE_SUBPATH,
    KEY_UPLOAD_SOURCE_TYPE,
    PAGE_UPLOAD,
)
from src.save_manager import save_defect_images
from src.save_manager import (
    apply_loaded_defect_values,
    build_next_version,
    build_next_version_filename,
    ensure_result_folder_from_selected_subpath,
    export_csv_without_filling_ok,
    find_latest_csv_file,
    find_latest_csv_version,
    load_previous_defect_values,
)
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
from utils.naming_utils import sanitize_token
from utils.path_utils import ensure_directory, list_subdirectories_relative


EMPLOYEE_ID_PATTERN = re.compile(r"^[A-Za-z]{2}\d{5}$")


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
    _render_sidebar_previous_csv_loader()

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


def _render_sidebar_previous_csv_loader() -> None:
    """Render two-step previous CSV load flow for folder-select mode."""
    upload_source_type = st.session_state.get(KEY_UPLOAD_SOURCE_TYPE, "drag_upload")
    selected_subpath = st.session_state.get(KEY_SELECTED_IMAGE_SUBPATH)
    if upload_source_type != "folder_select" or not isinstance(selected_subpath, str) or not selected_subpath.strip():
        return

    result_dir = ensure_result_folder_from_selected_subpath(CSV_OUTPUT_ROOT_DIR, selected_subpath)
    latest_csv = find_latest_csv_file(result_dir)

    st.sidebar.divider()
    st.sidebar.caption("이전 CSV 불러오기")
    if latest_csv is None:
        st.sidebar.caption("불러올 CSV가 없습니다.")
        return

    st.sidebar.caption(f"대상 파일: {latest_csv.name}")

    if st.sidebar.button("이전값 불러오기"):
        st.session_state["confirm_load_previous_csv"] = True

    if st.session_state.get("confirm_load_previous_csv", False):
        st.sidebar.warning("진짜 불러오겠습니까? 현재 작업 내용이 덮어 씌워질 수 있습니다.")
        if st.sidebar.button("불러오기 확인"):
            current_df = get_master_dataframe()
            if current_df is None or current_df.empty:
                st.sidebar.error("현재 데이터프레임이 비어 있어 불러올 수 없습니다.")
                st.session_state["confirm_load_previous_csv"] = False
                return

            loaded_df = load_previous_defect_values(latest_csv)
            merged_df = apply_loaded_defect_values(current_df, loaded_df)
            set_master_dataframe(merged_df)
            touch_label_sync_token()
            st.session_state["confirm_load_previous_csv"] = False
            st.sidebar.success(f"불러오기 완료: {latest_csv.name}")
            st.rerun()


def _render_save_section(df: pd.DataFrame, image_map: dict[str, dict[str, object]]) -> None:
    """Render CSV and image save controls."""
    st.divider()
    st.subheader("저장")

    employee_id = str(st.session_state.get("auth_employee_id", "")).strip() or "unknown"

    separate_image_path = st.checkbox("별도 경로 생성하기", value=False)
    custom_image_root = ""
    if separate_image_path:
        custom_image_root = st.text_input("이미지 저장 상위 폴더명", value="")

    image_save_root = IMAGE_EXPORT_ROOT_DIR
    if separate_image_path and custom_image_root.strip():
        image_save_root = Path(IMAGE_EXPORT_ROOT_DIR) / sanitize_token(custom_image_root.strip(), fallback="custom")

    session_name = st.text_input("이미지 저장 세션 폴더명", value="session_01")
    if st.button("이미지 저장"):
        result = save_defect_images(
            df=df,
            image_map=image_map,
            save_root=image_save_root,
            session_name=session_name,
        )
        st.success(
            f"이미지 저장 완료 - saved: {result['saved']}, skipped: {result['skipped']}"
        )

    csv_output_dir, csv_filename = _resolve_csv_output_dir_and_filename(employee_id)
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")

    st.caption(f"CSV 저장 경로: {csv_output_dir}")
    if st.button("CSV 파일 저장"):
        if not EMPLOYEE_ID_PATTERN.match(employee_id):
            st.error("CSV 저장 실패: employee_id 형식이 올바르지 않습니다. (예: so12345)")
            return
        saved_path = export_csv_without_filling_ok(df, csv_output_dir, csv_filename)
        st.success(f"CSV 저장 완료: {saved_path}")

    st.download_button(
        "CSV 저장",
        data=csv_bytes,
        file_name=csv_filename,
        mime="text/csv",
    )

    st.caption("CSV 추출 대상 데이터프레임")
    st.dataframe(df, use_container_width=True)


def _resolve_csv_output_dir_and_filename(employee_id: str) -> tuple[Path, str]:
    """Resolve matched output folder and next versioned file name."""
    upload_source_type = st.session_state.get(KEY_UPLOAD_SOURCE_TYPE, "drag_upload")
    selected_subpath = st.session_state.get(KEY_SELECTED_IMAGE_SUBPATH)

    if not EMPLOYEE_ID_PATTERN.match(employee_id):
        st.warning("employee_id 형식은 영문 2자 + 숫자 5자여야 합니다. (예: so12345)")

    if upload_source_type == "folder_select" and isinstance(selected_subpath, str) and selected_subpath.strip():
        parts = [part for part in selected_subpath.split("/") if part]
        if len(parts) >= 2:
            line, period = parts[0], parts[1]
            target_dir = ensure_result_folder_from_selected_subpath(CSV_OUTPUT_ROOT_DIR, f"{line}/{period}")
            latest = find_latest_csv_version(target_dir)
            next_version = build_next_version(latest)
            file_name = build_next_version_filename(line, period, employee_id, next_version)
            return target_dir, file_name

    root_dir = ensure_directory(CSV_OUTPUT_ROOT_DIR)
    existing_subdirs = ["(root)", *list_subdirectories_relative(root_dir)]
    selected_existing = st.selectbox("CSV 저장 하위 폴더 선택", options=existing_subdirs)
    chosen_dir = root_dir if selected_existing == "(root)" else ensure_directory(root_dir / selected_existing)
    latest = find_latest_csv_version(chosen_dir)
    next_version = build_next_version(latest)
    file_name = build_next_version_filename("manual", "manual", employee_id, next_version)
    return chosen_dir, file_name


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
