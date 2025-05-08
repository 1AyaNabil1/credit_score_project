-- ================================
-- Insert into users_db
-- ================================
USE users_db;
INSERT INTO users (user_id, full_name, national_id) VALUES
(1, 'Aya Nabil', 'EGY1234567890'),
(2, 'Mohamed Raslan', 'EGY9876543210'),
(3, 'Habiba Mohamed', 'EGY1122334455');

-- ================================
-- Insert into payments_db
-- ================================
USE payments_db;
INSERT INTO payment_records (user_id, on_time_payments, total_payments) VALUES
(1, 18, 20),
(2, 9, 12),
(3, 20, 20);

-- ================================
-- Insert into debt_db
-- ================================
USE debt_db;
INSERT INTO credit_usage (user_id, used_credit, credit_limit) VALUES
(1, 3000.00, 10000.00),
(2, 7000.00, 10000.00),
(3, 1000.00, 5000.00);

-- ================================
-- Insert into history_db
-- ================================
USE history_db;
INSERT INTO credit_history (user_id, account_open_date) VALUES
(1, '2018-05-01'),
(2, '2021-01-01'),
(3, '2020-09-15');

-- ================================
-- Insert into mix_reference_db
-- ================================
USE mix_reference_db;
INSERT INTO credit_mix (user_id, credit_types_used, total_credit_types) VALUES
(1, 2, 4),
(2, 1, 4),
(3, 3, 4);
