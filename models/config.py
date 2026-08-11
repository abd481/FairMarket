MODEL_CLS = "xgb.XGBRegressor"
BASE_PARAMS = {
    "objective": "reg:absoluteerror",
    "eval_metric": "mae",
    "n_estimators": 2000,
    "random_state": 42,
    "verbosity": 0,
    "n_jobs": -1,
}

MODE_PARAMS = {
    "only_villas": {
        **BASE_PARAMS,
        "learning_rate": 0.0117,
        "max_depth": 13,
        "min_child_weight": 3,
        "subsample": 0.80,
        "colsample_bytree": 0.61,
        "reg_lambda": 0.0013,
        "reg_alpha": 0.0152,
    },
    "no_villas": {
        **BASE_PARAMS,
        "learning_rate": 0.025,
        "max_depth": 10,
        "min_child_weight": 3,
        "subsample": 0.90,
        "colsample_bytree": 0.80,
        "reg_lambda": 0.1,
        "reg_alpha": 0.01,
    },
}

EARLY_STOPPING_ROUNDS = 50
