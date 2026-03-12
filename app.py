"""Streamlit app entrypoint with v1 two-page routing skeleton."""

from __future__ import annotations

import streamlit as st

from src.constants import PAGE_LABELING, PAGE_UPLOAD
from src.pages.upload_page import render_upload_page
from src.state_manager import initialize_session_state


def render_labeling_page_placeholder() -> None:
    """Temporary labeling placeholder for Step 3 routing validation."""
    st.title("라벨링 페이지")
    st.info("Step 3 범위에서는 라벨링 페이지 UI를 아직 구현하지 않았습니다.")

    if st.button("업로드 페이지로 돌아가기"):
        st.session_state["current_page"] = PAGE_UPLOAD
        st.rerun()


def main() -> None:
    """Application bootstrap and minimal two-page router."""
    initialize_session_state()

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = PAGE_UPLOAD

    with st.sidebar:
        st.header("Navigation")
        st.button("Upload", on_click=lambda: st.session_state.__setitem__("current_page", PAGE_UPLOAD))
        st.button("Labeling", on_click=lambda: st.session_state.__setitem__("current_page", PAGE_LABELING))

    if st.session_state["current_page"] == PAGE_UPLOAD:
        render_upload_page()
    else:
        render_labeling_page_placeholder()


if __name__ == "__main__":
    main()
