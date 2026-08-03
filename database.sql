CREATE DATABASE carpool;

USE carpool;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fname VARCHAR(100),
    lname VARCHAR(100),
    mobile VARCHAR(20),
    dob DATE,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    role ENUM('user','admin') DEFAULT 'user'
);

CREATE TABLE rides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    driver_id INT NOT NULL,
    from_location VARCHAR(50) NOT NULL,
    to_location VARCHAR(50) NOT NULL,
    pickup_point VARCHAR(100) NOT NULL,
    drop_point VARCHAR(100) NOT NULL,
    ride_date DATE NOT NULL,
    ride_time TIME NOT NULL,
    seats INT NOT NULL,
    car_number VARCHAR(20) NOT NULL,
    car_model VARCHAR(50) NOT NULL,
    fare DECIMAL(10,2) NOT NULL DEFAULT 0,
    driver_phone VARCHAR(20) NOT NULL,
    status ENUM('active','cancelled') DEFAULT 'active',
    FOREIGN KEY (driver_id) REFERENCES users(id)
);

CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ride_id INT NOT NULL,
    user_id INT NOT NULL,
    seats_booked INT NOT NULL,
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending','confirmed','rejected') DEFAULT 'pending',
    total_amount DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (ride_id) REFERENCES rides(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
