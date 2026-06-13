import pandas as pd
import numpy as np
from data.processing.cleaning import (
    clean_price_per_sqm,
    clean_baths,
    clean_studio,
    clean_beds,
    clean_amenities,
    clean_furnishing,
    clean_property_type,
    clean_transaction_type,
    clean_location,
    parse_location_with_unknown,
    parse_location_raw,
    validate,
)


class TestCleanPricePerSqm:
    def test_computes_price_per_sqm(self):
        df = pd.DataFrame({'price': [200000], 'area': [100]})
        result = clean_price_per_sqm(df)
        assert result['price_per_sqm'].iloc[0] == 2000.0

    def test_handles_zero_area(self):
        df = pd.DataFrame({'price': [200000], 'area': [0]})
        result = clean_price_per_sqm(df)
        assert pd.isna(result['price_per_sqm'].iloc[0])


class TestCleanBaths:
    def test_converts_to_integer(self):
        df = pd.DataFrame({
            'baths': ['2', 3, None, '1'],
            'property_type': ['Apartment', 'Villa', 'Apartment', 'Villa'],
            'area': [100, 200, 100, 200],
        })
        result = clean_baths(df)
        assert result['baths'].dtype == int
        assert not result['baths'].isna().any()

    def test_removes_rows_still_nan_after_fill(self):
        df = pd.DataFrame({
            'baths': [None, None],
            'property_type': ['Apartment', 'Villa'],
            'area': [100, 200],
        })
        result = clean_baths(df)
        assert len(result) == 0


class TestCleanStudio:
    def test_detects_studio(self):
        df = pd.DataFrame({'beds': ['Studio', '3', 'studio', 'STUDIO']})
        result = clean_studio(df)
        assert result['is_studio'].tolist() == [True, False, True, True]
        assert result['beds'].tolist() == [0, '3', 'studio', 'STUDIO']


class TestCleanBeds:
    def test_converts_to_integer(self):
        df = pd.DataFrame({
            'beds': ['3', '2', None, '4'],
            'property_type': ['Apartment', 'Villa', 'Apartment', 'Villa'],
        })
        result = clean_beds(df)
        assert result['beds'].dtype == int
        assert not result['beds'].isna().any()


class TestCleanAmenities:
    def test_fills_empty_with_not_mentioned(self):
        df = pd.DataFrame({'amenities': ['pool,gym', '', None, 'Not Mentioned']})
        result = clean_amenities(df)
        assert result['amenities'].tolist() == ['pool,gym', 'Not Mentioned', 'Not Mentioned', 'Not Mentioned']

    def test_computes_amenity_count(self):
        df = pd.DataFrame({'amenities': ['pool,gym,balcony', '', 'elevator', 'a,b,c,d']})
        result = clean_amenities(df)
        assert result['amenity_count'].tolist() == [3, 0, 1, 4]


class TestCleanFurnishing:
    def test_fills_missing(self):
        df = pd.DataFrame({'furnishing': ['Furnished', None, pd.NA, 'Unfurnished']})
        result = clean_furnishing(df)
        assert result['furnishing'].tolist() == ['Furnished', 'Not Specified', 'Not Specified', 'Unfurnished']


class TestCleanPropertyType:
    def test_standardizes_names(self):
        df = pd.DataFrame({'property_type': ['Town House', 'Standalone Villa', 'Ivilla', 'Roof', 'Apartment']})
        result = clean_property_type(df)
        assert result['property_type'].tolist() == ['Townhouse', 'Stand Alone Villa', 'Stand Alone Villa', 'Other', 'Apartment']

    def test_strips_and_titles(self):
        df = pd.DataFrame({'property_type': ['  APARTMENT ', 'villa']})
        result = clean_property_type(df)
        assert result['property_type'].tolist() == ['Apartment', 'Villa']


class TestCleanTransactionType:
    def test_detects_sale(self):
        df = pd.DataFrame({'link': ['https://example.com/property/for-sale/1',
                                    'https://example.com/property/for-rent/1']})
        result = clean_transaction_type(df)
        assert len(result) == 1
        assert result['transaction_type'].iloc[0] == 'sale'


class TestParseLocation:
    def test_parse_location_with_unknown_finds_city(self):
        district, city = parse_location_with_unknown("Cairo, New Cairo")
        assert district == "Cairo"
        assert city == "Cairo"

    def test_parse_location_with_unknown_falls_back(self):
        district, city = parse_location_with_unknown("Somewhere, Nowhere")
        assert district == "Somewhere"
        assert city == "Unknown"

    def test_parse_location_raw(self):
        district, city = parse_location_raw("Cairo, New Cairo, 5th Settlement")
        assert district == "Cairo"
        assert city == "5th Settlement"

    def test_parse_location_nan(self):
        district, city = parse_location_with_unknown(pd.NA)
        assert pd.isna(district)
        assert pd.isna(city)

        district, city = parse_location_raw(pd.NA)
        assert pd.isna(district)
        assert pd.isna(city)


class TestValidate:
    def test_drops_price_zero(self):
        df = pd.DataFrame({
            'price': [0, 100000], 'area': [100, 200],
            'beds': [2, 3], 'baths': [1, 2],
            'property_type': ['Apt', 'Apt'], 'city': ['Cairo', 'Giza'],
            'transaction_type': ['sale', 'sale'], 'amenity_count': [0, 0],
        })
        result = validate(df)
        assert len(result) == 1

    def test_drops_negative_price(self):
        df = pd.DataFrame({
            'price': [-100, 100000], 'area': [100, 200],
            'beds': [2, 3], 'baths': [1, 2],
            'property_type': ['Apt', 'Apt'], 'city': ['Cairo', 'Giza'],
            'transaction_type': ['sale', 'sale'], 'amenity_count': [0, 0],
        })
        result = validate(df)
        assert len(result) == 1

    def test_drops_negative_area(self):
        df = pd.DataFrame({
            'price': [100000, 100000], 'area': [-10, 200],
            'beds': [2, 3], 'baths': [1, 2],
            'property_type': ['Apt', 'Apt'], 'city': ['Cairo', 'Giza'],
            'transaction_type': ['sale', 'sale'], 'amenity_count': [0, 0],
        })
        result = validate(df)
        assert len(result) == 1

    def test_drops_urban_transaction_types(self):
        df = pd.DataFrame({
            'price': [100000, 100000], 'area': [100, 200],
            'beds': [2, 3], 'baths': [1, 2],
            'property_type': ['Apt', 'Apt'], 'city': ['Cairo', 'Giza'],
            'transaction_type': ['rent', 'sale'], 'amenity_count': [0, 0],
        })
        result = validate(df)
        assert len(result) == 1
        assert result['transaction_type'].iloc[0] == 'sale'

    def test_drops_duplicates(self):
        df = pd.DataFrame({
            'price': [100000, 100000], 'area': [100, 100],
            'beds': [2, 2], 'baths': [1, 1],
            'property_type': ['Apt', 'Apt'], 'city': ['Cairo', 'Cairo'],
            'transaction_type': ['sale', 'sale'], 'amenity_count': [0, 0],
        })
        result = validate(df)
        assert len(result) == 1

    def test_keeps_valid_rows(self):
        df = pd.DataFrame({
            'price': [100000, 200000], 'area': [100, 200],
            'beds': [2, 3], 'baths': [1, 2],
            'property_type': ['Apt', 'Villa'], 'city': ['Cairo', 'Giza'],
            'transaction_type': ['sale', 'sale'], 'amenity_count': [0, 1],
        })
        result = validate(df)
        assert len(result) == 2
