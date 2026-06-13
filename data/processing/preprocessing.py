from sklearn.preprocessing import FunctionTransformer, OneHotEncoder
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
import pandas as pd 
import numpy as np 


AMENITIES_MAP = {
    # --- 1. Utilities ---
    'electricity meter': 'utility',
    'water meter': 'utility',
    'natural gas': 'utility',
    'landline': 'utility',
    'broadband internet': 'utility',
    'satellite/cable tv': 'utility',
    
    # --- 2. Standard Amenities ---
    'balcony': 'standard',
    'balcony or terrace': 'standard',
    'elevator': 'standard',
    'service elevators': 'standard',
    'elevators in building: 2': 'standard',
    'security': 'standard',
    'security staff': 'standard',
    'cctv security': 'standard',
    'covered parking': 'standard',
    'parking spaces': 'standard',
    'parking spaces: 1': 'standard',
    'parking spaces: 2': 'standard',
    'pets allowed': 'standard',
    'intercom': 'standard',
    'waste disposal': 'standard',
    'maintenance staff': 'standard',
    'cleaning services': 'standard',
    'lobby in building': 'standard',
    'reception/waiting room': 'standard',
    'prayer room': 'standard',
    
    # --- 3. Premium / Space Features ---
    'private garden': 'premium',
    'lawn or garden': 'premium',
    'maids room': 'premium',
    'study room': 'premium',
    'storage areas': 'premium',
    'double glazed windows': 'premium',
    'sea view': 'premium',
    'view': 'premium',
    'freehold': 'premium',
    'kids play area': 'premium',
    'day care center': 'premium',
    'barbeque area': 'premium',
    'cafeteria or canteen': 'premium',
    'shared kitchen': 'premium',
    'laundry room': 'premium',
    'laundry facility': 'premium',
    'atm facility': 'premium',
    'business center': 'premium',
    'conference room': 'premium',
    
    # --- 4. Luxury Features ---
    'pool': 'luxury',
    'swimming pool': 'luxury',
    'jacuzzi': 'luxury',
    'sauna': 'luxury',
    'steam room': 'luxury',
    'gym': 'luxury',
    'gym or health club': 'luxury',
    'central a/c & heating': 'luxury',
    'centrally air-conditioned': 'luxury',
    'central heating': 'luxury',
    'built in kitchen appliances': 'luxury',
    'furnished': 'luxury',
    'electricity backup': 'luxury',
    '24 hours concierge': 'luxury',
    'facilities for disabled': 'luxury'
}


def filter_data(df):
    return df[df['area'] >= 50].copy()


def split_data(X, y):
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def log_target(y_train, y_val, y_test):
    return np.log1p(y_train), np.log1p(y_val), np.log1p(y_test)


class DropColumnsTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop(columns=self.columns, errors='ignore')


class CountBasedHierarchicalTargetEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, col, min_samples=10):
        self.col = col
        self.min_samples = min_samples

    def fit(self, X, y):
        self.global_mean = y.mean()

        self.level_maps = []
        self.level_counts = []

        # split location into levels
        parts = X[self.col].astype(str).str.split(",")

        levels = max(parts.apply(len))

        df = X[[self.col]].copy()
        df["_target"] = y
        df["_parts"] = parts

        # build per-level mappings
        for i in range(levels):
            level_values = df["_parts"].apply(
                lambda x: x[i].strip() if i < len(x) else np.nan
            )

            tmp = pd.DataFrame({
                "key": level_values,
                "target": y
            }).dropna()

            mean_map = tmp.groupby("key")["target"].mean()
            count_map = tmp.groupby("key")["target"].count()

            self.level_maps.append(mean_map)
            self.level_counts.append(count_map)

        return self

    def transform(self, X):
        X = X.copy()
        parts = X[self.col].astype(str).str.split(",")

        result = []

        for row in parts:
            encoded = self.global_mean

            for i in range(len(self.level_maps)):
                if i < len(row):
                    key = row[i].strip()

                    if key in self.level_counts[i]:
                        if self.level_counts[i][key] >= self.min_samples:
                            encoded = self.level_maps[i][key]
                            break

            result.append(encoded)

        X[self.col] = result
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
            'amenities_utility_score': 0,
            'amenities_standard_score': 0,
            'amenities_premium_score': 0,
            'amenities_luxury_score': 0
        }
        if pd.isna(text) or text == 'Not Mentioned' or str(text).strip() == '':
            return pd.Series(scores)

        items = [item.strip().lower() for item in str(text).split(',')]
        for item in items:
            category = self.amenities_map.get(item)
            if category is None:
                self.unknown_items_.add(item)
                category = 'standard'
            scores[f'amenities_{category}_score'] += 1
        return pd.Series(scores)

    def get_feature_names_out(self, input_features=None):
        return [
            'amenities_utility_score',
            'amenities_standard_score',
            'amenities_premium_score',
            'amenities_luxury_score'
        ]


def build_preprocessing_pipeline():
    drop_cols = DropColumnsTransformer(columns=[ 'link', 'source', 'price_per_sqm',
       'is_studio', 'amenity_count', 'transaction_type', 'district', 'city'])

    target_encoder = CountBasedHierarchicalTargetEncoder(col='location')

    preprocessor = ColumnTransformer([
        ('area_log', FunctionTransformer(np.log1p, np.expm1, feature_names_out='one-to-one'), ['area']),
        ('ohe', OneHotEncoder(drop='first', sparse_output=False), ['property_type', 'furnishing']),
        ('amenities', AmenityScoreTransformer(), ['amenities']),
    ], remainder='passthrough')

    return Pipeline([
        ('drop_cols', drop_cols),
        ('target_encode', target_encoder),
        ('preprocessor', preprocessor),
    ])


def preprocess(df):
    df = filter_data(df)


    X = df.drop(columns='price')
    y = df['price']

    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    y_train, y_val, y_test = log_target(y_train, y_val, y_test)

    pipeline = build_preprocessing_pipeline()
    X_train_tr = pipeline.fit_transform(X_train, y_train)
    X_val_tr = pipeline.transform(X_val)
    X_test_tr = pipeline.transform(X_test)

    return X_train_tr, X_val_tr, X_test_tr, y_train, y_val, y_test, pipeline



