"""Feature 6: choose which columns are visible in each table view."""
from __future__ import annotations
import pandas as pd
import streamlit as st


class ColumnSelector:
    """For every selected table, lets the user pick a subset of columns to
    display. Returns a dict of {view_name: DataFrame} trimmed to the chosen
    columns."""

    def render(self, views: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        st.header("3. Choose columns to display")

        trimmed = {}
        cols_ui = st.columns(min(len(views), 3) or 1)
        for i, (name, df) in enumerate(views.items()):
            with cols_ui[i % len(cols_ui)]:
                st.subheader(name)
                key = f"cols_{name}"
                default = st.session_state.get(key, list(df.columns))
                default = [c for c in default if c in df.columns] or list(df.columns)
                chosen = st.multiselect(
                    f"Columns for '{name}'",
                    list(df.columns),
                    default=default,
                    key=key,
                    label_visibility="collapsed",
                )
                trimmed[name] = df[chosen] if chosen else df.iloc[:, 0:0]
        return trimmed
