"""注册机：EasyWare 1.0（easy）

逆向结论：
    验证是硬编码字符串比较，序列号在二进制中直接可见。
    注册机只需输出该序列号。

练习建议：先自己写，再对照本文件。
"""


def generate() -> str:
    """返回合法注册码。"""
    return "H3LL0-K3YG3N-2024"


def main() -> int:
    print("EasyWare 1.0 注册机")
    print("注册码:", generate())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
