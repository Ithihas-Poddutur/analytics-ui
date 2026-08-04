"""Feature 7: build a chart from any of the (filtered) table views."""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st

CHART_TYPES = ["Bar", "Line", "Scatter", "Histogram", "Pie", "Box"]


class Visualizer:
    def _build(self, chart_type: str, df: pd.DataFrame, x: str, y: str | None, color: str | None):
        kwargs = {"color": color} if color and color != "None" else {}
        if chart_type == "Bar":
            return px.bar(df, x=x, y=y, **kwargs)
        if chart_type == "Line":
            return px.line(df, x=x, y=y, **kwargs)
        if chart_type == "Scatter":
            return px.scatter(df, x=x, y=y, **kwargs)
        if chart_type == "Histogram":
            return px.histogram(df, x=x, **kwargs)
        if chart_type == "Pie":
            return px.pie(df, names=x, values=y)
        if chart_type == "Box":
            return px.box(df, x=x, y=y, **kwargs)
        return None

    def render(self, views: dict[str, pd.DataFrame]):
        st.header("7. Visualize")

        views = {name: df for name, df in views.items() if not df.empty}
        if not views:
            st.info("No data available to visualize.")
            return

        table_name = st.selectbox("Table", list(views.keys()), key="viz_table")
        df = views[table_name]
        columns = list(df.columns)

        c1, c2, c3, c4 = st.columns(4)
        chart_type = c1.selectbox("Chart type", CHART_TYPES, key="viz_chart_type")
        x = c2.selectbox("X axis / labels", columns, key="viz_x")
        needs_y = chart_type != "Histogram"
        y = c3.selectbox("Y axis / values", columns, key="viz_y") if needs_y else None
        color = c4.selectbox("Color by", ["None"] + columns, key="viz_color")

        fig = self._build(chart_type, df, x, y, color)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
