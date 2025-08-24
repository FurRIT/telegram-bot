DROP TABLE IF EXISTS QUOTES;
DROP TABLE IF EXISTS USERS;

/* NOTE: limits taken from https://limits.tginfo.me/en */
CREATE TABLE USERS(
    id              INTEGER PRIMARY KEY,
    tg_id           INTEGER NOT NULL UNIQUE,
    tg_first_name   VARCHAR(64) NOT NULL,
    tg_last_name    VARCHAR(64),
    tg_username     VARCHAR(32),
    fines           INTEGER DEFAULT 0 NOT NULL CHECK(fines >= 0),
    n_awoo          INTEGER DEFAULT 0 NOT NULL CHECK(n_awoo >= 0),
    n_pan           INTEGER DEFAULT 0 NOT NULL CHECK(n_pan >= 0)
);

CREATE TABLE QUOTES(
    id              INTEGER PRIMARY KEY,
    sent_by         INTEGER REFERENCES USERS(tg_id) NOT NULL,
    sent_at         TEXT NOT NULL,
    sent_msg        INTEGER NOT NULL,
    added_by        INTEGER REFERENCES USERS(tg_id) NOT NULL,
    added_at        TEXT NOT NULL,
    added_msg       INTEGER NOT NULL,
    quote           VARCHAR(256) NOT NULL
);