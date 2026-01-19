from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import RootModel

# Add repo root to sys.path so "backend.*" imports work when running as a script
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.envelope.schema import Envelope  # type: ignore


class EnvelopeRoot(RootModel[Envelope]):
    """Root wrapper so Pydantic can emit a single JSON Schema for the union."""


def main() -> None:
    schema = EnvelopeRoot.model_json_schema()

    out_path = REPO_ROOT / "backend" / "app" / "schemas" / "envelope.schema.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False)
    out_path.write_text(data + "\n", encoding="utf-8")

    print(f"Wrote schema: {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
