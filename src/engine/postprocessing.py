from pathlib import Path

import polars as pl


def process_simulation_data(input_path: str | Path, output_path: str | Path) -> pl.DataFrame:
    """
    Parses raw simulation output data.
    Transforms by mapping each timestep to one row and each pedestrianId to a column.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # 1. Read data
    df = pl.read_csv(input_path, separator=" ")

    cols = df.columns
    if len(cols) < 4:
        print(f"Warning: Unexpected data format in {input_path}")
        return pl.DataFrame()

    # 2. Ensure consistent scheme
    df = df.rename(
        {cols[0]: "timeStep", cols[1]: "pedestrianId", cols[2]: "x", cols[3]: "y"}
    ).select(["timeStep", "pedestrianId", "x", "y"])

    # 3. Get unique pedestrian IDs by order of occurrence
    pids = df["pedestrianId"].unique(maintain_order=True).to_list()

    # 4. Pivot X and Y separately (transform long data to wide data)
    df_x = df.pivot(index="timeStep", on="pedestrianId", values="x", aggregate_function="first")
    df_x = df_x.rename({col: f"x{col}" for col in df_x.columns if col != "timeStep"})

    df_y = df.pivot(index="timeStep", on="pedestrianId", values="y", aggregate_function="first")
    df_y = df_y.rename({col: f"y{col}" for col in df_y.columns if col != "timeStep"})

    # 5. Join them together
    pivot_df = df_x.join(df_y, on="timeStep", how="inner").sort("timeStep")

    # 6. Reorder columns to an interleaved pattern (timeStep, x1, y1, x2, y2, ...)
    ordered_cols = ["timeStep"]
    for pid in pids:
        ordered_cols.extend([f"x{pid}", f"y{pid}"])

    pivot_df = pivot_df.select(ordered_cols)

    # 7. Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pivot_df.write_csv(output_path)

    print(f"Successfully processed: {output_path}")
    return pivot_df
