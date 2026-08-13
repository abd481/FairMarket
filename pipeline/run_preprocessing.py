import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.processing.preprocessing import preprocess
from utils.db import get_pg_engine

PIPELINE_DIR = PROJECT_ROOT / "artifacts" / "pipelines"
PIPELINE_DIR.mkdir(parents=True, exist_ok=True)


def load_clean_data() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM clean_properties", get_pg_engine())


def build_feature_names(pipeline, n_features):
    ct = pipeline.named_steps["preprocessor"]
    try:
        names = list(ct.get_feature_names_out())
        if len(names) == n_features:
            return names
    except Exception:
        pass
    return [f"feature_{i}" for i in range(n_features)]


def run_preprocessing():
    print("Loading clean_properties...")
    df = load_clean_data()
    print(f"Loaded {len(df)} rows")

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

    feature_names = build_feature_names(pipeline, X_train.shape[1])

    for split_name, X, y, ids in [
        ("train_data", X_train, y_train, ids_train),
        ("val_data", X_val, y_val, ids_val),
        ("test_data", X_test, y_test, ids_test),
    ]:
        out = pd.DataFrame(X, columns=feature_names)
        out["price_log"] = y
        if ids is not None:
            out["id"] = ids.values  # attach id as a plain column
        out.to_sql(split_name, get_pg_engine(), if_exists="replace", index=False)
        print(f"Saved {len(out)} rows to {split_name}")

    path = PIPELINE_DIR / "preprocessing_pipeline.joblib"
    joblib.dump(pipeline, path)
    print(f"Pipeline saved to {path}")


if __name__ == "__main__":
    run_preprocessing()
