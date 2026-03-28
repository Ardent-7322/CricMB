import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(__file__))
from sqlalchemy import create_engine
from data_loader import load_data, clean_data
from team_stats import standardize_team_names

DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5433/cricmb")

def setup_database():
    print("Loading and cleaning data...")
    ipl, players = load_data()
    ipl_clean, players = clean_data(ipl, players)
    ipl_clean = standardize_team_names(ipl_clean)

    print("Connecting to database...")
    engine = create_engine(DB_URL)

    print("Writing ipl_data table...")
    ipl_clean.to_sql('ipl_data', engine, if_exists='replace', index=False, chunksize=1000)
    print(f"Done! {len(ipl_clean)} rows written.")

    print("Writing players table...")
    players.to_sql('players', engine, if_exists='replace', index=False)
    print(f"Done! {len(players)} rows written.")

    print("All tables created successfully!")

if __name__ == '__main__':
    setup_database()

