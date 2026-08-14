import numpy as np
import pandas as pd
import pytest

from models.recommend import recommend_from_features


class _FakePipeline:
    def transform(self, df):
        return np.zeros((len(df), 3))


class _FakeKNN:
    """KNN whose neighbors are deliberately NOT in metadata row order."""

    def __init__(self, indices, distances):
        self.indices = indices
        self.distances = distances

    def kneighbors(self, query, n_neighbors):
        del query, n_neighbors
        return (
            np.asarray(self.distances, dtype=float)[None, :],
            np.asarray(self.indices, dtype=int)[None, :],
        )


@pytest.fixture
def metadata():
    # Rows are ordered [id 100, 200, 300, 400, 500] in the cached frame,
    # which does NOT match the KNN neighbor order used below.
    return pd.DataFrame(
        {
            "id": [100, 200, 300, 400, 500],
            "price": [3_000_000, 3_100_000, 3_200_000, 3_300_000, 3_400_000],
            "area": [150.0, 160.0, 170.0, 180.0, 190.0],
            "beds": [3, 3, 3, 4, 4],
            "baths": [2, 2, 3, 3, 3],
            "property_type": ["Apartment"] * 5,
            "furnishing": ["Unfurnished"] * 5,
            "amenities": ["pool", "pool", "pool", "pool", "pool"],
            "location": ["New Cairo"] * 5,
            "city": ["Cairo"] * 5,
            "district": ["New Cairo"] * 5,
            "compound": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
        }
    )


def run_recommend(metadata, k=3, **kwargs):
    # KNN returns (nearest-first) stored_ids indices [4, 1, 3, 0, 2].
    indices = [4, 1, 3, 0, 2]
    distances = [0.1, 0.2, 0.3, 0.4, 0.5]
    stored_ids = np.array([100, 200, 300, 400, 500])

    return recommend_from_features(
        {
            "location": "New Cairo",
            "property_type": "Apartment",
            "beds": 3,
            "baths": 2,
            "area": 150,
            "district": "New Cairo",
        },
        mode="no_villas",
        district_pps={"New Cairo": 20_000},
        global_pps=18_000,
        pipeline=_FakePipeline(),
        knn=_FakeKNN(indices, distances),
        stored_ids=stored_ids,
        metadata=metadata,
        k=k,
        **kwargs,
    )


class TestRecommendOrdering:
    def test_results_are_in_ascending_knn_distance_order(self, metadata):
        result = run_recommend(metadata, k=3)
        ids = [r["id"] for r in result["recommendations"]]

        # Nearest-first KNN order (distances 0.1, 0.2, 0.3) is ids
        # 500, 200, 400 — NOT the metadata frame order (100, 200, 300).
        assert ids == [500, 200, 400]

    def test_similarity_is_monotonically_decreasing_with_distance(self, metadata):
        result = run_recommend(metadata, k=3)
        sims = [r["similarity"] for r in result["recommendations"]]
        # similarity = 1 / (1 + dist) with dist 0.1, 0.2, 0.3
        assert sims == pytest.approx([1 / 1.1, 1 / 1.2, 1 / 1.3], rel=1e-9)
        assert sims == sorted(sims, reverse=True)

    def test_honors_k_limit(self, metadata):
        result = run_recommend(metadata, k=2)
        assert len(result["recommendations"]) == 2
        assert [r["id"] for r in result["recommendations"]] == [500, 200]

    def test_price_filter_preserves_ordering_and_fields(self, metadata):
        # ±3% of 3.35M keeps only ids 500 (3.4M) and 400 (3.3M), still in
        # ascending KNN-distance order (500 before 400).
        result = run_recommend(metadata, k=5, price=3_350_000, price_tolerance=0.03)
        ids = [r["id"] for r in result["recommendations"]]
        assert ids == [500, 400]
        for r in result["recommendations"]:
            assert "price" in r
            assert "property_type" in r
            assert "similarity" in r
            assert "_dist" not in r
