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

### 1. Setup Environment
**Using uv:**
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

**Interactive webinterface:**
```python
./run-app.sh
```

**Process data:**
```python
from engine.postprocessing import process_simulation_data

process_simulation_data("data/exp1/postvis_time.txt", "output/exp1.csv")
```

