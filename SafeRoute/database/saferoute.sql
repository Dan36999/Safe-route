-- ============================================================
--  SafeRoute — Community Safety Route Planner
--  CPU4106 Level 4 Computing Group Project
--  MySQL schema and sample data
--
--  Import with:  mysql -u root -p < database/saferoute.sql
-- ============================================================

DROP DATABASE IF EXISTS saferoute;
CREATE DATABASE saferoute CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE saferoute;

-- ------------------------------------------------------------
-- USERS
-- ------------------------------------------------------------
CREATE TABLE users (
    UserID       INT AUTO_INCREMENT PRIMARY KEY,
    FullName     VARCHAR(100)  NOT NULL,
    Email        VARCHAR(150)  NOT NULL UNIQUE,
    PasswordHash VARCHAR(255)  NOT NULL,
    DateCreated  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- REPORTS — one row per community hazard report
-- ------------------------------------------------------------
CREATE TABLE reports (
    ReportID     INT AUTO_INCREMENT PRIMARY KEY,
    UserID       INT           NOT NULL,
    IncidentType VARCHAR(60)   NOT NULL,
    Description  TEXT          NOT NULL,
    Location     VARCHAR(150)  NOT NULL,
    DateReported DATE          NOT NULL,
    CONSTRAINT fk_reports_user
        FOREIGN KEY (UserID) REFERENCES users(UserID) ON DELETE CASCADE,
    INDEX idx_reports_type (IncidentType),
    INDEX idx_reports_date (DateReported)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- ROUTES — one row per route search and its safety score
-- ------------------------------------------------------------
CREATE TABLE routes (
    RouteID     INT AUTO_INCREMENT PRIMARY KEY,
    UserID      INT          NOT NULL,
    StartPoint  VARCHAR(150) NOT NULL,
    EndPoint    VARCHAR(150) NOT NULL,
    SafetyScore INT          NOT NULL,
    SearchDate  DATE         NOT NULL,
    CONSTRAINT fk_routes_user
        FOREIGN KEY (UserID) REFERENCES users(UserID) ON DELETE CASCADE,
    INDEX idx_routes_user (UserID)
) ENGINE=InnoDB;

-- ============================================================
--  SAMPLE DATA — realistic Wembley-area content for the viva
-- ============================================================

-- Demo accounts. Passwords are shown here for the demonstration only;
-- app.py stores and verifies Werkzeug password hashes.
--   amina.k@example.ac.uk  / SafeRoute123
--   daniel.o@example.ac.uk / SafeRoute123
--   priya.s@example.ac.uk / SafeRoute123
INSERT INTO users (FullName, Email, PasswordHash, DateCreated) VALUES
('Amina Karim',  'amina.k@example.ac.uk',  'pbkdf2:sha256:600000$s4f3r0ut3D3m0X$3f999acb94ba0158fd4d9dd644ba7a5550ab6bb217258e4e4f2d5f601d3161db', '2026-09-28 09:14:00'),
('Daniel Owusu', 'daniel.o@example.ac.uk', 'pbkdf2:sha256:600000$s4f3r0ut3D3m0X$3f999acb94ba0158fd4d9dd644ba7a5550ab6bb217258e4e4f2d5f601d3161db', '2026-09-30 17:42:00'),
('Priya Shah',   'priya.s@example.ac.uk',  'pbkdf2:sha256:600000$s4f3r0ut3D3m0X$3f999acb94ba0158fd4d9dd644ba7a5550ab6bb217258e4e4f2d5f601d3161db', '2026-10-02 11:05:00');

INSERT INTO reports (UserID, IncidentType, Description, Location, DateReported) VALUES
(1, 'Poor Lighting',          'Street lights out along the approach to the station entrance.',            'Wembley Park Station',         '2026-10-18'),
(2, 'Flooding',               'Standing water across the pedestrian crossing after heavy rain.',          'High Road Wembley',            '2026-10-20'),
(3, 'Suspicious Activity',    'Group loitering near the underpass late at night; reported to police.',     'College Road, Wembley',        '2026-10-14'),
(1, 'Unsafe Crossing',        'No safe crossing point; pedestrians are crossing between traffic.',        'North Circular Road (A406)',   '2026-10-11'),
(2, 'Poor Lighting',          'Several lamps not working on the walkway towards the stadium.',           'Olympic Way',                  '2026-10-21'),
(3, 'Pothole',                'Deep pothole in the cycle lane, forcing cyclists into the traffic.',       'Ealing Road',                  '2026-10-09'),
(1, 'Road Damage',            'Damaged kerb and broken paving outside the station entrance.',             'Wembley Central Station',      '2026-10-16'),
(2, 'Anti-Social Behaviour',  'Repeated late-night noise and littering near the bus stop.',               'Forty Lane',                   '2026-10-05'),
(3, 'Flooding',               'Drainage blocked, water pooling under the railway bridge.',                'Alperton Station',             '2026-10-22'),
(1, 'Unsafe Crossing',        'Faded road markings at the school crossing with poor visibility.',         'Preston Road',                 '2026-10-13'),
(2, 'Poor Lighting',          'Park lighting has failed; the path is very dark after 18:00.',             'Kingsbury Road',               '2026-10-07'),
(3, 'Pothole',                'Road surface breaking up on the service road by the stadium.',             'Wembley Stadium',              '2026-10-19');

INSERT INTO routes (UserID, StartPoint, EndPoint, SafetyScore, SearchDate) VALUES
(1, 'Wembley Park Station', 'Wembley Central Station', 85, '2026-10-23'),
(2, 'High Road Wembley',    'Wembley Park Station',    90, '2026-10-22'),
(3, 'Olympic Way',          'Wembley Stadium',         95, '2026-10-21'),
(1, 'North Circular Road (A406)', 'Preston Road',       70, '2026-10-20'),
(2, 'College Road, Wembley','Alperton Station',        65, '2026-10-19'),
(3, 'Ealing Road',          'Wembley Central Station', 80, '2026-10-18');

-- Handy verification queries
--   SELECT COUNT(*) AS total_reports FROM reports;
--   SELECT COUNT(*) AS total_users   FROM users;
--   SELECT COUNT(*) AS total_routes  FROM routes;
--   SELECT IncidentType, Location, DateReported FROM reports ORDER BY DateReported DESC;
