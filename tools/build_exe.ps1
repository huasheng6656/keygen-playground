# 把演示"软件"打包成独立 exe，用于练习真实二进制逆向。
#
# 用法（在仓库根目录执行）：
#   pip install pyinstaller
#   powershell -ExecutionPolicy Bypass -File tools/build_exe.ps1 easy
#   powershell -ExecutionPolicy Bypass -File tools/build_exe.ps1 medium
#   powershell -ExecutionPolicy Bypass -File tools/build_exe.ps1 hard
#
# 产物在 dist/ 下，可用 DIE 查壳、Ghidra/x64dbg 分析。

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("easy", "medium", "hard")]
    [string]$Target
)

$map = @{
    easy   = @{ script = "targets/easy/serial_check.py";  name = "EasyWare"   }
    medium = @{ script = "targets/medium/name_serial.py"; name = "NameWare"   }
    hard   = @{ script = "targets/hard/rsa_license.py";   name = "SecureWare" }
}

$t = $map[$Target]
pyinstaller --onefile --console --name $t.name $t.script
if ($LASTEXITCODE -eq 0) {
    Write-Host "打包完成: dist/$($t.name).exe"
    Write-Host "下一步: 用 DIE 查壳 -> Ghidra/x64dbg 分析验证逻辑"
} else {
    Write-Host "打包失败，请确认已执行: pip install pyinstaller"
    exit 1
}
