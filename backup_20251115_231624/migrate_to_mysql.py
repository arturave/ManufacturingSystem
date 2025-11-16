#!/usr/bin/env python3
"""
Migration script from JSON backup to MySQL
"""

import json
import mysql.connector
from datetime import datetime
import base64

# MySQL connection config
MYSQL_CONFIG = {
    'host': 'your_host.seohost.pl',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'manufacturing_system'
}

def migrate_table(table_name, json_file):
    """Migrate single table from JSON to MySQL"""

    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print(f"No data in {table_name}")
        return

    # Connect to MySQL
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # Prepare insert statement
    columns = list(data[0].keys())
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

    # Insert data
    for row in data:
        # Handle binary data (decode from base64 if needed)
        values = []
        for col in columns:
            val = row.get(col)
            if col.endswith('_binary') and val and isinstance(val, str):
                # Decode base64 to bytes
                val = base64.b64decode(val)
            values.append(val)

        cursor.execute(insert_sql, values)

    conn.commit()
    print(f"Migrated {len(data)} records to {table_name}")

    cursor.close()
    conn.close()

# Main migration
if __name__ == "__main__":
    tables = [
        'customers',
        'materials_dict',
        'products_catalog',
        'orders',
        'order_parts',
        'quotes',
        'quote_parts'
    ]

    for table in tables:
        json_file = f"{table}.json"
        print(f"Migrating {table}...")
        try:
            migrate_table(table, json_file)
        except Exception as e:
            print(f"Error migrating {table}: {e}")
