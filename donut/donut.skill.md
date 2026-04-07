---
name: donut
description: Generate shellcode from .NET assemblies for defensive testing, based on TheWover/donut
triggers:
  - "donut shellcode"
  - "dotnet to shellcode"
  - "assembly to shellcode"
  - "donut generator"
---

# donut Skill

Shellcode 生成工具，基于 [Donut](https://github.com/TheWover/donut) 项目。

将 .NET EXE/DLL、VBS、JS 等文件转换为位置无关 shellcode，用于测试 EDR/检测规则。

## Commands

### generate

Generate shellcode from a .NET assembly.

```bash
generate <file> [-c class] [-m method] [-p params] [-a arch] [-b bypass] [-f format]
```

**Parameters:**
- `file`: Path to .NET assembly, VBS, JS, or XSL file
- `-c, --cls`: Class name (required for DLL)
- `-m, --method`: Method name (required for DLL)
- `-p, --params`: Parameters for the method
- `-a, --arch`: Architecture (1=x86, 2=amd64, 3=x86+amd64)
- `-b, --bypass`: AMSI/WLDP bypass (1=none, 2=abort, 3=continue)
- `-f, --format`: Output format (1=binary, 2=base64, 4=c, 5=python, 6=ps, 7=cs, 8=hex)

**Examples:**
```bash
generate malicious.exe -c Namespace.Class -m Main
generate malicious.dll -c TestClass -m RunProcess -p notepad.exe,calc.exe -a 3
```

### detect

Check if data contains Donut shellcode patterns.

```bash
detect <data>
```

**Examples:**
```bash
detect "cb2f6723-ab3a-11d2-9c40"
detect "AmsiScanBuffer"
```

### list

List available options.

```bash
list
```

---

## Architecture Options

| Value | Name | Description |
|-------|------|-------------|
| 1 | x86 | 32-bit only |
| 2 | amd64 | 64-bit only |
| 3 | x86+amd64 | Dual-mode (default) |

## Bypass Options

| Value | Name | Description |
|-------|------|-------------|
| 1 | none | No AMSI/WLDP bypass |
| 2 | abort | Abort on bypass failure |
| 3 | continue | Continue on bypass failure (default) |

## Format Options

| Value | Name | Description |
|-------|------|-------------|
| 1 | binary | Raw binary file |
| 2 | base64 | Base64 encoded |
| 4 | c | C byte array |
| 5 | python | Python bytes |
| 6 | powershell | PowerShell byte array |
| 7 | csharp | C# byte array |
| 8 | hex | Hex string |

## Compression Options

| Value | Name | Description |
|-------|------|-------------|
| 1 | none | No compression |
| 2 | aplib | aPLib compression (default) |

---

## Implementation

```python
from donut import generate_shellcode, detect

# Generate shellcode
result = generate_shellcode(
    file_path="malicious.exe",
    cls="Namespace.Class",
    method="Main",
    params="-arg1 value1",
    arch=3,  # x86+amd64
    bypass=3,  # continue on AMSI fail
    format=5  # python
)

if result['success']:
    print(result['shellcode'])

# Detect Donut patterns
matches = detect("cb2f6723-ab3a-11d2-9c40")
print(matches)
```

---

## Reference

- **Donut**: [https://github.com/TheWover/donut](https://github.com/TheWover/donut)
- **Authors**: [TheWover](https://github.com/TheWover), [Odzhan](https://github.com/Odzhan)
- **Python Extension**: [donut-shellcode](https://pypi.org/project/donut-shellcode/)
