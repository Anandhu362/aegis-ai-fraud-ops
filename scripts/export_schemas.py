"""Export Pydantic models to JSON Schemas for TypeScript and contract generation."""

import json
from pathlib import Path

from aegis_common.schemas.features import FeatureVector
from aegis_common.schemas.telemetry import TelemetryEvent
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import Verdict


def export_schemas() -> None:
    """Export schemas to contracts/jsonschema directory."""
    output_dir = Path(__file__).resolve().parent.parent / "contracts" / "jsonschema"
    output_dir.mkdir(parents=True, exist_ok=True)

    schemas = {
        "transaction.v1.json": Transaction.model_json_schema(),
        "verdict.v1.json": Verdict.model_json_schema(),
        "telemetry_event.v1.json": TelemetryEvent.model_json_schema(),
        "feature_vector.v1.json": FeatureVector.model_json_schema(),
    }

    for filename, schema_dict in schemas.items():
        target = output_dir / filename
        target.write_text(json.dumps(schema_dict, indent=2) + "\n", encoding="utf-8")
        print(f"Exported {filename} -> {target}")


if __name__ == "__main__":
    export_schemas()
