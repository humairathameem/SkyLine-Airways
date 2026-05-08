-- ============================================================
--  Flight Management and Booking System — MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS flight_db;
USE flight_db;

-- ─── TABLES ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS Users (
    user_id   INT AUTO_INCREMENT PRIMARY KEY,
    username  VARCHAR(100) NOT NULL UNIQUE,
    password  VARCHAR(255) NOT NULL,
    role      ENUM('admin','user') NOT NULL DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS Airports (
    airport_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    city        VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Aircraft (
    aircraft_id  INT AUTO_INCREMENT PRIMARY KEY,
    model        VARCHAR(100) NOT NULL,
    capacity     INT NOT NULL
);

CREATE TABLE IF NOT EXISTS Flights (
    flight_id              INT AUTO_INCREMENT PRIMARY KEY,
    source_airport_id      INT NOT NULL,
    destination_airport_id INT NOT NULL,
    departure_time         DATETIME NOT NULL,
    arrival_time           DATETIME NOT NULL,
    aircraft_id            INT NOT NULL,
    price                  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (source_airport_id)      REFERENCES Airports(airport_id) ON DELETE CASCADE,
    FOREIGN KEY (destination_airport_id) REFERENCES Airports(airport_id) ON DELETE CASCADE,
    FOREIGN KEY (aircraft_id)            REFERENCES Aircraft(aircraft_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Bookings (
    booking_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    flight_id   INT NOT NULL,
    seats       INT NOT NULL,
    FOREIGN KEY (user_id)   REFERENCES Users(user_id)   ON DELETE CASCADE,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Payments (
    payment_id  INT AUTO_INCREMENT PRIMARY KEY,
    booking_id  INT NOT NULL UNIQUE,
    amount      DECIMAL(10,2) NOT NULL,
    status      ENUM('Pending','Paid') NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id) ON DELETE CASCADE
);

-- ─── USERS ──────────────────────────────────────────────────

INSERT INTO Users (username, password, role) VALUES
('admin', 'admin123', 'admin'),
('john_doe', 'user123', 'user');

-- ─── AIRPORTS (20 real-world) ────────────────────────────────

INSERT INTO Airports (name, city) VALUES
('Indira Gandhi International Airport',    'New Delhi'),
('Chhatrapati Shivaji Maharaj International Airport', 'Mumbai'),
('Kempegowda International Airport',       'Bangalore'),
('Chennai International Airport',          'Chennai'),
('Netaji Subhas Chandra Bose International Airport', 'Kolkata'),
('Rajiv Gandhi International Airport',     'Hyderabad'),
('Cochin International Airport',           'Kochi'),
('Sardar Vallabhbhai Patel International Airport', 'Ahmedabad'),
('Pune Airport',                           'Pune'),
('Jaipur International Airport',           'Jaipur'),
('Hamad International Airport',            'Doha'),
('Dubai International Airport',            'Dubai'),
('Heathrow Airport',                       'London'),
('John F. Kennedy International Airport',  'New York'),
('Los Angeles International Airport',      'Los Angeles'),
('Singapore Changi Airport',               'Singapore'),
('Hong Kong International Airport',        'Hong Kong'),
('Charles de Gaulle Airport',              'Paris'),
('Frankfurt Airport',                      'Frankfurt'),
('Sydney Kingsford Smith Airport',         'Sydney'),
('Toronto Pearson International Airport',  'Toronto'),
('O Hare International Airport',           'Chicago');

-- ─── AIRCRAFT ────────────────────────────────────────────────

INSERT INTO Aircraft (model, capacity) VALUES
('Boeing 737-800',   189),
('Boeing 777-300ER', 396),
('Airbus A320',      180),
('Airbus A380',      555),
('Boeing 787-9',     296),
('Airbus A321neo',   220);

-- ─── FLIGHTS ─────────────────────────────────────────────────

INSERT INTO Flights (source_airport_id, destination_airport_id, departure_time, arrival_time, aircraft_id, price) VALUES
(1, 2,  '2026-06-01 06:00:00', '2026-06-01 08:15:00', 3, 4500.00),
(2, 3,  '2026-06-01 09:00:00', '2026-06-01 10:45:00', 1, 3800.00),
(3, 4,  '2026-06-01 11:00:00', '2026-06-01 13:00:00', 3, 4200.00),
(4, 5,  '2026-06-01 14:00:00', '2026-06-01 17:30:00', 1, 5500.00),
(1, 6,  '2026-06-01 07:30:00', '2026-06-01 09:30:00', 6, 4100.00),
(6, 7,  '2026-06-01 10:00:00', '2026-06-01 11:30:00', 3, 3200.00),
(7, 8,  '2026-06-02 06:00:00', '2026-06-02 08:30:00', 1, 4800.00),
(8, 1,  '2026-06-02 09:00:00', '2026-06-02 11:15:00', 6, 3900.00),
(1, 11, '2026-06-02 22:00:00', '2026-06-03 01:30:00', 5, 28000.00),
(11,13, '2026-06-03 03:00:00', '2026-06-03 08:00:00', 2, 45000.00),
(11,12, '2026-06-03 10:00:00', '2026-06-03 10:45:00', 3, 8500.00),
(12,14, '2026-06-04 01:00:00', '2026-06-04 09:30:00', 4, 62000.00),
(14,15, '2026-06-04 11:00:00', '2026-06-04 14:00:00', 1, 22000.00),
(16,11, '2026-06-05 23:30:00', '2026-06-06 05:00:00', 5, 35000.00),
(13,18, '2026-06-05 08:00:00', '2026-06-05 10:00:00', 2, 18000.00),
(18,19, '2026-06-05 12:00:00', '2026-06-05 13:15:00', 3, 9500.00),
(2, 11, '2026-06-06 21:00:00', '2026-06-07 00:30:00', 5, 27000.00),
(1, 16, '2026-06-07 01:00:00', '2026-06-07 08:30:00', 2, 32000.00),
(9, 1,  '2026-06-07 05:00:00', '2026-06-07 06:45:00', 3, 3500.00),
(10,1,  '2026-06-07 07:00:00', '2026-06-07 08:30:00', 1, 3600.00),
(5, 1,  '2026-06-08 06:00:00', '2026-06-08 09:00:00', 6, 5200.00),
(20,16, '2026-06-08 10:00:00', '2026-06-08 17:30:00', 4, 55000.00),
(21,14, '2026-06-09 08:00:00', '2026-06-09 11:30:00', 1, 19000.00),
(22,14, '2026-06-09 06:00:00', '2026-06-09 09:45:00', 6, 18500.00);
