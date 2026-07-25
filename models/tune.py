import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sqlalchemy import create_engine
from sklearn.metrics import mean_absolute_error

from data.processing.preprocessing import preprocess
from utils.secrets import get_secret

ENGINE = create_engine(get_secret("POSTGRES", "postgres"))
VILLA_TYPES = ["Villa", "Stand Alone Villa"]

N_TRIALS = 100

SEARCH_SPACE = {
    "learning_rate": ("float", 0.005, 0.3, True),
    "max_depth": ("int", 3, 15),
    "min_child_weight": ("int", 1, 10),
    "subsample": ("float", 0.6, 1.0, False),
    "colsample_bytree": ("float", 0.6, 1.0, False),
    "reg_lambda": ("float", 1e-3, 10.0, True),
    "reg_alpha": ("float", 1e-3, 10.0, True),
}


def suggest_params(trial):
    params = {
        "objective": "reg:absoluteerror",
        "eval_metric": "mae",
        "n_estimators": 2000,
        "random_state": 42,
        "verbosity": 0,
        "n_jobs": -1,
    }
    for name, spec in SEARCH_SPACE.items():
        if spec[0] == "float" and spec[3]:
            params[name] = trial.suggest_float(name, spec[1], spec[2], log=True)
        elif spec[0] == "float":
            params[name] = trial.suggest_float(name, spec[1], spec[2])
        elif spec[0] == "int":
            params[name] = trial.suggest_int(name, spec[1], spec[2])
    return params


def objective(X_train, y_train, X_val, y_val, trial):
    params = suggest_params(trial)
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    y_pred = np.expm1(model.predict(X_val))
    y_true = np.expm1(y_val)
    return mean_absolute_error(y_true, y_pred)


def tune(mode):
    print(f"\n{'='*60}")
    print(f"Tuning XGBoost for {mode}")
    print(f"{'='*60}")

    df = pd.read_sql("SELECT * FROM clean_properties", ENGINE)
    if mode == "only_villas":
        df = df[df["property_type"].isin(VILLA_TYPES)]
    else:
        df = df[~df["property_type"].isin(VILLA_TYPES)]
    print(f"{len(df)} rows after filtering")

    X_train, X_val, X_test, y_train, y_val, y_test, pipeline, *_ = preprocess(df)
    print(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

    study = optuna.create_study(direction="minimize", study_name=f"xgb_{mode}")
    study.optimize(
        lambda trial: objective(X_train, y_train, X_val, y_val, trial),
        n_trials=N_TRIALS,
        show_progress_bar=True,
    )

    print(f"\nBest val MAE for {mode}: ${study.best_value:,.0f}")
    print(f"Best params:")
    for k, v in sorted(study.best_params.items()):
        print(f"    {k}: {v}")

    return study.best_params


if __name__ == "__main__":
    best_only_villas = tune("only_villas")
    best_no_villas = tune("no_villas")

    print(f"\n{'='*60}")
    print("SUMMARY - Update models/config.py with these:")
    print(f"{'='*60}")
    print("\n# Use these for ONLY VILLAS:")
    for k, v in sorted(best_only_villas.items()):
        print(f'    "{k}": {v!r},')
    print("\n# Use these for NO VILLAS:")
    for k, v in sorted(best_no_villas.items()):
        print(f'    "{k}": {v!r},')
