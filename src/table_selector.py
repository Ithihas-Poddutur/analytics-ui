"""Feature 2: pick which sheets/tables should be used for analytics."""
from __future__ import annotations
import pandas as pd
import streamlit as st


class TableSelector:
    """Given all tables found in the file, lets the user pick a subset to
    actually work with (avoids dragging unused sheets through the rest of
    the pipeline)."""

    def render(self, sheets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        st.header("2. Select tables to use")

        names = list(sheets.keys())
        selected_names = st.multiselect(
            "Tables (sheets) to include in this analysis",
            names,
            default=names,
            key="selected_table_names",
        )

        if not selected_names:
            st.info("Select at least one table to continue.")
            return {}

        with st.expander("Preview selected tables"):
            for name in selected_names:
                df = sheets[name]
                st.write(f"**{name}** — {df.shape[0]} rows x {df.shape[1]} cols")
                st.dataframe(df.head(5), use_container_width=True)

        return {name: sheets[name] for name in selected_names}
