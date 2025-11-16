#!/usr/bin/env python3
"""
Database Backup and Migration Tool
For Supabase -> MySQL migration
"""

import os
import json
import csv
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
import argparse

load_dotenv()

class DatabaseBackupMigrate:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def backup_all_tables(self):
        """Backup all tables from Supabase"""
        print("="*60)
        print("SUPABASE DATABASE BACKUP")
        print("="*60)

        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        print(f"\nBackup directory: {self.backup_dir}")

        # List of tables to backup (correct names from Supabase)
        tables = [
            'customers',
            'materials_dict',
            'products_catalog',
            'orders',
            'order_items',      # Not 'order_parts'
            'quotations',       # Not 'quotes'
            'quotation_items'   # Not 'quote_parts'
        ]

        backup_summary = {}

        for table in tables:
            print(f"\nBacking up {table}...")
            try:
                # Fetch all data
                response = self.client.table(table).select("*").execute()
                data = response.data

                # Save as JSON
                json_file = os.path.join(self.backup_dir, f"{table}.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)

                # Save as CSV (for easier MySQL import)
                if data:
                    csv_file = os.path.join(self.backup_dir, f"{table}.csv")
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)

                backup_summary[table] = len(data)
                print(f"  [OK] Backed up {len(data)} records")

            except Exception as e:
                print(f"  [ERROR] {e}")
                backup_summary[table] = f"Error: {e}"

        # Save backup summary
        summary_file = os.path.join(self.backup_dir, "backup_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Backup Date: {datetime.now()}\n")
            f.write(f"Source: {self.supabase_url}\n\n")
            f.write("Tables backed up:\n")
            for table, count in backup_summary.items():
                f.write(f"  {table}: {count} records\n")

        print("\n" + "="*60)
        print(f"BACKUP COMPLETE - Check {self.backup_dir}/")
        print("="*60)

    def generate_mysql_schema(self):
        """Generate MySQL schema from Supabase structure"""
        schema_file = os.path.join(self.backup_dir, "mysql_schema.sql")

        mysql_schema = """-- MySQL Schema for Manufacturing System
-- Generated from Supabase structure

CREATE DATABASE IF NOT EXISTS manufacturing_system;
USE manufacturing_system;

-- Customers table
CREATE TABLE customers (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(100),
    nip VARCHAR(20),
    address TEXT,
    email VARCHAR(255),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customers_active (is_active),
    INDEX idx_customers_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Materials dictionary
CREATE TABLE materials_dict (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    thickness_mm DECIMAL(10,2),
    price_per_kg DECIMAL(10,2),
    density_kg_m3 DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_materials_active (is_active),
    INDEX idx_materials_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Products catalog (optimized)
CREATE TABLE products_catalog (
    id CHAR(36) PRIMARY KEY,
    idx_code VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    material_id CHAR(36),
    thickness_mm DECIMAL(10,2),
    customer_id CHAR(36),
    material_laser_cost DECIMAL(10,2),
    bending_cost DECIMAL(10,2),
    additional_costs DECIMAL(10,2),
    description TEXT,
    notes TEXT,
    category VARCHAR(100),

    -- Binary storage (using MEDIUMBLOB for larger files)
    cad_2d_binary MEDIUMBLOB,
    cad_2d_filename VARCHAR(255),
    cad_2d_filesize INT,

    cad_3d_binary MEDIUMBLOB,
    cad_3d_filename VARCHAR(255),
    cad_3d_filesize INT,

    user_image_binary MEDIUMBLOB,
    user_image_filename VARCHAR(255),

    thumbnail_100 BLOB,
    preview_800 MEDIUMBLOB,
    preview_4k MEDIUMBLOB,

    primary_graphic_source ENUM('2D', '3D', 'USER'),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (material_id) REFERENCES materials_dict(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),

    INDEX idx_products_active (is_active),
    INDEX idx_products_customer (customer_id),
    INDEX idx_products_material (material_id),
    INDEX idx_products_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Orders table
CREATE TABLE orders (
    id CHAR(36) PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE,
    customer_id CHAR(36),
    status ENUM('NEW', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') DEFAULT 'NEW',
    total_value DECIMAL(10,2),
    delivery_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id),

    INDEX idx_orders_status (status),
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Order items (not order_parts)
CREATE TABLE order_items (
    id CHAR(36) PRIMARY KEY,
    order_id CHAR(36),
    product_id CHAR(36),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products_catalog(id),

    INDEX idx_order_items_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Quotations table (not quotes)
CREATE TABLE quotations (
    id CHAR(36) PRIMARY KEY,
    quote_number VARCHAR(50) UNIQUE,
    customer_id CHAR(36),
    status VARCHAR(50),
    total_value DECIMAL(10,2),
    valid_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id),

    INDEX idx_quotations_customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Quotation items (not quote_parts)
CREATE TABLE quotation_items (
    id CHAR(36) PRIMARY KEY,
    quotation_id CHAR(36),
    product_id CHAR(36),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),

    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products_catalog(id),

    INDEX idx_quotation_items_quotation (quotation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Views
CREATE VIEW v_orders_full AS
SELECT
    o.*,
    c.name as customer_name,
    c.short_name as customer_short,
    COUNT(oi.id) as parts_count,
    SUM(oi.total_price) as calculated_total
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id;

CREATE VIEW v_orders_status_counts AS
SELECT
    status,
    COUNT(*) as count
FROM orders
WHERE is_active = TRUE
GROUP BY status;

-- Stored Procedures
DELIMITER //

CREATE PROCEDURE backup_database()
BEGIN
    -- This would contain backup logic
    SELECT 'Backup procedure placeholder' as message;
END//

CREATE PROCEDURE cleanup_old_data(IN days_to_keep INT)
BEGIN
    -- Delete old inactive records
    DELETE FROM products_catalog
    WHERE is_active = FALSE
    AND updated_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
END//

DELIMITER ;

-- Users and permissions (adjust as needed)
-- CREATE USER 'mfg_app'@'%' IDENTIFIED BY 'secure_password';
-- GRANT ALL PRIVILEGES ON manufacturing_system.* TO 'mfg_app'@'%';
-- FLUSH PRIVILEGES;
"""

        with open(schema_file, 'w') as f:
            f.write(mysql_schema)

        print(f"\nMySQL schema saved to: {schema_file}")

    def generate_migration_script(self):
        """Generate Python script for data migration"""
        migration_file = os.path.join(self.backup_dir, "migrate_to_mysql.py")

        migration_script = '''#!/usr/bin/env python3
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
        'order_items',
        'quotations',
        'quotation_items'
    ]

    for table in tables:
        json_file = f"{table}.json"
        print(f"Migrating {table}...")
        try:
            migrate_table(table, json_file)
        except Exception as e:
            print(f"Error migrating {table}: {e}")
'''

        with open(migration_file, 'w') as f:
            f.write(migration_script)

        print(f"Migration script saved to: {migration_file}")

    def analyze_database_size(self):
        """Analyze current database size and usage"""
        print("\n" + "="*60)
        print("DATABASE SIZE ANALYSIS")
        print("="*60)

        tables = [
            'products_catalog',
            'customers',
            'materials_dict',
            'orders',
            'order_items',
            'quotations',
            'quotation_items'
        ]

        total_size = 0
        for table in tables:
            try:
                response = self.client.table(table).select("id").execute()
                count = len(response.data)

                # Estimate size (rough)
                if table == 'products_catalog':
                    # Check for binary data
                    sample = self.client.table(table).select("*").limit(1).execute()
                    if sample.data:
                        # Estimate based on sample
                        sample_size = len(json.dumps(sample.data[0], default=str))
                        estimated_size = sample_size * count
                        total_size += estimated_size
                        print(f"{table}: {count} records, ~{estimated_size/1024/1024:.2f} MB")
                else:
                    estimated_size = count * 1024  # 1KB per record average
                    total_size += estimated_size
                    print(f"{table}: {count} records, ~{estimated_size/1024:.2f} KB")

            except Exception as e:
                print(f"{table}: Error - {e}")

        print(f"\nTotal estimated size: {total_size/1024/1024:.2f} MB")
        print(f"Supabase free tier limit: 500 MB")
        print(f"Usage: {(total_size/1024/1024/500)*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description='Database Backup and Migration Tool')
    parser.add_argument('--backup', action='store_true', help='Backup all tables')
    parser.add_argument('--schema', action='store_true', help='Generate MySQL schema')
    parser.add_argument('--analyze', action='store_true', help='Analyze database size')
    parser.add_argument('--all', action='store_true', help='Run all operations')

    args = parser.parse_args()

    tool = DatabaseBackupMigrate()

    if args.all or args.backup:
        tool.backup_all_tables()

    if args.all or args.schema:
        tool.generate_mysql_schema()
        tool.generate_migration_script()

    if args.all or args.analyze:
        tool.analyze_database_size()

    if not any([args.backup, args.schema, args.analyze, args.all]):
        print("Usage: python database_backup_migrate.py [--backup] [--schema] [--analyze] [--all]")


if __name__ == "__main__":
    main()