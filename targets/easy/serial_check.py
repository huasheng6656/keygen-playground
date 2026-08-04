"""EasyWare 1.0 —— 虚构教学软件，难度：easy

注册机制（最朴素的一种）：
    程序内置一个序列号，用户输入的序列号和它完全相等即注册成功。

逆向思路（详见 docs/04）：
    1. 用 DIE 查壳、用字符串工具搜索，会直接看到这个内置序列号；
    2. 或对 strcmp/lstrcmp 下断点，观察第二个参数。

练习目标：写一个注册机，输出能让本程序通过的序列号。
"""

import sys

# 内置序列号（在真实二进制里，它通常就在 .rdata/.data 段中）
VALID_SERIAL = "H3LL0-K3YG3N-2024"


def check_serial(serial: str) -> bool:
    """验证序列号：硬编码字符串比较。"""
    return serial == VALID_SERIAL


def main() -> int:
    print("=" * 40)
    print("  EasyWare 1.0 (教学演示)")
    print("=" * 40)
    serial = input("请输入注册码: ").strip()
    if check_serial(serial):
        print("[OK] 注册成功！感谢购买正版 EasyWare。")
        return 0
    print("[X] 注册码无效，请检查后重试。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
