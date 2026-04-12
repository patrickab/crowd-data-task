from pathlib import Path
from time import perf_counter

import polars as pl


def process_simulation_data(
    input_path: str | Path,
    output_path: str | Path,
    start_step: int | None = None,
    end_step: int | None = None,
) -> tuple[pl.DataFrame, dict[str, float]]:
    """
    Parses raw simulation output data.
    Transforms by mapping each timestep to one row and each pedestrianId to a column.
    Returns the processed DataFrame and a dictionary of profiling durations (seconds).
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    timers: dict[str, float] = {}

    # 1. Read data
    t0 = perf_counter()
    df = pl.read_csv(input_path, separator=" ")
    timers["read"] = perf_counter() - t0

    cols = df.columns
    if len(cols) < 4:
        print(f"Warning: Unexpected data format in {input_path}")
        return pl.DataFrame(), timers

    # 2. Ensure consistent scheme
    df = df.rename(
        {cols[0]: "timeStep", cols[1]: "pedestrianId", cols[2]: "x", cols[3]: "y"}
    ).select(["timeStep", "pedestrianId", "x", "y"])

    # 3. Filter by time range if specified
    if start_step is not None:
        df = df.filter(pl.col("timeStep") >= start_step)
    if end_step is not None:
        df = df.filter(pl.col("timeStep") <= end_step)

    # 4. Get unique pedestrian IDs by order of occurrence
    pids = df["pedestrianId"].unique(maintain_order=True).to_list()

    # 5. Pivot X and Y separately (transform long data to wide data)
    t0 = perf_counter()
    df_x = df.pivot(index="timeStep", on="pedestrianId", values="x", aggregate_function="first")
    df_x = df_x.rename({col: f"x{col}" for col in df_x.columns if col != "timeStep"})

    df_y = df.pivot(index="timeStep", on="pedestrianId", values="y", aggregate_function="first")
    df_y = df_y.rename({col: f"y{col}" for col in df_y.columns if col != "timeStep"})
    timers["pivot"] = perf_counter() - t0

    # 6. Join them together
    t0 = perf_counter()
    pivot_df = df_x.join(df_y, on="timeStep", how="inner").sort("timeStep")
    timers["join"] = perf_counter() - t0

    # 7. Reorder columns to an interleaved pattern (timeStep, x1, y1, x2, y2, ...)
    ordered_cols = ["timeStep"]
    for pid in pids:
        ordered_cols.extend([f"x{pid}", f"y{pid}"])

    t0 = perf_counter()
    pivot_df = pivot_df.select(ordered_cols)
    timers["select"] = perf_counter() - t0

    # 8. Cast to float
    pivot_df = pivot_df.with_columns(
        [pl.col(c).cast(pl.Float64) for c in ordered_cols if c != "timeStep"]
    )

    # 9. Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = perf_counter()
    pivot_df.write_csv(output_path)
    timers["write_csv"] = perf_counter() - t0

    print(f"Successfully processed: {output_path}")
    return pivot_df, timers


if __name__ == "__main__":
    input_path = Path("data/spiral_OSM_2026-04-09_16-29-16.153/postvis_time.txt")
    output_path = Path("data_processed/spiral_OSM_2026-04-09_16-29-16.153/postvis_time.csv")

    process_simulation_data(input_path, output_path)
