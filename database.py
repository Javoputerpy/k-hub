import os
import sqlite3
import datetime
import random

DB_FILE = os.environ.get('DATABASE_PATH', 'khub.db')

def _conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_db_connection():
    return _conn()

def init_db():
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            name TEXT, username TEXT, token TEXT,
            university TEXT, field TEXT,
            gpa REAL DEFAULT 0, ielts REAL DEFAULT 0,
            research INTEGER DEFAULT 0, awards INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
            joined_at TEXT, tips_enabled INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0, is_public INTEGER DEFAULT 1,
            theme TEXT DEFAULT 'glass', lang TEXT DEFAULT 'uz',
            avatar_path TEXT, show_avatar INTEGER DEFAULT 1,
            passport_face_path TEXT, passport_dob TEXT,
            passport_nationality TEXT, passport_number TEXT,
            otp TEXT
        );
        CREATE TABLE IF NOT EXISTS docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, doc_name TEXT,
            checked INTEGER DEFAULT 0,
            checked_at TEXT, file_path TEXT
        );
        CREATE TABLE IF NOT EXISTS interview_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, question TEXT, answer TEXT,
            score INTEGER, practiced_at TEXT
        );
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, type TEXT, title TEXT,
            description TEXT, date TEXT, link TEXT,
            file_path TEXT, verified INTEGER DEFAULT 0
        );
        -- Admin / Ecosystem Tables
        CREATE TABLE IF NOT EXISTS admin_labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, desc TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_vocab (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT, def TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, date TEXT, cat TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, detail TEXT, badge TEXT, type TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_roadmap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, done INTEGER
        );
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER, to_id INTEGER, status TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS kaist_labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, major TEXT, focus TEXT, link TEXT, pi TEXT
        );
        CREATE TABLE IF NOT EXISTS user_roadmap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, title TEXT, done INTEGER DEFAULT 0, date TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, name TEXT, text TEXT, timestamp TEXT
        );
        -- Blog & Courses
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, -- Added for community ownership
            title TEXT, content TEXT, author TEXT, category TEXT,
            date TEXT, views INTEGER DEFAULT 0, image_url TEXT,
            is_html INTEGER DEFAULT 0, excerpt TEXT
        );
        CREATE TABLE IF NOT EXISTS blog_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER, tg_id INTEGER, 
            text TEXT, timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS blog_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER, tg_id INTEGER, 
            type TEXT -- 'like', 'fire', 'clap'
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, description TEXT, category TEXT,
            level TEXT, image_url TEXT
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER, title TEXT, content TEXT, 
            video_url TEXT, ai_prompt TEXT
        );
        CREATE TABLE IF NOT EXISTS user_lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, lesson_id INTEGER, completed INTEGER DEFAULT 0,
            last_accessed TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_docs_tg_id ON docs(tg_id);
        CREATE INDEX IF NOT EXISTS idx_portfolio_tg_id ON portfolio(tg_id);
    """)
    c.commit()

    # ── SAFE COLUMN MIGRATIONS (for existing databases) ──
    # This adds new columns to old databases without crashing
    migrations = [
        ("ALTER TABLE users ADD COLUMN university TEXT", "university"),
        ("ALTER TABLE users ADD COLUMN field TEXT", "field"),
        ("ALTER TABLE users ADD COLUMN is_public INTEGER DEFAULT 1", "is_public"),
        ("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0", "is_admin"),
        ("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'glass'", "theme"),
        ("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'uz'", "lang"),
        ("ALTER TABLE users ADD COLUMN avatar_path TEXT", "avatar_path"),
        ("ALTER TABLE users ADD COLUMN show_avatar INTEGER DEFAULT 1", "show_avatar"),
        ("ALTER TABLE users ADD COLUMN passport_face_path TEXT", "passport_face_path"),
        ("ALTER TABLE users ADD COLUMN passport_dob TEXT", "passport_dob"),
        ("ALTER TABLE users ADD COLUMN passport_nationality TEXT", "passport_nationality"),
        ("ALTER TABLE users ADD COLUMN passport_number TEXT", "passport_number"),
        ("ALTER TABLE users ADD COLUMN otp TEXT", "otp"),
        # Community blog migrations
        ("ALTER TABLE blog_posts ADD COLUMN tg_id INTEGER", "blog_posts.tg_id"),
        ("ALTER TABLE blog_posts ADD COLUMN is_html INTEGER DEFAULT 0", "blog_posts.is_html"),
        ("ALTER TABLE blog_posts ADD COLUMN excerpt TEXT", "blog_posts.excerpt"),
    ]
    for sql, col in migrations:
        try:
            c.execute(sql)
            c.commit()
        except Exception:
            pass  # Column already exists, skip

    # Ensure new community + adaptive learning tables exist (safe for old DBs)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS blog_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER, tg_id INTEGER,
            text TEXT, timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS blog_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER, tg_id INTEGER,
            type TEXT
        );
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, course_id INTEGER,
            level TEXT DEFAULT 'beginner',
            target_score REAL DEFAULT 7.0,
            exam_date TEXT,
            strategy_json TEXT,
            streak INTEGER DEFAULT 0,
            last_active TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER, course_id INTEGER,
            date TEXT,
            task_type TEXT,
            content_json TEXT,
            completed INTEGER DEFAULT 0,
            ai_feedback TEXT,
            score REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS vocab_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            word TEXT, translation TEXT,
            context TEXT, date_added TEXT,
            times_seen INTEGER DEFAULT 1,
            mastered INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS listening_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            transcript TEXT,
            audio_path TEXT,
            questions_json TEXT,
            blanks_json TEXT,
            score REAL,
            completed_at TEXT
        );
    """)
    c.commit()

    # Verify/Seed Data
    if c.execute("SELECT COUNT(*) FROM admin_deadlines").fetchone()[0] < 3:
        c.execute("DELETE FROM admin_deadlines")
        c.executescript("""
            INSERT INTO admin_deadlines (name, date, cat) VALUES 
            ('KAIST Fall 2026 (Early)', '2025-10-21', 'Closed'),
            ('KAIST Fall 2026 (Regular)', '2026-01-15', 'Closed'),
            ('KAIST Fall 2026 (Late)', '2026-05-25', 'Active'),
            ('KAIST Spring 2027 (Early)', '2026-09-01', 'Upcoming'),
            ('KAIST Spring 2027 (Regular)', '2026-11-20', 'Upcoming');
        """)
    
    if c.execute("SELECT COUNT(*) FROM admin_scholarships").fetchone()[0] < 3:
        c.execute("DELETE FROM admin_scholarships")
        c.executescript("""
            INSERT INTO admin_scholarships (name, detail, badge, type) VALUES 
            ('KAIST ISS', 'International Student Scholarship. Full tuition + Monthly allowance.', 'KAIST', 'cyan-border'),
            ('GKS Undergraduate', 'Global Korea Scholarship. Full ride + Airfare + Monthly stipend.', 'GKS', 'gold-border'),
            ('SAMSUNG Dream', 'Merit-based scholarship for STEM excellence.', 'SAMSUNG', 'blue-border');
        """)
    
    if c.execute("SELECT COUNT(*) FROM courses").fetchone()[0] < 2:
        c.execute("DELETE FROM courses")
        c.executescript("""
            INSERT INTO courses (title, description, category, level, image_url) VALUES 
            ('IELTS Mastery: 7.5+', 'Advanced AI-powered IELTS preparation with personalized feedback.', 'English', 'Advanced', 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?q=80&w=1000&auto=format&fit=crop'),
            ('TOPIK II Explorer', 'Master Korean for TOPIK II with interactive AI lessons.', 'Korean', 'Intermediate', 'https://images.unsplash.com/photo-1541339907198-e08756ebafe3?q=80&w=1000&auto=format&fit=crop');
        """)
    c.commit()
    c.close()

# Users
def create_user(tg_id, name, username):
    import uuid
    c = _conn()
    u = c.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    if not u:
        token = str(uuid.uuid4())
        dt = datetime.datetime.now().isoformat()
        # First user is admin
        is_admin = 1 if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0 else 0
        c.execute("INSERT INTO users (tg_id,name,username,token,joined_at,is_admin) VALUES (?,?,?,?,?,?)",
                  (tg_id, name, username, token, dt, is_admin))
        # Initial docs
        for d in ["Passport", "Diploma", "Transcript", "IELTS", "Recommendation 1", "SOP"]:
            c.execute("INSERT INTO docs (tg_id, doc_name) VALUES (?,?)", (tg_id, d))
        c.commit()
        u = c.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    c.close()
    return u['token'] if u and 'token' in u.keys() else None

def get_user_by_username(username):
    c = _conn()
    u = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    c.close()
    return dict(u) if u else None

def get_user(tg_id):
    c = _conn()
    u = c.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    c.close()
    return dict(u) if u else None

def get_user_by_token(token):
    c = _conn()
    u = c.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()
    c.close()
    return dict(u) if u else None

ALLOWED_USER_COLUMNS = {
    'name', 'username', 'university', 'field', 'gpa', 'ielts', 
    'research', 'awards', 'xp', 'level', 'tips_enabled', 
    'is_admin', 'is_public', 'theme', 'lang', 'avatar_path', 
    'show_avatar', 'passport_face_path', 'passport_dob', 
    'passport_nationality', 'passport_number', 'otp'
}

def update_user(tg_id, **kwargs):
    c = _conn()
    safe_kwargs = {k: v for k, v in kwargs.items() if k in ALLOWED_USER_COLUMNS}
    if not safe_kwargs: return
    
    fields = [f"{k}=?" for k in safe_kwargs.keys()]
    values = list(safe_kwargs.values()) + [tg_id]
    c.execute(f"UPDATE users SET {','.join(fields)} WHERE tg_id=?", values)
    c.commit()
    c.close()

def get_user_by_otp(otp):
    c = _conn()
    u = c.execute("SELECT * FROM users WHERE otp=?", (otp,)).fetchone()
    c.close()
    return dict(u) if u else None

def add_xp(tg_id, amount):
    u = get_user(tg_id)
    if not u: return
    nx = min(u['xp'] + amount, 10000)
    nl = (nx // 1000) + 1
    update_user(tg_id, xp=nx, level=nl)

# Docs & Portfolio
def get_docs(tg_id):
    c = _conn()
    docs = c.execute("SELECT * FROM docs WHERE tg_id=?", (tg_id,)).fetchall()
    c.close()
    return [dict(d) for d in docs]

def update_doc_status(tg_id, doc_name, checked, path=''):
    c = _conn()
    dt = datetime.datetime.now().isoformat()
    c.execute("UPDATE docs SET checked=?, checked_at=?, file_path=? WHERE tg_id=? AND doc_name=?", 
              (checked, dt, path, tg_id, doc_name))
    c.commit()
    c.close()

def get_portfolio(tg_id):
    c = _conn()
    p = c.execute("SELECT * FROM portfolio WHERE tg_id=? ORDER BY id DESC", (tg_id,)).fetchall()
    c.close()
    return [dict(x) for x in p]

def add_portfolio_item(tg_id, itype, title, desc, date, link='', file_path='', verified=0):
    c = _conn()
    c.execute("INSERT INTO portfolio (tg_id, type, title, description, date, link, file_path, verified) VALUES (?,?,?,?,?,?,?,?)",
              (tg_id, itype, title, desc, date, link, file_path, verified))
    c.commit()
    item_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return item_id

def delete_portfolio_item(tg_id, item_id):
    c = _conn()
    c.execute("DELETE FROM portfolio WHERE tg_id=? AND id=?", (tg_id, item_id))
    c.commit()
    c.close()

# Admin Ecosystem
ALLOWED_ADMIN_TABLES = {
    'admin_labs', 'admin_vocab', 'admin_deadlines', 
    'admin_scholarships', 'admin_roadmap', 'kaist_labs', 'messages'
}

def _get_table(name):
    if name not in ALLOWED_ADMIN_TABLES: 
        raise ValueError(f"Unauthorized table access: {name}")
    c = _conn()
    rows = c.execute(f"SELECT * FROM {name}").fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_admin_labs(): return _get_table('admin_labs')
def get_admin_vocab(): return _get_table('admin_vocab')
def get_admin_deadlines(): return _get_table('admin_deadlines')
def get_admin_scholarships(): return _get_table('admin_scholarships')
def get_admin_roadmap(): return _get_table('admin_roadmap')
def get_all_labs(): return _get_table('kaist_labs')

def get_lab_matches(field):
    c = _conn()
    matches = c.execute("SELECT * FROM kaist_labs WHERE major LIKE ? OR focus LIKE ?", (f'%{field}%', f'%{field}%')).fetchall()
    c.close()
    return [dict(m) for m in matches]

# High-Level Admin Data
def get_all_users():
    c = _conn()
    users = c.execute("SELECT * FROM users ORDER BY xp DESC").fetchall()
    c.close()
    return [dict(u) for u in users]

def get_all_portfolio_items():
    c = _conn()
    items = c.execute("""
        SELECT p.*, u.name as user_name 
        FROM portfolio p 
        JOIN users u ON p.tg_id = u.tg_id 
        ORDER BY p.id DESC
    """).fetchall()
    c.close()
    return [dict(i) for i in items]

# CMS Operations
def add_admin_item(table, **kwargs):
    if table not in ALLOWED_ADMIN_TABLES:
        raise ValueError(f"Unauthorized table access: {table}")
    c = _conn()
    cols = ",".join(kwargs.keys())
    placeholders = ",".join(["?"] * len(kwargs))
    c.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(kwargs.values()))
    c.commit()
    c.close()

def delete_admin_item(table, item_id):
    if table not in ALLOWED_ADMIN_TABLES:
        raise ValueError(f"Unauthorized table access: {table}")
    c = _conn()
    c.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
    c.commit()
    c.close()

# User Roadmap & Community Chat
def get_user_roadmap(tg_id):
    c = _conn()
    rows = c.execute("SELECT * FROM user_roadmap WHERE tg_id=?", (tg_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def add_roadmap_item(tg_id, title, date):
    c = _conn()
    c.execute("INSERT INTO user_roadmap (tg_id, title, date) VALUES (?,?,?)", (tg_id, title, date))
    c.commit()
    c.close()

def delete_roadmap_item(tg_id, item_id):
    c = _conn()
    c.execute("DELETE FROM user_roadmap WHERE tg_id=? AND id=?", (tg_id, item_id))
    c.commit()
    c.close()

def get_messages(limit=50):
    c = _conn()
    rows = c.execute("SELECT * FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in reversed(rows)]

def add_message(tg_id, name, text):
    c = _conn()
    dt = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO messages (tg_id, name, text, timestamp) VALUES (?,?,?,?)", (tg_id, name, text, dt))
    c.commit()
    c.close()

# ── BLOG & COURSES HELPERS ──
def get_blog_posts():
    c = _conn()
    # Join with users to get author names if tg_id present
    rows = c.execute("""
        SELECT b.*, u.name as user_name 
        FROM blog_posts b 
        LEFT JOIN users u ON b.tg_id = u.tg_id 
        ORDER BY b.id DESC
    """).fetchall()
    c.close()
    return [dict(r) for r in rows]

def add_blog_post(tg_id, title, content, author, category, image_url='', is_html=0):
    c = _conn()
    dt = datetime.datetime.now().strftime('%Y-%m-%d')
    c.execute("INSERT INTO blog_posts (tg_id, title, content, author, category, date, image_url, is_html) VALUES (?,?,?,?,?,?,?,?)",
              (tg_id, title, content, author, category, dt, image_url, is_html))
    c.commit()
    c.close()

def get_blog_post(post_id):
    c = _conn()
    c.execute("UPDATE blog_posts SET views = views + 1 WHERE id=?", (post_id,))
    c.commit()
    post = c.execute("SELECT b.*, u.name as user_name FROM blog_posts b LEFT JOIN users u ON b.tg_id = u.tg_id WHERE b.id=?", (post_id,)).fetchone()
    if not post: 
        c.close()
        return None
    
    comments = c.execute("""
        SELECT c.*, u.name as user_name 
        FROM blog_comments c 
        JOIN users u ON c.tg_id = u.tg_id 
        WHERE c.post_id=? 
        ORDER BY c.id ASC
    """, (post_id,)).fetchall()
    
    reactions = c.execute("SELECT type, COUNT(*) as count FROM blog_reactions WHERE post_id=? GROUP BY type", (post_id,)).fetchall()
    
    c.close()
    res = dict(post)
    res['comments'] = [dict(cm) for cm in comments]
    res['reactions'] = {r['type']: r['count'] for r in reactions}
    return res

def add_blog_comment(post_id, tg_id, text):
    c = _conn()
    dt = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO blog_comments (post_id, tg_id, text, timestamp) VALUES (?,?,?,?)", (post_id, tg_id, text, dt))
    c.commit()
    c.close()

def toggle_blog_reaction(post_id, tg_id, rtype):
    c = _conn()
    existing = c.execute("SELECT id FROM blog_reactions WHERE post_id=? AND tg_id=? AND type=?", (post_id, tg_id, rtype)).fetchone()
    if existing:
        c.execute("DELETE FROM blog_reactions WHERE id=?", (existing['id'],))
    else:
        c.execute("INSERT INTO blog_reactions (post_id, tg_id, type) VALUES (?,?,?)", (post_id, tg_id, rtype))
    c.commit()
    c.close()

def get_courses(category=None):
    c = _conn()
    if category:
        rows = c.execute("SELECT * FROM courses WHERE category=?", (category,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM courses").fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_lessons(course_id):
    c = _conn()
    rows = c.execute("SELECT * FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_lesson(lesson_id):
    c = _conn()
    row = c.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    c.close()
    return dict(row) if row else None

def complete_lesson(tg_id, lesson_id):
    c = _conn()
    dt = datetime.datetime.now().isoformat()
    # Check if already exists
    exists = c.execute("SELECT id FROM user_lessons WHERE tg_id=? AND lesson_id=?", (tg_id, lesson_id)).fetchone()
    if exists:
        c.execute("UPDATE user_lessons SET completed=1, last_accessed=? WHERE tg_id=? AND lesson_id=?", (dt, tg_id, lesson_id))
    else:
        c.execute("INSERT INTO user_lessons (tg_id, lesson_id, completed, last_accessed) VALUES (?,?,1,?)", (tg_id, lesson_id, dt))
    c.commit()
    c.close()

def get_user_progress(tg_id):
    c = _conn()
    rows = c.execute("SELECT lesson_id FROM user_lessons WHERE tg_id=? AND completed=1", (tg_id,)).fetchall()
    c.close()
    return [r['lesson_id'] for r in rows]

# ── ADAPTIVE LEARNING HELPERS ──

def get_student_profile(tg_id, course_id):
    c = _conn()
    row = c.execute("SELECT * FROM student_profiles WHERE tg_id=? AND course_id=?", (tg_id, course_id)).fetchone()
    c.close()
    return dict(row) if row else None

def save_student_profile(tg_id, course_id, level, target_score, exam_date, strategy_json):
    c = _conn()
    dt = datetime.datetime.now().isoformat()
    existing = c.execute("SELECT id FROM student_profiles WHERE tg_id=? AND course_id=?", (tg_id, course_id)).fetchone()
    if existing:
        c.execute("""UPDATE student_profiles SET level=?, target_score=?, exam_date=?, strategy_json=?, last_active=?
                     WHERE tg_id=? AND course_id=?""", (level, target_score, exam_date, strategy_json, dt, tg_id, course_id))
    else:
        c.execute("""INSERT INTO student_profiles (tg_id, course_id, level, target_score, exam_date, strategy_json, created_at, last_active)
                     VALUES (?,?,?,?,?,?,?,?)""", (tg_id, course_id, level, target_score, exam_date, strategy_json, dt, dt))
    c.commit()
    c.close()

def get_today_tasks(tg_id, course_id):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    c = _conn()
    rows = c.execute("SELECT * FROM daily_tasks WHERE tg_id=? AND course_id=? AND date=?", (tg_id, course_id, today)).fetchall()
    import json
    res = []
    for r in rows:
        d = dict(r)
        try:
            d['content'] = json.loads(d['content_json']) if d.get('content_json') else {}
        except:
            d['content'] = {}
        res.append(d)
    c.close()
    return res

def save_daily_tasks(tg_id, course_id, tasks_list):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    c = _conn()
    c.execute("DELETE FROM daily_tasks WHERE tg_id=? AND course_id=? AND date=?", (tg_id, course_id, today))
    import json
    for t in tasks_list:
        c.execute("INSERT INTO daily_tasks (tg_id, course_id, date, task_type, content_json) VALUES (?,?,?,?,?)",
                  (tg_id, course_id, today, t['type'], json.dumps(t['content'])))
    c.commit()
    c.close()

def complete_task(task_id, ai_feedback, score):
    c = _conn()
    c.execute("UPDATE daily_tasks SET completed=1, ai_feedback=?, score=? WHERE id=?", (ai_feedback, score, task_id))
    c.commit()
    c.close()

# ── VOCAB BANK HELPERS ──
def add_vocab(tg_id, word, translation, context=''):
    c = _conn()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    existing = c.execute("SELECT id, times_seen FROM vocab_bank WHERE tg_id=? AND LOWER(word)=LOWER(?)", (tg_id, word)).fetchone()
    if existing:
        c.execute("UPDATE vocab_bank SET times_seen=? WHERE id=?", (existing['times_seen'] + 1, existing['id']))
        c.commit()
        c.close()
        return 'duplicate'
    c.execute("INSERT INTO vocab_bank (tg_id, word, translation, context, date_added) VALUES (?,?,?,?,?)",
              (tg_id, word, translation, context, today))
    c.commit()
    c.close()
    return 'added'

def get_vocab(tg_id, date=None, limit=100):
    c = _conn()
    if date:
        rows = c.execute("SELECT * FROM vocab_bank WHERE tg_id=? AND date_added=? ORDER BY id DESC LIMIT ?", (tg_id, date, limit)).fetchall()
    else:
        rows = c.execute("SELECT * FROM vocab_bank WHERE tg_id=? ORDER BY id DESC LIMIT ?", (tg_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_vocab_count_today(tg_id):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    c = _conn()
    count = c.execute("SELECT COUNT(*) FROM vocab_bank WHERE tg_id=? AND date_added=?", (tg_id, today)).fetchone()[0]
    c.close()
    return count

def mark_vocab_mastered(vocab_id, tg_id):
    c = _conn()
    c.execute("UPDATE vocab_bank SET mastered=1 WHERE id=? AND tg_id=?", (vocab_id, tg_id))
    c.commit()
    c.close()

# ── LISTENING SESSION HELPERS ──
def save_listening_session(tg_id, transcript, audio_path, questions_json, blanks_json):
    import json
    c = _conn()
    c.execute("INSERT INTO listening_sessions (tg_id, transcript, audio_path, questions_json, blanks_json) VALUES (?,?,?,?,?)",
              (tg_id, transcript, audio_path,
               json.dumps(questions_json) if not isinstance(questions_json, str) else questions_json,
               json.dumps(blanks_json) if not isinstance(blanks_json, str) else blanks_json))
    c.commit()
    last_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return last_id

def get_listening_session(session_id):
    c = _conn()
    row = c.execute("SELECT * FROM listening_sessions WHERE id=?", (session_id,)).fetchone()
    c.close()
    return dict(row) if row else None

def complete_listening_session(session_id, score):
    c = _conn()
    dt = datetime.datetime.now().isoformat()
    c.execute("UPDATE listening_sessions SET score=?, completed_at=? WHERE id=?", (score, dt, session_id))
    c.commit()
    c.close()


init_db()
