"""Session-state management utilities for the Streamlit app (Step 1)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.constants import (
    KEY_CURRENT_CELL_INDEX,
    KEY_IMAGE_MAP,
    KEY_LABEL_SYNC_TOKEN,
    KEY_MASTER_DF,
    KEY_UPLOAD_COMPLETED,
    SESSION_DEFAULTS,
)


def initialize_session_state() -> None:
    """Initialize required session_state keys with stable defaults."""
    for key, default_value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            # Copy mutable defaults to avoid accidental cross-reference updates.
            st.session_state[key] = default_value.copy() if isinstance(default_value, dict) else default_value


def set_master_dataframe(df: pd.DataFrame | None) -> None:
    """Store the master dataframe in session state."""
    st.session_state[KEY_MASTER_DF] = df


def get_master_dataframe() -> pd.DataFrame | None:
    """Return the stored master dataframe, if available."""
    value: Any = st.session_state.get(KEY_MASTER_DF)
    if value is None:
        return None
    if isinstance(value, pd.DataFrame):
        return value
    raise TypeError("Session state value for master dataframe is not a pandas DataFrame.")


def set_image_map(image_map: dict[str, dict[str, Any]]) -> None:
    """Store image references outside dataframe as image_map."""
    st.session_state[KEY_IMAGE_MAP] = image_map


def get_image_map() -> dict[str, dict[str, Any]]:
    """Get image_map from session state."""
    value: Any = st.session_state.get(KEY_IMAGE_MAP, {})
    if isinstance(value, dict):
        return value
    raise TypeError("Session state value for image_map is not a dictionary.")


def set_current_cell_index(index: int) -> None:
    """Store selected cell index for navigation persistence."""
    if index < 0:
        raise ValueError("Current cell index cannot be negative.")
    st.session_state[KEY_CURRENT_CELL_INDEX] = index


def get_current_cell_index() -> int:
    """Retrieve current selected cell index."""
    value: Any = st.session_state.get(KEY_CURRENT_CELL_INDEX, 0)
    if isinstance(value, int):
        return value
    raise TypeError("Session state value for current cell index is not an integer.")


def set_upload_completed(is_completed: bool) -> None:
    """Update upload completion status."""
    st.session_state[KEY_UPLOAD_COMPLETED] = is_completed


def is_upload_completed() -> bool:
    """Return upload completion status."""
    value: Any = st.session_state.get(KEY_UPLOAD_COMPLETED, False)
    if isinstance(value, bool):
        return value
    raise TypeError("Session state value for upload completion is not a boolean.")


def touch_label_sync_token() -> int:
    """Increment and return a sync token to trigger labeling UI refresh logic."""
    current = st.session_state.get(KEY_LABEL_SYNC_TOKEN, 0)
    if not isinstance(current, int):
        current = 0
    current += 1
    st.session_state[KEY_LABEL_SYNC_TOKEN] = current
    return current


def get_label_sync_token() -> int:
    """Get the current label sync token value."""
    value: Any = st.session_state.get(KEY_LABEL_SYNC_TOKEN, 0)
    if isinstance(value, int):
        return value
    raise TypeError("Session state value for label sync token is not an integer.")
