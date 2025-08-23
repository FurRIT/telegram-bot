DROP TABLE IF EXISTS QUOTES;
DROP TABLE IF EXISTS USERS;

CREATE TABLE USERS(
    telegram_id     VARCHAR(64),
    firstName       VARCHAR(64),
    lastName        VARCHAR(64),
    username        VARCHAR(64),
    awoo_fine       INTEGER DEFAULT 0,
    pan_count       INTEGER DEFAULT 0
);

CREATE TABLE QUOTES(
    telegram_id     VARCHAR(64) REFERENCES USERS(telegram_id),
    quote           VARCHAR(265),
    date_issued     VARCHAR(64),
    issued_by_id    VARCHAR(64) REFERENCES USERS(telegram_id)
);