# Analytics UI

A Streamlit app for exploring CSV/Excel data: pick a file, choose which sheets to use, blend (join) tables together, filter and pick columns interactively, and visualize the results.

## Features

- Choose a CSV or Excel file from your Desktop, or upload one from anywhere
- Excel files with multiple sheets: pick which sheets (tables) to include
- Data blending: join two or more tables together (inner/left/right/outer)
- Table views: see the combined result and each original table separately, with scrolling for large tables
- Column selector: show/hide columns per table view
- Drag-and-drop filters: drag a column into the "Active filters" zone to filter that table, tables update live
- Visualization: build bar/line/scatter/histogram/pie/box charts from any table view

## Project structure

```
analytics_ui/
  app.py                  # main entry point (AnalyticsApp class)
  requirements.txt
  src/
    file_loader.py        # pick & load CSV/Excel files
    table_selector.py      # choose which sheets to use
    data_blender.py        # join tables together
    column_selector.py     # show/hide columns per view
    filter_manager.py       # drag-and-drop filters
    table_viewer.py          # tabbed table views
    visualizer.py             # charts
```

## Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/<your-username>/analytics-ui.git
   cd analytics-ui
   ```
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```
3. Activate it:
   - Mac/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run

```bash
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501`.

## Requirements

- Python 3.9+
