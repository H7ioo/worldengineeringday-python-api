from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import json
import os

app = FastAPI(title="Istanbul Seismic Dashboard API - Full Data Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'master_datasheet.csv')
DEFAULT_W = {"lives": 0.5, "buildings": 0.3, "infra": 0.2}

# Load base data once on startup
df_base = pd.read_csv(DATA_FILE)

@app.get("/neighborhoods-priority")
async def get_dashboard_data(
    w_lives: float = Query(None),
    w_buildings: float = Query(None),
    w_infra: float = Query(None)
):
    wl = w_lives if w_lives is not None else DEFAULT_W["lives"]
    wb = w_buildings if w_buildings is not None else DEFAULT_W["buildings"]
    wi = w_infra if w_infra is not None else DEFAULT_W["infra"]

    is_default = (wl == DEFAULT_W["lives"] and wb == DEFAULT_W["buildings"] and wi == DEFAULT_W["infra"])
    
    df = df_base.copy()

    if not is_default:
        # --- DYNAMIC CALCULATION ENGINE ---
        df['infra_score_calc'] = df[['dogalgaz_boru_hasari', 'icme_suyu_boru_hasari', 'atik_su_boru_hasari']].sum(axis=1)
        df['life_density'] = df['can_kaybi_sayisi'] / (df['total_buildings_mahalle'] + 1)
        
        mask_valid = (df[['cok_agir_hasarli_bina_sayisi', 'can_kaybi_sayisi', 'infra_score_calc']].sum(axis=1) > 0)
        valid_df = df[mask_valid].copy()
        
        if not valid_df.empty:
            scaler = MinMaxScaler()
            cols = ['life_density', 'infra_score_calc', 'structural_fragility_score', 'cok_agir_hasarli_bina_sayisi']
            scaled = scaler.fit_transform(valid_df[cols])
            
            total_w = wl + wb + wi
            s = (scaled[:, 0] * (wl/total_w) + scaled[:, 3] * (wb/total_w) + scaled[:, 1] * (wi/total_w))
            
            valid_df['risk_score'] = (s * 100).round(2)
            valid_df['risk_category'] = pd.qcut(s, 4, labels=['LOW', 'MEDIUM', 'HIGH', 'EXTREME'])
            
            df.loc[mask_valid, 'risk_score'] = valid_df['risk_score']
            df.loc[mask_valid, 'risk_category'] = valid_df['risk_category']
    else:
        # Scale static score to 0-100
        df['risk_score'] = (df['risk_score'] * 100).round(2)

    # --- FULL DATA JSON MAPPING ---
    response = []
    for _, row in df.iterrows():
        # Safely parse address if it's a stringified JSON
        try:
            addr_obj = json.loads(row['address'])
        except:
            addr_obj = row['address']

        response.append({
            "metadata": {
                "ilce_adi": row['ilce_adi'],
                "mahalle_adi": row['mahalle_adi'],
                "uavt_code": int(row['mahalle_koy_uavt']),
                "display_name": row['display_name'],
                "address_details": addr_obj
            },
            "geometry": {
                "lat": row['latitude'],
                "lng": row['longitude']
            },
            "demographics": {
                "estimated_population": int(row['estimated_population_mahalle'])
            },
            "building_inventory": {
                "total_count": int(row['total_buildings_mahalle']),
                "age_distribution": {
                    "pre_1980": int(row['1980_oncesi']),
                    "1980_2000": int(row['1980-2000_arasi']),
                    "post_2000": int(row['2000_sonrasi'])
                },
                "floor_distribution": {
                    "floors_1_4": int(row['1-4 kat_arasi']),
                    "floors_5_9": int(row['5-9 kat_arasi']),
                    "floors_9_19": int(row['9-19 kat_arasi'])
                }
            },
            "seismic_impact": {
                "building_damage": {
                    "very_severe": int(row['cok_agir_hasarli_bina_sayisi']),
                    "severe": int(row['agir_hasarli_bina_sayisi']),
                    "moderate": int(row['orta_hasarli_bina_sayisi']),
                    "slight": int(row['hafif_hasarli_bina_sayisi'])
                },
                "human_impact": {
                    "casualties": int(row['can_kaybi_sayisi']),
                    "severe_injuries": int(row['agir_yarali_sayisi']),
                    "hospitalizations": int(row['hastanede_tedavi_sayisi']),
                    "temporary_shelter_needed": int(row['gecici_barinma'])
                },
                "infrastructure_damage": {
                    "natural_gas": int(row['dogalgaz_boru_hasari']),
                    "drinking_water": int(row['icme_suyu_boru_hasari']),
                    "wastewater": int(row['atik_su_boru_hasari'])
                }
            },
            "analysis": {
                "fragility_score": row['structural_fragility_score'],
                "priority_score": row['risk_score'],
                "risk_label": row['risk_category']
            }
        })
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)