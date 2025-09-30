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
    author_tg_id        INTEGER REFERENCES USERS(tg_id) NOT NULL,
    author_msg_sent_at  TEXT,
    author_msg_id       INTEGER UNIQUE,
    quoter_tg_id        INTEGER REFERENCES USERS(tg_id) NOT NULL,
    quoter_msg_sent_at  TEXT NOT NULL,
    quoter_msg_id       INTEGER,
    quote               VARCHAR(3584) NOT NULL
);

CREATE TABLE EVENTS(
    id                  INTEGER PRIMARY KEY,
    ext_id              VARCHAR(24) NOT NULL UNIQUE
);

CREATE TABLE EVENT_MESSAGES(
    event_id            INTEGER REFERENCES EVENTS(id) NOT NULL,
    tg_msg_id           INTEGER NOT NULL,
    tg_chat_id          INTEGER NOT NULL,
    PRIMARY KEY (event_id, tg_msg_id, tg_chat_id)
);
