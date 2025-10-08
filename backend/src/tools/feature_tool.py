"""Ferramenta para cálculo de importância de variáveis (feature importance)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:  # pragma: no cover - optional
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore

try:  # pragma: no cover - optional
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover - optional
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.preprocessing import LabelEncoder
except ImportError:  # pragma: no cover
    RandomForestClassifier = None  # type: ignore
    RandomForestRegressor = None  # type: ignore
    LabelEncoder = None  # type: ignore

try:  # pragma: no cover
    from langchain_core.tools import tool
except ImportError:  # pragma: no cover
    tool = None  # type: ignore

from src.pipelines.visualization import export_figure
from src.pipelines.utils import to_pandas_for_viz


@dataclass
class FeatureImportanceResult:
    importances: List[Tuple[str, float]]
    plot_path: Optional[str]
    message: str


def _ensure_dataframe(data: Any) -> "pd.DataFrame":
    if pd is None:
        raise RuntimeError("Pandas não está instalado")
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return pd.DataFrame(data)
    raise RuntimeError("Formato de dados não suportado para cálculo de importância de variáveis")


def compute_feature_importances(
    data: Any,
    *,
    target_column: str,
    task: str = "auto",
    method: str = "rf",
    top_k: int = 20,
    sample_n: Optional[int] = None,
) -> FeatureImportanceResult:
    # Convert to pandas with optional sampling. By default sample_n=None -> full dataset.
    df = to_pandas_for_viz(data, sample_n=sample_n)

    if target_column not in df.columns:
        raise ValueError(f"Coluna alvo '{target_column}' não encontrada no dataset")

    # Prepare X and y
    working = df.copy()
    working = working.dropna(subset=[target_column])
    if working.shape[0] == 0:
        raise ValueError("Após remover valores nulos da coluna alvo não restaram linhas para treino")

    y = working[target_column]
    X = working.drop(columns=[target_column])

    # Infer task
    if task == "auto":
        # If target is numeric -> regression, else classification
        task = "regression" if pd.api.types.is_numeric_dtype(y) else "classification"

    # Encode target for classification
    if task == "classification":
        if LabelEncoder is None:
            raise RuntimeError("scikit-learn necessário para classificação (LabelEncoder) não encontrado")
        le = LabelEncoder()
        y_enc = le.fit_transform(y.astype(str))
    else:
        # regression
        try:
            y_enc = pd.to_numeric(y)
        except Exception:
            raise ValueError("Coluna alvo não é numérica; especifique task='classification' se apropriado")

    # One-hot encode categorical features so models can handle them
    # Use a unique prefix separator to avoid collisions with underscores in original names
    PREFIX_SEP = "__ONEHOTSEP__"
    X_processed = pd.get_dummies(X, prefix_sep=PREFIX_SEP, drop_first=False)
    if X_processed.shape[1] == 0:
        raise ValueError("Nenhuma feature válida para treinar o modelo (todas as colunas foram removidas ou vazias)")

    feat_names = X_processed.columns.tolist()

    # Compute importances using the selected method
    imp_series: List[Tuple[str, float]]
    method = (method or "rf").lower()
    if method not in {"rf", "mutual_info"}:
        raise ValueError("method deve ser 'rf' ou 'mutual_info'")

    if method == "rf":
        # Select model
        if task == "classification":
            if RandomForestClassifier is None:
                raise RuntimeError("scikit-learn necessário para RandomForestClassifier não instalado")
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            if RandomForestRegressor is None:
                raise RuntimeError("scikit-learn necessário para RandomForestRegressor não instalado")
            model = RandomForestRegressor(n_estimators=100, random_state=42)

        model.fit(X_processed.values, y_enc)
        importances = getattr(model, "feature_importances_", None)
        if importances is None:
            raise RuntimeError("O modelo treinado não expôs importances")

        imp_series = list(zip(feat_names, importances.tolist()))
    else:
        # mutual_info
        try:
            from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
        except Exception:
            raise RuntimeError("scikit-learn necessário para mutual information não instalado")

        X_vals = X_processed.values
        if task == "classification":
            mi = mutual_info_classif(X_vals, y_enc, random_state=42)
        else:
            mi = mutual_info_regression(X_vals, y_enc, random_state=42)

        imp_series = list(zip(feat_names, mi.tolist()))

    # Aggregate one-hot encoded columns back to original feature names by prefix
    agg: Dict[str, float] = {}
    for name, val in imp_series:
        # split using the unique prefix separator to recover original feature name
        if "__ONEHOTSEP__" in name:
            root = name.split("__ONEHOTSEP__")[0]
        else:
            root = name.split("_")[0]
        agg[root] = agg.get(root, 0.0) + float(val)

    agg_items = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    top = agg_items[:top_k]

    # Plot bar chart
    try:
        import plotly.express as px  # local import optional

        fig = px.bar(
            x=[n for n, v in top],
            y=[v for n, v in top],
            labels={"x": "feature", "y": "importance"},
            title=f"Feature importances (top {len(top)})",
        )
        plot_path = export_figure(fig, filename=f"feature_importance_{target_column}")
    except Exception:
        plot_path = None

    message = f"Calculadas importâncias para '{target_column}' (task={task})."
    return FeatureImportanceResult(importances=top, plot_path=str(plot_path) if plot_path else None, message=message)


if tool is not None:  # pragma: no cover - register as LangChain tool when available

    @tool("feature_importance")
    def feature_importance_tool(dataset: Any, target_column: str, task: str = "auto", top_k: int = 20) -> Dict[str, Any]:
        """Calcula importância das features para uma coluna alvo e retorna top_k e gráfico."""

        result = compute_feature_importances(dataset, target_column=target_column, task=task, top_k=top_k)
        return {
            "summary": result.message,
            "importances": [{"feature": k, "importance": v} for k, v in result.importances],
            "plot": result.plot_path,
        }
