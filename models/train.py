import argparse
import sys
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
import xgboost as xgb
from sqlalchemy import create_engine
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from data.processing.preprocessing import preprocess
from models.config import MODE_PARAMS,EARLY_STOPPING_ROUNDS
from utils.secrets import get_secret


ENGINE = create_engine(get_secret("POSTGRES", "postgres"))

VILLA_TYPES = ["Villa", "Stand Alone Villa"]


def filter_by_mode(df, mode):
    """Filter dataset based on selected mode."""

    if mode == "only_villas":
        return df[df["property_type"].isin(VILLA_TYPES)]

    return df[~df["property_type"].isin(VILLA_TYPES)]


def evaluate(model, datasets):
    """Evaluate model on train/val/test."""

    for name, X, y in datasets:

        y_true = np.expm1(y)
        y_pred = np.expm1(model.predict(X))

        metrics = {
            f"{name}_mae": mean_absolute_error(y_true, y_pred),
            f"{name}_mape": mean_absolute_percentage_error(y_true, y_pred),
            f"{name}_r2": r2_score(y_true, y_pred),
        }

        mlflow.log_metrics(metrics)

        print(
            f"{name:6s} "
            f"MAE=${metrics[f'{name}_mae']:>9,.0f} "
            f"MAPE={metrics[f'{name}_mape']:.4f} "
            f"R²={metrics[f'{name}_r2']:.4f}"
        )
        


def save_artifacts(model, pipeline, mode, val_preds=None, val_actuals=None):
    """Save model and preprocessing pipeline."""

    artifacts_dir = PROJECT_ROOT / "artifacts"

    model_dir = artifacts_dir / "models"
    pipeline_dir = artifacts_dir / "pipelines"

    model_dir.mkdir(parents=True, exist_ok=True)
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        model,
        model_dir / f"{mode}_xgb_model.joblib",
    )

    joblib.dump(
        pipeline,
        pipeline_dir / f"{mode}_pipeline.joblib",
    )

    mlflow.xgboost.log_model(model, "model")

    if val_preds is not None and val_actuals is not None:
        residuals = np.abs(val_actuals - val_preds)
        
        bins = [0, 5_000_000, 10_000_000, 23_000_000]
        calib_df = pd.DataFrame({'pred': val_preds, 'residual': residuals})
        calib_df['bin'] = pd.cut(calib_df['pred'], bins=bins, include_lowest=True)
        calib_map = calib_df.groupby('bin', observed=True)['residual'].quantile(0.80).to_dict()
        joblib.dump({'bins': bins, 'calib_map': calib_map}, model_dir / f'{mode}_calib.joblib')

    print(f"\nArtifacts saved for '{mode}'.")


def compute_weights(y_train, weighting):
    if weighting == "none":
        return None
    price = np.expm1(y_train)
    if weighting == "inv":
        w = 1.0 / price
    elif weighting == "sqrt_inv":
        w = 1.0 / np.sqrt(price)
    w = w / w.mean()
    p5, p95 = np.percentile(w, [5, 95])
    w = np.clip(w, p5, p95)
    return w


def train(mode, weighting="none"):

    df = pd.read_sql("SELECT * FROM clean_properties", ENGINE)
    df = filter_by_mode(df, mode)

    print(f"{mode}: {len(df)} rows after filtering")

    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
        pipeline,
        ids_train,
        ids_val,
        ids_test,
    ) = preprocess(df)

    print(
        f"Train: {len(X_train)} | "
        f"Val: {len(X_val)} | "
        f"Test: {len(X_test)}"
    )

    params = MODE_PARAMS[mode].copy()
    params["early_stopping_rounds"] = EARLY_STOPPING_ROUNDS

    sample_weight = compute_weights(y_train, weighting)

    if sample_weight is not None:
        rn_str = f"{mode}_{weighting}"
        print(f"Weighting: {weighting}  mean={sample_weight.mean():.4f}  "
              f"min={sample_weight.min():.4f}  max={sample_weight.max():.4f}")
    else:
        rn_str = mode

    mlflow.set_experiment("price_prediction")

    with mlflow.start_run(run_name=rn_str):

        mlflow.set_tag("mode", mode)
        if weighting != "none":
            mlflow.set_tag("weighting", weighting)
        mlflow.log_params(params)

        model = xgb.XGBRegressor(**params)

        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)], 
            sample_weight=sample_weight,
            verbose=False,
        )
       
        evaluate(
            model,
            [
                ("train", X_train, y_train),
                ("val", X_val, y_val),
                ("test", X_test, y_test),
            ],
        )

        save_artifacts(model, pipeline, f"{mode}" if weighting == "none" else f"{mode}_{weighting}",
                       val_preds=np.expm1(model.predict(X_val)),
                       val_actuals=np.expm1(y_val))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["only_villas", "no_villas"],
        required=True,
    )

    parser.add_argument(
        "--weighting",
        choices=["none", "sqrt_inv", "inv"],
        default="none",
    )

    args = parser.parse_args()

    train(args.mode, weighting=args.weighting)