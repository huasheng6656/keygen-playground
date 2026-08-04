# Keygen Playground · 注册机学习实验室

> 一个用来学习「注册机（Keygen / 序列号生成器）」原理的练习项目。
> 仓库里的所有"软件"均为**虚构的教学演示**，仅供学习逆向分析，请勿用于破解他人软件。

## 这是什么

软件作者为了防止盗版，会在程序里加入注册验证逻辑：

```
用户输入注册码 → 程序用内置算法计算期望值 → 与输入比较 → 通过则解锁
```

「注册机」就是逆向分析者还原出这套校验算法后，写出的一个**能生成合法注册码的小工具**。

本项目用 **3 个难度递增的虚构演示软件**，带你走完完整的学习路径：

| 难度 | 演示软件 | 验证算法 | 你要学到的 |
|------|----------|----------|------------|
| easy | EasyWare 1.0 | 硬编码字符串比较 | 找关键字符串、下断点 |
| medium | NameWare 2.0 | 用户名 + FNV-1a 哈希 | 还原哈希算法、编写注册机 |
| hard | SecureWare Pro 3.0 | RSA 签名验签 | 非对称签名原理、公钥/私钥 |

## 目录结构

```
keygen-playground/
├── docs/                  # 理论知识（建议先读）
│   ├── 01-认识注册机.md
│   ├── 02-常见注册验证算法.md
│   ├── 03-逆向分析工具.md
│   └── 04-实战分析方法.md
├── targets/               # 虚构的演示"软件"
│   ├── easy/              # 序列号硬编码比较
│   ├── medium/            # 用户名 + FNV-1a 哈希
│   └── hard/              # RSA 签名注册码
├── keygens/               # 对应注册机（参考答案）
│   ├── easy/
│   ├── medium/
│   └── hard/
├── tools/                 # 辅助工具
│   ├── gen_rsa_keys.py    # 生成 RSA 教学密钥对
│   └── build_exe.ps1      # 把演示软件打包成 exe
└── tests/                 # 自动化验证注册机是否有效
```

## 学习路线

1. **读理论**：按顺序读 `docs/01` 到 `docs/04`，建立整体概念。
2. **当用户**：运行演示软件，输入注册码看看效果。
   ```powershell
   python targets/easy/serial_check.py
   ```
3. **读源码**：打开 `targets/` 下的源码，理解验证算法长什么样。
4. **写注册机**：先别看 `keygens/`，自己动手实现一个能生成合法注册码的脚本。
5. **验证**：运行测试，确认你的注册机生成的注册码能被演示软件接受。
   ```powershell
   python -m unittest discover -s tests -v
   ```
6. **进阶（真机逆向）**：用 `tools/build_exe.ps1` 把演示软件打包成 `.exe`，
   再用 Ghidra / x64dbg 等工具做真正的二进制分析（详见 `docs/03`、`docs/04`）。

## 法律声明

本项目仅用于**学习、CTF 练习、自有软件测试**等合法用途。
请勿使用本项目中的方法破解他人享有版权的商业软件。

## 环境要求

- Python 3.8+（无需任何第三方库，全部使用标准库）
- 进阶练习：Windows + [Detect It Easy](https://github.com/horsicq/Detect-It-Easy)、
  [Ghidra](https://github.com/NationalSecurityAgency/ghidra)、
  [x64dbg](https://x64dbg.com/)（均为免费工具）
