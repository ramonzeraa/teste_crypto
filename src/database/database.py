import sqlite3
from datetime import datetime
import json
import pandas as pd

class Database:
    def __init__(self):
        self.db_path = 'trading_bot.db'
        self._create_tables()
    
    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY,
                    parameters TEXT,
                    score REAL,
                    timestamp DATETIME,
                    market_data TEXT,
                    signals TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS model_state (
                    id INTEGER PRIMARY KEY,
                    state BLOB,
                    timestamp DATETIME
                )
            ''')
            
    def save_performance(self, params, score, market_data, signals):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO performance_history (parameters, score, timestamp, market_data, signals) VALUES (?, ?, ?, ?, ?)',
                (json.dumps(params), score, datetime.now(), json.dumps(market_data), json.dumps(signals))
            )
            
    def get_historical_performance(self):
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('SELECT * FROM performance_history', conn)
            df['parameters'] = df['parameters'].apply(json.loads)
            df['market_data'] = df['market_data'].apply(json.loads)
            df['signals'] = df['signals'].apply(json.loads)
            return df
