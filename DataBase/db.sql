

CREATE TABLE Participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    discord_id BIGINT,  
    score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE Tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(255),
    weight FLOAT,
    participant_id INT,
    deadline DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES Participants(id)
);


CREATE TABLE Evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT,
    task_id INT,
    score FLOAT,
    status INT DEFAULT 1,
    evaluated_at DATETIME,
    FOREIGN KEY (participant_id) REFERENCES Participants(id),
    FOREIGN KEY (task_id) REFERENCES Tasks(id)
);

CREATE TABLE Submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT,
    task_id INT,
    status ENUM('pending', 'accepted', 'rejected'),
    submitted_at DATETIME,
    FOREIGN KEY (participant_id) REFERENCES Participants(id),
    FOREIGN KEY (task_id) REFERENCES Tasks(id)
);
