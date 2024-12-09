import sqlite3
import pandas as pd
from typing import List, Dict
import logging

class DatabaseManager:
    def __init__(self, db_path: str = "businesses.db"):
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self):
        """Create the necessary database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT,
                address TEXT,
                address_type TEXT,
                phone TEXT,
                rating REAL,
                reviews INTEGER,
                website TEXT,
                business_type TEXT,
                latitude REAL,
                longitude REAL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_businesses(self, businesses: List[Dict]):
        """Save business data to the database"""
        conn = sqlite3.connect(self.db_path)
        
        for business in businesses:
            location = business.get('Location', {})
            
            try:
                conn.execute('''
                    INSERT INTO businesses (
                        business_name, address, address_type, phone, rating, 
                        reviews, website, business_type, latitude, longitude, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    business.get('Business Name', ''),
                    business.get('Address', ''),
                    business.get('Address Type', 'Unknown'),
                    business.get('Phone', ''),
                    business.get('Rating', 0.0),
                    business.get('Reviews', 0),
                    business.get('Website', ''),
                    business.get('Business Type', ''),
                    location.get('lat', 0),
                    location.get('lng', 0),
                    business.get('Source', '')
                ))
            except Exception as e:
                logging.error(f"Error saving business: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
    
    def get_businesses(self) -> pd.DataFrame:
        """Retrieve all businesses from the database"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query('''
            SELECT 
                business_name as "Business Name",
                address as "Address",
                address_type as "Address Type",
                phone as "Phone",
                rating as "Rating",
                reviews as "Reviews",
                website as "Website",
                business_type as "Business Type",
                latitude,
                longitude,
                source as "Source"
            FROM businesses
        ''', conn)
        
        # Create Location column
        df['Location'] = df.apply(
            lambda row: {'lat': row['latitude'], 'lng': row['longitude']},
            axis=1
        )
        
        # Drop individual lat/lng columns
        df = df.drop(['latitude', 'longitude'], axis=1)
        
        conn.close()
        return df
