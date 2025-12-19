import pandas as pd
import sqlite3
import joblib
import os
from sklearn.ensemble import RandomForestClassifier

print("🚀 Starting Training Script...")

# --- 1. SMART PATH SETUP ---
# This logic finds the 'pl project' root folder no matter where this script is saved
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_dir) == "models":
    BASE_DIR = os.path.dirname(current_dir) # Go up one level to 'pl project'
else:
    BASE_DIR = current_dir

# Define exact paths
db_path = os.path.join(BASE_DIR, "database", "premier_league.db")
model_path = os.path.join(BASE_DIR, "models", "rolling_rf_model.joblib")
data_path = os.path.join(BASE_DIR, "database", "rolling_data.csv")

print(f"📂 looking for DB at: {db_path}")

if not os.path.exists(db_path):
    print("❌ ERROR: Database not found!")
    exit()

# --- 2. LOAD DATA ---
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM matches", conn)
conn.close()

# Sort by date is crucial for rolling averages
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# --- 3. CREATE ROLLING AVERAGES (The "Data Fix") ---
def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    # min_periods=1: This is the MAGIC FIX. 
    # It allows the model to predict even if a team only has 1 previous game.
    rolling_stats = group[cols].rolling(3, closed='left', min_periods=1).mean()
    group[new_cols] = rolling_stats
    
    # We remove rows ONLY if they are completely empty (no history at all)
    group = group.dropna(subset=new_cols)
    return group

cols = ["gf", "ga", "xg", "xga", "poss", "sh", "sot", "dist"]
new_cols = [f"{c}_rolling" for c in cols]

matches_rolling = df.groupby("home_team_id").apply(lambda x: rolling_averages(x, cols, new_cols))
matches_rolling = matches_rolling.reset_index(drop=True)

print(f"✅ Processed {len(matches_rolling)} matches with rolling stats.")

# --- 4. TRAIN MODEL ---
matches_rolling["venue_code"] = (matches_rolling["venue"] == "Home").astype(int)
matches_rolling["target"] = matches_rolling["result"].map({"L": 0, "D": 1, "W": 2})

predictors = new_cols + ["home_team_id", "away_team_id", "venue_code"]

rf = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=1)
rf.fit(matches_rolling[predictors], matches_rolling["target"])

# --- 5. SAVE EVERYTHING ---
joblib.dump(rf, model_path)
matches_rolling.to_csv(data_path, index=False)

print("✅ SUCCESS: Model and Data saved!")
print("👉 You can now restart your API and Streamlit app.")