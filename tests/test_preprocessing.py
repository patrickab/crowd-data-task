from pathlib import Path

import polars as pl
from polars.testing import assert_frame_equal
import pytest

from src.engine.postprocessing import process_simulation_data

# --- Configurable Variables ---
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
EXPECTED_OUTPUT_DIR = ROOT_DIR / "expected_output"

SIMULATION_FOLDERS = [
    "rimea_4_OSM_clone_1_2026-04-09_16-58-14.715",
    "spiral_OSM_2026-04-09_16-14-54.924",
    "spiral_OSM_2026-04-09_16-26-44.727",
    "spiral_OSM_2026-04-09_16-29-16.153",
]


@pytest.mark.parametrize("sim_folder", SIMULATION_FOLDERS)
def test_processed_shape_and_pattern(sim_folder: str, tmp_path: Path) -> None:
    """
    Tests that the processed DataFrame has the correct shape and interleaved column pattern.
    Runs independently for each folder defined in SIMULATION_FOLDERS.
    """
    input_path = DATA_DIR / sim_folder / "postvis_time.txt"

    output_path = tmp_path / "postvis_time.csv"

    df = process_simulation_data(input_path, output_path)

    # 1. Check basic shape properties
    assert not df.is_empty(), f"DataFrame for {sim_folder} should not be empty"

    assert df.shape[1] % 2 != 0, "Number of columns should be odd (1 timeStep + pairs of x and y)"

    # 2. Check column pattern
    cols = df.columns
    assert cols[0] == "timeStep", "First column must be 'timeStep'"

    # Verify the interleaved pattern: x_i, y_i, x_j, y_j...
    if len(cols) > 1:
        assert cols[1].startswith("x"), "Second column should be an 'x' coordinate"
        assert cols[2].startswith("y"), "Third column should be a 'y' coordinate"

        # Ensure the Pedestrian ID matches between the x and y pairs
        ped_id_x = cols[1][1:]  # strip 'x'
        ped_id_y = cols[2][1:]  # strip 'y'
        assert ped_id_x == ped_id_y, "x and y coordinate pairs must belong to the same pedestrianId"


@pytest.mark.parametrize("sim_folder", SIMULATION_FOLDERS)
def test_matches_expected_output(sim_folder: str, tmp_path: Path) -> None:
    """Tests that the output of our function exactly matches the provided expected_output CSVs."""
    input_path = DATA_DIR / sim_folder / "postvis_time.txt"
    expected_csv_path = EXPECTED_OUTPUT_DIR / sim_folder / "postvis_time.csv"
    output_path = tmp_path / "postvis_time.csv"

    assert expected_csv_path.exists(), f"Expected output missing for {sim_folder}"

    result_df = process_simulation_data(input_path, output_path)
    expected_df = pl.read_csv(expected_csv_path)

    # Cast to Float64 to ignore String/Float type discrepancies and sort by timeStep
    res = result_df.cast(pl.Float64, strict=False).sort("timeStep")
    exp = expected_df.cast(pl.Float64, strict=False).sort("timeStep")

    assert_frame_equal(res, exp)
