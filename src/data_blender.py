"""Feature 3: blend (join) two or more tables together."""
from __future__ import annotations
import pandas as pd
import streamlit as st

JOIN_TYPES = ["inner", "left", "right", "outer"]


class DataBlender:
    """Builds a chain of joins on top of a base table. Each step joins the
    result-so-far with one more selected table. Returns the final blended
    DataFrame, or None if the user hasn't configured any joins."""

    def _init_state(self):
        if "join_steps" not in st.session_state:
            st.session_state.join_steps = []  # list of dicts: table, left_on, right_on, how

    def render(self, tables: dict[str, pd.DataFrame]) -> pd.DataFrame | None:
        st.header("3. Data blending (joins)")
        self._init_state()

        names = list(tables.keys())
        if len(names) < 2:
            st.caption("Select 2 or more tables above to enable blending.")
            st.session_state.join_steps = []
            return None

        base_name = st.selectbox("Base table", names, key="blend_base_table")

        # keep only steps whose table is still a valid, not-yet-used choice
        already_used = {base_name}
        valid_steps = []
        for step in st.session_state.join_steps:
            if step["table"] in tables and step["table"] not in already_used:
                valid_steps.append(step)
                already_used.add(step["table"])
        st.session_state.join_steps = valid_steps

        blended = tables[base_name].copy()
        blended_source_cols = {c: base_name for c in blended.columns}

        for i, step in enumerate(st.session_state.join_steps):
            right_df = tables[step["table"]]
            try:
                blended = blended.merge(
                    right_df,
                    left_on=step["left_on"],
                    right_on=step["right_on"],
                    how=step["how"],
                    suffixes=("", f"_{step['table']}"),
                )
            except Exception as e:
                st.error(f"Join #{i + 1} with '{step['table']}' failed: {e}")
                continue
            for c in right_df.columns:
                blended_source_cols.setdefault(c, step["table"])

            cols_line = st.columns([5, 1])
            cols_line[0].success(
                f"Joined **{step['table']}** on "
                f"{step['left_on']} = {step['right_on']} ({step['how']})"
            )
            if cols_line[1].button("Remove", key=f"remove_join_{i}"):
                st.session_state.join_steps.pop(i)
                st.rerun()

        remaining = [n for n in names if n not in already_used]
        if remaining:
            with st.expander("Add a join step", expanded=len(st.session_state.join_steps) == 0):
                join_table = st.selectbox("Join with table", remaining, key="new_join_table")
                left_cols = st.multiselect(
                    "Key column(s) from left/blended side",
                    list(blended.columns),
                    key="new_join_left_cols",
                )
                right_cols = st.multiselect(
                    "Key column(s) from right table",
                    list(tables[join_table].columns),
                    key="new_join_right_cols",
                )
                how = st.selectbox("Join type", JOIN_TYPES, key="new_join_how")

                if st.button("Add join"):
                    if not left_cols or not right_cols:
                        st.warning("Pick at least one key column on each side.")
                    elif len(left_cols) != len(right_cols):
                        st.warning("Left and right key columns must have the same count.")
                    else:
                        st.session_state.join_steps.append(
                            {
                                "table": join_table,
                                "left_on": left_cols,
                                "right_on": right_cols,
                                "how": how,
                            }
                        )
                        st.rerun()

        if not st.session_state.join_steps:
            return None

        st.caption(f"Blended result: {blended.shape[0]} rows x {blended.shape[1]} cols")
        return blended
