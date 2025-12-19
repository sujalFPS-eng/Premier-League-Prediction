from fastapi import FastAPI
import joblib
import pandas as pd
import os

app = FastAPI()

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "rolling_rf_model.joblib")
data_path = os.path.join(BASE_DIR, "database", "rolling_data.csv")

# --- LOAD RESOURCES ---
if not os.path.exists(model_path) or not os.path.exists(data_path):
    raise FileNotFoundError("Model or Data not found. Run train_rolling.py first.")

model = joblib.load(model_path)
rolling_data = pd.read_csv(data_path)

@app.get("/")
def home():
    return {"status": "Advanced Predictor Online"}

@app.get("/predict/{home_id}/{away_id}")
def predict_match(home_id: int, away_id: int):
    # 1. Get stats for BOTH teams (to send to frontend for graphing)
    h_stats = rolling_data[rolling_data["home_team_id"] == home_id].iloc[-1:]
    a_stats = rolling_data[rolling_data["home_team_id"] == away_id].iloc[-1:]
    
    if h_stats.empty or a_stats.empty:
        return {"error": "Insufficient data"}
    
    # 2. Prepare Input for Model (Home Perspective)
    cols = ["gf_rolling", "ga_rolling", "xg_rolling", "xga_rolling", 
            "poss_rolling", "sh_rolling", "sot_rolling", "dist_rolling"]
    
    input_data = h_stats[cols].copy()
    input_data["home_team_id"] = home_id
    input_data["away_team_id"] = away_id
    input_data["venue_code"] = 1 
    
    # 3. Get Prediction AND Probabilities
    pred_code = model.predict(input_data)[0]
    probabilities = model.predict_proba(input_data)[0] # Returns [prob_loss, prob_draw, prob_win]
    
    result_map = {0: "Away Win", 1: "Draw", 2: "Home Win"}
    
    return {
        "prediction": result_map[pred_code],
        "probs": {
            "away": round(probabilities[0], 2),
            "draw": round(probabilities[1], 2),
            "home": round(probabilities[2], 2)
        },
        "stats": {
            "home": h_stats[cols].to_dict(orient="records")[0],
            "away": a_stats[cols].to_dict(orient="records")[0]
        }
    }