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
    # make a copy so we don't modify the original dataframe
    df = df.copy()

    # convert baths column to numeric
    # invalid values become NaN
    df['baths'] = pd.to_numeric(
        df['baths'],
        errors='coerce'
    )

    # fill missing baths values using the median
    # inside each (property_type, area) group
    df['baths'] = df.groupby(
        ['property_type', 'area']
    )['baths'].transform(
        lambda x: x.fillna(x.median())
    )

    # remove rows where baths is still NaN
    df = df.dropna(subset=['baths'])

    # convert to integer
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

def clean_amenities(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df['amenities'] = df['amenities'].replace('', pd.NA)
    df['amenities'] = df['amenities'].fillna('Not Mentioned')

    def parse_amenities(text):
        if pd.isna(text) or text == 'Not Mentioned':
            return 0
        return len([item.strip() for item in str(text).split(',') if item.strip()])

    df['amenity_count'] = df['amenities'].apply(parse_amenities)

    return df

def clean_furnishing(df: pd.DataFrame) -> pd.DataFrame:
    df['furnishing'] = df['furnishing'].fillna('Not Specified')
    return df


def clean_property_type(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        'Town House': 'Townhouse',
        'Standalone Villa': 'Stand Alone Villa',
        'Ivilla': 'Stand Alone Villa',
        'Roof': 'Other',
        'Other Residential': 'Other',
        'Room': 'Other'
    }
    df['property_type'] = (
        df['property_type']
        .str.strip()
        .str.title()
        .replace(mapping)
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
    # print(f"✅ Saved {len(df)} rows to clean_properties")

def validate(df: pd.DataFrame) -> pd.DataFrame:
    initial_count = len(df)
    
    # 1. drop nulls in critical columns
    critical_columns = ['price', 'area', 'beds', 'baths', 'property_type', 'city']
    df = df.dropna(subset=critical_columns)
    
    # 2. drop invalid price and area
    df = df[df['price'] > 0]
    df = df[df['area'] > 0]
    
    # 3. drop negative beds and baths
    df = df[df['beds'] >= 0]
    df = df[df['baths'] >= 0]
    
    # 4. drop unexpected transaction types
    df = df[df['transaction_type'] == 'sale']
    
    # 5. drop negative amenity_count
    df = df[df['amenity_count'] >= 0]
    
    # 6. drop duplicates
    df = df.drop_duplicates()
    
    dropped = initial_count - len(df)
    if dropped > 0:
        print(f"⚠️ Validation dropped {dropped} bad rows — {len(df)} rows remaining")
    else:
        print(f"✅ All {len(df)} rows passed validation")
    
    return df

def clean():
    df = load_data()
    df = clean_price_per_sqm(df)
    df = clean_baths(df)
    df = clean_studio(df)
    df = clean_beds(df)
    df = clean_amenities(df)
    df = clean_furnishing(df)
    df = clean_property_type(df)
    df = clean_transaction_type(df)
    df = clean_location(df, use_known_cities=True)
    df = drop_columns(df)
    df = validate(df)
    save_data(df)

if __name__ == "__main__":
    clean()
