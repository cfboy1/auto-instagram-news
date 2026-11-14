"""SQLite persistence — accounts, modes, jobs, oauth states."""
import threading
import time

import sqlite3

from app import config

_lock = threading.Lock()
_conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row

with _lock:
    _conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts(
            telegram_id INTEGER PRIMARY KEY,
            username TEXT, access_token TEXT, ig_user_id TEXT, connected_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings(
            telegram_id INTEGER PRIMARY KEY,
            publish_mode INTEGER DEFAULT 0, audio_mode INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER, path TEXT, caption TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS oauth_states(
            state TEXT PRIMARY KEY, telegram_id INTEGER, created_at TEXT
        );
        """
    )
    _conn.commit()


def _one(sql, args=()):
    with _lock:
        return _conn.execute(sql, args).fetchone()


def _run(sql, args=()):
    with _lock:
        _conn.execute(sql, args)
        _conn.commit()


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


# ---------- accounts ----------
def upsert_account(telegram_id, username, access_token, ig_user_id):
    _run(
        "INSERT INTO accounts(telegram_id,username,access_token,ig_user_id,connected_at)"
        " VALUES(?,?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET"
        " username=excluded.username, access_token=excluded.access_token,"
        " ig_user_id=excluded.ig_user_id, connected_at=excluded.connected_at",
        (telegram_id, username, access_token, ig_user_id, _now()),
    )


def get_account(telegram_id):
    r = _one("SELECT * FROM accounts WHERE telegram_id=?", (telegram_id,))
    return dict(r) if r else None


def delete_account(telegram_id):
    _run("DELETE FROM accounts WHERE telegram_id=?", (telegram_id,))


# ---------- modes ----------
def _settings(telegram_id):
    _run(
        "INSERT OR IGNORE INTO settings(telegram_id) VALUES(?)", (telegram_id,)
    )
    return dict(_one("SELECT * FROM settings WHERE telegram_id=?", (telegram_id,)))


def set_publish_mode(telegram_id, on: bool):
    _settings(telegram_id)
    _run(
        "UPDATE settings SET publish_mode=? WHERE telegram_id=?",
        (1 if on else 0, telegram_id),
    )


def get_publish_mode(telegram_id) -> bool:
    return bool(_settings(telegram_id)["publish_mode"])


def set_audio_mode(telegram_id, on: bool):
    _settings(telegram_id)
    _run(
        "UPDATE settings SET audio_mode=? WHERE telegram_id=?",
        (1 if on else 0, telegram_id),
    )


def get_audio_mode(telegram_id) -> bool:
    return bool(_settings(telegram_id)["audio_mode"])


# ---------- jobs ----------
def add_job(telegram_id, path, caption) -> int:
    _run(
        "INSERT INTO jobs(telegram_id,path,caption,created_at) VALUES(?,?,?,?)",
        (telegram_id, path, caption, _now()),
    )
    return _one("SELECT last_insert_rowid() AS id")["id"]


def get_job(job_id):
    r = _one("SELECT * FROM jobs WHERE id=?", (job_id,))
    return dict(r) if r else None


# ---------- oauth states ----------
def save_state(state, telegram_id):
    _run(
        "INSERT OR REPLACE INTO oauth_states(state,telegram_id,created_at) VALUES(?,?,?)",
        (state, telegram_id, _now()),
    )


def pop_state(state):
    r = _one("SELECT * FROM oauth_states WHERE state=?", (state,))
    if r:
        _run("DELETE FROM oauth_states WHERE state=?", (state,))
    return dict(r) if r else None
