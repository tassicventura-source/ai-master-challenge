from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.schemas import SCHEMA_CHANGES, NEW_FIELDS


def test_five_target_bases_are_represented():
    targets={x["base_nova"] for x in SCHEMA_CHANGES}
    assert {"accounts","subscriptions","feature_usage","customer_interactions","lifecycle_events"}.issubset(targets)


def test_new_fields_cover_company_functions():
    text=" ".join(x["area"] for x in NEW_FIELDS)
    for term in ["Growth","Sales","CS","Suporte","Produto","Finance","RevOps"]:
        assert term in text
