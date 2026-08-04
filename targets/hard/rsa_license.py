"""SecureWare Pro 3.0 —— 虚构教学软件，难度：hard

注册机制：
    注册码是"RSA 签名"。流程：
        用户名 -> SHA-256 -> PKCS#1 v1.5 填充 -> 用作者私钥签名 -> base64 输出注册码
    程序内置公钥 (N, E)，验证时对注册码做模幂运算，结果等于填充后的摘要即通过。

逆向思路（详见 docs/02）：
    1. 程序里只有公钥，没有私钥——理论上无法伪造注册码；
    2. 实际破解这类软件通常走 Patch（改跳转）或内存注册机；
    3. 本教学示例假设你已经通过某种途径获得私钥 D（例如从官方注册机中提取），
       因此可以写一个"真·算法注册机"。

练习目标：写一个注册机 sign(username) -> license，
    要求生成的注册码能被本程序的 verify 接受。
"""

import base64
import hashlib
import sys

# ---- 内置公钥（教学用 1024 位，请勿用于真实安全场景） ----
N = int(
    "B1699AD5B2A8A1C18EEB6CDA497E70FC2997DCF437FB135356915FC72BADD1D74D2C67F9093E14EA990BD7CCBC37CE37456DA9C76DBBEFB5F8BF4F65943A4D01AF1AE371E4B4F49F702F128F06AEBE2170BF41C963E0ED8549AB8AE320660DF4E611AD8BDB38D08C8380818B2EC5D3D158CC7E989B2C0B62FE20F416F815CFA9",
    16,
)
E = 0x10001

# SHA-256 的 DigestInfo 前缀（EMSA-PKCS1-v1_5 填充用）
_DIGEST_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _modulus_bytes() -> int:
    """N 的字节长度 k。"""
    return (N.bit_length() + 7) // 8


def sha256_hex(username: str) -> bytes:
    """用户名的 SHA-256 十六进制文本（ASCII）。"""
    return hashlib.sha256(username.encode("utf-8")).hexdigest().encode("ascii")


def pkcs1_pad(digest_hex: bytes) -> int:
    """EMSA-PKCS1-v1_5 填充：0x00 01 FF..FF 00 <DigestInfo> <digest>"""
    t = _DIGEST_PREFIX + digest_hex
    k = _modulus_bytes()
    ps_len = k - len(t) - 3
    em = b"\x00\x01" + b"\xff" * ps_len + b"\x00" + t
    return int.from_bytes(em, "big")


def verify(username: str, license_b64: str) -> bool:
    """验签：pow(sig, E, N) == 填充后的摘要。"""
    try:
        sig = int.from_bytes(base64.b64decode(license_b64.strip()), "big")
    except Exception:
        return False
    if sig >= N:
        return False
    return pow(sig, E, N) == pkcs1_pad(sha256_hex(username))


def main() -> int:
    print("=" * 40)
    print("  SecureWare Pro 3.0 (教学演示)")
    print("  RSA 签名注册码")
    print("=" * 40)
    username = input("请输入用户名: ").strip()
    license_b64 = input("请输入注册码: ").strip()
    if verify(username, license_b64):
        print("[OK] 注册成功！欢迎使用 SecureWare Pro，", username)
        return 0
    print("[X] 注册码无效（用户名或注册码不正确）。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
