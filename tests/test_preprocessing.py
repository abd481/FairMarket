import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from data.processing.preprocessing import (
    PRICE_CAP,
    filter_data,
    split_data,
    log_target,
    SmoothedHierarchicalTargetEncoder,
    DropColumnsTransformer,
    AmenityScoreTransformer,
    build_preprocessing_pipeline,
    preprocess,
)


class TestFilterData:
    def test_keeps_rows_above_threshold(self):
        df = pd.DataFrame(
            {"area": [50, 100, 30, 200], "price": [2000000, 3000000, 2000000, 2000000]}
        )
        result = filter_data(df)
        assert len(result) == 3

    def test_filters_area_below_50(self):
        df = pd.DataFrame({"area": [49, 10, 0], "price": [2000000, 2000000, 2000000]})
        result = filter_data(df)
        assert len(result) == 0

    def test_filters_price_below_one_million(self):
        df = pd.DataFrame({"area": [100, 100], "price": [500000, 2000000]})
        result = filter_data(df)
        assert len(result) == 1
        assert result["price"].iloc[0] == 2000000

    def test_filters_price_above_cap(self):
        df = pd.DataFrame({"area": [100, 100], "price": [PRICE_CAP + 1, 2000000]})
        result = filter_data(df)
        assert len(result) == 1
        assert result["price"].iloc[0] == 2000000

    def test_returns_copy(self):
        df = pd.DataFrame({"area": [50, 100], "price": [2000000, 2000000]})
        result = filter_data(df)
        result.iloc[0, 0] = 999
        assert df.iloc[0, 0] == 50


class TestSplitData:
    def test_splits_into_three_sets(self, sample_df):
        X = sample_df.drop(columns="price")
        y = sample_df["price"]
        X_train, X_val, X_test, y_train, y_val, y_test, ids_tr, ids_val, ids_te = (
            split_data(X, y)
        )
        assert len(X_train) > 0
        assert len(X_val) > 0
        assert len(X_test) > 0
        total = len(X_train) + len(X_val) + len(X_test)
        assert total == len(sample_df)
        assert ids_tr is None and ids_val is None and ids_te is None

    def test_approximate_ratios(self, sample_df):
        X = sample_df.drop(columns="price")
        y = sample_df["price"]
        X_train, X_val, X_test, _, _, _, _, _, _ = split_data(X, y)
        total = len(sample_df)
        assert abs(len(X_train) / total - 0.70) < 0.05
        assert abs(len(X_val) / total - 0.15) < 0.05
        assert abs(len(X_test) / total - 0.15) < 0.05

    def test_returns_ids_when_provided(self, sample_df):
        X = sample_df.drop(columns="price")
        y = sample_df["price"]
        ids = pd.Series(sample_df.index, name="id").astype(str)
        _, _, _, _, _, _, ids_tr, ids_val, ids_te = split_data(X, y, ids=ids)
        total = len(sample_df)
        assert len(ids_tr) + len(ids_val) + len(ids_te) == total

    def test_indices_are_reset(self, sample_df):
        X = sample_df.drop(columns="price")
        y = sample_df["price"]
        X_train, X_val, X_test, _, _, _, _, _, _ = split_data(X, y)
        for split in (X_train, X_val, X_test):
            assert list(split.index) == list(range(len(split)))


class TestLogTarget:
    def test_returns_log_transformed_values(self):
        y_train = np.array([0, 100, 1000])
        y_val = np.array([50, 500])
        y_test = np.array([200])
        lyt, lyv, lytst = log_target(y_train, y_val, y_test)
        expected = np.log1p(y_train)
        assert np.allclose(lyt, expected)
        assert np.allclose(lyv, np.log1p(y_val))
        assert np.allclose(lytst, np.log1p(y_test))


class TestDropColumnsTransformer:
    def test_drops_specified_columns(self):
        X = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        transformer = DropColumnsTransformer(columns=["b", "c"])
        result = transformer.transform(X)
        assert list(result.columns) == ["a"]

    def test_ignores_missing_columns(self):
        X = pd.DataFrame({"a": [1]})
        transformer = DropColumnsTransformer(columns=["b", "c"])
        result = transformer.transform(X)
        assert list(result.columns) == ["a"]

    def test_fit_returns_self(self):
        X = pd.DataFrame({"a": [1]})
        transformer = DropColumnsTransformer(columns=["a"])
        assert transformer.fit(X) is transformer


class TestSmoothedHierarchicalTargetEncoder:
    def test_encodes_known_location(self):
        X = pd.DataFrame(
            {"location": ["Cairo,New Cairo", "Giza", "Cairo,New Cairo", "Alexandria"]}
        )
        y = np.array([10, 20, 30, 40])
        encoder = SmoothedHierarchicalTargetEncoder(col="location", k=2)
        encoder.fit(X, y)
        result = encoder.transform(X)
        col = result["location"]
        assert col[0] == col[2]

    def test_unknown_falls_back_to_global_mean(self):
        X_train = pd.DataFrame({"location": ["Cairo", "Giza"]})
        y_train = np.array([10, 20])
        X_test = pd.DataFrame({"location": ["UnknownCity"]})
        encoder = SmoothedHierarchicalTargetEncoder(col="location", k=1)
        encoder.fit(X_train, y_train)
        result = encoder.transform(X_test)
        assert result["location"].iloc[0] == pytest.approx(15.0)

    def test_returns_dataframe_with_location_column(self):
        X = pd.DataFrame({"location": ["Cairo"], "area": [100]})
        y = np.array([10])
        encoder = SmoothedHierarchicalTargetEncoder(col="location", k=1)
        encoder.fit(X, y)
        result = encoder.transform(X)
        assert "location" in result.columns
        assert "area" in result.columns


class TestAmenityScoreTransformer:
    def test_counts_known_amenities(self):
        X = pd.DataFrame({"amenities": ["pool,gym,balcony"]})
        transformer = AmenityScoreTransformer()
        result = transformer.transform(X)
        assert result[0][0] == 0  # utility
        assert result[0][1] == 1  # standard (balcony)
        assert result[0][2] == 0  # premium
        assert result[0][3] == 2  # luxury (pool, gym)

    def test_handles_empty_amenities(self):
        X = pd.DataFrame({"amenities": [""]})
        transformer = AmenityScoreTransformer()
        result = transformer.transform(X)
        assert (result == 0).all()

    def test_handles_not_mentioned(self):
        X = pd.DataFrame({"amenities": ["Not Mentioned"]})
        transformer = AmenityScoreTransformer()
        result = transformer.transform(X)
        assert (result == 0).all()

    def test_unknown_defaults_to_standard(self):
        X = pd.DataFrame({"amenities": ["unknown_xyz"]})
        transformer = AmenityScoreTransformer()
        result = transformer.transform(X)
        assert result[0][1] == 1  # unknown counted as standard
        assert "unknown_xyz" in transformer.unknown_items_

    def test_feature_names_out(self):
        transformer = AmenityScoreTransformer()
        names = transformer.get_feature_names_out()
        assert names == [
            "amenities_utility_score",
            "amenities_standard_score",
            "amenities_premium_score",
            "amenities_luxury_score",
        ]


class TestBuildPreprocessingPipeline:
    def test_returns_pipeline_with_correct_steps(self):
        pipeline = build_preprocessing_pipeline()
        assert isinstance(pipeline, Pipeline)
        step_names = [s[0] for s in pipeline.steps]
        assert step_names == [
            "drop_cols",
            "target_encode",
            "compound_encode",
            "district_encode",
            "city_encode",
            "loc_proptype_encode",
            "preprocessor",
        ]


class TestPreprocessEndToEnd:
    def test_returns_correct_outputs(self, sample_df):
        (
            X_train,
            X_val,
            X_test,
            y_train,
            y_val,
            y_test,
            pipeline,
            ids_tr,
            ids_val,
            ids_te,
        ) = preprocess(sample_df)
        assert isinstance(X_train, np.ndarray)
        assert isinstance(X_val, np.ndarray)
        assert isinstance(X_test, np.ndarray)
        assert isinstance(y_train, (np.ndarray, pd.Series))
        assert isinstance(y_val, (np.ndarray, pd.Series))
        assert isinstance(y_test, (np.ndarray, pd.Series))
        assert ids_tr is None and ids_val is None and ids_te is None

    def test_shapes_are_consistent(self, sample_df):
        X_train, X_val, X_test, y_train, y_val, y_test, _, _, _, _ = preprocess(
            sample_df
        )
        assert X_train.shape[1] == X_val.shape[1] == X_test.shape[1]
        assert X_train.shape[0] == len(y_train)
        assert X_val.shape[0] == len(y_val)
        assert X_test.shape[0] == len(y_test)

    def test_no_nan_in_outputs(self, sample_df):
        X_train, X_val, X_test, y_train, y_val, y_test, _, _, _, _ = preprocess(
            sample_df
        )
        assert not np.any(np.isnan(X_train))
        assert not np.any(np.isnan(X_val))
        assert not np.any(np.isnan(X_test))
        assert not np.any(np.isnan(y_train))
        assert not np.any(np.isnan(y_val))
        assert not np.any(np.isnan(y_test))

    def test_pipeline_persists_and_loads(self, sample_df):
        _, _, _, _, _, _, pipeline, _, _, _ = preprocess(sample_df)
        import joblib
        from io import BytesIO

        buf = BytesIO()
        joblib.dump(pipeline, buf)
        buf.seek(0)
        loaded = joblib.load(buf)

        input_df = self._build_pipeline_input()
        original_out = pipeline.transform(input_df)
        loaded_out = loaded.transform(input_df)
        assert np.allclose(original_out, loaded_out)

    def test_feature_names_match_output_shape(self, sample_df):
        _, X_val, _, _, _, _, pipeline, _, _, _ = preprocess(sample_df)
        ct = pipeline.named_steps["preprocessor"]
        names = list(ct.get_feature_names_out())
        assert len(names) == X_val.shape[1]

    @staticmethod
    def _build_pipeline_input():
        return pd.DataFrame(
            {
                "location": ["Cairo,New Cairo", "Giza,6th October"],
                "compound": ["Cairo", "Giza"],
                "district": ["New Cairo", "6th October"],
                "city": ["New Cairo", "6th October"],
                "location_proptype": [
                    "Cairo,New Cairo, Apartment",
                    "Giza,6th October, Villa",
                ],
                "property_type": ["Apartment", "Villa"],
                "furnishing": ["Unfurnished", "Furnished"],
                "source": ["bayut", "olx"],
                "amenities": ["pool,gym,balcony", "elevator,security"],
                "title": ["Finished apartment", "Ready to move villa"],
                "area": [150, 300],
                "beds": [2, 4],
                "baths": [2, 3],
                "beds_baths": [4, 12],
                "amenity_count": [3, 2],
                "district_avg_pps": [20000.0, 20000.0],
                "price_per_sqm": [20000, 20000],
                "link": ["https://example.com/1", "https://example.com/2"],
                "transaction_type": ["sale", "sale"],
                "is_studio": [False, False],
            }
        )
