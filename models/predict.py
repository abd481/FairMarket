import argparse 
import sys 
from pathlib import Path 

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT_ROOT))

import pandas as pd 
import numpy as np
import joblib
from sqlalchemy import create_engine

from utils.secrets import get_secret 

ENGINE = create_engine(get_secret('POSTGRES','postgres'))
VILLA_TYPES = ['Villa','Stand Alone Villa']



def load_artifacts(mode): 
    base = PROJECT_ROOT / 'artifacts'
    pipeline = joblib.load(base / 'pipelines' / f'{mode}_pipeline.joblib')
    model = joblib.load(base / 'models' / f'{mode}_xgb_model.joblib')
    pps = joblib.load(base / 'models' / f'{mode}_district_pps.joblib')
    calib = joblib.load(base / 'models' / f'{mode}_calib.joblib')
    return pipeline,model,pps['district_pps'],pps['global_pps'],calib


def classify_mode(property_type) : 
    return 'only_villas' if property_type in VILLA_TYPES else 'no_villas'

def prepare_row(row,district_pps,global_pps): 
    row = row.copy() 
    loc = row.get('location','') or ''
    row['compound'] = loc.split(',')[0].strip() if ',' in loc else loc.strip() 
    row['location_proptype'] = f"{loc},{row.get('property_type', '')}"
    row['beds_baths'] = row.get('beds',0) * row.get('baths',0)
    row['district_avg_pps'] = district_pps.get(row.get('district'),global_pps)
    return row 

def predict_single(property_id): 
    df = pd.read_sql(f'SELECT * FROM clean_properties WHERE id = {property_id}',ENGINE)
    if df.empty : 
        print(f"No property found with id={property_id}")
        return 
    row = df.iloc[0]
    mode = classify_mode(row['property_type'])
    pipeline, model, district_pps, global_pps, calib = load_artifacts(mode)

    prepared = prepare_row(row,district_pps,global_pps)
    X = pipeline.transform(pd.DataFrame([prepared]))
    pred_log = model.predict(X)[0]
    pred_price = np.expm1(pred_log)
   
    pred_bin = pd.cut([pred_price], bins=calib['bins'], include_lowest=True)[0]
    q = calib['calib_map'].get(pred_bin, 0)
    lower = pred_price - q 
    upper = pred_price + q 

    
    print(f"Property {property_id} ({row['property_type']}, {row['district']})")
    print(f'Mode: {mode}')
    print(f'Predicted Price ${pred_price:,.0f}  [${lower:,.0f} - ${upper:,.0f}]')


def predict_batch():
    try:
        df = pd.read_sql("""
                  SELECT * FROM clean_properties 
                  WHERE id NOT IN (SELECT property_id FROM property_predictions)
               """, ENGINE)
    except Exception:
        df = pd.read_sql("SELECT * FROM clean_properties", ENGINE)

    if df.empty : 
        print("No unpredicted listings found.")
        return 
    
    villa_df = df[df['property_type'].isin(VILLA_TYPES)].copy()
    no_villa_df = df[~df['property_type'].isin(VILLA_TYPES)].copy()

    results = []

    for group_df, mode in [(villa_df, 'only_villas'), (no_villa_df, 'no_villas')]:
        if group_df.empty:
            continue

        pipeline, model, district_pps, global_pps, calib = load_artifacts(mode)
        prepared = group_df.apply(lambda r: prepare_row(r, district_pps, global_pps), axis=1)
        X = pipeline.transform(prepared)
        preds = np.expm1(model.predict(X))

        for i, (_, row) in enumerate(group_df.iterrows()):
            pred_bin = pd.cut([preds[i]], bins=calib['bins'], include_lowest=True)[0]
            q = calib['calib_map'].get(pred_bin, 0)
            results.append({
                'property_id': int(row['id']),
                'mode': mode,
                'predicted_price': float(preds[i]),
                'predicted_price_lower': float(preds[i] - q),
                'predicted_price_upper': float(preds[i] + q),
            })

    results_df = pd.DataFrame(results)
    print(f'Predicted {len(results_df)} listings')
    save_predictions(results_df)

def predict_from_features(features:dict, district_pps:dict, 
                          global_pps: float, pipeline, model, calib,resolved_location) -> dict : 
    # prepare_row(features,district_pps,global_pps)
    # transform - predict exmp1 
    # bin - get residual lower/upper 
    # return dict 
    
    features['city'] = resolved_location['city'] 
    features['district'] = resolved_location['district']
    features['furnishing'] = 'Not Mentioned'
    features['source'] = ''
    features['title'] = ''
    features['amenities'] = ''

    prep_feat = prepare_row(features,district_pps,global_pps)
    X = pipeline.transform(pd.DataFrame([prep_feat]))

    pred_log = model.predict(X)[0]
    pred_price = np.expm1(pred_log)

    pred_bin = pd.cut([pred_price],bins=calib['bins'],include_lowest=True)[0]
    q = calib['calib_map'].get(pred_bin,0)

    return  {
        'predicted_price': pred_price, 
        'price_lower': pred_price - q , 
        'price_upper': pred_price + q 
    }
 
def save_predictions(df) : 
    conn = ENGINE.raw_connection()
    with conn.cursor() as cur : 
        cur.execute("""
           CREATE TABLE IF NOT EXISTS property_predictions (
                id  SERIAL PRIMARY KEY , 
                property_id       INTEGER NOT NULL , 
                mode              VARCHAR(20) NOT NULL , 
                predicted_price   FLOAT NOT NULL , 
                predicted_price_lower FLOAT NOT NULL , 
                 predicted_price_upper FLOAT NOT NULL ,
                 predicted_at    TIMESTAMP DEFAULT NOW()   
                    
                )
""")
    conn.commit()
    conn.close()

    df.to_sql('property_predictions',ENGINE,if_exists='append',index=False)
    print(f'Saved {len(df)} predictions to property_predictions table')


    
if __name__ == '__main__' : 
    parser = argparse.ArgumentParser()
    parser.add_argument("--property-id",type=int,help='Preidct a single property by ID')
    args = parser.parse_args()

    if args.property_id: 
        predict_single(args.property_id)
    
    else : 
        predict_batch()