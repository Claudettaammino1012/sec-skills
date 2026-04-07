# donut

Shellcode 生成工具，用于从 .NET 程序集生成可用于测试检测规则的 shellcode 样本。

## 来源

本工具基于 [Donut](https://github.com/TheWover/donut) 项目，由 [TheWover](https://github.com/TheWover) 和 [Odzhan](https://github.com/Odzhan) 开发。

Donut 将 .NET EXE/DLL、VBS、JS 等文件转换为位置无关代码（shellcode），支持 AMSI/WLDP bypass 和多种输出格式。

## 核心功能

### Shellcode 生成

Donut 可以将以下类型的文件转换为 shellcode：
- .NET EXE/DLL 程序集
- VBS 脚本
- JavaScript 脚本
- XSL 样式表

### 输出格式

| 格式 | 说明 |
|------|------|
| Binary | 原始二进制 shellcode |
| Base64 | Base64 编码 |
| C | C 语言字节数组 |
| Python | Python bytes 对象 |
| PowerShell | PowerShell 字节数组 |
| C# | C# 字节数组 |
| Hex | 十六进制字符串 |

### AMSI/WLDP Bypass

Donut 内置对 AMSI（反恶意软件扫描接口）和 WLDP（Windows 锁定屏策略）的 bypass 机制：

| 级别 | 说明 |
|------|------|
| none | 不尝试 bypass |
| abort | bypass 失败时中止 |
| continue | bypass 失败时继续执行（默认） |

## 使用方法

### 命令行

```bash
# 生成 shellcode（EXE）
python3 donut/donut.py generate malicious.exe -c Namespace.Class -m Main

# 生成 shellcode（DLL）
python3 donut/donut.py generate malicious.dll -c TestClass -m RunProcess -p notepad.exe

# 指定架构
python3 donut/donut.py generate malicious.exe -a 2  # amd64 only

# 指定输出格式
python3 donut/donut.py generate malicious.exe -f 8  # hex

# 检测 Donut 模式
python3 donut/donut.py detect "cb2f6723-ab3a-11d2-9c40"
```

### Python 模块

```python
from donut import generate_shellcode, detect

# 生成 shellcode
result = generate_shellcode(
    file_path="malicious.exe",
    cls="Namespace.Class",
    method="Main",
    params="-arg1 value1",
    arch=3,        # x86+amd64
    bypass=3,      # continue on AMSI fail
    format=5       # python format
)

print(result['shellcode'])

# 检测模式
matches = detect("AmsiScanBuffer")
print(matches)
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-f` | 输入文件路径 | - |
| `-c` | 类名 | - |
| `-m` | 方法名 | - |
| `-p` | 参数 | - |
| `-a` | 架构: 1=x86, 2=amd64, 3=x86+amd64 | 3 |
| `-b` | bypass: 1=none, 2=abort, 3=continue | 3 |
| `-r` | CLR 运行时版本 | v4.0.30319 |
| `-d` | AppDomain 名称 | 随机生成 |
| `-e` | 压缩: 1=none, 2=aplib | 2 |
| `-h` | 熵: 1=none, 2=random, 3=default | 3 |
| `-o` | 输出格式 | 5 (python) |

## 检测模式

内置的检测规则：

| 模式 | 严重性 | 说明 |
|------|--------|------|
| `DONUT_CLR_GUID` | high | CLR GUID 特征 |
| `DONUT_MODULE_NAME` | medium | Donut 模块名标记 |
| `AMSI_BYPASS` | high | AMSI bypass API |
| `HIGH_ENTROPY_PAYLOAD` | medium | 高熵加密 payload |
| `APLIB_COMPRESSION` | medium | aPLib 压缩签名 |
| `SHELLCODE_PROLOGUE` | low | Shellcode 典型序言 |
| `VIRTUALALLOC_CREATETHREAD` | high | 内存分配+线程创建模式 |

## 示例

### 示例 1: 基本 shellcode 生成

```bash
$ python3 donut/donut.py generate Mimikatz.exe -c Dump -m Main

shellcode = bytes.fromhex("4d5a9000...")
```

### 示例 2: 完整参数

```bash
$ python3 donut/donut.py generate malicious.dll \
    -c GetPasswords -m Execute \
    -p "targetServer" \
    -a 3 \
    -b 3 \
    -f 8
```

### 示例 3: 检测能力测试

```bash
$ python3 donut/donut.py detect "cb2f6723-ab3a-11d2-9c40"

[
  {
    "pattern": "DONUT_CLR_GUID",
    "description": "Donut CLR GUID - used for runtime binding",
    "severity": "high",
    "match": "cb2f6723-ab3a-11d2-9c40"
  }
]
```

## 工作原理

1. **CLR Hosting API**: Donut 使用非托管 CLR Hosting API 在任意 Windows 进程中加载 .NET 运行时
2. **内存加载**: .NET 程序集可以从内存加载，无需触碰磁盘
3. **加密**: 使用 Chaskey 块密码和 128 位随机密钥加密
4. **AppDomain**: 在新的应用域中执行，加载后清除原始引用

## 参考

- **原项目**: [Donut](https://github.com/TheWover/donut) by [@TheWover](https://github.com/TheWover)
- **论文**: [Introducing Donut](https://github.com/TheWover/donut/blob/master/docs/2019-5-9-Introducing-Donut.md)
- **Python 扩展**: [donut-shellcode](https://pypi.org/project/donut-shellcode/)

## 许可

本 skill 是 Donut 项目的 Python 封装，遵循原项目 BSD-3-Clause 许可。
