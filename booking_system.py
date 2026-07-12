import sqlite3
import datetime
import hashlib
import os

class BookingSystem:
    def __init__(self, db_path="booking_system.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 升级 users 表，增加密码哈希和盐值
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS barbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                barber_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                hour INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'confirmed', 'cancelled')),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(barber_id) REFERENCES barbers(id)
            )
        ''')
        
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_active_bookings 
            ON bookings(barber_id, date, hour) 
            WHERE status != 'cancelled'
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(date)')
        
        conn.commit()
        conn.close()

    def _get_current_warsaw_time(self):
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Warsaw")
        return datetime.datetime.now(tz)

    # 密码学处理函数
    def _hash_password(self, password: str, salt: bytes = None) -> tuple[str, str]:
        """使用 PBKDF2 算法对密码进行加盐哈希，防止彩虹表攻击"""
        if salt is None:
            salt = os.urandom(16)  # 生成 16 字节的安全随机盐
        # 使用 SHA256 迭代 100,000 次进行加密
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return key.hex(), salt.hex()

    #真正的注册与登录控制
    def register_user(self, username, password) -> bool:
        """注册新用户：校验重名，安全存储密码哈希"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 1. 密码加盐哈希
            password_hash, salt = self._hash_password(password)
            # 2. 插入数据库
            cursor.execute(
                'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
                (username, password_hash, salt)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 用户名已存在
            return False
        finally:
            conn.close()

    def verify_user(self, username, password) -> bool:
        """登录验证：读取盐值并比对密码哈希"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT password_hash, salt FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if not row:
                return False
            
            stored_hash, stored_salt = row
            # 使用提取出的盐值，重新对输入的密码加密
            test_hash, _ = self._hash_password(password, bytes.fromhex(stored_salt))
            
            # 安全比对哈希值是否一致
            return hmac_compare_digest(stored_hash, test_hash)
        finally:
            conn.close()

    def get_or_create_barber(self, barber_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR IGNORE INTO barbers (name) VALUES (?)', (barber_name,))
            conn.commit()
            cursor.execute('SELECT id FROM barbers WHERE name = ?', (barber_name,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def create_booking(self, username, barber_name, date, hour):
        # 通过 username 查找用户
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return None
        
        user_id = user_row[0]
        barber_id = self.get_or_create_barber(barber_name)
        
        try:
            cursor.execute('''
                INSERT INTO bookings (user_id, barber_id, date, hour, status) 
                VALUES (?, ?, ?, ?, 'pending')
            ''', (user_id, barber_id, date, hour))
            
            booking_id = cursor.lastrowid
            conn.commit()
            return booking_id
        except sqlite3.IntegrityError:
            conn.rollback()
            return None
        except Exception as e:
            conn.rollback()
            print(f"Database error during creation: {e}")
            return None
        finally:
            conn.close()

    def confirm_booking(self, booking_id, username):
        conn = self._get_connection()
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT b.date, b.hour, b.status FROM bookings b
                JOIN users u ON b.user_id = u.id
                WHERE b.id = ? AND u.username = ?
            ''', (booking_id, username))
            result = cursor.fetchone()
            
            if not result or result[2] != 'pending':
                return False
                
            booking_date_str, booking_hour, _ = result
            now = self._get_current_warsaw_time()
            today_str = now.strftime("%Y-%m-%d")
            current_hour = now.hour
            
            if booking_date_str < today_str or (booking_date_str == today_str and booking_hour < current_hour):
                return False
                
            cursor.execute('UPDATE bookings SET status = "confirmed" WHERE id = ?', (booking_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()

    def cancel_booking(self, booking_id, username):
        conn = self._get_connection()
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT b.date, b.hour, b.status FROM bookings b
                JOIN users u ON b.user_id = u.id
                WHERE b.id = ? AND u.username = ?
            ''', (booking_id, username))
            result = cursor.fetchone()
            
            if not result or result[2] == 'cancelled':
                return False
                
            booking_date_str, booking_hour, _ = result
            now = self._get_current_warsaw_time()
            today_str = now.strftime("%Y-%m-%d")
            current_hour = now.hour
            
            if booking_date_str < today_str or (booking_date_str == today_str and booking_hour <= current_hour):
                return False
                
            cursor.execute('UPDATE bookings SET status = "cancelled" WHERE id = ?', (booking_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_user_bookings(self, username):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return []
        
        cursor.execute('''
            SELECT b.id, br.name, b.date, b.hour, b.status 
            FROM bookings b
            JOIN barbers br ON b.barber_id = br.id
            WHERE b.user_id = ? AND b.status != 'cancelled'
            ORDER BY b.date DESC, b.hour DESC
        ''', (user_row[0],))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "barber": r[1], "date": r[2], "hour": r[3], "status": r[4]} for r in rows]

    def get_availability(self, barber_name: str, date_str: str) -> list:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM barbers WHERE name = ?", (barber_name,))
            barber_row = cursor.fetchone()

            if not barber_row:
                return [{"hour": h, "status": "free"} for h in range(9, 18)]

            barber_id = barber_row[0]

            cursor.execute(
                "SELECT hour FROM bookings WHERE barber_id = ? AND date = ? AND status != 'cancelled'",
                (barber_id, date_str)
            )
            taken_hours = {row[0] for row in cursor.fetchall()}

            return [{"hour": h, "status": "taken" if h in taken_hours else "free"} for h in range(9, 18)]
        finally:
            conn.close()

def hmac_compare_digest(a, b):
    """防止计时攻击的时序恒定字符串比对方法"""
    return hashlib.pbkdf2_hmac('sha256', a.encode(), b'', 1) == hashlib.pbkdf2_hmac('sha256', b.encode(), b'', 1)
