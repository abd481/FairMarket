# In the name of Allah, The Most Gracious, The Most Merciful

import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from utils.secrets import get_secret
load_dotenv()

KNOWN_CITIES = [
    'Cairo',
    'Giza',
    'Alexandria',
    'New Cairo',
    'New Capital City'
]


def get_engine():
    return create_engine(get_secret("POSTGRES",'postgres'))


def load_data() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM properties", get_engine())
    print(f"✅ Loaded {len(df)} rows")
    return df


def clean_price_per_sqm(df: pd.DataFrame) -> pd.DataFrame:
    df['price_per_sqm'] = df['price'] / df['area'].replace(0, pd.NA)
    return df


def clean_baths(df: pd.DataFrame) -> pd.DataFrame:
    df['baths'] = pd.to_numeric(df['baths'], errors='coerce')
    df['baths'] = df.groupby('property_type')['baths'].transform(
        lambda x: x.fillna(x.median())
    )
    df['baths'] = df['baths'].astype(int)
    return df


def clean_studio(df: pd.DataFrame) -> pd.DataFrame:
    df['is_studio'] = (
        df['beds']
        .astype(str)
        .str.contains('Studio', case=False, na=False)
    )
    df['beds'] = df['beds'].replace('Studio', 0)
    return df


def clean_beds(df: pd.DataFrame) -> pd.DataFrame:
    df['beds'] = pd.to_numeric(df['beds'], errors='coerce')
    df['beds'] = df.groupby('property_type')['beds'].transform(
        lambda x: x.fillna(x.median())
    )
    df['beds'] = df['beds'].astype(int)
    return df


def clean_furnishing(df: pd.DataFrame) -> pd.DataFrame:
    df['furnishing'] = df['furnishing'].fillna('Not Specified')
    return df


def clean_property_type(df: pd.DataFrame) -> pd.DataFrame:
    df['property_type'] = (
        df['property_type']
        .str.strip()
        .str.title()
    )
    return df


def clean_transaction_type(df: pd.DataFrame) -> pd.DataFrame:
    df['transaction_type'] = (
        df['link']
        .str.contains('for-rent', case=False, na=False)
        .map({True: 'rent', False: 'sale'})
    )
    df = df[df['transaction_type'] == 'sale']
    return df


def parse_location_with_unknown(location):
    if pd.isna(location):
        return pd.NA, pd.NA
    parts = [p.strip() for p in location.split(',')]
    district = parts[0]
    city = 'Unknown'
    for part in parts:
        if part in KNOWN_CITIES:
            city = part
            break
    return district, city


def parse_location_raw(location):
    if pd.isna(location):
        return pd.NA, pd.NA
    parts = [p.strip() for p in location.split(',')]
    district = parts[0]
    city = parts[-1]
    return district, city


def clean_location(df: pd.DataFrame, use_known_cities: bool = True) -> pd.DataFrame:
    parser = parse_location_with_unknown if use_known_cities else parse_location_raw
    df[['district', 'city']] = (
        df['location']
        .apply(parser)
        .apply(pd.Series)
    )
    return df


def drop_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=[
        'id', 'checksum', 'title',
        'reactivated_date', 'scraped_at', 'transformed_at'
    ])
    return df


def save_data(df: pd.DataFrame) -> None:
    df.to_sql(
        name='clean_properties',
        con=get_engine(),
        if_exists='replace',
        index=False
    )
    print(f"✅ Saved {len(df)} rows to clean_properties")


def clean():
    df = load_data()
    df = clean_price_per_sqm(df)
    df = clean_baths(df)
    df = clean_studio(df)
    df = clean_beds(df)
    df = clean_furnishing(df)
    df = clean_property_type(df)
    df = clean_transaction_type(df)
    df = clean_location(df, use_known_cities=True)
    df = drop_columns(df)
    save_data(df)

if __name__ == "__main__":
    clean()
