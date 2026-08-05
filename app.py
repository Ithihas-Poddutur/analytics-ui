"""Entry point: run with `streamlit run app.py`.

AnalyticsApp is the main class. It owns one instance of each feature class
and simply calls them in sequence, passing each stage's output into the
next. All the actual feature logic lives in src/*.py.
"""
import streamlit as st

from src.column_selector import ColumnSelector
from src.data_blender import DataBlender
from src.file_loader import FileLoader
from src.filter_manager import FilterManager
from src.table_selector import TableSelector
from src.table_viewer import TableViewer
from src.visualizer import Visualizer


class AnalyticsApp:
    def __init__(self):
        self.file_loader = FileLoader()
        self.table_selector = TableSelector()
        self.blender = DataBlender()
        self.column_selector = ColumnSelector()
        self.filter_manager = FilterManager()
        self.table_viewer = TableViewer()
        self.visualizer = Visualizer()

    def run(self):
        st.set_page_config(page_title="Analytics UI", layout="wide")
        st.title("Analytics UI")

        sheets = self.file_loader.render()
        if not sheets:
            return

        st.divider()
        selected_tables = self.table_selector.render(sheets)
        if not selected_tables:
            return

        st.divider()
        visible_tables = self.column_selector.render(selected_tables)

        st.divider()
        blended_df = self.blender.render(visible_tables)
        join_key_groups = self.blender.get_join_key_groups()

        views = dict(visible_tables)
        if blended_df is not None:
            views = {"Combined": blended_df, **visible_tables}

        st.divider()
        filtered_views = self.filter_manager.render(views, join_key_groups)

        st.divider()
        self.table_viewer.render(filtered_views)

        st.divider()
        self.visualizer.render(filtered_views)


if __name__ == "__main__":
    AnalyticsApp().run()
