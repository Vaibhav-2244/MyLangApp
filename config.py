# config.py

import os
import pyodbc

class Config:
    DRIVER = '{ODBC Driver 17 for SQL Server}'
    SERVER = os.getenv('DB_SERVER')           
    DATABASE = os.getenv('DB_DATABASE')        
    USERNAME = os.getenv('DB_USERNAME')       
    PASSWORD = os.getenv('DB_PASSWORD')       

    CONNECTION_STRING = (
        f'DRIVER={DRIVER};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'UID={USERNAME};'
        f'PWD={PASSWORD};'
        f'Encrypt=yes;'
        f'TrustServerCertificate=no;'
        f'Connection Timeout=30;'
    )

def get_connection():
    try:
        return pyodbc.connect(Config.CONNECTION_STRING)
    except Exception as e:
        print("Connection failed:", e)
        return None
