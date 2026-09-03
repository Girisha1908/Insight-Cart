"""Model evaluation metrics for churn and next-purchase prediction.

Provides a unified ``evaluate_classification`` function that returns
precision, recall, F1, ROC-AUC, and a confusion matrix in a single dict.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_classification(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Evaluate binary classification predictions.

    Parameters
    ----------
    y_true : array-like of 0/1
    y_prob : predicted probabilities (continuous 0-1)
    threshold : decision threshold for converting probabilities to labels

    Returns
    -------
    dict with keys: accuracy, precision, recall, f1, roc_auc, confusion_matrix
    """
    y_pred = (y_prob >= threshold).astype(int)

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_true, y_pred))

    # ROC-AUC requires both classes present in y_true.
    unique_classes = np.unique(y_true)
    if len(unique_classes) >= 2:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    else:
        roc_auc = 0.0

    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": cm,
    }


def select_best_model(
    model_metrics: dict[str, dict[str, Any]],
) -> str:
    """Return the name of the model with the highest F1 score."""
    return max(model_metrics, key=lambda k: model_metrics[k].get("f1", 0.0))
