"""Smoke test for feature_tool.compute_feature_importances

Run this script from the repository root inside a Python venv with the backend requirements installed.
"""

from __future__ import annotations

import sys

try:
    import pandas as pd
except Exception as exc:  # pragma: no cover - helpful local error
    print("pandas is required to run this smoke test. Install dependencies: pip install -r backend/requirements.txt")
    raise SystemExit(1) from exc

try:
    from src.tools.feature_tool import compute_feature_importances
except Exception as exc:  # pragma: no cover
    # If running from repo root, package path may need adjustment
    try:
        from backend.src.tools.feature_tool import compute_feature_importances
    except Exception as exc2:
        print("Could not import compute_feature_importances; ensure PYTHONPATH includes backend or run from project root.")
        raise SystemExit(1) from exc2


def main() -> None:
    df = pd.DataFrame(
        {
            "age": [23, 45, 31, 35, 52, 40],
            "income": [40000, 80000, 54000, 60000, 120000, 70000],
            "gender": ["M", "F", "M", "F", "M", "F"],
            "target": [0, 1, 0, 1, 1, 0],
        }
    )

    try:
        res = compute_feature_importances(df, target_column="target", task="classification", method="rf", top_k=10)
    except Exception as exc:
        print("Feature importance computation failed:", exc)
        raise SystemExit(1) from exc

    print("Summary:", res.message)
    print("Top importances:")
    for feat, imp in res.importances:
        print(f"  {feat}: {imp:.6f}")
    if res.plot_path:
        print("Plot exported to:", res.plot_path)


if __name__ == "__main__":
    main()
