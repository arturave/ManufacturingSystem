-- MySQL Schema for Manufacturing System
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

-- Order parts
CREATE TABLE order_parts (
    id CHAR(36) PRIMARY KEY,
    order_id CHAR(36),
    product_id CHAR(36),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products_catalog(id),

    INDEX idx_order_parts_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Quotes table
CREATE TABLE quotes (
    id CHAR(36) PRIMARY KEY,
    quote_number VARCHAR(50) UNIQUE,
    customer_id CHAR(36),
    status VARCHAR(50),
    total_value DECIMAL(10,2),
    valid_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id),

    INDEX idx_quotes_customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Quote parts
CREATE TABLE quote_parts (
    id CHAR(36) PRIMARY KEY,
    quote_id CHAR(36),
    product_id CHAR(36),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),

    FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products_catalog(id),

    INDEX idx_quote_parts_quote (quote_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Views
CREATE VIEW v_orders_full AS
SELECT
    o.*,
    c.name as customer_name,
    c.short_name as customer_short,
    COUNT(op.id) as parts_count,
    SUM(op.total_price) as calculated_total
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id
LEFT JOIN order_parts op ON o.id = op.order_id
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
