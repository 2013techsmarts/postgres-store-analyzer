-- Create products schema
CREATE SCHEMA IF NOT EXISTS products;

-- 1. Create categories table
CREATE TABLE products.categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

COMMENT ON TABLE products.categories IS 'Product categories like Electronics, Apparel, and Home Goods';
COMMENT ON COLUMN products.categories.category_id IS 'Unique identifier for each product category';
COMMENT ON COLUMN products.categories.name IS 'Unique name of the category';
COMMENT ON COLUMN products.categories.description IS 'Detailed description of the category type';

-- 2. Create items table
CREATE TABLE products.items (
    item_id SERIAL PRIMARY KEY,
    category_id INT REFERENCES products.categories(category_id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE products.items IS 'Available products or items in the store inventory';
COMMENT ON COLUMN products.items.item_id IS 'Unique identifier for the item';
COMMENT ON COLUMN products.items.category_id IS 'Foreign key referencing the product category';
COMMENT ON COLUMN products.items.name IS 'Name of the item/product';
COMMENT ON COLUMN products.items.description IS 'Details and specifications of the item';
COMMENT ON COLUMN products.items.price IS 'Unit price of the item in USD';
COMMENT ON COLUMN products.items.stock_quantity IS 'Current quantity available in the warehouse';
COMMENT ON COLUMN products.items.created_at IS 'Timestamp when the item was added to inventory';

-- 3. Create customers table
CREATE TABLE products.customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE products.customers IS 'Registered store customers';
COMMENT ON COLUMN products.customers.customer_id IS 'Unique identifier for the customer';
COMMENT ON COLUMN products.customers.first_name IS 'First name of the customer';
COMMENT ON COLUMN products.customers.last_name IS 'Last name of the customer';
COMMENT ON COLUMN products.customers.email IS 'Primary email contact of the customer (unique)';
COMMENT ON COLUMN products.customers.city IS 'City of the customer''s shipping address';
COMMENT ON COLUMN products.customers.state IS 'State of the customer''s shipping address';
COMMENT ON COLUMN products.customers.created_at IS 'Timestamp when the customer account was registered';

-- 4. Create orders table
CREATE TABLE products.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES products.customers(customer_id) ON DELETE CASCADE,
    order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled')),
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0)
);

COMMENT ON TABLE products.orders IS 'Customer order transaction logs';
COMMENT ON COLUMN products.orders.order_id IS 'Unique identifier for the order transaction';
COMMENT ON COLUMN products.orders.customer_id IS 'Foreign key referencing the customer who placed the order';
COMMENT ON COLUMN products.orders.order_date IS 'Timestamp when the order was placed';
COMMENT ON COLUMN products.orders.status IS 'Current status of the order order lifecycle';
COMMENT ON COLUMN products.orders.total_amount IS 'Total cost of the order including all item lines';

-- 5. Create order_items table
CREATE TABLE products.order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES products.orders(order_id) ON DELETE CASCADE,
    item_id INT REFERENCES products.items(item_id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0)
);

COMMENT ON TABLE products.order_items IS 'Line items detail for each order transaction';
COMMENT ON COLUMN products.order_items.order_item_id IS 'Unique identifier for the line item';
COMMENT ON COLUMN products.order_items.order_id IS 'Foreign key referencing the parent order';
COMMENT ON COLUMN products.order_items.item_id IS 'Foreign key referencing the product item purchased';
COMMENT ON COLUMN products.order_items.quantity IS 'Number of units of the item purchased';
COMMENT ON COLUMN products.order_items.unit_price IS 'Selling unit price of the item at the time of order';


-- ==========================================
-- SEED DATA
-- ==========================================

-- Insert Categories
INSERT INTO products.categories (name, description) VALUES
('Electronics', 'Gadgets, devices, computers, and accessories'),
('Apparel', 'Clothing, footwear, and fashion accessories'),
('Home & Kitchen', 'Furniture, appliances, cookware, and home decor'),
('Books', 'Physical and electronic books across genres'),
('Fitness', 'Sporting goods, workout equipment, and activewear');

-- Insert Items
INSERT INTO products.items (category_id, name, description, price, stock_quantity) VALUES
(1, 'Wireless Noise-Canceling Headphones', 'Over-ear headphones with 30-hour battery life', 199.99, 50),
(1, 'Mechanical Keyboard', 'RGB backlit keyboard with tactile switches', 89.99, 120),
(1, 'UltraWide Monitor 34-inch', 'Curved IPS monitor with 144Hz refresh rate', 349.99, 25),
(2, 'Classic Denim Jacket', 'Unisex blue denim jacket with fleece lining', 59.99, 75),
(2, 'Running Shoes', 'Lightweight breathable sneakers for training', 79.99, 60),
(3, 'Stainless Steel Air Fryer', '5.8-quart digital air fryer with 8 presets', 119.99, 40),
(3, 'Memory Foam Pillow', 'Ergonomic neck support pillow for sleeping', 29.99, 150),
(4, 'Designing Data-Intensive Applications', 'O''Reilly book by Martin Kleppmann', 45.00, 200),
(4, 'The Hobbit', 'Classic fantasy novel by J.R.R. Tolkien', 14.99, 300),
(5, 'Adjustable Dumbbell Set', 'Set of 2 dumbbells adjustable up to 52.5 lbs each', 249.99, 15);

-- Insert Customers
INSERT INTO products.customers (first_name, last_name, email, city, state) VALUES
('Alice', 'Smith', 'alice.smith@example.com', 'New York', 'NY'),
('Bob', 'Johnson', 'bob.johnson@example.com', 'San Francisco', 'CA'),
('Charlie', 'Brown', 'charlie.brown@example.com', 'Austin', 'TX'),
('Diana', 'Prince', 'diana.prince@example.com', 'Seattle', 'WA'),
('Ethan', 'Hunt', 'ethan.hunt@example.com', 'Los Angeles', 'CA'),
('Fiona', 'Gallagher', 'fiona.g@example.com', 'Chicago', 'IL'),
('George', 'Costanza', 'george.c@example.com', 'New York', 'NY');

-- Insert Orders (with various dates, statuses, and total amounts)
INSERT INTO products.orders (customer_id, order_date, status, total_amount) VALUES
(1, '2026-07-01 10:30:00+00', 'Delivered', 289.98),
(2, '2026-07-02 14:45:00+00', 'Delivered', 439.98),
(3, '2026-07-05 09:15:00+00', 'Shipped', 134.99),
(4, '2026-07-10 16:20:00+00', 'Delivered', 249.99),
(5, '2026-07-12 11:00:00+00', 'Pending', 59.99),
(1, '2026-07-15 13:00:00+00', 'Pending', 89.99),
(6, '2026-07-16 08:30:00+00', 'Cancelled', 119.99),
(7, '2026-07-17 15:45:00+00', 'Pending', 34.98);

-- Insert Order Items
INSERT INTO products.order_items (order_id, item_id, quantity, unit_price) VALUES
-- Order 1 (Alice): Headphones (1) + Mechanical Keyboard (1) = 199.99 + 89.99 = 289.98
(1, 1, 1, 199.99),
(1, 2, 1, 89.99),
-- Order 2 (Bob): Mechanical Keyboard (1) + UltraWide Monitor (1) = 89.99 + 349.99 = 439.98
(2, 2, 1, 89.99),
(2, 3, 1, 349.99),
-- Order 3 (Charlie): Running Shoes (1) + Denim Jacket (0.91-ish, wait, jacket is 59.99, running shoes 79.99 = 139.98, wait, let's keep unit price exact)
-- Running shoes (1 @ 79.99) + Denim Jacket (1 @ 55.00 discounted) = 134.99 total
(3, 5, 1, 79.99),
(3, 4, 1, 55.00),
-- Order 4 (Diana): Dumbbells (1) = 249.99
(4, 10, 1, 249.99),
-- Order 5 (Ethan): Denim Jacket (1) = 59.99
(5, 4, 1, 59.99),
-- Order 6 (Alice): Mechanical Keyboard (1) = 89.99
(6, 2, 1, 89.99),
-- Order 7 (Fiona): Air Fryer (1) = 119.99
(7, 6, 1, 119.99),
-- Order 8 (George): Hobbit Book (1 @ 14.99) + Memory Foam Pillow (1 @ 19.99 discounted) = 34.98
(8, 9, 1, 14.99),
(8, 7, 1, 19.99);
