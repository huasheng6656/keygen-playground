"""register-demo 沙盒注册服务（模拟"GitHub 风格"的注册流程）

这个服务只运行在本地 127.0.0.1，数据全部在内存里，专门用于教学。
它模拟了真实注册系统的常见环节：
    1. 图形验证码（这里用数学题代替）
    2. 用户名规则校验 + 唯一性检查
    3. 密码强度校验
    4. 加盐哈希存储密码（PBKDF2）
    5. 邮箱验证码（6 位、10 分钟过期、一次性）
    6. 模拟邮箱收件箱（GET /api/mail/<邮箱> 查收验证码）
    7. IP 速率限制（每分钟最多 5 次注册尝试）
    8. 连续登录失败锁定账号（防暴力破解）

真实网站（如 GitHub）在这些基础上还有 IP 信誉、邮箱域名信誉、真人检测等
更复杂的反滥用手段。本沙盒只保留最核心的教学内容。

运行:
    python register-demo/server.py
然后浏览器打开 http://127.0.0.1:8765 体验网页版注册表单。
"""

import hashlib
import http.server
import json
import os
import re
import secrets
import threading
import time
from urllib.parse import unquote

HOST = "127.0.0.1"
PORT = 8765
STATIC_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")

# ---------------- 内存"数据库" ----------------
USERS = {}        # username -> {password_hash, salt, email, verified, locked_until, failed}
EMAIL_CODES = {}  # username -> {code, expires, used}
MAILBOX = {}      # email -> [{code, expires}]  模拟邮箱收件箱
CAPTCHAS = {}     # captcha_id -> {answer, expires}
IP_HITS = {}      # ip -> [最近1分钟的时间戳]
LOCK = threading.Lock()

# ---------------- 规则常量 ----------------
USERNAME_RE = re.compile(r"^[a-zA-Z0-9-]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CAPTCHA_TTL = 120          # 验证码 2 分钟过期
EMAIL_CODE_TTL = 600       # 邮箱验证码 10 分钟过期
RATE_LIMIT_PER_MIN = 5     # 每 IP 每分钟最多 5 次注册尝试
FAIL_LIMIT = 5             # 连续失败 5 次
FAIL_LOCK_SECONDS = 600    # 锁定 10 分钟


def hash_password(password: str, salt: str) -> str:
    """加盐 PBKDF2 哈希，绝不明文存密码。"""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def make_captcha() -> tuple[str, str]:
    """生成一道数学题验证码，返回 (id, 题目)。"""
    a = secrets.randbelow(10) + 1
    b = secrets.randbelow(10) + 1
    cid = secrets.token_hex(8)
    with LOCK:
        CAPTCHAS[cid] = {"answer": str(a + b), "expires": time.time() + CAPTCHA_TTL}
    return cid, f"{a} + {b} = ?"


def rate_limited(ip: str) -> bool:
    """简单的滑动窗口限流。"""
    now = time.time()
    with LOCK:
        hits = [t for t in IP_HITS.get(ip, []) if now - t < 60]
        hits.append(now)
        IP_HITS[ip] = hits
        return len(hits) > RATE_LIMIT_PER_MIN


def validate_captcha(cid, answer) -> str | None:
    """校验验证码，通过返回 None，失败返回错误信息。"""
    with LOCK:
        cap = CAPTCHAS.pop(cid, None)  # 一次性
    if cap is None:
        return "验证码不存在"
    if cap["expires"] < time.time():
        return "验证码已过期，请重新获取"
    if str(answer).strip() != cap["answer"]:
        return "验证码错误"
    return None


def do_register(data: dict, ip: str) -> tuple[int, dict]:
    # 1. 验证码
    err = validate_captcha(data.get("captcha_id", ""), data.get("captcha_answer", ""))
    if err:
        return 400, {"error": err}
    # 2. 限流
    if rate_limited(ip):
        return 429, {"error": "尝试过于频繁，请 1 分钟后再试"}
    # 3. 用户名规则 + 唯一性 + 锁定状态
    username = data.get("username", "")
    if not USERNAME_RE.match(username):
        return 400, {"error": "用户名需为 3-20 位字母/数字/横线"}
    with LOCK:
        existing = USERS.get(username)
        if existing and existing["locked_until"] > time.time():
            return 403, {"error": "该用户名已被临时锁定"}
        if existing:
            return 400, {"error": "用户名已被占用"}
    # 4. 密码强度
    password = data.get("password", "")
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if len(password) < 8 or not (has_lower and has_upper and has_digit):
        return 400, {"error": "密码至少 8 位，且需包含大写、小写字母和数字"}
    # 5. 邮箱格式
    email = data.get("email", "")
    if not EMAIL_RE.match(email):
        return 400, {"error": "邮箱格式不正确"}
    # 6. 创建账号 + 邮箱验证码 + 投递到"模拟收件箱"
    salt = secrets.token_hex(16)
    code = f"{secrets.randbelow(1_000_000):06d}"
    with LOCK:
        USERS[username] = {
            "password_hash": hash_password(password, salt),
            "salt": salt,
            "email": email,
            "verified": False,
            "locked_until": 0,
            "failed": 0,
        }
        EMAIL_CODES[username] = {"code": code, "expires": time.time() + EMAIL_CODE_TTL, "used": False}
        MAILBOX.setdefault(email, []).append({"code": code, "expires": time.time() + EMAIL_CODE_TTL})
    return 200, {
        "message": "注册成功，请验证邮箱",
        "need_email_verify": True,
        "email": email,
        "debug_email_code": code,  # 沙盒兜底：省去查收邮箱这一步
    }


def do_verify_email(data: dict) -> tuple[int, dict]:
    username = data.get("username", "")
    code = str(data.get("code", "")).strip()
    with LOCK:
        rec = EMAIL_CODES.get(username)
        if rec is None:
            return 400, {"error": "没有找到该用户的验证码"}
        if rec["used"]:
            return 400, {"error": "验证码已使用"}
        if rec["expires"] < time.time():
            return 400, {"error": "验证码已过期"}
        if rec["code"] != code:
            return 400, {"error": "验证码错误"}
        rec["used"] = True
        USERS[username]["verified"] = True
    return 200, {"message": "邮箱验证成功", "username": username, "token": secrets.token_hex(16)}


def do_mail(email: str) -> tuple[int, dict]:
    """模拟邮箱收件箱：返回该邮箱未过期的验证码。"""
    now = time.time()
    with LOCK:
        codes = [c for c in MAILBOX.get(email, []) if c["expires"] > now]
    return 200, {"email": email, "codes": codes}


def do_login(data: dict) -> tuple[int, dict]:
    """登录接口：演示密码哈希校验 + 防爆破锁定。"""
    username = data.get("username", "")
    password = data.get("password", "")
    with LOCK:
        user = USERS.get(username)
        if user is None:
            return 401, {"error": "用户名或密码错误"}
        if user["locked_until"] > time.time():
            return 403, {"error": "连续失败次数过多，账号已临时锁定"}
        if hash_password(password, user["salt"]) != user["password_hash"]:
            user["failed"] += 1
            if user["failed"] >= FAIL_LIMIT:
                user["locked_until"] = time.time() + FAIL_LOCK_SECONDS
                return 403, {"error": "连续失败次数过多，账号已临时锁定"}
            return 401, {"error": "用户名或密码错误"}
        user["failed"] = 0
        if not user["verified"]:
            return 403, {"error": "请先完成邮箱验证"}
    return 200, {"message": "登录成功", "username": username}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[server]", fmt % args)

    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_index(self):
        try:
            with open(STATIC_INDEX, "rb") as f:
                body = f.read()
        except OSError:
            self._send(500, {"error": "static/index.html not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_index()
        elif self.path == "/api/captcha":
            cid, question = make_captcha()
            self._send(200, {"id": cid, "question": question})
        elif self.path == "/api/health":
            self._send(200, {"ok": True})
        elif self.path.startswith("/api/mail/"):
            email = unquote(self.path[len("/api/mail/"):])
            self._send(*do_mail(email))
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._send(400, {"error": "请求体必须是 JSON"})
            return
        ip = self.client_address[0]
        if self.path == "/api/register":
            self._send(*do_register(data, ip))
        elif self.path == "/api/verify-email":
            self._send(*do_verify_email(data))
        elif self.path == "/api/login":
            self._send(*do_login(data))
        else:
            self._send(404, {"error": "not found"})


def make_server(port: int = PORT):
    return http.server.ThreadingHTTPServer((HOST, port), Handler)


def main() -> int:
    server = make_server()
    print(f"register-demo 沙盒服务已启动: http://{HOST}:{server.server_address[1]}")
    print("打开浏览器访问上面的地址体验网页版注册表单。")
    print("按 Ctrl+C 停止。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
