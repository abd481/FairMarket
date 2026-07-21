from sklearn.preprocessing import FunctionTransformer, OneHotEncoder
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

AMENITIES_MAP = {
    # --- 1. Utilities ---
    "electricity meter": "utility",
    "water meter": "utility",
    "natural gas": "utility",
    "landline": "utility",
    "broadband internet": "utility",
    "satellite/cable tv": "utility",
    # --- 2. Standard Amenities ---
    "balcony": "standard",
    "balcony or terrace": "standard",
    "elevator": "standard",
    "service elevators": "standard",
    "elevators in building: 2": "standard",
    "security": "standard",
    "security staff": "standard",
    "cctv security": "standard",
    "covered parking": "standard",
    "parking spaces": "standard",
    "parking spaces: 1": "standard",
    "parking spaces: 2": "standard",
    "pets allowed": "standard",
    "intercom": "standard",
    "waste disposal": "standard",
    "maintenance staff": "standard",
    "cleaning services": "standard",
    "lobby in building": "standard",
    "reception/waiting room": "standard",
    "prayer room": "standard",
    # --- 3. Premium / Space Features ---
    "private garden": "premium",
    "lawn or garden": "premium",
    "maids room": "premium",
    "study room": "premium",
    "storage areas": "premium",
    "double glazed windows": "premium",
    "sea view": "premium",
    "view": "premium",
    "freehold": "premium",
    "kids play area": "premium",
    "day care center": "premium",
    "barbeque area": "premium",
    "cafeteria or canteen": "premium",
    "shared kitchen": "premium",
    "laundry room": "premium",
    "laundry facility": "premium",
    "atm facility": "premium",
    "business center": "premium",
    "conference room": "premium",
    # --- 4. Luxury Features ---
    "pool": "luxury",
    "swimming pool": "luxury",
    "jacuzzi": "luxury",
    "sauna": "luxury",
    "steam room": "luxury",
    "gym": "luxury",
    "gym or health club": "luxury",
    "central a/c & heating": "luxury",
    "centrally air-conditioned": "luxury",
    "central heating": "luxury",
    "built in kitchen appliances": "luxury",
    "furnished": "luxury",
    "electricity backup": "luxury",
    "24 hours concierge": "luxury",
    "facilities for disabled": "luxury",
}


PRICE_CAP = 23_000_000  # set to e.g. 23_000_000 to cap; None = no cap

def filter_data(df):
    cond = (df["area"] >= 50) & (df["price"] >= 1_000_000)
    if PRICE_CAP is not None:
        cond &= (df["price"] <= PRICE_CAP)
    return df[cond].copy()


def split_data(X, y, ids=None, stratify=None):
    split_kwargs = dict(test_size=0.30, random_state=42)
    if stratify is not None:
        split_kwargs['stratify'] = stratify

    if ids is not None:
        X_train, X_temp, y_train, y_temp, ids_train, ids_temp = train_test_split(
            X, y, ids, **split_kwargs
        )
        if stratify is not None:
            stratify_temp = stratify.loc[X_temp.index]
        else:
            stratify_temp = None
        X_val, X_test, y_val, y_test, ids_val, ids_test = train_test_split(
            X_temp, y_temp, ids_temp, test_size=0.50, random_state=42, stratify=stratify_temp
        )
        ids_train = ids_train.reset_index(drop=True)
        ids_val = ids_val.reset_index(drop=True)
        ids_test = ids_test.reset_index(drop=True)
    else:
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, **split_kwargs
        )
        if stratify is not None:
            stratify_temp = stratify.loc[X_temp.index]
        else:
            stratify_temp = None
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.50, random_state=42, stratify=stratify_temp
        )
        ids_train = ids_val = ids_test = None

    X_train = X_train.reset_index(drop=True)
    X_val = X_val.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)
    y_train = y_train.reset_index(drop=True)
    y_val = y_val.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    return X_train, X_val, X_test, y_train, y_val, y_test, ids_train, ids_val, ids_test


def log_target(y_train, y_val, y_test):
    return np.log1p(y_train), np.log1p(y_val), np.log1p(y_test)


class DropColumnsTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop(columns=self.columns, errors="ignore")


class SmoothedHierarchicalTargetEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, col, k=10):
        self.col = col
        self.k = k  # smoothing strength

    def fit(self, X, y):
        self.global_mean = y.mean()
        self.level_maps = []
        self.level_counts = []

        parts = X[self.col].astype(str).str.split(",")
        levels = max(parts.apply(len))

        df = X[[self.col]].copy()
        df["_target"] = y
        df["_parts"] = parts

        for i in range(levels):
            level_values = df["_parts"].apply(
                lambda x: x[i].strip() if i < len(x) else np.nan
            )
            tmp = pd.DataFrame({"key": level_values, "target": y}).dropna()
            self.level_maps.append(tmp.groupby("key")["target"].mean())
            self.level_counts.append(tmp.groupby("key")["target"].count())

        return self

    def _encode_row(self, row_parts):
        smoothed = self.global_mean
        # walk coarsest -> finest
        for i in range(len(row_parts) - 1, -1, -1):
            key = row_parts[i].strip()
            if i < len(self.level_maps) and key in self.level_counts[i]:
                n_i = self.level_counts[i][key]
                raw_mean_i = self.level_maps[i][key]
                smoothed = (n_i * raw_mean_i + self.k * smoothed) / (n_i + self.k)
        return smoothed

    def transform(self, X):
        X = X.copy()
        parts = X[self.col].astype(str).str.split(",")
        X[self.col] = parts.apply(self._encode_row)
        return X


class AmenityScoreTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, amenities_map=AMENITIES_MAP):
        self.amenities_map = amenities_map
        self.unknown_items_ = set()

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        col = X.iloc[:, 0]
        scores_df = col.apply(self._extract_scores)
        return scores_df.values

    def _extract_scores(self, text):
        scores = {
            "amenities_utility_score": 0,
            "amenities_standard_score": 0,
            "amenities_premium_score": 0,
            "amenities_luxury_score": 0,
        }
        if pd.isna(text) or text == "Not Mentioned" or str(text).strip() == "":
            return pd.Series(scores)

        items = [item.strip().lower() for item in str(text).split(",")]
        for item in items:
            category = self.amenities_map.get(item)
            if category is None:
                self.unknown_items_.add(item)
                category = "standard"
            scores[f"amenities_{category}_score"] += 1
        return pd.Series(scores)

    def get_feature_names_out(self, input_features=None):
        return [
            "amenities_utility_score",
            "amenities_standard_score",
            "amenities_premium_score",
            "amenities_luxury_score",
        ]


TITLE_KEYWORDS = [
    'finished', 'fully finished', 'semi finished', 'corner',
    'ready to move', 'prime', 'overlooking', 'installment',
    'luxury', 'modern', 'spacious', 'private',
    'exclusive', 'garden view', 'with balcony',
]


class FrequentAmenityFlagsTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, min_count=50):
        self.min_count = min_count
        self.frequent_amenities_ = []

    def fit(self, X, y=None):
        col = X.iloc[:, 0]
        all_amenities = []
        for text in col.dropna():
            if text != 'Not Mentioned':
                all_amenities.extend([x.strip().lower() for x in str(text).split(',')])
        counts = pd.Series(all_amenities).value_counts()
        self.frequent_amenities_ = counts[counts >= self.min_count].index.tolist()
        return self

    def transform(self, X):
        col = X.iloc[:, 0]
        return col.apply(self._extract_flags).values

    def _extract_flags(self, text):
        flags = {self._sanitize(am): 0 for am in self.frequent_amenities_}
        if pd.isna(text) or text == 'Not Mentioned':
            return pd.Series(flags)
        items = [x.strip().lower() for x in str(text).split(',')]
        for item in items:
            norm = self._sanitize(item)
            if norm in flags:
                flags[norm] = 1
        return pd.Series(flags)

    def _sanitize(self, name):
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '_', name.replace(' ', '_').replace('/', '_'))

    def get_feature_names_out(self, input_features=None):
        return [f'am__{self._sanitize(am)}' for am in self.frequent_amenities_]


class TitleKeywordTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, keywords=None):
        self.keywords = keywords or TITLE_KEYWORDS

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        col = X.iloc[:, 0]
        return col.apply(self._extract_keywords).values

    def _extract_keywords(self, text):
        flags = {f'title_{kw.replace(" ", "_")}': 0 for kw in self.keywords}
        if pd.isna(text):
            return pd.Series(flags)
        text_lower = str(text).lower()
        for kw in self.keywords:
            if kw in text_lower:
                flags[f'title_{kw.replace(" ", "_")}'] = 1
        return pd.Series(flags)

    def get_feature_names_out(self, input_features=None):
        return [f'title_{kw.replace(" ", "_")}' for kw in self.keywords]


def build_preprocessing_pipeline():
    drop_cols = DropColumnsTransformer(
        columns=[
            "link",
            "price_per_sqm",
            "is_studio",
            "transaction_type",
        ]
    )

    target_encoder = SmoothedHierarchicalTargetEncoder(col="location", k=10)
    compound_encoder = SmoothedHierarchicalTargetEncoder(col="compound", k=5)
    district_encoder = SmoothedHierarchicalTargetEncoder(col="district", k=3)
    city_encoder = SmoothedHierarchicalTargetEncoder(col="city", k=3)
    loc_proptype_encoder = SmoothedHierarchicalTargetEncoder(col="location_proptype", k=10)

    preprocessor = ColumnTransformer(
        [
            (
                "area_log",
                FunctionTransformer(np.log1p, np.expm1, feature_names_out="one-to-one"),
                ["area"],
            ),
            (
                "ohe",
                OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"),
                ["property_type", "furnishing", "source"],
            ),
            ("amenities", AmenityScoreTransformer(), ["amenities"]),
            ("amenity_flags", FrequentAmenityFlagsTransformer(), ["amenities"]),
            ("title_keywords", TitleKeywordTransformer(), ["title"]),
        ],
        remainder="passthrough",
    )

    return Pipeline(
        [
            ("drop_cols", drop_cols),
            ("target_encode", target_encoder),
            ("compound_encode", compound_encoder),
            ("district_encode", district_encoder),
            ("city_encode", city_encoder),
            ("loc_proptype_encode", loc_proptype_encoder),
            ("preprocessor", preprocessor),
        ]
    )

PRICE_BINS = [0, 3_000_000, 10_000_000, 23_000_000]
PRICE_LABELS = ['1-3M', '3-10M', '10-23M']

def price_bucket_labels(prices):
    if PRICE_CAP is not None:
        return pd.cut(prices, bins=[0, 3_000_000, 10_000_000, PRICE_CAP], labels=['1-3M', '3-10M', '10-23M'])
    else:
        return pd.cut(prices, bins=[0, 3_000_000, 10_000_000, 23_000_000, 50_000_000, float('inf')],
                      labels=['1-3M', '3-10M', '10-23M', '23-50M', '>50M'])


def preprocess(df):
    df = filter_data(df)
    df = df.drop(columns=['link'], errors='ignore')
    df = df.drop_duplicates()

    df['compound'] = df['location'].apply(
        lambda x: x.split(',')[0].strip() if pd.notna(x) and ',' in x else (x.strip() if pd.notna(x) else 'Unknown')
    )

    df['location_proptype'] = df['location'].fillna('Unknown') + ', ' + df['property_type']
    df['beds_baths'] = df['beds'] * df['baths']

    ids = df['id'] if 'id' in df.columns else None

    sort_col = 'scraped_at' if 'scraped_at' in df.columns else None
    if sort_col is not None:
        df = df.sort_values(sort_col).reset_index(drop=True)

    drop_for_X = ['price', 'scraped_at'] + (['id'] if 'id' in df.columns else [])

    X = df.drop(columns=drop_for_X)
    y = df['price']

    total = len(df)
    train_end = int(total * 0.70)
    val_end = int(total * 0.85)

    X_train = X.iloc[:train_end].reset_index(drop=True)
    X_val = X.iloc[train_end:val_end].reset_index(drop=True)
    X_test = X.iloc[val_end:].reset_index(drop=True)

    y_train = y.iloc[:train_end].reset_index(drop=True)
    y_val = y.iloc[train_end:val_end].reset_index(drop=True)
    y_test = y.iloc[val_end:].reset_index(drop=True)

    ids_train = ids.iloc[:train_end].reset_index(drop=True) if ids is not None else None
    ids_val = ids.iloc[train_end:val_end].reset_index(drop=True) if ids is not None else None
    ids_test = ids.iloc[val_end:].reset_index(drop=True) if ids is not None else None

    district_pps = X_train.groupby('district')['price_per_sqm'].mean()
    global_pps = X_train['price_per_sqm'].mean()
    for split_df in [X_train, X_val, X_test]:
        split_df['district_avg_pps'] = split_df['district'].map(district_pps).fillna(global_pps)

    y_train, y_val, y_test = log_target(y_train, y_val, y_test)

    pipeline = build_preprocessing_pipeline()
    X_train_tr = pipeline.fit_transform(X_train, y_train)
    X_val_tr = pipeline.transform(X_val)
    X_test_tr = pipeline.transform(X_test)

    return X_train_tr, X_val_tr, X_test_tr, y_train, y_val, y_test, pipeline, ids_train, ids_val, ids_test