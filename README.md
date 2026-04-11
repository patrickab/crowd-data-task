# Crowd Data Processor

Tool to parse and transform simulation data from `postvis_time.txt` to a wide-format CSV where each row represents one timestep.

## Expected Folder Structure
```text
├── data/
│   └── <experiment_name>/
│       └── postvis_time.txt
├── expected_output/
│   └── <experiment_name>/
│       └── postvis_time.csv
```

## Getting Started

This project is configured via `pyproject.toml`, making it compatible with all standard Python package managers.

### 1. Setup Environment
**Using uv (Recommended):**
```bash
uv sync
```

**Using pip:**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install .
```

### 2. Execution
**Run tests:**
```bash
pytest -v
```

**Process data:**
Import and use the processor in your own scripts:
```python
from engine.postprocessing import process_simulation_data

process_simulation_data("data/exp1/postvis_time.txt", "output/exp1.csv")
```
