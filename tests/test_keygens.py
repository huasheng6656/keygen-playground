"""自动化验证：注册机生成的注册码必须能被对应演示软件接受。

运行:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from keygens.easy.keygen import generate as easy_generate
from keygens.medium.keygen import generate as medium_generate
from keygens.hard.keygen import sign as hard_sign

from targets.easy.serial_check import check_serial as easy_check
from targets.medium.name_serial import check_serial as medium_check
from targets.hard.rsa_license import verify as hard_check


class EasyTest(unittest.TestCase):
    def test_keygen_serial_is_accepted(self):
        self.assertTrue(easy_check(easy_generate()))

    def test_wrong_serial_is_rejected(self):
        self.assertFalse(easy_check("wrong-serial"))


class MediumTest(unittest.TestCase):
    def test_keygen_serial_is_accepted(self):
        self.assertTrue(medium_check("Alice", medium_generate("Alice")))

    def test_serial_is_bound_to_username(self):
        # 用 Alice 的注册码给 Bob 用，必须无效
        self.assertFalse(medium_check("Bob", medium_generate("Alice")))

    def test_wrong_serial_is_rejected(self):
        self.assertFalse(medium_check("Alice", "DEADBEEF"))


class HardTest(unittest.TestCase):
    def test_keygen_license_is_accepted(self):
        self.assertTrue(hard_check("张三", hard_sign("张三")))

    def test_license_is_bound_to_username(self):
        self.assertFalse(hard_check("李四", hard_sign("张三")))

    def test_garbage_license_is_rejected(self):
        self.assertFalse(hard_check("张三", "not-a-license"))


if __name__ == "__main__":
    unittest.main()
