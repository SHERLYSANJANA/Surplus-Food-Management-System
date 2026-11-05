--CREATE DATABASE food_redistribution;

CREATE TABLE Donor
(donor_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 donor_name VARCHAR(100) NOT NULL,
 donor_location VARCHAR(250) NOT NULL,
 email_id VARCHAR(50) UNIQUE NOT NULL,
 phone_no VARCHAR(20) NOT NULL);

CREATE TABLE Donation
(post_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
 expiry_time TIMESTAMP NOT NULL,
 post_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
 donor_id INT NOT NULL REFERENCES Donor(donor_id));

CREATE TABLE Receiver
(receiver_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 receiver_name varchar(100) NOT NULL,
 email VARCHAR(100) UNIQUE NOT NULL,
 phone_no VARCHAR(20) NOT NULL);

CREATE TABLE Donation_Items
(post_id INT REFERENCES Donation(post_id) ON DELETE CASCADE,
 item_no INT NOT NULL,
 item_name VARCHAR(100) NOT NULL,
 quantity INT NOT NULL CHECK(quantity>0),
 PRIMARY KEY(post_id,item_no)); 

CREATE TABLE Receiver_request
(request_id INT GENERATED ALWAYS AS IDENTITY ,
 receiver_id INT NOT NULL REFERENCES Receiver(receiver_id),
 food_item VARCHAR(50) NOT NULL,
 quantity INT NOT NULL CHECK(quantity>0), 
 request_date TIMESTAMP NOT NULL DEFAULT LOCALTIMESTAMP,
 status VARCHAR(20) DEFAULT 'Pending' 
 CHECK (status in ('Pending','Partial','Fulfilled','Cancelled')),
 PRIMARY KEY(request_id)); 

CREATE TABLE Match_Allocation
(match_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
 match_percent NUMERIC(5,2) CHECK(match_percent BETWEEN 0 AND 100), 
 allocation_status varchar(20) NOT NULL DEFAULT 'Pending' 
 CHECK(allocation_status in ('Pending','Approved','Completed','Rejected')), 
 allocated_quantity INT NOT NULL CHECK(allocated_quantity>0),
 post_id INT NOT NULL REFERENCES Donation(post_id), 
 item_no INT NOT NULL, 
 request_id INT NOT NULL REFERENCES Receiver_request(request_id), 
 FOREIGN KEY(post_id,item_no) REFERENCES Donation_items(post_id,item_no));

CREATE TABLE Donor_photos
(donor_id INT REFERENCES Donor(donor_id) ON DELETE CASCADE, 
 photo TEXT NOT NULL,
PRIMARY KEY(donor_id,photo));
