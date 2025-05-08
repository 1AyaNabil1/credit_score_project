-- ================================
-- USERS DATABASE
-- ================================
CREATE DATABASE IF NOT EXISTS users_db;
USE users_db;

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    national_id VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- PAYMENTS DATABASE
-- ================================
CREATE DATABASE IF NOT EXISTS payments_db;
USE payments_db;

CREATE TABLE IF NOT EXISTS payment_records (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    on_time_payments INT DEFAULT 0,
    total_payments INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users_db.users(user_id)
);

-- ================================
-- DEBT DATABASE
-- ================================
CREATE DATABASE IF NOT EXISTS debt_db;
USE debt_db;

CREATE TABLE IF NOT EXISTS credit_usage (
    usage_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    used_credit DECIMAL(10,2),
    credit_limit DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users_db.users(user_id)
);

-- ================================
-- HISTORY DATABASE
-- ================================
CREATE DATABASE IF NOT EXISTS history_db;
USE history_db;

CREATE TABLE IF NOT EXISTS credit_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_open_date DATE,
    FOREIGN KEY (user_id) REFERENCES users_db.users(user_id)
);

-- ================================
-- MIX REFERENCE DATABASE
-- ================================
CREATE DATABASE IF NOT EXISTS mix_reference_db;
USE mix_reference_db;

CREATE TABLE IF NOT EXISTS credit_mix (
    mix_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    credit_types_used INT,
    total_credit_types INT,
    FOREIGN KEY (user_id) REFERENCES users_db.users(user_id)
);
-- ================================