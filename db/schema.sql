DROP TABLE IF EXISTS QUOTES;
DROP TABLE IF EXISTS USERS;

/* NOTE: limits taken from https://limits.tginfo.me/en */
CREATE TABLE USERS(
    id              INTEGER PRIMARY KEY,
    tg_id           INTEGER NOT NULL UNIQUE,
    tg_first_name   VARCHAR(64) NOT NULL,
    tg_last_name    VARCHAR(64),
    tg_username     VARCHAR(32),
    awoo_debt       INTEGER DEFAULT 0 NOT NULL,
    pan_count       INTEGER DEFAULT 0 NOT NULL
);

CREATE TABLE QUOTES(
    id              INTEGER PRIMARY KEY,
    sent_by         INTEGER REFERENCES USERS(id) NOT NULL,
    sent_at         INTEGER NOT NULL,
    sent_msg        INTEGER NOT NULL,
    added_by        INTEGER REFERENCES USERS(id) NOT NULL,
    added_at        INTEGER NOT NULL,
    quote           VARCHAR(256) NOT NULL,
);