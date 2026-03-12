"""Shared constants for dataframe schema, session keys, and page names."""

from __future__ import annotations

# Dataframe columns (must remain stable)
COL_CELL_ID = "cell_id"

COL_CA_TOP = "CA(TOP)"
COL_CA_BOT = "CA(BOT)"
COL_AN_TOP = "AN(TOP)"
COL_AN_BOT = "AN(BOT)"
POSITION_COLUMNS = [COL_CA_TOP, COL_CA_BOT, COL_AN_TOP, COL_AN_BOT]

COL_DEFECT_CA_TOP = "Defect_CA(TOP)"
COL_DEFECT_CA_BOT = "Defect_CA(BOT)"
COL_DEFECT_AN_TOP = "Defect_AN(TOP)"
COL_DEFECT_AN_BOT = "Defect_AN(BOT)"
DEFECT_COLUMNS = [
    COL_DEFECT_CA_TOP,
    COL_DEFECT_CA_BOT,
    COL_DEFECT_AN_TOP,
    COL_DEFECT_AN_BOT,
]

BASE_DF_COLUMNS = [COL_CELL_ID, *POSITION_COLUMNS, *DEFECT_COLUMNS]

# Session state keys
KEY_MASTER_DF = "master_df"
KEY_IMAGE_MAP = "image_map"
KEY_CURRENT_CELL_INDEX = "current_cell_index"
KEY_UPLOAD_COMPLETED = "upload_completed"
KEY_LABEL_SYNC_TOKEN = "label_sync_token"

SESSION_DEFAULTS = {
    KEY_MASTER_DF: None,
    KEY_IMAGE_MAP: {},
    KEY_CURRENT_CELL_INDEX: 0,
    KEY_UPLOAD_COMPLETED: False,
    KEY_LABEL_SYNC_TOKEN: 0,
}

# Page names (v1, two-page structure)
PAGE_UPLOAD = "upload"
PAGE_LABELING = "labeling"
PAGES = [PAGE_UPLOAD, PAGE_LABELING]
