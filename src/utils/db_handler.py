import sqlite3
import os
from typing import List

class DatabaseHandler:
    def __init__(self):
        # create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # set database path
        self.db_path = os.path.join(data_dir, 'listings.db')
        self._initialize_db()
    
    def _initialize_db(self):
        """create database and tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    item_code TEXT PRIMARY KEY,
                    description TEXT,
                    price REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def get_existing_listings(self) -> List[str]:
        """get list of existing item codes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_code FROM listings")
            return [row[0] for row in cursor.fetchall()]
    
    def add_listing(self, item_code: str, description: str):
        """add new listing to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO listings (item_code, description) VALUES (?, ?)",
                (item_code, description)
            )
            conn.commit()
    
    def get_connection(self):
        """get database connection"""
        return sqlite3.connect(self.db_path)