# Python 3.14 compatibility patch

- Detects Python 3.14 explicitly.
- Recreates a clean virtual environment.
- Upgrades pip, setuptools and wheel.
- Removes fragile dependency pins.
- Uses the virtual environment's Python to start Uvicorn.
- Generates `nexus_diagnostic.txt` for failures.
