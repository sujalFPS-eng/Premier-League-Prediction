import streamlit as st
import pandas as pd
import sqlite3
import requests
import os
import plotly.graph_objects as go

st.set_page_config(page_title="PL Pro Predictor", page_icon="⚽", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1 { color: #ffffff; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stSelectbox"] > label { color: #ffffff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. ROBUST LOGO LINKS (Verified) ---
logos = {
    "Arsenal": "https://resources.premierleague.com/premierleague/badges/t3.svg",
    "Aston Villa": "https://resources.premierleague.com/premierleague/badges/t7.svg",
    "Bournemouth": "https://resources.premierleague.com/premierleague/badges/t91.svg",
    "Brentford": "https://resources.premierleague.com/premierleague/badges/t94.svg",
    "Brighton": "https://resources.premierleague.com/premierleague/badges/t36.svg",
    "Burnley": "https://resources.premierleague.com/premierleague/badges/t90.svg",
    "Chelsea": "https://resources.premierleague.com/premierleague/badges/t8.svg",
    "Crystal Palace": "https://resources.premierleague.com/premierleague/badges/t31.svg",
    "Everton": "https://resources.premierleague.com/premierleague/badges/t11.svg",
    "Fulham": "https://resources.premierleague.com/premierleague/badges/t54.svg",
    "Leeds United": "https://resources.premierleague.com/premierleague/badges/t2.svg",
    "Leicester City": "https://resources.premierleague.com/premierleague/badges/t13.svg",
    "Liverpool": "https://resources.premierleague.com/premierleague/badges/t14.svg",
    "Luton Town": "https://resources.premierleague.com/premierleague/badges/t102.svg",
    "Manchester City": "https://resources.premierleague.com/premierleague/badges/t43.svg",
    "Manchester United": "https://resources.premierleague.com/premierleague/badges/t1.svg",
    "Newcastle United": "https://resources.premierleague.com/premierleague/badges/t4.svg",
    "Nottingham Forest": "https://resources.premierleague.com/premierleague/badges/t17.svg",
    "Sheffield United": "https://resources.premierleague.com/premierleague/badges/t49.svg",
    "Southampton": "https://resources.premierleague.com/premierleague/badges/t20.svg",
    "Tottenham Hotspur": "https://resources.premierleague.com/premierleague/badges/t6.svg",
    "West Ham United": "https://resources.premierleague.com/premierleague/badges/t21.svg",
    "Wolverhampton Wanderers": "https://resources.premierleague.com/premierleague/badges/t39.svg"
}

# --- 2. NAME FIXER (Matches DB names to Logo Keys) ---
name_fixer = {
    "Man Utd": "Manchester United",
    "Manchester Utd": "Manchester United",
    "Man City": "Manchester City",
    "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "West Ham": "West Ham United",
    "Newcastle": "Newcastle United",
    "Brighton & Hove Albion": "Brighton",
    "Nott'm Forest": "Nottingham Forest",
    "Wolves": "Wolverhampton Wanderers",
    "Sheffield Utd": "Sheffield United",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Aston Villa": "Aston Villa" # Explicit keep
}

# --- PATH SETUP ---
current_file_path = os.path.abspath(__file__)
root_dir = os.path.dirname(os.path.dirname(current_file_path))
db_path = os.path.join(root_dir, "database", "premier_league.db")

@st.cache_data
def get_teams():
    if not os.path.exists(db_path): return {}
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql("SELECT team_id, team_name FROM teams", conn)
        conn.close()
    except: return {}
    
    clean_map = {}
    for index, row in df.iterrows():
        raw_name = row['team_name']
        t_id = row['team_id']
        # Normalize name
        clean_name = name_fixer.get(raw_name, raw_name)
        clean_map[clean_name] = t_id
        
    return clean_map

team_mapping = get_teams()

# --- HEADER ---
st.title("⚽ PREMIER LEAGUE AI ANALYST")
st.markdown("---")

if not team_mapping:
    st.error("Database Error: No teams found.")
    st.stop()

# --- TEAM SELECTION ---
col1, col2, col3 = st.columns([1, 0.2, 1])

with col1:
    st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>HOME</h3>", unsafe_allow_html=True)
    home_team = st.selectbox("Select Home Team", options=sorted(team_mapping.keys()), index=0, label_visibility="collapsed")
    if home_team in logos:
        st.markdown(f"<div style='text-align: center; padding: 10px;'><img src='{logos[home_team]}' width='120'></div>", unsafe_allow_html=True)
    else:
        st.warning(f"Logo missing: {home_team}")

with col2:
    st.markdown("<h1 style='text-align: center; padding-top: 50px;'>VS</h1>", unsafe_allow_html=True)

with col3:
    st.markdown("<h3 style='text-align: center; color: #4b4bff;'>AWAY</h3>", unsafe_allow_html=True)
    away_team = st.selectbox("Select Away Team", options=sorted(team_mapping.keys()), index=1, label_visibility="collapsed")
    if away_team in logos:
        st.markdown(f"<div style='text-align: center; padding: 10px;'><img src='{logos[away_team]}' width='120'></div>", unsafe_allow_html=True)
    else:
        st.warning(f"Logo missing: {away_team}")

# --- PREDICTION LOGIC ---
st.markdown("---")
if st.button("🚀 ANALYZE MATCHUP", use_container_width=True):
    if home_team == away_team:
        st.error("Teams must be different!")
    else:
        h_id = team_mapping[home_team]
        a_id = team_mapping[away_team]
        
        try:
            response = requests.get(f"http://127.0.0.1:8000/predict/{h_id}/{a_id}")
            data = response.json()
            
            if "error" in data:
                st.warning("⚠️ Not enough history to predict this exact matchup.")
                st.info("Tip: This team might be newly promoted or lack 3 recent games in the database.")
            else:
                pred = data["prediction"]
                probs = data["probs"]
                stats = data["stats"]
                
                # 1. RESULT BANNER
                res_col1, res_col2 = st.columns([1, 2])
                with res_col1:
                    st.subheader("AI Prediction")
                    if "Home" in pred:
                        st.success(f"🏆 {home_team} WIN")
                    elif "Away" in pred:
                        st.error(f"🏆 {away_team} WIN")
                    else:
                        st.warning("🤝 DRAW PREDICTED")
                
                with res_col2:
                    st.subheader("Confidence Meter")
                    st.progress(probs['home'], text=f"{home_team} Win: {int(probs['home']*100)}%")
                    st.progress(probs['draw'], text=f"Draw: {int(probs['draw']*100)}%")
                    st.progress(probs['away'], text=f"{away_team} Win: {int(probs['away']*100)}%")

                # 2. RADAR CHART
                st.markdown("### 📊 Statistical Comparison")
                categories = ['Goals', 'xG', 'Possession', 'SOT']
                
                # Handle cases where possession might be missing or 0
                h_poss = stats['home']['poss_rolling'] if stats['home']['poss_rolling'] > 0 else 50
                a_poss = stats['away']['poss_rolling'] if stats['away']['poss_rolling'] > 0 else 50
                
                # Scale for visibility
                h_vals = [stats['home']['gf_rolling'], stats['home']['xg_rolling'], h_poss/10, stats['home']['sot_rolling']]
                a_vals = [stats['away']['gf_rolling'], stats['away']['xg_rolling'], a_poss/10, stats['away']['sot_rolling']]
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=h_vals, theta=categories, fill='toself', name=home_team, line_color='#ff4b4b'))
                fig.add_trace(go.Scatterpolar(r=a_vals, theta=categories, fill='toself', name=away_team, line_color='#4b4bff'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(max(h_vals), max(a_vals)) + 1])), template="plotly_dark", height=450)
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Connection Error: {e}")