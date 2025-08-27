# Migration

This document elaborates the schema changes introduced in PR #19.

## Users

### Original Schema

```sql
CREATE TABLE "USERS" (
    "telegram_id"   VARCHAR(64),
    "firstName"     VARCHAR(64),
    "lastName"      VARCHAR(64),
    "username"      VARCHAR(64),
    "awoo_fine"     INTEGER DEFAULT 0,
    "pan_count"     INTEGER DEFAULT 0,
    PRIMARY KEY("telegram_id")
);
```

### Columns

| Column        | Description                |
| ------------- | -------------------------- |
| `telegram_id` | User's Telegram ID         |
| `firstName`   | User's Telegram First Name |
| `lastName`    | User's Telegram Last Name  |
| `username`    | User's Telegram Username   |
| `awoo_fine`   | User's awoo fine total     |
| `pan_count`   | User's pan count           |

### Mapping

```
[NONE]      -> id
telegram_id -> tg_id
firstName   -> tg_first_name
lastName    -> tg_last_name
username    -> tg_username
awoo_fine   -> fines
[NONE]      -> n_awoo
[NONE]      -> n_pan
```

### New Schema

```sql
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
```

## Quotes

### Original Schema

```sql
CREATE TABLE "QUOTES" (
    "Quote_Author"  VARCHAR(64),
    "quote"         VARCHAR(265),
    "date_issued"   VARCHAR(64),
    "issued_by_id"  VARCHAR(64),
    "Chat_ID"       VARCHAR(64),
    "NSFW"          INTEGER,
    FOREIGN KEY("Quote_Author") REFERENCES "USERS"("telegram_id"),
    FOREIGN KEY("issued_by_id") REFERENCES "USERS"("telegram_id")
);
```

### Columns

| Column         | Description            |
| -------------- | ---------------------- |
| `Quote_Author` | Author's Telegram ID   |
| `quote`        | Quote content          |
| `date_issued`  | Date Author was Quoted |
| `issued_by_id` | Quoter's Telegram ID   |
| `Chat_ID`      | Source chat identifier |
| `NSFW`         | 0 or 1; NSFW status.   |

### Mapping

```
[NONE]              -> id
Chat_ID             -> tg_chat_id
Quote_Author        -> author_tg_id
[NONE]              -> author_msg_sent_at
[NONE]              -> author_msg_id
issued_by_id        -> quoter_tg_id
date_issued         -> quoter_msg_sent_at
[NONE]              -> quoter_msg_id
quote               -> quote
```

### New Schema

```sql
CREATE TABLE QUOTES(
    id                  INTEGER PRIMARY KEY,
    tg_chat_id          INTEGER NOT NULL,
    author_tg_id        INTEGER REFERENCES USERS(tg_id) NOT NULL,
    author_msg_sent_at  TEXT NOT NULL,
    author_msg_id       INTEGER NOT NULL UNIQUE,
    quoter_tg_id        INTEGER REFERENCES USERS(tg_id) NOT NULL,
    quoter_msg_sent_at  TEXT NOT NULL,
    quoter_msg_id       INTEGER NOT NULL,
    quote               VARCHAR(3584) NOT NULL
);
```

However, this new schema has hard `NOT NULL` constraints in place that are not
compatible with missing values in `author_msg_sent_at`, `author_msg_id`, and
`quoter_msg_id`. So, it was adjusted to,

```sql
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
```
