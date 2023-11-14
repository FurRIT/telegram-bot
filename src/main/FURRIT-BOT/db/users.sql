DROP TABLE IF EXISTS USERS;
DROP TABLE IF EXISTS QUOTES;

CREATE TABLE USERS(
    telegram_id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64),
    awoo_fine INTEGER DEFAULT 0,
    pan_count INTEGER DEFAULT 0
    );

CREATE TABLE QUOTES(
    telegram_id VARCHAR(64) REFERENCES USERS(telegram_id),
    quote VARCHAR(265),
    date_issued DATE,
    issued_by_id VARCHAR(64) REFERENCES USERS(telegram_id)
    );
