"""Feature 1 & 2: pick a CSV/Excel file and load its sheets as separate tables."""
from __future__ import annotations
from pathlib import Path

import pandas as pd
import streamlit as st

SUPPORTED_SUFFIXES = (".csv", ".xlsx", ".xls", ".xlsm")


class FileLoader:
    """Lets the user pick a file (from the Desktop or via upload) and returns
    a dict of {table_name: DataFrame}, one entry per sheet (Excel) or a single
    entry (CSV)."""

    def __init__(self, desktop_dir: Path | None = None):
        self.desktop_dir = desktop_dir or (Path.home() / "Desktop")

    def _find_desktop_files(self) -> list[Path]:
        if not self.desktop_dir.exists():
            return []
        files = [
            p
            for p in self.desktop_dir.rglob("*")
            if p.is_file()
            and p.suffix.lower() in SUPPORTED_SUFFIXES
            and not any(part.startswith(".") for part in p.parts)
        ]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    @staticmethod
    @st.cache_data(show_spinner="Reading file...")
    def _read_sheets(file_bytes: bytes, suffix: str, name: str) -> dict[str, pd.DataFrame]:
        import io

        buf = io.BytesIO(file_bytes)
        if suffix == ".csv":
            return {name: pd.read_csv(buf)}
        return pd.read_excel(buf, sheet_name=None)

    def render(self) -> dict[str, pd.DataFrame]:
        st.header("1. Choose a data file")

        source = st.radio(
            "Where is the file?",
            ["Desktop", "Upload from elsewhere"],
            horizontal=True,
            key="file_source",
        )

        file_bytes = None
        suffix = None
        base_name = None

        if source == "Desktop":
            desktop_files = self._find_desktop_files()
            if not desktop_files:
                st.warning(f"No CSV/Excel files found under {self.desktop_dir}.")
                return {}
            labels = [str(p.relative_to(self.desktop_dir)) for p in desktop_files]
            choice = st.selectbox("File on Desktop", labels, key="desktop_file_choice")
            path = desktop_files[labels.index(choice)]
            file_bytes = path.read_bytes()
            suffix = path.suffix.lower()
            base_name = path.stem
        else:
            uploaded = st.file_uploader(
                "Upload a CSV or Excel file", type=["csv", "xlsx", "xls", "xlsm"]
            )
            if uploaded is None:
                return {}
            file_bytes = uploaded.getvalue()
            suffix = Path(uploaded.name).suffix.lower()
            base_name = Path(uploaded.name).stem

        sheets = self._read_sheets(file_bytes, suffix, base_name)
        st.caption(f"Loaded {len(sheets)} table(s) from **{base_name}{suffix}**.")
        return sheets
