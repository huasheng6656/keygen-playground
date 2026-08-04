"""注册机：SecureWare Pro 3.0（hard）

前置知识：
    已通过逆向分析确认验证算法是「RSA 验签」；
    本例假设私钥 D 已被提取（真实世界通常来自官方注册机泄露/提取）。

原理：
    注册码 = base64( RSA私钥签名( SHA256(用户名) ) )
    与 targets/hard/rsa_license.py 中的验签流程严格对应。
"""

import base64
import hashlib
import sys

# ---- 私钥（教学示例，从"官方注册机"提取而来） ----
N = int(
    "B1699AD5B2A8A1C18EEB6CDA497E70FC2997DCF437FB135356915FC72BADD1D74D2C67F9093E14EA990BD7CCBC37CE37456DA9C76DBBEFB5F8BF4F65943A4D01AF1AE371E4B4F49F702F128F06AEBE2170BF41C963E0ED8549AB8AE320660DF4E611AD8BDB38D08C8380818B2EC5D3D158CC7E989B2C0B62FE20F416F815CFA9",
    16,
)
D = int(
    "93ECADC148B9FA455D5946E5AB29D6232ABB08EC4850FC881C42124E0B495F11D9B310EE409A96EE14B61F35022AB5B2B81CFBD6E0D436C6CFA5141A6A41423AA57D54B951AD8483EEB13238625928EB8EC3D9847DF53BA3E787BB0367560EF2D1F67604260CEA5F87C2AF7C33D705E4CED91728A3F9520DF84E8F31BB214201",
    16,
)

# SHA-256 的 DigestInfo 前缀（与 targets 保持一致）
_DIGEST_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _modulus_bytes() -> int:
    return (N.bit_length() + 7) // 8


def sha256_hex(username: str) -> bytes:
    return hashlib.sha256(username.encode("utf-8")).hexdigest().encode("ascii")


def pkcs1_pad(digest_hex: bytes) -> int:
    t = _DIGEST_PREFIX + digest_hex
    k = _modulus_bytes()
    ps_len = k - len(t) - 3
    em = b"\x00\x01" + b"\xff" * ps_len + b"\x00" + t
    return int.from_bytes(em, "big")


def sign(username: str) -> str:
    """生成注册码（base64）。"""
    m = pkcs1_pad(sha256_hex(username))
    sig = pow(m, D, N)
    k = _modulus_bytes()
    return base64.b64encode(sig.to_bytes(k, "big")).decode("ascii")


def main() -> int:
    username = input("请输入用户名: ").strip()
    print("注册码:", sign(username))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
