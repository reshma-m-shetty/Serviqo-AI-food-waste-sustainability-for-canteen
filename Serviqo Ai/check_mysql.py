import os
import sys
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST", "localhost")
port = int(os.getenv("DB_PORT", 3306))
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "root123")
database = os.getenv("DB_NAME", "serviqo_ai")

print(f"Connecting to MySQL at {host}:{port} as user '{user}'...")

# Attempt 1: PyMySQL
try:
    import pymysql
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"[SUCCESS via PyMySQL] MySQL Server is connected! Version: {version}")
    
    cursor.execute("SHOW DATABASES")
    dbs = [row[0] for row in cursor.fetchall()]
    print(f"Databases on server: {', '.join(dbs)}")
    print(f"Database '{database}' exists: {'YES' if database in dbs else 'NO'}")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"[PyMySQL attempt error]: {e}")

import importlib

# Attempt 2: mysql.connector with use_pure=True (if installed)
try:
    mysql_connector = importlib.import_module("mysql.connector")
    conn = mysql_connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        use_pure=True
    )
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"[SUCCESS via mysql.connector (pure)] MySQL Server is connected! Version: {version}")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"[mysql.connector use_pure=True error/not installed]: {e}")

# Attempt 3: mysql.connector default (if installed)
try:
    mysql_connector = importlib.import_module("mysql.connector")
    conn = mysql_connector.connect(
        host=host,
        port=port,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"[SUCCESS via mysql.connector] MySQL Server is connected! Version: {version}")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"[mysql.connector default error/not installed]: {e}")
