"""Model comparison across XGBoost / LightGBM / CatBoost / RandomForest.

Heavy gradient-boosting libraries are optional; RandomForest (scikit-learn) is the
always-available baseline so the pipeline runs in CI without extra wheels.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .dataset import FEATURES, time_series_split

log = logging.getLogger("ghc.ml")


@dataclass
class ModelResult:
    name: str
    target: str
    mae: float
    r2: float
    cv_mae: float
    n_train: int
    n_test: int


def _candidates(seed: int = 42) -> dict[str, object]:
    models: dict[str, object] = {
        "random_forest": RandomForestRegressor(n_estimators=200, max_depth=8, random_state=seed, n_jobs=-1),
    }
    try:  # pragma: no cover - optional
        from xgboost import XGBRegressor

        models["xgboost"] = XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                                         subsample=0.8, random_state=seed)
    except ImportError:
        pass
    try:  # pragma: no cover - optional
        from lightgbm import LGBMRegressor

        models["lightgbm"] = LGBMRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05, random_state=seed,
        )
    except ImportError:
        pass
    try:  # pragma: no cover - optional
        from catboost import CatBoostRegressor

        models["catboost"] = CatBoostRegressor(iterations=300, depth=4, verbose=False, random_seed=seed)
    except ImportError:
        pass
    return models


def evaluate_models(frame: pd.DataFrame, target: str, n_splits: int = 4) -> list[ModelResult]:
    if len(frame) < 50:
        raise ValueError("need at least 50 rows to train; ingest more history")
    train, test = time_series_split(frame)
    x_train, y_train = train[FEATURES].to_numpy(float), train[target].to_numpy(float)
    x_test, y_test = test[FEATURES].to_numpy(float), test[target].to_numpy(float)
    results: list[ModelResult] = []

    for name, estimator in _candidates().items():
        pipe = Pipeline([("scale", StandardScaler()), ("model", estimator)])
        pipe.fit(x_train, y_train)
        pred = pipe.predict(x_test)
        cv_scores = []
        for tr_idx, te_idx in TimeSeriesSplit(n_splits=n_splits).split(x_train):
            cv = Pipeline([("scale", StandardScaler()), ("model", type(estimator)(**estimator.get_params()))])
            cv.fit(x_train[tr_idx], y_train[tr_idx])
            cv_scores.append(mean_absolute_error(y_train[te_idx], cv.predict(x_train[te_idx])))
        results.append(ModelResult(
            name=name, target=target,
            mae=round(float(mean_absolute_error(y_test, pred)), 6),
            r2=round(float(r2_score(y_test, pred)), 4),
            cv_mae=round(float(np.mean(cv_scores)), 6),
            n_train=len(train), n_test=len(test),
        ))
    return sorted(results, key=lambda r: r.mae)


def train_all(frame: pd.DataFrame, targets: list[str]) -> dict[str, list[ModelResult]]:
    return {t: evaluate_models(frame, t) for t in targets if t in frame.columns}
