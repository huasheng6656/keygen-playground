"""NameWare 2.0 —— 虚构教学软件，难度：medium

注册机制：
    注册码与用户名绑定。程序对用户名做 FNV-1a 32 位哈希，
    转成 8 位大写十六进制作为"期望注册码"，与用户输入比较。

逆向思路（详见 docs/02）：
    1. 多注册几个用户名，观察注册码规律（长度、字符集）；
    2. 认出 FNV-1a 的两个魔法常量 0x811C9DC5 与 0x01000193；
    3. 哈希不可逆，但注册机不需要逆——照抄算法正向算即可。

练习目标：写一个注册机 generate(username) -> serial，
    要求生成的注册码能被本程序的 check_serial 接受。
"""

import sys


def fnv1a_32(data: bytes) -> int:
    """FNV-1a 32 位哈希。"""
    h = 0x811C9DC5
    for b in data:
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def make_serial(username: str) -> str:
    """由用户名计算期望注册码。"""
    return f"{fnv1a_32(username.encode('utf-8')):08X}"


def check_serial(username: str, serial: str) -> bool:
    """验证：用户名至少 3 个字符，且注册码与期望值相等。"""
    if len(username.strip()) < 3:
        return False
    return serial.strip().upper() == make_serial(username)


def main() -> int:
    print("=" * 40)
    print("  NameWare 2.0 (教学演示)")
    print("  注册码与用户名绑定")
    print("=" * 40)
    username = input("请输入用户名: ").strip()
    serial = input("请输入注册码: ").strip()
    if check_serial(username, serial):
        print("[OK] 注册成功！欢迎使用 NameWare，", username)
        return 0
    print("[X] 注册码无效（用户名或注册码不正确）。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
