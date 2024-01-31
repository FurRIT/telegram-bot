DROP TABLE IF EXISTS QUOTES CASCADE ;

CREATE TABLE QUOTES(
    chat_id VARCHAR(64),
    message_id VARCHAR(64),
    issued_by_id VARCHAR(64) REFERENCES USERS(telegram_id),
    authored_telegram_id VARCHAR(64) REFERENCES USERS(telegram_id),
    date_issued VARCHAR(64),
    quote VARCHAR(265),
    nsfw VARCHAR(1)
    );
