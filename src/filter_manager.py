"""Feature 8 & 9: drag columns into an 'active filters' zone, then filter
tables interactively as those filters are adjusted."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items

MAX_CATEGORICAL_OPTIONS = 50


class FilterManager:
    @staticmethod
    def _clear_stale_widget_state(key: str):
        """Drop a widget's remembered value if it no longer fits the current
        data (e.g. the user loaded a different file with the same column
        name), which would otherwise raise a Streamlit API error."""
        st.session_state.pop(key, None)

    def _widget_for_column(self, df: pd.DataFrame, col: str, key: str):
        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            lo, hi = float(series.min()), float(series.max())
            if lo == hi:
                st.caption(f"**{col}**: single value ({lo})")
                return None
            current = st.session_state.get(key)
            if not (isinstance(current, tuple) and lo <= current[0] <= current[1] <= hi):
                self._clear_stale_widget_state(key)
            chosen = st.slider(col, lo, hi, (lo, hi), key=key)
            return lambda d: d[(d[col] >= chosen[0]) & (d[col] <= chosen[1])]

        if pd.api.types.is_datetime64_any_dtype(series):
            lo, hi = series.min().date(), series.max().date()
            self._clear_stale_widget_state(key)
            chosen = st.date_input(col, (lo, hi), min_value=lo, max_value=hi, key=key)
            if isinstance(chosen, tuple) and len(chosen) == 2:
                start, end = chosen
                return lambda d: d[(d[col].dt.date >= start) & (d[col].dt.date <= end)]
            return None

        uniques = sorted(series.dropna().unique().tolist(), key=str)
        if len(uniques) <= MAX_CATEGORICAL_OPTIONS:
            current = st.session_state.get(key)
            if current is not None and any(v not in uniques for v in current):
                self._clear_stale_widget_state(key)
            chosen = st.multiselect(col, uniques, default=uniques, key=key)
            return lambda d: d[d[col].isin(chosen)]

        text = st.text_input(f"{col} contains", key=key)
        if text:
            return lambda d: d[d[col].astype(str).str.contains(text, case=False, na=False)]
        return None

    def render(self, views: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        st.header("5. Filters (drag columns to build them)")

        filtered_views = {}
        for name, df in views.items():
            st.subheader(name)

            state_key = f"active_filters_{name}"
            active = [c for c in st.session_state.get(state_key, []) if c in df.columns]
            available = [c for c in df.columns if c not in active]

            containers = [
                {"header": "Available columns", "items": available},
                {"header": "Active filters (drag columns here)", "items": active},
            ]
            result = sort_items(
                containers, multi_containers=True, direction="horizontal", key=f"sortable_{name}"
            )
            new_active = result[1]["items"] if result else active
            st.session_state[state_key] = new_active

            filtered = df
            if new_active:
                filter_cols = st.columns(min(len(new_active), 3))
                for i, col in enumerate(new_active):
                    if col not in filtered.columns:
                        continue
                    with filter_cols[i % len(filter_cols)]:
                        predicate = self._widget_for_column(df, col, f"filter_{name}_{col}")
                    if predicate is not None:
                        filtered = predicate(filtered)

            st.caption(f"{filtered.shape[0]} of {df.shape[0]} rows shown after filters")
            filtered_views[name] = filtered
        return filtered_views
