from pathlib import Path

import plotly.express as px
import polars as pl
import streamlit as st

from engine.postprocessing import process_simulation_data


def create_animation(df: pl.DataFrame, bounds: dict[str, list[float]]):
    """Creates an animated Plotly scatter chart from all timesteps."""
    records = []
    for row in df.iter_rows(named=True):
        ts = row["timeStep"]
        for col, val in row.items():
            if col.startswith("x") and val is not None:
                pid = col[1:]
                y_val = row.get(f"y{pid}")
                if y_val is not None:
                    records.append(
                        {
                            "Pedestrian": pid,
                            "X": val,
                            "Y": y_val,
                            "timeStep": ts,
                        }
                    )

    if not records:
        return None

    anim_df = pl.DataFrame(records)

    fig = px.scatter(
        anim_df,
        x="X",
        y="Y",
        hover_name="Pedestrian",
        animation_frame="timeStep",
        range_x=bounds["x"],
        range_y=bounds["y"],
    )

    fig.update_traces(marker_size=10, marker_color="red", marker_opacity=0.7)
    fig.update_layout(
        plot_bgcolor="white",
        xaxis_title="X (m)",
        yaxis_title="Y (m)",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
    )

    return fig


def render_timeline(df: pl.DataFrame, bounds: dict[str, list[float]]) -> None:
    """Renders the slider and the Plotly scatter chart for a given dataframe."""
    min_ts = df["timeStep"].min()
    max_ts = df["timeStep"].max()

    current_step = st.number_input(
        "TimeStep (Timeline)", min_value=min_ts, max_value=max_ts, value=min_ts
    )

    # Extract row for current timestep
    row_dict = df.filter(pl.col("timeStep") == current_step).to_dicts()[0]

    # Fast conversion from wide dict to long list of point dicts
    points = []
    for col, val in row_dict.items():
        if col.startswith("x") and val is not None:
            pid = col[1:]
            y_val = row_dict.get(f"y{pid}")
            if y_val is not None:
                points.append({"Pedestrian": pid, "X": val, "Y": y_val})

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Timestep")
        if points:
            plot_df = pl.DataFrame(points)

            fig = px.scatter(
                plot_df,
                x="X",
                y="Y",
                hover_name="Pedestrian",
                range_x=bounds["x"],
                range_y=bounds["y"],
            )

            fig.update_traces(marker_size=10, marker_color="blue", marker_opacity=0.7)
            fig.update_layout(
                plot_bgcolor="white",
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                xaxis_showgrid=False,
                yaxis_showgrid=False,
            )

            st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Animation")
        anim_fig = create_animation(df, bounds)
        st.plotly_chart(anim_fig, width="stretch")


def main() -> None:
    """Main application flow."""
    DATA_DIR = Path("data")
    OUTPUT_DIR = Path("expected_output")

    if not DATA_DIR.exists():
        st.sidebar.error(f"Directory `{DATA_DIR}` not found.")
        st.stop()

    folders = [f.name for f in DATA_DIR.iterdir() if f.is_dir()]
    selected_folder = st.sidebar.selectbox("Select Experiment", folders)

    if st.sidebar.button("Process Data", type="secondary"):
        input_file = DATA_DIR / selected_folder / "postvis_time.txt"
        output_file = OUTPUT_DIR / selected_folder / "postvis_time.csv"

        with st.spinner("Processing data..."):
            df = process_simulation_data(input_file, output_file)
            st.session_state["df"] = df

            # Precalculate global bounds across all timesteps
            x_cols = [c for c in df.columns if c.startswith("x")]
            y_cols = [c for c in df.columns if c.startswith("y")]

            st.session_state["bounds"] = {
                "x": [
                    df.select(pl.min_horizontal(x_cols)).min()[0, 0] - 1,
                    df.select(pl.max_horizontal(x_cols)).max()[0, 0] + 1,
                ],
                "y": [
                    df.select(pl.min_horizontal(y_cols)).min()[0, 0] - 1,
                    df.select(pl.max_horizontal(y_cols)).max()[0, 0] + 1,
                ],
            }

    # --- MAIN WINDOW ---
    if "df" in st.session_state:
        render_timeline(st.session_state["df"], st.session_state["bounds"])


if __name__ == "__main__":
    main()
