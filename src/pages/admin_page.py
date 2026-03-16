"""Admin page for access history visibility."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import AUTH_DB_PATH
from src.auth.user_store import list_dataset_access_history, list_successful_login_history


def render_admin_page() -> None:
    """Render admin-only history dashboards."""
    st.title("관리자 페이지")

    st.subheader("로그인 이력")
    login_rows = list_successful_login_history(AUTH_DB_PATH)
    if login_rows:
        st.dataframe(pd.DataFrame(login_rows), use_container_width=True)
    else:
        st.info("로그인 이력이 없습니다.")

    st.subheader("데이터셋 접근 이력")
    access_rows = list_dataset_access_history(AUTH_DB_PATH)
    if access_rows:
        st.dataframe(pd.DataFrame(access_rows), use_container_width=True)
    else:
        st.info("데이터셋 접근 이력이 없습니다.")
