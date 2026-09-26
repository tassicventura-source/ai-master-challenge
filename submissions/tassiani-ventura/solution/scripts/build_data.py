from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.transform import build_all
from src.schemas import SCHEMA_CHANGES, NEW_FIELDS
import pandas as pd

if __name__ == "__main__":
    data = build_all(
        ROOT / "data" / "raw",
        ROOT / "data" / "processed",
        ROOT / "data" / "audit",
        ROOT / "data" / "ravenstack.sqlite",
    )
    pd.DataFrame(SCHEMA_CHANGES).to_csv(ROOT / "data" / "audit" / "schema_changes.csv", index=False)
    pd.DataFrame(NEW_FIELDS).to_csv(ROOT / "data" / "audit" / "new_fields_to_capture.csv", index=False)
    print("Build concluído.")
    for name, df in data.items():
        print(f"- {name}: {len(df):,} linhas")
