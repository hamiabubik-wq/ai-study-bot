import sqlite3
from datetime import datetime, timezone
from app.config import settings

def con():
    c=sqlite3.connect(settings.database_path); c.row_factory=sqlite3.Row; return c

def now(): return datetime.now(timezone.utc).isoformat()

def init_db():
    with con() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(telegram_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, access_type TEXT NOT NULL DEFAULT 'free', subscription_until TEXT, created_at TEXT NOT NULL, last_activity TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS request_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL, request_type TEXT NOT NULL, success INTEGER NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS chat_history(id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL, mode TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')

def upsert_user(u):
    n=now()
    with con() as c: c.execute('''INSERT INTO users(telegram_id,username,first_name,created_at,last_activity) VALUES(?,?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name,last_activity=excluded.last_activity''',(u.id,u.username,u.first_name,n,n))

def get_user(uid):
    with con() as c: return c.execute('SELECT * FROM users WHERE telegram_id=?',(uid,)).fetchone()

def is_premium(uid):
    u=get_user(uid)
    if not u: return False
    if u['access_type']=='unlimited': return True
    if u['access_type']=='premium' and u['subscription_until']:
        try: return datetime.fromisoformat(u['subscription_until'])>datetime.now(timezone.utc)
        except ValueError: return False
    return False

def requests_today(uid):
    with con() as c: return c.execute("SELECT COUNT(*) c FROM request_logs WHERE telegram_id=? AND success=1 AND DATE(created_at)=DATE('now')",(uid,)).fetchone()['c']

def can_request(uid): return is_premium(uid) or requests_today(uid)<settings.free_daily_limit

def log(uid, kind, success=True):
    with con() as c: c.execute('INSERT INTO request_logs(telegram_id,request_type,success,created_at) VALUES(?,?,?,?)',(uid,kind,int(success),now()))

def save_history(uid, mode, role, content):
    with con() as c: c.execute('INSERT INTO chat_history(telegram_id,mode,role,content,created_at) VALUES(?,?,?,?,?)',(uid,mode,role,content[:12000],now()))

def history(uid, mode=None, limit=10):
    q='SELECT * FROM chat_history WHERE telegram_id=?'; p=[uid]
    if mode: q+=' AND mode=?'; p.append(mode)
    q+=' ORDER BY id DESC LIMIT ?'; p.append(limit)
    with con() as c: return list(reversed(c.execute(q,p).fetchall()))

def clear_history(uid):
    with con() as c: c.execute('DELETE FROM chat_history WHERE telegram_id=?',(uid,))

def grant(uid):
    with con() as c: return c.execute("UPDATE users SET access_type='unlimited',subscription_until=NULL WHERE telegram_id=?",(uid,)).rowcount>0

def revoke(uid):
    with con() as c: return c.execute("UPDATE users SET access_type='free',subscription_until=NULL WHERE telegram_id=?",(uid,)).rowcount>0

def stats():
    with con() as c:
        one=lambda q: c.execute(q).fetchone()['c']
        return dict(total=one('SELECT COUNT(*) c FROM users'), new=one("SELECT COUNT(*) c FROM users WHERE DATE(created_at)=DATE('now')"), active=one("SELECT COUNT(*) c FROM users WHERE last_activity>=datetime('now','-5 minutes')"), req=one("SELECT COUNT(*) c FROM request_logs WHERE success=1 AND DATE(created_at)=DATE('now')"), err=one("SELECT COUNT(*) c FROM request_logs WHERE success=0 AND DATE(created_at)=DATE('now')"), premium=one("SELECT COUNT(*) c FROM users WHERE access_type IN ('premium','unlimited')"))
