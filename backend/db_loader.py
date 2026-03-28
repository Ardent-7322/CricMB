import pandas as pd
from sqlalchemy import create_engine
import os

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:pass123@localhost:5433/cricmb')

# Fix for Render's postgres:// vs postgresql://
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace('postgres://', 'postgresql://', 1)

def get_engine():
    return create_engine(DB_URL)

def load_from_db():
    engine = get_engine()
    print("Loading IPL data from database...")
    ipl = pd.read_sql('SELECT * FROM ipl_data', engine)
    players = pd.read_sql('SELECT * FROM players', engine)
    print(f"Loaded {len(ipl)} rows from database!")
    return ipl, players