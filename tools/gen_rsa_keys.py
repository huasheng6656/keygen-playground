"""生成教学用 RSA 密钥对（纯 Python 标准库，无第三方依赖）。

用法:
    python tools/gen_rsa_keys.py            # 默认 1024 位
    python tools/gen_rsa_keys.py 2048       # 指定位数

输出:
    N/E/D 的十六进制与十进制，方便直接嵌入演示软件与注册机。

注意: 本工具生成的密钥仅用于教学演示，不可用于真实安全场景。
"""

import math
import secrets
import sys


def is_probable_prime(n: int, rounds: int = 40) -> bool:
    """Miller-Rabin 素性检测。"""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def gen_prime(bits: int) -> int:
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if is_probable_prime(candidate):
            return candidate


def gen_rsa(bits: int = 1024):
    """生成 (n, e, d, p, q)，保证 n 恰好为 bits 位。"""
    e = 65537
    while True:
        p = gen_prime(bits // 2)
        q = gen_prime(bits // 2)
        if p == q:
            continue
        n = p * q
        if n.bit_length() != bits:
            continue
        phi = (p - 1) * (q - 1)
        if math.gcd(e, phi) != 1:
            continue
        d = pow(e, -1, phi)
        return n, e, d, p, q


def main() -> int:
    bits = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
    print(f"正在生成 {bits} 位 RSA 密钥对（纯 Python，可能需要几秒）...")
    n, e, d, p, q = gen_rsa(bits)
    print()
    print(f"=== 公钥（嵌入演示软件 targets/hard/rsa_license.py） ===")
    print(f"N = 0x{n:X}")
    print(f"E = 0x{E if False else e:X}")
    print()
    print(f"=== 私钥（嵌入注册机 keygens/hard/keygen.py） ===")
    print(f"D = 0x{d:X}")
    print()
    print("=== 十进制（备查） ===")
    print(f"n = {n}")
    print(f"e = {e}")
    print(f"d = {d}")
    print()
    print("=== 素数（备查） ===")
    print(f"p = {p}")
    print(f"q = {q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
