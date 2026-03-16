"""Application configuration for the Streamlit defect labeling platform (Step 1)."""

from __future__ import annotations

from pathlib import Path

# Upload settings
ALLOWED_EXTENSIONS: tuple[str, ...] = ("jpg", "jpeg", "png")
MAX_UPLOAD_COUNT: int = 4000

# Label settings
DEFAULT_DEFECT_LIST: list[str] = [
    "Crack",
    "Damage",
    "Scrap",
    "Dust",
    "Contamination",
    "Wrinkle",
    "Scratch",
    "Etc",
]
MAX_DEFECT_COUNT: int = 16

# Position settings (must stay fixed)
POSITIONS: list[str] = [
    "CA(TOP)",
    "CA(BOT)",
    "AN(TOP)",
    "AN(BOT)",
]

# Data source / output paths
IMAGE_ROOT_PATH: Path = Path("./data/images")
ATIS_FILE_PATH: Path = Path("./data/atis/atis.xlsx")
DEFAULT_SAVE_ROOT: Path = Path("./outputs")

# ATIS mapping placeholder for future merge rules
# key: target output column name, value: source ATIS column name
# Example:
# ATIS_COLUMN_MAPPING = {
#     "cell_id": "Cell ID",
#     "ATIS_CA(TOP)": "ENG Top Cathode",
#     "ATIS_CA(BOT)": "ENG Bottom Cathode",
#     "ATIS_AN(TOP)": "ENG Top Anode",
#     "ATIS_AN(BOT)": "ENG Bottom Anode",
# }
ATIS_COLUMN_MAPPING: dict[str, str] = {}

# Timestamp formatting
TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"
