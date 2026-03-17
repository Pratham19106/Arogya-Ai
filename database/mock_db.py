# Mock Database Setup

import sqlite3
import os

DB_PATH = "arogya_ai.db"

def init_db():
    """
    Initializes a basic SQLite schema for demo purposes.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            complaint TEXT NOT NULL,
            priority TEXT NOT NULL,
            wait_time_mins INTEGER,
            score INTEGER,
            status TEXT DEFAULT 'waiting' -- waiting, treated, discharged
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
