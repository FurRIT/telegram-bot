DROP TABLE IF EXISTS QUOTES;

CREATE TABLE QUOTES(
    telegram_id VARCHAR(64) REFERENCES USERS(telegram_id),
    quote VARCHAR(265),
    date_issued VARCHAR(64),
    issued_by_id VARCHAR(64) REFERENCES USERS(telegram_id)

    );
