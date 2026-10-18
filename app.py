import hashlib, hmac, os, re, secrets, sqlite3, threading
from flask import Flask, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(BASE, "public")
DB = os.path.join(BASE, "crm.db")
ROLES = {"Admin", "Quản lý", "Sales", "CSKH"}
PORT = 8080

app = Flask(__name__)
app.json.ensure_ascii = False          # trả tiếng Việt có dấu

# ---------- CSDL ----------
def q(sql, params=()):
    """Chạy câu SQL có tham số (chống SQL injection). Trả về danh sách dòng."""
    con = sqlite3.connect(DB)
    try:
        rows = con.execute(sql, params).fetchall()
        con.commit()
        return rows
    finally:
        con.close()

def init_db():
    q("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
         full_name TEXT NOT NULL, role TEXT NOT NULL, pass_hash TEXT NOT NULL, salt TEXT NOT NULL,
         active INTEGER DEFAULT 1, must_change INTEGER DEFAULT 1)""")
    if q("SELECT COUNT(*) FROM users")[0][0] == 0:      # tài khoản mẫu cho lần chạy đầu
        add_user("admin", "Quản trị viên", "Admin", "admin123", False)
        add_user("sales", "Nhân viên kinh doanh", "Sales", "sales123", False)

# ---------- Mật khẩu: PBKDF2-HMAC-SHA256, 100.000 vòng, mỗi người một salt (giống bản C++) ----------
def hash_pw(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100000, 32).hex()

def temp_pw():
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(10))

def add_user(username, name, role, pw, must):
    salt = secrets.token_hex(16)
    try:
        q("INSERT INTO users(username,full_name,role,pass_hash,salt,must_change) VALUES(?,?,?,?,?,?)",
          (username, name, role, hash_pw(pw, salt), salt, 1 if must else 0))
        return True
    except sqlite3.IntegrityError:
        return False

def set_pw(uid, pw, must):
    salt = secrets.token_hex(16)
    q("UPDATE users SET pass_hash=?,salt=?,must_change=? WHERE id=?", (hash_pw(pw, salt), salt, 1 if must else 0, uid))

# ---------- Phiên đăng nhập (lưu trong bộ nhớ, gửi qua cookie HttpOnly) ----------
sessions, s_lock = {}, threading.Lock()

def current():
    with s_lock:
        return sessions.get(request.cookies.get("sid", ""))

def drop_sessions(uid):
    with s_lock:
        for t in [t for t, s in sessions.items() if s["id"] == uid]:
            del sessions[t]

def err(code, msg):
    return jsonify(ok=False, message=msg), code

def body():
    d = request.get_json(force=True, silent=True)
    return d if isinstance(d, dict) else None

def text(d, key):
    v = d.get(key)
    return v if isinstance(v, str) else ""

def need(admin=False):
    """Trả về (phiên, None) nếu hợp lệ, hoặc (None, phản hồi lỗi)."""
    s = current()
    if not s:
        return None, err(401, "Chưa đăng nhập")
    if admin and s["role"] != "Admin":
        return None, err(403, "Bạn không có quyền thực hiện thao tác này")
    return s, None

# ---------- Trang tĩnh ----------
@app.get("/")
def index():
    return send_from_directory(PUBLIC, "SignUp_LogIn_Form.html", max_age=0)

@app.get("/<path:name>")
def static_file(name):
    return send_from_directory(PUBLIC, name, max_age=0)    # an toàn trước đường dẫn ../

# ---------- API ----------
@app.post("/api/login")
def login():
    d = body()
    if d is None:
        return err(400, "Dữ liệu không hợp lệ")
    u = text(d, "username")
    r = q("SELECT id,full_name,role,pass_hash,salt,active,must_change FROM users WHERE username=?", (u,))
    if not r or not hmac.compare_digest(r[0][3], hash_pw(text(d, "password"), r[0][4])):
        return err(401, "Sai tên đăng nhập hoặc mật khẩu")
    if r[0][5] != 1:
        return err(403, "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên")
    tok = secrets.token_hex(32)
    with s_lock:
        sessions[tok] = {"id": r[0][0], "user": u, "name": r[0][1], "role": r[0][2]}
    resp = jsonify(ok=True, fullName=r[0][1], role=r[0][2], mustChange=r[0][6] == 1)
    resp.set_cookie("sid", tok, httponly=True, samesite="Strict", path="/")
    return resp

@app.post("/api/logout")
def logout():
    with s_lock:
        sessions.pop(request.cookies.get("sid", ""), None)
    resp = jsonify(ok=True)
    resp.set_cookie("sid", "", max_age=0, path="/")
    return resp

@app.get("/api/me")
def me():
    s, e = need()
    if e: return e
    r = q("SELECT must_change FROM users WHERE id=?", (s["id"],))
    return jsonify(ok=True, username=s["user"], fullName=s["name"], role=s["role"], mustChange=bool(r and r[0][0] == 1))

@app.post("/api/password")
def change_password():
    s, e = need()
    if e: return e
    d = body()
    if d is None: return err(400, "Dữ liệu không hợp lệ")
    r = q("SELECT pass_hash,salt FROM users WHERE id=?", (s["id"],))
    if not r or not hmac.compare_digest(r[0][0], hash_pw(text(d, "oldPassword"), r[0][1])):
        return err(400, "Mật khẩu hiện tại không đúng")
    new = text(d, "newPassword")
    if len(new) < 8: return err(400, "Mật khẩu mới phải có ít nhất 8 ký tự")
    set_pw(s["id"], new, False)
    return jsonify(ok=True)

@app.get("/api/users")
def list_users():
    s, e = need(admin=True)
    if e: return e
    rows = q("SELECT id,username,full_name,role,active,must_change FROM users ORDER BY id")
    return jsonify(ok=True, users=[dict(id=r[0], username=r[1], fullName=r[2], role=r[3],
                                        active=r[4] == 1, mustChange=r[5] == 1) for r in rows])

@app.post("/api/users")
def create_user():
    s, e = need(admin=True)
    if e: return e
    d = body()
    if d is None: return err(400, "Dữ liệu không hợp lệ")
    u, name, role = text(d, "username"), text(d, "fullName"), text(d, "role")
    if not re.fullmatch(r"[A-Za-z0-9_.]{3,30}", u) or not name or len(name) > 80 or role not in ROLES:
        return err(400, "Thông tin không hợp lệ (tên đăng nhập 3-30 ký tự: chữ, số, _ hoặc .)")
    pw = temp_pw()
    if not add_user(u, name, role, pw, True):
        return err(409, "Tên đăng nhập đã tồn tại")
    return jsonify(ok=True, tempPassword=pw)

@app.post("/api/users/<int:uid>/reset")
def reset_user(uid):
    s, e = need(admin=True)
    if e: return e
    if not q("SELECT id FROM users WHERE id=?", (uid,)):
        return err(404, "Không tìm thấy tài khoản")
    pw = temp_pw(); set_pw(uid, pw, True); drop_sessions(uid)
    return jsonify(ok=True, tempPassword=pw)

@app.post("/api/users/<int:uid>/toggle")
def toggle_user(uid):
    s, e = need(admin=True)
    if e: return e
    if uid == s["id"]:
        return err(400, "Không thể khóa chính tài khoản đang đăng nhập")
    r = q("SELECT active FROM users WHERE id=?", (uid,))
    if not r: return err(404, "Không tìm thấy tài khoản")
    now_active = r[0][0] != 1
    q("UPDATE users SET active=? WHERE id=?", (1 if now_active else 0, uid))
    if not now_active: drop_sessions(uid)
    return jsonify(ok=True, active=now_active)

if __name__ == "__main__":
    init_db()
    print(f"CRM đang chạy tại http://localhost:{PORT}  (Ctrl+C để dừng)")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
