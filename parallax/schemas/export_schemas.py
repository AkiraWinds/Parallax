"""Regenerate the committed JSON Schema exports from the Pydantic models.

Run with `uv run python -m parallax.schemas.export_schemas` whenever
`models.py` changes. `tests/test_models.py` fails if the committed files
drift from what this script would produce, so this is not optional
bookkeeping — it is how Section 11's "canonical schema" stays a real,
checkable artifact instead of just prose.
"""

from __future__ import annotations

import json
from pathlib import Path

from parallax.schemas.models import ReviewFinding, ReviewReport

_SCHEMAS_DIR = Path(__file__).parent

EXPORTS = {
    "review_finding.schema.json": ReviewFinding,
    "review_report.schema.json": ReviewReport,
}


def export_all() -> None:
    for filename, model in EXPORTS.items():
        schema = model.model_json_schema()
        (_SCHEMAS_DIR / filename).write_text(json.dumps(schema, indent=2) + "\n")


if __name__ == "__main__":
    export_all()
