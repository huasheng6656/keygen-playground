"""学习版"注册机"——自动注册客户端（仅针对本地 register-demo 沙盒）

这段代码演示"自动注册工具"的核心写法：
    1. 自动获取图形验证码并"解题"（真实场景对应 OCR / 打码平台）
    2. 自动生成用户名/密码/邮箱并提交注册表单
    3. 解析 JSON 响应、处理各种校验错误
    4. 从"邮箱"取出验证码完成验证（沙盒里服务器直接把码放在响应中）
    5. 遇到 429 限流时指数退避重试
    6. 注册完成后自动登录，证明账号真的可用

重要声明：
    本脚本只能连本地 register-demo 沙盒。真实网站（GitHub 等）有验证码、
    IP 信誉、邮箱域名信誉等反滥用机制，批量自动注册违反其服务条款，
    本脚本的教学代码绝不适用于真实网站。

运行（先启动服务）:
    python register-demo/server.py
    python register-demo/registrar.py --count 3
"""

import argparse
import json
import random
import re
import string
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8765"


def http_json(method: str, path: str, payload: dict | None = None, base: str = BASE):
    """发 HTTP 请求并解析 JSON 响应，返回 (status, body)。"""
    req = urllib.request.Request(base + path, method=method)
    data = None
    if payload is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(payload).encode("utf-8")
    try:
        with urllib.request.urlopen(req, data=data, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {}
        e.close()
        return e.code, body


def random_username(prefix: str = "learner") -> str:
    return f"{prefix}-{random.randint(100, 999)}"


def random_password() -> str:
    """生成满足服务器强度规则的随机密码。"""
    lower = random.choice(string.ascii_lowercase)
    upper = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    rest = "".join(random.choices(string.ascii_letters + string.digits, k=7))
    chars = list(lower + upper + digit + rest)
    random.shuffle(chars)
    return "".join(chars)


def random_email(username: str) -> str:
    return f"{username}@example.com"


def solve_captcha(base: str = BASE) -> tuple[str, str]:
    """获取验证码并"解题"。

    沙盒的题目是数学题。这里用正则解析题目，模拟真实世界里
    用 OCR 识别验证码图片 / 调打码平台的流程。
    """
    status, body = http_json("GET", "/api/captcha", base=base)
    if status != 200:
        raise RuntimeError(f"获取验证码失败: {status} {body}")
    question = body["question"]
    m = re.search(r"(\d+)\s*\+\s*(\d+)", question)
    if not m:
        raise RuntimeError(f"无法解析验证码题目: {question!r}")
    answer = str(int(m.group(1)) + int(m.group(2)))
    print(f"  [验证码] 题目: {question} -> 答案: {answer}")
    return body["id"], answer


def read_mailbox(email: str, base: str = BASE) -> str | None:
    """模拟"登录邮箱查收验证码"。

    真实场景里这一步是你打开邮箱（或调用邮箱 API）读取邮件；
    沙盒里服务器提供了模拟收件箱 GET /api/mail/<邮箱>。
    """
    status, body = http_json("GET", "/api/mail/" + urllib.parse.quote(email, safe=""), base=base)
    if status != 200:
        return None
    codes = body.get("codes", [])
    return codes[-1]["code"] if codes else None


def submit_with_backoff(path: str, payload: dict, base: str = BASE, max_retries: int = 3):
    """提交请求；遇到 429 限流时指数退避重试（教学点）。"""
    status, body = None, {}
    for attempt in range(max_retries):
        status, body = http_json("POST", path, payload, base=base)
        if status != 429:
            return status, body
        wait = 2 ** attempt
        print(f"  [限流] 429，等待 {wait}s 后重试...")
        time.sleep(wait)
    return status, body


def register_one(base: str = BASE) -> dict | None:
    """完成一次完整注册：验证码 -> 注册 -> 邮箱验证 -> 登录。"""
    # 1. 图形验证码
    cid, answer = solve_captcha(base)

    # 2. 随机生成资料并提交注册
    username = random_username()
    password = random_password()
    payload = {
        "username": username,
        "password": password,
        "email": random_email(username),
        "captcha_id": cid,
        "captcha_answer": answer,
    }
    status, body = submit_with_backoff("/api/register", payload, base=base)
    if status != 200:
        print(f"  [注册失败] {status} {body.get('error', body)}")
        return None
    print(f"  [注册成功] {username} / {body['email']}")

    # 3. 取"邮箱验证码"并验证（真实场景：这一步是你登录邮箱读取邮件）
    email = body["email"]
    email_code = read_mailbox(email, base=base)
    if email_code is None:
        email_code = body["debug_email_code"]  # 沙盒兜底
    print(f"  [邮箱] 从模拟收件箱收到验证码: {email_code}")
    status, body = http_json("POST", "/api/verify-email", {"username": username, "code": email_code}, base=base)
    if status != 200:
        print(f"  [邮箱验证失败] {status} {body.get('error', body)}")
        return None
    print(f"  [邮箱验证] 通过，token={body['token'][:8]}...")

    # 4. 登录验证账号可用
    status, body = http_json("POST", "/api/login", {"username": username, "password": password}, base=base)
    if status != 200:
        print(f"  [登录失败] {status} {body.get('error', body)}")
        return None
    print(f"  [登录成功] {username} 可以正常使用")
    return {"username": username, "password": password, "email": body.get("email")}


def main() -> int:
    parser = argparse.ArgumentParser(description="学习版注册机（仅限本地沙盒）")
    parser.add_argument("--count", type=int, default=1, help="要注册的账号数量")
    parser.add_argument("--base", default=BASE, help="沙盒服务地址")
    args = parser.parse_args()

    print(f"学习版注册机启动，目标: {args.base}，注册 {args.count} 个账号")
    ok = 0
    for i in range(args.count):
        print(f"--- 第 {i + 1}/{args.count} 个 ---")
        if register_one(base=args.base):
            ok += 1
        time.sleep(0.5)
    print(f"完成：成功 {ok}/{args.count} 个账号")
    return 0 if ok == args.count else 1


if __name__ == "__main__":
    raise SystemExit(main())


