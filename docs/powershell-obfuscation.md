# powershell-obfuscation

PowerShell命令混淆工具，用于生成可用于测试检测规则的混淆样本。

## 来源

本工具基于 [Invoke-Obfuscation](https://github.com/danielbohannon/Invoke-Obfuscation) 项目，由 [Daniel Bohannon](https://github.com/danielbohannon) 开发。

Invoke-Obfuscation 是 PowerShell 命令混淆框架，提供了 5 大类混淆技术。本 skill 用 Python 重新实现了核心算法。

## 混淆技术分类

### 1. ENCODING 编码类 (8种)

将 PowerShell 代码转换为各种进制/编码格式。

| 编码 | 基数 | 解码模式 |
|------|------|----------|
| **ASCII** | 10 | `([Int][Char]'$_' + delimiter)` |
| **Hex** | 16 | `[Convert]::ToString(([Int][Char]'$_'), 16)` |
| **Octal** | 8 | `[Convert]::ToString(([Int][Char]'$_'), 8)` |
| **Binary** | 2 | `[Convert]::ToString(([Int][Char]'$_'), 2)` |
| **BXOR** | N/A | `([Int][Char]'$_' -BXOR $Key)` |
| **Whitespace** | N/A | Tab/Space 重复表示数字 |
| **SpecialCharOnly** | N/A | 特殊字符替代字母数字 |
| **Compressed** | N/A | DeflateStream + Base64 |

#### 示例

**ASCII编码:**
```powershell
$([Int][Char]'W'+[String]|[Int][Char]'r'+[String]|[Int][Char]'i'+[String]) -join ''
```

**Hex编码:**
```powershell
$('57]o[72]o[69]o[74]o[65]o...' -split '.{1}' | % { [Convert]::ToString([int]$_, 16) } | % { [Char][Convert]::ToInt32($_, 16) } -join '')
```

**BXOR编码:**
```powershell
([123]k[94]k[69]k... | % { [Char]($_ -BXOR 0x2c) } -join ''
```

### 2. LAUNCHER 启动器类 (12种)

通过各种方式启动 PowerShell 进程以隐藏真实命令。

| 类型 | 名称 | 机制 |
|------|------|------|
| **PS** | PowerShell | 直接调用 `powershell.exe` |
| **CMD** | CMD Wrapper | 通过 `cmd.exe /c` 包装 |
| **WMIC** | WMIC | `wmic process call create` |
| **RUNDLL** | Rundll32 | `rundll32.exe javascript:` |
| **VAR+** | 环境变量 | 推送到父进程的环境变量 |
| **STDIN+** | 标准输入 | 通过 StdIn 推送 |
| **CLIP+** | 剪贴板 | 复制到剪贴板供父进程执行 |
| **VAR++** | 祖父进程 | 推送到祖父进程 |
| **MSHTA++** | MSHTA | `mshta.exe` + VBScript |

#### 示例

**PS Launcher:**
```bash
powershell -NoP -NonI -Enc <base64>
```

**CMD Launcher:**
```bash
cmd /c powershell -NoP -NonI -Enc <base64>
```

**WMIC Launcher:**
```bash
wmic process call create "powershell -NoP -NonI -Enc <base64>"
```

### 3. TOKEN 令牌类 (7种)

对 PowerShell AST Token 进行混淆。

- **STRING** - 字符串字面量
- **COMMAND** - 命令名称
- **ARGUMENT** - 命令参数
- **MEMBER** - 对象成员
- **VARIABLE** - 变量名称
- **TYPE** - 类型引用
- **COMMENT** - 注释

### 4. STRING 字符串类

拆分字符串并通过变量拼接重建。

```powershell
$qfydvc='Writ'; $qwcqac='e-Ho'; $ijxpzb='st ''; ...
$qfydvc+$qwcqac+$ijxpzb+...
```

### 5. AST 抽象语法树类

操作 PowerShell AST 结构进行混淆。

## 使用方法

### 命令行

```bash
# 列出所有技术
python3 powershell-obfuscation.py --list

# 基本混淆 (Base64 + PS launcher)
python3 powershell-obfuscation.py "Write-Host 'Hello'" --encoding base64 --launcher ps

# 多种编码
python3 powershell-obfuscation.py "Get-Process" --encoding all

# 指定级别
python3 powershell-obfuscation.py "Invoke-Mimikatz" --encoding hex --level 3

# 检测模式
python3 powershell-obfuscation.py "powershell -NoP -NonI -Enc SQBFAFgAKAA=" --detect
```

### Python模块

```python
from powershell_obfuscation import obfuscate, detect, list_techniques

# 列出技术
print(list_techniques())

# 混淆PowerShell脚本
results = obfuscate("Write-Host 'Hello'", encoding='hex', level=2)
for r in results:
    print(f"[{r['technique']}] {r['command']}")

# 检测已知模式
matches = detect("powershell -NoP -NonI -Enc ...")
print(matches)
```

## 检测模式

内置的检测规则（可用于测试 EDR/SIEM 规则）：

| Pattern | Severity | Language | Description |
|---------|----------|----------|-------------|
| `BASE64_ENC` | medium | PowerShell | Base64编码命令 |
| `INVOKE_EXPRESSION` | high | PowerShell | IEX动态执行 |
| `ENCODED_COMMAND` | medium | PowerShell | 编码/解码函数 |
| `DEFLATESTREAM` | medium | PowerShell | 压缩流 |
| `WMIC_LAUNCH` | high | Batch | WMIC进程创建 |
| `RUNDLL32_JS` | high | Batch | RUNDLL32+JS |
| `MSHTA_VBS` | high | Batch | MSHTA+VBS |
| `SET_CLIPBOARD` | low | PowerShell | 剪贴板操作 |

## 参考

- [Invoke-Obfuscation](https://github.com/danielbohannon/Invoke-Obfuscation) by [@danielbohannon](https://github.com/danielbohannon)
- [BH Arsenal 2018](https://www.blackhat.com/arsenal.html) - "Invoke-DOSfuscation: Techniques for Forrest's Spaces"
- [相关演讲视频](https://www.youtube.com/watch?v=DdBcWM5Lglg)

## 许可

本工具仅用于防御性安全研究和检测规则开发。
