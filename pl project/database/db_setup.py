import pandas as pd
import sqlite3
import os

# --- Configuration ---
# Your absolute path to the data
csv_path = r'C:\Users\sujal\Downloads\pl project\data\premier_league_matches_2022-2025.csv'
db_path = 'premier_league.db' # This creates it inside the database folder

def setup_normalized_db():
    if not os.path.exists(csv_path):
        print(f"Error: CSV not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)

    # 1. Data Cleaning (Requirement #1 & Task 4)
    # Drop empty/useless columns identified during EDA
    df_clean = df.drop(columns=['notes', 'match report'], errors='ignore')

    # 2. Normalization (3NF - Task 1)
    # Create Table: Teams
    all_teams = sorted(pd.concat([df_clean['team'], df_clean['opponent']]).unique())
    teams_df = pd.DataFrame({'team_id': range(1, len(all_teams) + 1), 'team_name': all_teams})
    
    # Create Table: Referees
    all_refs = sorted(df_clean['referee'].dropna().unique())
    referees_df = pd.DataFrame({'referee_id': range(1, len(all_refs) + 1), 'referee_name': all_refs})
    
    # Map text names to IDs for the final Matches table
    df_norm = df_clean.merge(teams_df, left_on='team', right_on='team_name').rename(columns={'team_id': 'home_team_id'})
    df_norm = df_norm.merge(teams_df, left_on='opponent', right_on='team_name').rename(columns={'team_id': 'away_team_id'})
    df_norm = df_norm.merge(referees_df, left_on='referee', right_on='referee_name', how='left').rename(columns={'referee_id': 'ref_id'})
    
    # Drop original text columns to strictly adhere to 3NF
    matches_table = df_norm.drop(columns=['team', 'opponent', 'referee', 'team_name_x', 'team_name_y', 'referee_name'])
    
    # 3. Save to SQLite
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    teams_df.to_sql('teams', conn, index=False, if_exists='replace')
    referees_df.to_sql('referees', conn, index=False, if_exists='replace')
    matches_table.to_sql('matches', conn, index=False, if_exists='replace')
    
    # 4. Verification: SQL JOIN statement (Task 2 Requirement)
    check = pd.read_sql("""
        SELECT m.date, t1.team_name as Home, t2.team_name as Away, m.result
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        LIMIT 5
    """, conn)
    conn.close()
    
    print("✅ Database created and 3NF Normalization complete.")
    print(check)

if __name__ == "__main__":
    setup_normalized_db()