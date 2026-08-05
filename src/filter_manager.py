"""Feature 8 & 9: drag columns into an 'active filters' zone, then filter
tables interactively as those filters are adjusted."""
from __future__ import annotations
import hashlib
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

    def _widget_for_column(self, df: pd.DataFrame, col: str, key: str, label: str):
        """Renders the filter widget and returns a predicate(df, col) that
        applies it — col is passed in at apply-time so the same predicate can
        be reused against a view where the field has a different name."""
        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            lo, hi = float(series.min()), float(series.max())
            if lo == hi:
                st.caption(f"**{label}**: single value ({lo})")
                return None
            current = st.session_state.get(key)
            if not (isinstance(current, tuple) and lo <= current[0] <= current[1] <= hi):
                self._clear_stale_widget_state(key)
            chosen = st.slider(label, lo, hi, (lo, hi), key=key)
            return lambda d, c: d[(d[c] >= chosen[0]) & (d[c] <= chosen[1])]

        if pd.api.types.is_datetime64_any_dtype(series):
            lo, hi = series.min().date(), series.max().date()
            self._clear_stale_widget_state(key)
            chosen = st.date_input(label, (lo, hi), min_value=lo, max_value=hi, key=key)
            if isinstance(chosen, tuple) and len(chosen) == 2:
                start, end = chosen
                return lambda d, c: d[(d[c].dt.date >= start) & (d[c].dt.date <= end)]
            return None

        uniques = sorted(series.dropna().unique().tolist(), key=str)
        if len(uniques) <= MAX_CATEGORICAL_OPTIONS:
            current = st.session_state.get(key)
            if current is not None and any(v not in uniques for v in current):
                self._clear_stale_widget_state(key)
            chosen = st.multiselect(label, uniques, default=uniques, key=key)
            return lambda d, c: d[d[c].isin(chosen)]

        text = st.text_input(f"{label} contains", key=key)
        if text:
            return lambda d, c: d[d[c].astype(str).str.contains(text, case=False, na=False)]
        return None

    @staticmethod
    def _build_groups(
        views: dict[str, pd.DataFrame], join_key_groups: list[set[str]]
    ) -> list[tuple[str, list[str]]]:
        """Collapses columns that were used as equal join keys (e.g. Symbol /
        TICKER) into a single logical field, so one filter drives every
        table that field appears in under any of its names. Returns a list
        of (label, [raw column names]) in first-seen order."""
        seen: set[str] = set()
        groups: list[tuple[str, list[str]]] = []
        for df in views.values():
            for col in df.columns:
                if col in seen:
                    continue
                names = next((g for g in join_key_groups if col in g), {col})
                ordered_names = [col] + sorted(names - {col})
                seen.update(names)
                groups.append((" = ".join(ordered_names), ordered_names))
        return groups

    def render(
        self,
        views: dict[str, pd.DataFrame],
        join_key_groups: list[set[str]] | None = None,
    ) -> dict[str, pd.DataFrame]:
        st.header("5. Filters (drag columns to build them)")

        if not views:
            return views

        # One shared filter builder across every view: a column that exists
        # in multiple tables (or was used as a join key, even under a
        # different name) gets a single control, applied to every view that
        # has a matching field — like a data model.
        groups = self._build_groups(views, join_key_groups or [])
        label_to_names = dict(groups)
        labels = [label for label, _ in groups]

        state_key = "active_filters"
        active = [c for c in st.session_state.get(state_key, []) if c in labels]
        available = [c for c in labels if c not in active]

        containers = [
            {"header": "Available columns", "items": available},
            {"header": "Active filters (drag columns here)", "items": active},
        ]
        # streamlit_sortables keeps its own client-side drag state once
        # mounted under a key, so the key must change whenever the set of
        # groups changes (e.g. a join merges two columns into one field) —
        # otherwise it keeps showing the stale, pre-join item list.
        groups_signature = hashlib.md5("|".join(labels).encode()).hexdigest()[:8]
        result = sort_items(
            containers,
            multi_containers=True,
            direction="horizontal",
            key=f"sortable_filters_{groups_signature}",
        )
        new_active = result[1]["items"] if result else active
        st.session_state[state_key] = new_active

        predicates = {}
        if new_active:
            filter_cols = st.columns(min(len(new_active), 3))
            for i, label in enumerate(new_active):
                names = label_to_names.get(label, [label])
                source = next(
                    ((df, c) for df in views.values() for c in names if c in df.columns),
                    None,
                )
                if source is None:
                    continue
                source_df, source_col = source
                with filter_cols[i % len(filter_cols)]:
                    predicate = self._widget_for_column(
                        source_df, source_col, f"filter_{label}", label
                    )
                if predicate is not None:
                    predicates[label] = (predicate, names)

        filtered_views = {}
        for name, df in views.items():
            filtered = df
            for predicate, names in predicates.values():
                matching_col = next((c for c in names if c in filtered.columns), None)
                if matching_col is not None:
                    filtered = predicate(filtered, matching_col)
            st.caption(f"{name}: {filtered.shape[0]} of {df.shape[0]} rows shown after filters")
            filtered_views[name] = filtered
        return filtered_views
