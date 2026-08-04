"""Feature 4 & 5: show the combined table and each separate table, laying
out tabs so large tables get their own scrollable area."""
from __future__ import annotations
import pandas as pd
import streamlit as st

ROW_HEIGHT_PX = 35
MAX_TABLE_HEIGHT_PX = 500
MIN_TABLE_HEIGHT_PX = 150


class TableViewer:
    def render(self, views: dict[str, pd.DataFrame]):
        st.header("6. Table views")

        if not views:
            st.info("No tables to display yet.")
            return

        tab_names = list(views.keys())
        tabs = st.tabs(tab_names)
        for tab, name in zip(tabs, tab_names):
            with tab:
                df = views[name]
                st.caption(f"{df.shape[0]} rows x {df.shape[1]} columns")
                height = min(
                    MAX_TABLE_HEIGHT_PX,
                    max(MIN_TABLE_HEIGHT_PX, ROW_HEIGHT_PX * (len(df) + 1)),
                )
                st.dataframe(df, use_container_width=True, height=height)
