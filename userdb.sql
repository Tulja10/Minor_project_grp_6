CREATE DATABASE user_db;
USE user_db;
SHOW databases;

-- Users table
CREATE TABLE User(user_id INT PRIMARY KEY AUTO_INCREMENT , 
    name VARCHAR(25), email VARCHAR(50) UNIQUE NOT NULL, hashed_psswd VARCHAR(15) , 
    created_at DATE DEFAULT (CURRENT_DATE), role ENUM('student','admin') DEFAULT 'student');
ALTER TABLE User MODIFY COLUMN hashed_psswd VARCHAR(255);

-- Testing users table with dummy data
INSERT INTO User(user_id, name, email, hashed_psswd, created_at) VALUES(1, "test", "test@acropolis.in", "hashed psswd here", "2025-01-01");

-- Results table
CREATE TABLE results( result_id INT PRIMARY KEY AUTO_INCREMENT, 
user_id INT NOT NULL, sem INT, sgpa  DECIMAL(3,2) , cgpa DECIMAL(3,2), FOREIGN KEY (user_id) REFERENCES user(user_id)); 

-- Attendance table
CREATE TABLE attendance( attendance_id INT PRIMARY KEY, user_id INT NOT NULL, sem INT,total_classes INT , attended_classes INT,
percentage INT , last_updated DATE DEFAULT (CURRENT_DATE), FOREIGN KEY (user_id) REFERENCES user(user_id));

-- Chat history table
CREATE TABLE chat_history( chat_id INT PRIMARY KEY AUTO_INCREMENT, user_id INT NOT NULL,
 ques TEXT NOT NULL, ans TEXT NOT NULL, context TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES user(user_id));