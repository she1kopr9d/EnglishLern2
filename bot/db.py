import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'words.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS words (
        user_id INTEGER,
        word TEXT,
        translation TEXT,
        next_reminder DATETIME,
        interval INTEGER,
        PRIMARY KEY (user_id, word)
    )''')
    conn.commit()
    conn.close()

def word_exists(user_id, word):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT 1 FROM words WHERE user_id=? AND word=?''', (user_id, word))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_word(user_id, word, translation):
    if word_exists(user_id, word):
        return False
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now()
    c.execute('''INSERT OR REPLACE INTO words (user_id, word, translation, next_reminder, interval)
                 VALUES (?, ?, ?, ?, ?)''',
              (user_id, word, translation, now + timedelta(minutes=1), 1))
    conn.commit()
    conn.close()
    return True

def get_due_words():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now()
    c.execute('''SELECT user_id, word, translation FROM words WHERE next_reminder <= ?''', (now,))
    due = c.fetchall()
    conn.close()
    return due

def get_word_info(user_id, word):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT translation, interval FROM words WHERE user_id=? AND word=?''', (user_id, word))
    result = c.fetchone()
    conn.close()
    if result:
        return {'ru': result[0], 'interval': result[1]}
    return None

def update_word_interval(user_id, word, new_interval):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    next_time = datetime.now() + timedelta(minutes=new_interval)
    c.execute('''UPDATE words 
                 SET next_reminder=?, interval=? 
                 WHERE user_id=? AND word=?''',
              (next_time, new_interval, user_id, word))
    conn.commit()
    conn.close()

def delete_word(user_id, word):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''DELETE FROM words WHERE user_id=? AND word=?''', (user_id, word))
    conn.commit()
    conn.close()
    return True

init_db()
