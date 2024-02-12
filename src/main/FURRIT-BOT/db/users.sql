DROP TABLE USERS
CREATE TABLE USERS(
    telegram_id VARCHAR(64),
    firstName VARCHAR(64),
    lastName VARCHAR(64),
    username VARCHAR(64),
    awoo_fine INTEGER DEFAULT 0,
    pan_count INTEGER DEFAULT 0
    );
