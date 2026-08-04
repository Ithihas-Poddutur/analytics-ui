"""Feature 1 & 2: pick a CSV/Excel file and load its sheets as separate tables."""
from __future__ import annotations
from pathlib import Path

import pandas as pd
import streamlit as st

SUPPORTED_SUFFIXES = (".csv", ".xlsx", ".xls", ".xlsm")


class FileLoader:
    """Lets the user pick one or more files (from the Desktop or via upload)
    and returns a dict of {table_name: DataFrame}, one entry per sheet
    (Excel) or a single entry (CSV), merged across all selected files."""

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

    def _merge_sheets(
        self, files: list[tuple[str, str, bytes]]
    ) -> dict[str, pd.DataFrame]:
        """files is a list of (base_name, suffix, file_bytes). Prefixes table
        names with the source file name once more than one file is loaded,
        so sheets/tables from different files don't collide or overwrite
        each other."""
        multiple = len(files) > 1
        merged: dict[str, pd.DataFrame] = {}
        for base_name, suffix, file_bytes in files:
            sheets = self._read_sheets(file_bytes, suffix, base_name)
            for sheet_name, df in sheets.items():
                key = f"{base_name} — {sheet_name}" if multiple else sheet_name
                if key in merged:
                    key = f"{base_name} — {sheet_name} ({suffix.lstrip('.')})"
                merged[key] = df
        return merged

    def render(self) -> dict[str, pd.DataFrame]:
        st.header("1. Choose data file(s)")

        source = st.radio(
            "Where are the files?",
            ["Desktop", "Upload from elsewhere"],
            horizontal=True,
            key="file_source",
        )

        files: list[tuple[str, str, bytes]] = []

        if source == "Desktop":
            desktop_files = self._find_desktop_files()
            if not desktop_files:
                st.warning(f"No CSV/Excel files found under {self.desktop_dir}.")
                return {}
            labels = [str(p.relative_to(self.desktop_dir)) for p in desktop_files]
            choices = st.multiselect(
                "File(s) on Desktop", labels, key="desktop_file_choices"
            )
            if not choices:
                return {}
            for choice in choices:
                path = desktop_files[labels.index(choice)]
                files.append((path.stem, path.suffix.lower(), path.read_bytes()))
        else:
            uploaded_files = st.file_uploader(
                "Upload CSV or Excel file(s)",
                type=["csv", "xlsx", "xls", "xlsm"],
                accept_multiple_files=True,
            )
            if not uploaded_files:
                return {}
            for uploaded in uploaded_files:
                files.append(
                    (
                        Path(uploaded.name).stem,
                        Path(uploaded.name).suffix.lower(),
                        uploaded.getvalue(),
                    )
                )

        merged = self._merge_sheets(files)
        file_names = ", ".join(f"**{name}{suffix}**" for name, suffix, _ in files)
        st.caption(f"Loaded {len(merged)} table(s) from {file_names}.")
        return merged
