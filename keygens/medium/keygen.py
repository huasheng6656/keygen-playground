"""注册机：NameWare 2.0（medium）

逆向结论：
    注册码 = FNV-1a(用户名) 的 8 位大写十六进制。
    哈希不可逆，但注册机不需要逆运算——正向复现即可。

练习建议：先自己写，再对照本文件。
"""


def fnv1a_32(data: bytes) -> int:
    """FNV-1a 32 位哈希（与 targets/medium/name_serial.py 同款）。"""
    h = 0x811C9DC5
    for b in data:
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def generate(username: str) -> str:
    """由用户名生成注册码。"""
    return f"{fnv1a_32(username.encode('utf-8')):08X}"


def main() -> int:
    username = input("请输入用户名: ").strip()
    print("注册码:", generate(username))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
