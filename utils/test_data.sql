-- ================================
-- USERS DATABASE
-- ================================
USE users_db;

INSERT INTO users (user_id, full_name, national_id) VALUES
(1, 'Aya Nabil', 'EGY1234567890'),
(2, 'Ahlam Mohammed', 'EGY9876543210'),
(3, 'Retag Ayman', 'EGY1122334455'),
(4, 'Elham Hamed', 'EGY5566778899'),
(5, 'Aya Ahmed',   'EGY6677889900'),
(6, 'Nada Youssef',   'EGY7788990011');

-- ================================
-- PAYMENTS DATABASE
-- ================================
USE payments_db;

INSERT INTO payment_records (user_id, on_time_payments, total_payments) VALUES
(1, 18, 20),
(2, 9, 12),
(3, 20, 20),
(4, 15, 20),
(5, 20, 20),
(6, 18, 20);  -- Aya Nabil again

-- ================================
-- DEBT DATABASE
-- ================================
USE debt_db;

INSERT INTO credit_usage (user_id, used_credit, credit_limit) VALUES
(1, 3000.00, 10000.00),
(2, 7000.00, 10000.00),
(3, 1000.00, 5000.00),
(4, 4000.00, 10000.00),
(5, 1500.00, 5000.00),
(6, 3000.00, 10000.00);  -- repeat for Aya Nabil

-- ================================
-- HISTORY DATABASE
-- ================================
USE history_db;

INSERT INTO credit_history (user_id, account_open_date) VALUES
(1, '2018-05-01'),
(2, '2021-01-01'),
(3, '2020-09-15'),
(4, '2017-02-10'),
(5, '2019-09-20'),
(6, '2018-05-01');  -- Aya Nabil

-- ================================
-- MIX REFERENCE DATABASE
-- ================================
USE mix_reference_db;

INSERT INTO credit_mix (user_id, credit_types_used, total_credit_types) VALUES
(1, 2, 4),
(2, 1, 4),
(3, 3, 4),
(4, 2, 4),
(5, 3, 4),
(6, 2, 4);  -- Aya Nabil
