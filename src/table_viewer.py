"""Feature 4 & 5: show the combined table and each separate table at once —
the combined table full-width on top, the individual tables tiled below."""
from __future__ import annotations
import pandas as pd
import streamlit as st

ROW_HEIGHT_PX = 35
MAX_TABLE_HEIGHT_PX = 500
MIN_TABLE_HEIGHT_PX = 150
MAX_TABLES_PER_ROW = 3


class TableViewer:
    @staticmethod
    def _render_table(name: str, df: pd.DataFrame):
        st.subheader(name)
        st.caption(f"{df.shape[0]} rows x {df.shape[1]} columns")
        height = min(
            MAX_TABLE_HEIGHT_PX,
            max(MIN_TABLE_HEIGHT_PX, ROW_HEIGHT_PX * (len(df) + 1)),
        )
        st.dataframe(df, use_container_width=True, height=height)

    def render(self, views: dict[str, pd.DataFrame]):
        st.header("6. Table views")

        if not views:
            st.info("No tables to display yet.")
            return

        remaining = dict(views)
        if "Combined" in remaining:
            self._render_table("Combined", remaining.pop("Combined"))

        names = list(remaining.keys())
        if not names:
            return

        cols = st.columns(min(len(names), MAX_TABLES_PER_ROW) or 1)
        for i, name in enumerate(names):
            with cols[i % len(cols)]:
                self._render_table(name, remaining[name])
