

CREATE DATABASE IF NOT EXISTS vms_db;
USE vms_db;


CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, 
    email VARCHAR(150) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role)
);


CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department_id INT NOT NULL,
    employee_code VARCHAR(50) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT,
    INDEX idx_employee_code (employee_code)
);


CREATE TABLE IF NOT EXISTS visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    email VARCHAR(150) NOT NULL,
    gender VARCHAR(20),
    company_name VARCHAR(150),
    address TEXT,
    id_type VARCHAR(50), 
    id_proof_path VARCHAR(255), 
    photo_path VARCHAR(255), 
    vehicle_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_mobile (mobile_number)
);


CREATE TABLE IF NOT EXISTS visitor_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id INT NOT NULL,
    employee_id INT NOT NULL, 
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    purpose_of_visit VARCHAR(255) NOT NULL,
    visitor_type VARCHAR(100) NOT NULL, 
    status VARCHAR(50) DEFAULT 'pending', 
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (visitor_id) REFERENCES visitors(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_visit_date (visit_date)
);


CREATE TABLE IF NOT EXISTS visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id INT NOT NULL,
    request_id INT, 
    employee_id INT NOT NULL, 
    check_in_time TIMESTAMP NULL,
    check_out_time TIMESTAMP NULL,
    badge_number VARCHAR(100) UNIQUE,
    qr_code_path VARCHAR(255),
    status VARCHAR(50) DEFAULT 'checked_in', 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (visitor_id) REFERENCES visitors(id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES visitor_requests(id) ON DELETE SET NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    INDEX idx_visit_status (status),
    INDEX idx_check_in (check_in_time)
);


CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT, 
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
