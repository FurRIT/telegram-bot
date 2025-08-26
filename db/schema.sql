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
    id                  INTEGER PRIMARY KEY,
    tg_chat_id          INTEGER NOT NULL,
    quotee_tg_id        INTEGER REFERENCES USERS(tg_id) NOT NULL,
    quotee_msg_sent_at  TEXT,
    quotee_msg_id       INTEGER UNIQUE,
    quoter_tg_id        INTEGER REFERENCES USERS(tg_id) NOT NULL,
    quoter_msg_sent_at  TEXT NOT NULL,
    quoter_msg_id       INTEGER,
    quote               VARCHAR(512) NOT NULL
);
