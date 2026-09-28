-- src/main/resources/schema.sql
CREATE TABLE IF NOT EXISTS messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    text VARCHAR(255),
    user_name VARCHAR(255)
);