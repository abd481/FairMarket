import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_raw_listing():
    return {
        "Price": 1500000,
        "Location": "Cairo, New Cairo",
        "Title": "Nice Apartment",
        "Beds": 3,
        "Baths": 2,
        "Area": "150 sqm",
        "Type": "Apartment",
        "Furnishing": "Furnished",
        "Amenities": '["pool", "gym"]',
        "Link": "https://example.com/1",
        "Reactivated date": "12 March 2024",
    }


@pytest.fixture
def sample_normalized_row():
    return {
        "price": 1500000,
        "location": "Cairo, New Cairo",
        "title": "Nice Apartment",
        "beds": 3,
        "baths": 2,
        "area": 150.0,
        "property_type": "Apartment",
        "furnishing": "Furnished",
        "amenities": '["pool", "gym"]',
        "link": "https://example.com/1",
        "reactivated_date": "12 March 2024",
    }


@pytest.fixture
def sample_df():
    n = 50
    return pd.DataFrame({
        'price': np.random.uniform(50000, 5000000, n),
        'area': np.random.uniform(50, 500, n),
        'beds': np.random.randint(1, 5, n),
        'baths': np.random.randint(1, 4, n),
        'property_type': np.random.choice(['Apartment', 'Villa', 'Duplex'], n),
        'furnishing': np.random.choice(['Furnished', 'Unfurnished', 'Semi-Furnished'], n),
        'location': ['Cairo,New Cairo,5th Settlement' if i % 3 == 0
                     else 'Giza,6th October' if i % 3 == 1
                     else 'Alexandria' for i in range(n)],
        'amenities': np.random.choice(['pool,gym,balcony', 'elevator,security',
                                       'balcony,pets allowed,gym', ''], n),
        'link': ['https://example.com/' + str(i) for i in range(n)],
        'source': ['bayut'] * n,
        'price_per_sqm': [0.0] * n,
        'transaction_type': ['sale'] * n,
        'is_studio': [False] * n,
        'amenity_count': [0] * n,
        'district': [''] * n,
        'city': [''] * n,
    })


@pytest.fixture
def sample_df_with_issues():
    df = pd.DataFrame({
        'price': [100000, -5000, 0, 200000, 150000],
        'area': [100, 50, 0, -10, 200],
        'beds': [2, 0, -1, 3, 25],
        'baths': [1, 0, -1, 2, 3],
        'property_type': ['Apartment', 'Villa', 'Duplex', 'Unknown', 'Apartment'],
        'furnishing': ['Furnished', 'Unfurnished', 'Semi-Furnished', '', None],
        'location': ['Cairo', 'Giza', 'Alexandria', None, 'New Cairo'],
        'amenities': ['pool,gym', 'elevator', '', 'balcony', 'Not Mentioned'],
        'link': ['url1', 'url2', 'url3', 'url4', 'url5'],
        'source': ['bayut', 'olx', 'unknown', 'dubizzle', 'aqarmap'],
        'price_per_sqm': [0.0] * 5,
        'transaction_type': ['sale', 'sale', 'rent', 'sale', 'sale'],
        'is_studio': [False] * 5,
        'amenity_count': [0] * 5,
        'district': [''] * 5,
        'city': [''] * 5,
    })
    return df
