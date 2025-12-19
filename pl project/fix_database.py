import sqlite3
import os

print("🧹 Starting Database Cleanup...")

# 1. Connect to Database
db_path = os.path.join("database", "premier_league.db")
if not os.path.exists(db_path):
    print("❌ Error: Database not found!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2. Define the Cleanup Map (Bad Name -> Good Name)
# This merges split data into one single team
name_map = {
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
    "Leicester": "Leicester City"
}

# 3. Execute Merge
changes = 0
for bad_name, good_name in name_map.items():
    # Find IDs
    cursor.execute("SELECT team_id FROM teams WHERE team_name = ?", (bad_name,))
    bad_row = cursor.fetchone()
    
    cursor.execute("SELECT team_id FROM teams WHERE team_name = ?", (good_name,))
    good_row = cursor.fetchone()

    if bad_row and good_row:
        bad_id = bad_row[0]
        good_id = good_row[0]
        
        print(f"🔗 Merging '{bad_name}' (ID {bad_id}) -> '{good_name}' (ID {good_id})...")
        
        # Move all matches from Bad ID to Good ID
        cursor.execute("UPDATE matches SET home_team_id = ? WHERE home_team_id = ?", (good_id, bad_id))
        cursor.execute("UPDATE matches SET away_team_id = ? WHERE away_team_id = ?", (good_id, bad_id))
        
        # Delete the Bad Team from teams table
        cursor.execute("DELETE FROM teams WHERE team_id = ?", (bad_id,))
        changes += 1

conn.commit()
print(f"✅ Cleanup Complete! Merged {changes} duplicate teams.")

# 4. Verification
print("\n📋 Final Team List in Database:")
cursor.execute("SELECT team_name FROM teams ORDER BY team_name")
teams = [row[0] for row in cursor.fetchall()]
print(teams)
conn.close()