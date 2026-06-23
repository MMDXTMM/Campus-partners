#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import uuid
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "campus_buddy.db")
INTERESTS = ["阅读","运动","音乐","电影","游戏","摄影","旅行","美食","编程","设计","绘画","写作","舞蹈","乐器","健身","跑步","篮球","足球","羽毛球","乒乓球","网球","游泳","瑜伽","烹饪","手工","动漫","追星","宠物","学习","考研","考公","实习","创业","理财","英语","日语","韩语","吉他","钢琴","唱歌"]
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, salt TEXT NOT NULL, nickname TEXT NOT NULL, gender TEXT DEFAULT 'secret', age INTEGER DEFAULT 0, school TEXT DEFAULT '', department TEXT DEFAULT '', grade TEXT DEFAULT '', interests TEXT DEFAULT '[]', preferences TEXT DEFAULT '{}', goal_intensity TEXT DEFAULT 'light', time_rhythm TEXT DEFAULT 'flexible', interaction_style TEXT DEFAULT 'relaxed', contact_wechat TEXT DEFAULT '', contact_qq TEXT DEFAULT '', contact_phone TEXT DEFAULT '', coins INTEGER DEFAULT 10, avatar_color TEXT DEFAULT '#6C63FF', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS match_rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, user1_id INTEGER NOT NULL, user2_id INTEGER NOT NULL, match_type TEXT NOT NULL, status TEXT DEFAULT 'active', ended_by INTEGER, ended_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER NOT NULL, sender_id INTEGER NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER NOT NULL, rater_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def generate_token():
    return str(uuid.uuid4())

def get_user_id_from_token(token):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id FROM tokens WHERE token = ? AND created_at > ?', (token, datetime.now() - timedelta(days=7)))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id,username,nickname,gender,age,school,department,grade,interests,preferences,goal_intensity,time_rhythm,interaction_style,contact_wechat,contact_qq,contact_phone,coins,avatar_color,created_at FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {'id':row[0],'username':row[1],'nickname':row[2],'gender':row[3],'age':row[4],'school':row[5],'department':row[6],'grade':row[7],'interests':json.loads(row[8]),'preferences':json.loads(row[9]),'goal_intensity':row[10],'time_rhythm':row[11],'interaction_style':row[12],'contact_wechat':row[13],'contact_qq':row[14],'contact_phone':row[15],'coins':row[16],'avatar_color':row[17],'created_at':row[18]}

def get_other_user_in_room(room_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user1_id,user2_id FROM match_rooms WHERE id = ?', (room_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    other_id = row[1] if row[0] == user_id else row[0]
    return get_user_by_id(other_id)

def get_last_message(room_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT content FROM messages WHERE room_id = ? ORDER BY id DESC LIMIT 1', (room_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ''

def get_matches(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id,user1_id,user2_id,match_type,status,created_at FROM match_rooms WHERE user1_id = ? OR user2_id = ? ORDER BY created_at DESC', (user_id, user_id))
    rows = c.fetchall()
    conn.close()
    matches = []
    for row in rows:
        room_id,u1,u2,mtype,status,created = row
        other_user = get_user_by_id(u2 if u1 == user_id else u1)
        matches.append({'room_id':room_id,'match_type':mtype,'status':status,'created_at':created,'other_user':other_user,'last_message':get_last_message(room_id)})
    return matches
class APIHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_json({}, 200)

    def parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        try:
            return json.loads(body)
        except:
            return {}

    def get_token(self):
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:]
        cookie = self.headers.get('Cookie', '')
        for part in cookie.split(';'):
            if 'token=' in part:
                return part.split('=')[1].strip()
        return None

    def require_auth(self):
        token = self.get_token()
        user_id = get_user_id_from_token(token)
        if not user_id:
            self.send_json({'error': 'Unauthorized'}, 401)
            return None
        return user_id
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/register':
            data = self.parse_body()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            nickname = data.get('nickname', '').strip()
            school = data.get('school', '')
            department = data.get('department', '')
            grade = data.get('grade', '')
            interests = data.get('interests', [])
            preferences = data.get('preferences', '{}')
            if not username or not password or not nickname:
                self.send_json({'error': 'Missing fields'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute('SELECT id FROM users WHERE username = ?', (username,))
                if c.fetchone():
                    self.send_json({'error': 'Username exists'}, 400)
                    return
                salt = str(uuid.uuid4())[:8]
                password_hash = hash_password(password, salt)
                c.execute('INSERT INTO users (username, password_hash, salt, nickname, school, department, grade, interests, preferences) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (username, password_hash, salt, nickname, school, department, grade, json.dumps(interests), preferences))
                conn.commit()
                self.send_json({'message': 'Register success'}, 201)
            except Exception as e:
                conn.rollback()
                self.send_json({'error': str(e)}, 500)
            finally:
                conn.close()

        elif path == '/api/login':
            data = self.parse_body()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id, password_hash, salt FROM users WHERE username = ?', (username,))
            row = c.fetchone()
            conn.close()
            if not row:
                self.send_json({'error': 'Invalid credentials'}, 401)
                return
            user_id, stored_hash, salt = row
            if hash_password(password, salt) != stored_hash:
                self.send_json({'error': 'Invalid credentials'}, 401)
                return
            token = generate_token()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO tokens (token, user_id) VALUES (?, ?)', (token, user_id))
            conn.commit()
            conn.close()
            user = get_user_by_id(user_id)
            self.send_json({'token': token, 'user': user}, 200)
        elif path == '/api/matching/random':
            user_id = self.require_auth()
            if not user_id:
                return
            user = get_user_by_id(user_id)
            if user['coins'] < 1:
                self.send_json({'error': 'Insufficient coins'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE id != ? ORDER BY RANDOM() LIMIT 1', (user_id,))
            row = c.fetchone()
            conn.close()
            if not row:
                self.send_json({'error': 'No users available'}, 400)
                return
            other_id = row[0]
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute('INSERT INTO match_rooms (user1_id, user2_id, match_type) VALUES (?, ?, ?)', (user_id, other_id, 'random'))
                room_id = c.lastrowid
                c.execute('UPDATE users SET coins = coins - 1 WHERE id = ?', (user_id,))
                c.execute('INSERT INTO messages (room_id, sender_id, content) VALUES (?, ?, ?)', (room_id, 0, '匹配成功！开始聊天吧~'))
                conn.commit()
                other_user = get_user_by_id(other_id)
                self.send_json({'room_id': room_id, 'other_user': other_user}, 200)
            except Exception as e:
                conn.rollback()
                self.send_json({'error': str(e)}, 500)
            finally:
                conn.close()

        elif path == '/api/matching/targeted':
            user_id = self.require_auth()
            if not user_id:
                return
            user = get_user_by_id(user_id)
            if user['coins'] < 3:
                self.send_json({'error': 'Insufficient coins'}, 400)
                return
            data = self.parse_body()
            interests = data.get('interests', [])
            gender = data.get('gender', '')
            age_min = data.get('age_min', 0)
            age_max = data.get('age_max', 100)
            school = data.get('school', '')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            query = 'SELECT id, interests FROM users WHERE id != ?'
            params = [user_id]
            if gender:
                query += ' AND gender = ?'
                params.append(gender)
            if age_min > 0:
                query += ' AND age >= ?'
                params.append(age_min)
            if age_max < 100:
                query += ' AND age <= ?'
                params.append(age_max)
            if school:
                query += ' AND school LIKE ?'
                params.append('%' + school + '%')
            c.execute(query, params)
            rows = c.fetchall()
            if interests:
                candidates = []
                for uid, u_interests in rows:
                    u_ints = set(json.loads(u_interests))
                    match_count = len(set(interests) & u_ints)
                    if match_count > 0:
                        candidates.append((uid, match_count))
                candidates.sort(key=lambda x: -x[1])
                if candidates:
                    other_id = candidates[0][0]
                else:
                    self.send_json({'error': 'No matching users'}, 400)
                    conn.close()
                    return
            else:
                if rows:
                    other_id = rows[0][0]
                else:
                    self.send_json({'error': 'No matching users'}, 400)
                    conn.close()
                    return
            try:
                c.execute('INSERT INTO match_rooms (user1_id, user2_id, match_type) VALUES (?, ?, ?)', (user_id, other_id, 'targeted'))
                room_id = c.lastrowid
                c.execute('UPDATE users SET coins = coins - 3 WHERE id = ?', (user_id,))
                c.execute('INSERT INTO messages (room_id, sender_id, content) VALUES (?, ?, ?)', (room_id, 0, '定向匹配成功！开始聊天吧~'))
                conn.commit()
                other_user = get_user_by_id(other_id)
                self.send_json({'room_id': room_id, 'other_user': other_user}, 200)
            except Exception as e:
                conn.rollback()
                self.send_json({'error': str(e)}, 500)
            finally:
                conn.close()
        elif path == '/api/messages':
            user_id = self.require_auth()
            if not user_id:
                return
            data = self.parse_body()
            room_id = data.get('room_id')
            content = data.get('content', '').strip()
            if not room_id or not content:
                self.send_json({'error': 'Missing fields'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT status FROM match_rooms WHERE id = ? AND (user1_id = ? OR user2_id = ?)', (room_id, user_id, user_id))
            row = c.fetchone()
            if not row or row[0] != 'active':
                self.send_json({'error': 'Room not active'}, 400)
                conn.close()
                return
            try:
                c.execute('INSERT INTO messages (room_id, sender_id, content) VALUES (?, ?, ?)', (room_id, user_id, content))
                conn.commit()
                self.send_json({'message': 'Message sent'}, 200)
            except Exception as e:
                conn.rollback()
                self.send_json({'error': str(e)}, 500)
            finally:
                conn.close()

        elif path == '/api/room/end':
            user_id = self.require_auth()
            if not user_id:
                return
            data = self.parse_body()
            room_id = data.get('room_id')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute('UPDATE match_rooms SET status = ?, ended_by = ?, ended_at = ? WHERE id = ? AND (user1_id = ? OR user2_id = ?)', ('ended', user_id, datetime.now(), room_id, user_id, user_id))
                if c.rowcount == 0:
                    self.send_json({'error': 'Room not found or not yours'}, 400)
                else:
                    conn.commit()
                    self.send_json({'message': 'Room ended'}, 200)
            except Exception as e:
                conn.rollback()
                self.send_json({'error': str(e)}, 500)
            finally:
                conn.close()

        elif path == '/api/room/rate':
            user_id = self.require_auth()
            if not user_id:
                return
            data = self.parse_body()
            room_id = data.get('room_id')
            rating = data.get('rating')
            comment = data.get('comment', '')
            if not room_id or not rating or rating < 1 or rating > 5:
                self.send_json({'error': 'Invalid rating'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute('SELECT status FROM match_rooms WHERE id = ? AND (user1_id = ? OR user2_id = ?)', (room_id, user_id, user_id))
                row = c.fetchone()
                if not row or row[0] != 'ended':
                    self.send_json({'error': 'Room not ended'}, 400)
                    conn.close()
                    return
                c.execute('SELECT id FROM ratings WHERE room_id = ? AND rater_id = ?', (room_id, user_id))
                if c.fetchone():
                    self.send_json({'error': 'Already rated'}, 400)
                    conn.close()
                    return
                c.execute('INSERT INTO ratings (room_id, rater_id, rating, comment) VALUES (?, ?, ?, ?)', (room_id, user_id, rating, comment))
                conn.commit()
                self.send_json({'message': 'Rating submitted'}, 200)
            except Exception as e:
                conn.rollback()
                self.send_json({'error': str(e)}, 500)
            finally:
                conn.close()

        else:
            self.send_json({'error': 'Not found'}, 404)
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/api/interests':
            self.send_json({'interests': INTERESTS}, 200)

        elif path == '/api/profile':
            user_id = self.require_auth()
            if not user_id:
                return
            user = get_user_by_id(user_id)
            self.send_json(user, 200)

        elif path == '/api/matches':
            user_id = self.require_auth()
            if not user_id:
                return
            matches = get_matches(user_id)
            self.send_json(matches, 200)

        elif path == '/api/matches/active':
            user_id = self.require_auth()
            if not user_id:
                return
            matches = [m for m in get_matches(user_id) if m['status'] == 'active']
            self.send_json(matches, 200)

        elif path == '/api/messages':
            user_id = self.require_auth()
            if not user_id:
                return
            room_id = params.get('room_id', [None])[0]
            after_id = params.get('after_id', [0])[0]
            if not room_id:
                self.send_json({'error': 'Missing room_id'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id, sender_id, content, created_at FROM messages WHERE room_id = ? AND id > ? ORDER BY id ASC', (room_id, after_id))
            rows = c.fetchall()
            conn.close()
            messages = []
            for row in rows:
                messages.append({'id': row[0], 'sender_id': row[1], 'content': row[2], 'created_at': row[3]})
            self.send_json(messages, 200)
        elif path == '/api/room/status':
            user_id = self.require_auth()
            if not user_id:
                return
            room_id = params.get('room_id', [None])[0]
            if not room_id:
                self.send_json({'error': 'Missing room_id'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT status, created_at FROM match_rooms WHERE id = ?', (room_id,))
            room_row = c.fetchone()
            if not room_row:
                self.send_json({'error': 'Room not found'}, 404)
                conn.close()
                return
            c.execute('SELECT rater_id, rating, comment FROM ratings WHERE room_id = ?', (room_id,))
            ratings = []
            for row in c.fetchall():
                ratings.append({'rater_id': row[0], 'rating': row[1], 'comment': row[2]})
            conn.close()
            self.send_json({'status': room_row[0], 'created_at': room_row[1], 'ratings': ratings}, 200)

        elif path == '/api/room/contact':
            user_id = self.require_auth()
            if not user_id:
                return
            room_id = params.get('room_id', [None])[0]
            if not room_id:
                self.send_json({'error': 'Missing room_id'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT status, user1_id, user2_id FROM match_rooms WHERE id = ?', (room_id,))
            room_row = c.fetchone()
            if not room_row:
                self.send_json({'error': 'Room not found'}, 404)
                conn.close()
                return
            status, u1, u2 = room_row
            other_id = u2 if u1 == user_id else u1
            c.execute('SELECT rating FROM ratings WHERE room_id = ?', (room_id,))
            ratings = [row[0] for row in c.fetchall()]
            conn.close()
            if len(ratings) < 2:
                self.send_json({'error': 'Waiting for other to rate'}, 400)
                return
            if any(r < 4 for r in ratings):
                self.send_json({'error': 'Rating below 4'}, 400)
                return
            other_user = get_user_by_id(other_id)
            self.send_json({'nickname': other_user['nickname'], 'wechat': other_user['contact_wechat'], 'qq': other_user['contact_qq'], 'phone': other_user['contact_phone']}, 200)

        elif path == '/api/coin/balance':
            user_id = self.require_auth()
            if not user_id:
                return
            user = get_user_by_id(user_id)
            self.send_json({'coins': user['coins']}, 200)

        elif path == '/api/user/ratings':
            user_id = self.require_auth()
            if not user_id:
                return
            target_user_id = params.get('user_id', [None])[0]
            if not target_user_id:
                self.send_json({'error': 'Missing user_id'}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT r.rating, r.comment, r.created_at FROM ratings r JOIN match_rooms m ON r.room_id = m.id WHERE (m.user1_id = ? OR m.user2_id = ?) AND r.rater_id != ?', (target_user_id, target_user_id, target_user_id))
            rows = c.fetchall()
            conn.close()
            ratings = []
            for row in rows:
                ratings.append({'rating': row[0], 'comment': row[1], 'created_at': row[2]})
            self.send_json(ratings, 200)
        elif path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            with open(os.path.join(os.path.dirname(__file__), 'templates', 'index.html'), 'rb') as f:
                self.wfile.write(f.read())

        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/profile':
            user_id = self.require_auth()
            if not user_id:
                return
            data = self.parse_body()
            nickname = data.get('nickname')
            gender = data.get('gender')
            age = data.get('age')
            school = data.get('school')
            department = data.get('department')
            grade = data.get('grade')
            interests = data.get('interests')
            preferences = data.get('preferences')
            goal_intensity = data.get('goal_intensity')
            time_rhythm = data.get('time_rhythm')
            interaction_style = data.get('interaction_style')
            contact_wechat = data.get('contact_wechat')
            contact_qq = data.get('contact_qq')
            contact_phone = data.get('contact_phone')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                updates = []
                params = []
                if nickname:
                    updates.append('nickname = ?')
                    params.append(nickname)
                if gender:
                    updates.append('gender = ?')
                    params.append(gender)
                if age:
                    updates.append('age = ?')
                    params.append(age)
                if school:
                    updates.append('school = ?')
                    params.append(school)
                if department:
                    updates.append('department = ?')
                    params.append(department)
                if grade:
                    updates.append('grade = ?')
                    params.append(grade)
                if interests:
                    updates.append('interests = ?')
                    params.append(json.dumps(interests))
                if preferences:
                    updates.append('preferences = ?')
                    params.append(preferences)
                if goal_intensity:
                    updates.append('goal_intensity = ?')
                    params.append(goal_intensity)
                if time_rhythm:
                    updates.append('time_rhythm = ?')
                    params.append(time_rhythm)
                if interaction_style:
                    updates.append('interaction_style = ?')
                    params.append(interaction_style)
                if contact_wechat:
                    updates.append('contact_wechat = ?')
                    params.append(contact_wechat)
                if contact_qq:
                    updates.append('contact_qq = ?')
                    params.append(contact_qq)
                if contact_phone:
                    updates.append('contact_phone = ?')
                    params.append(contact_phone)
                if updates:
                    params.append(user_id)
                    c.execute('UPDATE users SET ' + ', '.join(updates) + ' WHERE id = ?', params)
                    conn.commit()
                user = get_user_by_id(user_id)
                self.send_json(user, 200)
            except Exception as e:
                conn.rollback()
                self.send_json({'error': str(e)}, 500)
            finally:
                conn.close()

        else:
            self.send_json({'error': 'Not found'}, 404)

def main():
    init_db()
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print('Server running on http://0.0.0.0:' + str(port))
    server.serve_forever()

if __name__ == '__main__':
    main()