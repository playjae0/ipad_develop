"""Saving utilities for CSV export and labeled image export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import TIMESTAMP_FORMAT
from src.constants import (
    COL_CELL_ID,
    COL_DEFECT_AN_BOT,
    COL_DEFECT_AN_TOP,
    COL_DEFECT_CA_BOT,
    COL_DEFECT_CA_TOP,
)
from utils.io_utils import dataframe_to_csv_bytes, get_timestamp
from utils.naming_utils import (
    build_labeled_image_filename,
    infer_extension_from_path,
    sanitize_token,
)
from utils.path_utils import ensure_directory

POSITION_TO_DEFECT_COLUMN: dict[str, str] = {
    "CA(TOP)": COL_DEFECT_CA_TOP,
    "CA(BOT)": COL_DEFECT_CA_BOT,
    "AN(TOP)": COL_DEFECT_AN_TOP,
    "AN(BOT)": COL_DEFECT_AN_BOT,
}


def build_csv_export_payload(df: pd.DataFrame, base_filename: str) -> tuple[str, bytes]:
    """Build timestamped CSV filename and payload bytes.

    Returns:
        (output_filename, csv_bytes)
    """
    safe_base = sanitize_token(base_filename or "labeling_result", fallback="labeling_result")
    timestamp = get_timestamp(TIMESTAMP_FORMAT)
    output_name = f"{safe_base}_{timestamp}.csv"
    return output_name, dataframe_to_csv_bytes(df)


def save_defect_images(
    *,
    df: pd.DataFrame,
    image_map: dict[str, dict[str, Any]],
    save_root: str | Path,
    session_name: str,
) -> dict[str, int]:
    """Save non-empty and non-ok defect images into structured folders.

    Save structure:
        [session_folder]/[position]/[defect]/[position]_[defect]_[cell_id].[ext]
    """
    safe_session = sanitize_token(session_name or "session", fallback="session")
    session_root = ensure_directory(Path(save_root) / safe_session)

    saved_count = 0
    skipped_count = 0

    for _, row in df.iterrows():
        cell_id = str(row[COL_CELL_ID])

        for position, defect_column in POSITION_TO_DEFECT_COLUMN.items():
            defect_raw = str(row.get(defect_column, "") or "").strip()
            if not defect_raw:
                skipped_count += 1
                continue
            if defect_raw.lower() == "ok":
                skipped_count += 1
                continue

            image_ref = image_map.get(cell_id, {}).get(position)
            if image_ref is None:
                skipped_count += 1
                continue

            try:
                extension = _infer_extension(image_ref)
                file_name = build_labeled_image_filename(position, defect_raw, cell_id, extension)
                defect_dir = ensure_directory(
                    session_root / sanitize_token(position) / sanitize_token(defect_raw)
                )
                output_path = defect_dir / file_name
                output_path.write_bytes(_read_image_bytes(image_ref))
                saved_count += 1
            except Exception:
                skipped_count += 1

    return {"saved": saved_count, "skipped": skipped_count}


def _infer_extension(image_ref: Any) -> str:
    """Infer extension from path-like or uploaded-file-like reference."""
    if isinstance(image_ref, (str, Path)):
        return infer_extension_from_path(str(image_ref))

    if hasattr(image_ref, "name"):
        return infer_extension_from_path(str(image_ref.name))

    raise ValueError("Cannot infer image extension from image reference.")


def _read_image_bytes(image_ref: Any) -> bytes:
    """Read image bytes from path-like or uploaded-file-like object."""
    if isinstance(image_ref, Path):
        return image_ref.read_bytes()

    if isinstance(image_ref, str):
        return Path(image_ref).read_bytes()

    if hasattr(image_ref, "getvalue"):
        data = image_ref.getvalue()
        return data if isinstance(data, bytes) else bytes(data)

    if hasattr(image_ref, "read"):
        data = image_ref.read()
        if hasattr(image_ref, "seek"):
            image_ref.seek(0)
        return data if isinstance(data, bytes) else bytes(data)

    raise ValueError("Unsupported image reference type for saving.")
