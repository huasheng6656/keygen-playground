"""register-demo 沙盒注册服务的自动化测试。

运行:
    python -m unittest discover -s register-demo/tests -v
"""

import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

# 让测试能 import register-demo 下的模块
REGISTER_DEMO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REGISTER_DEMO)

import server as srv  # noqa: E402
import registrar  # noqa: E402


def post(url, payload):
    req = urllib.request.Request(url, method="POST",
                                 data=json.dumps(payload).encode("utf-8"))
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8")) if e.headers.get("Content-Type") else {}
        e.close()
        return e.code, body


def get(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


class RegisterDemoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = srv.make_server(port=0)
        cls.port = cls.httpd.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        # 每个用例前清空内存状态，避免限流器 / 用户数据跨用例互相干扰
        srv.USERS.clear()
        srv.EMAIL_CODES.clear()
        srv.CAPTCHAS.clear()
        srv.IP_HITS.clear()

    def _register(self, username, password, captcha_ok=True):
        cid, answer = registrar.solve_captcha(self.base)
        payload = {
            "username": username,
            "password": password,
            "email": f"{username}@example.com",
            "captcha_id": cid if captcha_ok else "bad-id",
            "captcha_answer": answer if captcha_ok else "0",
        }
        return post(f"{self.base}/api/register", payload)

    def test_full_registration_flow(self):
        status, body = self._register("alice-01", "Passw0rd!x")
        self.assertEqual(status, 200, body)
        self.assertTrue(body["need_email_verify"])

        # 从"模拟收件箱"取验证码（代替 debug 字段）
        status, body = get(f"{self.base}/api/mail/alice-01@example.com")
        self.assertEqual(status, 200, body)
        self.assertTrue(body["codes"])
        code = body["codes"][-1]["code"]

        status, body = post(f"{self.base}/api/verify-email",
                            {"username": "alice-01", "code": code})
        self.assertEqual(status, 200, body)

        status, body = post(f"{self.base}/api/login",
                            {"username": "alice-01", "password": "Passw0rd!x"})
        self.assertEqual(status, 200, body)

    def test_wrong_email_code_rejected(self):
        self._register("bob-02", "Passw0rd!x")
        status, body = post(f"{self.base}/api/verify-email",
                            {"username": "bob-02", "code": "000000"})
        self.assertEqual(status, 400, body)
        self.assertIn("验证码错误", body["error"])

    def test_weak_password_rejected(self):
        status, body = self._register("carol-03", "short")
        self.assertEqual(status, 400, body)
        self.assertIn("密码至少 8 位", body["error"])

    def test_duplicate_username_rejected(self):
        self._register("dave-04", "Passw0rd!x")
        status, body = self._register("dave-04", "Passw0rd!x")
        self.assertEqual(status, 400, body)
        self.assertIn("已被占用", body["error"])

    def test_bad_captcha_rejected(self):
        status, body = self._register("erin-05", "Passw0rd!x", captcha_ok=False)
        self.assertEqual(status, 400, body)
        self.assertIn("验证码", body["error"])

    def test_login_locks_after_failures(self):
        self._register("frank-06", "Passw0rd!x")
        for _ in range(5):
            post(f"{self.base}/api/login", {"username": "frank-06", "password": "Wrong!123"})
        status, body = post(f"{self.base}/api/login",
                            {"username": "frank-06", "password": "Passw0rd!x"})
        self.assertEqual(status, 403, body)
        self.assertIn("锁定", body["error"])

    def test_registrar_register_one_works(self):
        result = registrar.register_one(self.base)
        self.assertIsNotNone(result)
        self.assertIn("username", result)


if __name__ == "__main__":
    unittest.main()

