# bash-obfuscation

Bash命令混淆工具，用于生成可用于测试检测规则的混淆样本。

## 来源

本工具基于 [Bashfuscator](https://github.com/Bashfuscator/Bashfuscator) 项目，由 [capnspacehook](https://github.com/capnspacehook) 开发。

Bashfuscator 是模块化且可扩展的 Bash 混淆框架，提供多种方式使 Bash 命令难以理解。本 skill 用 Python 重新实现了核心算法。

## 混淆技术

### 1. Encoding 编码类

#### Base64

```bash
echo "Y2F0IC9ldGMvcGFzc3dk" | base64 -d | bash
```

#### Hex

```bash
echo -e "\x63\x61\x74\x20\x2f\x65\x74\x63\x2f\x70\x61\x73\x73\x77\x64" | xxd -r -p | bash
```

#### Gzip

```bash
printf "\x1f\x8b..." | base64 -d | gunzip -c | bash
```

#### Bzip2

```bash
printf "QlpoOTFBWSZTWV..." | base64 -d | bunzip2 -c | bash
```

#### ROT13

```bash
echo "png synt /ratgvbg/" | tr "a-zA-Z" "n-za-mN-ZA-M" | bash
```

### 2. Command Obfuscation 命令混淆类

#### Reverse

```bash
printf "dwssap/cte/ tac" | rev | bash
```

#### Case Swap

```bash
VAR="CAT /ETC/PASSWD"; eval "$(printf "${VAR~~}")"
```

#### FOR Code

```bash
ARR=(t c a " " / e t c / p a s s w d); for i in 2 0 3 1 4 5 6 7 8 9 10 11 12 13 14 15; do printf "${ARR[$i]}"; done | bash
```

#### Special Char Only

```bash
bash -c $\'\x63\x61\x74\x20\x2f\x65\x74\x63\x2f\x70\x61\x73\x73\x77\x64\'
```

### 3. Obfuscation Styles 混淆风格

#### Whitespace Injection

```bash
e c ho   "hello"
```

#### Quote Wrapping

```bash
bash -c 'cat /etc/passwd'
bash -c "cat /etc/passwd"
```

#### Subshell

```bash
$(cat /etc/passwd)
```

#### Pipe Dummy Stages

```bash
cat /etc/passwd | true | cat | true
```

## 使用方法

### 命令行

```bash
# 混淆所有技术
python3 bash_obfuscation.py "cat /etc/passwd" --technique all --level 2

# 指定技术
python3 bash_obfuscation.py "ls -la" --technique base64

# Hex编码
python3 bash_obfuscation.py "whoami" --technique hex --level 3

# 检测已知模式
python3 bash_obfuscation.py "echo 'data' | base64 -d | bash" --detect

# 列出所有技术
python3 bash_obfuscation.py --list
```

### Python 模块

```python
from bash_obfuscation import obfuscate, detect, list_techniques

# 列出技术
print(list_techniques())

# 混淆命令
results = obfuscate("cat /etc/passwd", technique='all', level=2)
for r in results:
    print(f"[{r['technique']}] {r['command']}")

# 检测模式
matches = detect("echo 'a被害' | base64 -d | bash")
print(matches)
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `command` | 要混淆的命令 | - |
| `--technique` | 混淆技术: `base64\|hex\|gzip\|bzip2\|rot13\|reverse\|case_swap\|for_code\|special_char\|all` | `all` |
| `--level` | 混淆级别 1-3（3最激进） | `2` |
| `--detect` | 检测模式而非混淆 | `False` |

## 检测模式

内置的检测规则（可用于测试 EDR/SIEM 规则）：

| 模式 | 严重性 | 说明 |
|------|--------|------|
| `BASE64_PIPE` | medium | Base64解码后管道执行 |
| `HEX_ENCODING` | low | Hex编码字符串 |
| `GZIP_DECOMPRESS` | medium | Gzip解压 |
| `BZIP_DECOMPRESS` | medium | Bzip2解压 |
| `REV_COMMAND` | low | 反转命令 |
| `EVAL_EXECUTION` | medium | Eval执行变量 |
| `FOR_LOOP_SHELL` | low | FOR循环 |
| `XXD_HEXDUMP` | low | Hexdump反转 |
| `TR_ROT13` | low | ROT13转换 |
| `SUBSHELL_EXEC` | low | 子shell执行 |

## 示例

### 示例 1: 基本混淆

```bash
$ python3 bash_obfuscation.py "cat /etc/passwd" --technique all

[
  {"technique": "base64", "command": "echo \"Y2F0IC9ldGMvcGFzc3dk\" | base64 -d | bash"},
  {"technique": "hex", "command": "echo -e \"\\x63\\x61\\x74\" | xxd -r -p | bash"},
  ...
]
```

### 示例 2: Base64 编码

```bash
$ python3 bash_obfuscation.py "whoami" --technique base64 --level 3

{
  "technique": "base64",
  "command": "wH3n=$(printf \"d2hvYW1p\"); ${wH3n} | base64 -d | bash"
}
```

### 示例 3: 检测能力测试

```bash
$ python3 bash_obfuscation.py "echo 'test' | base64 -d | bash" --detect

[
  {"pattern": "BASE64_PIPE", "severity": "medium", "match": "base64 -d |"}
]
```

## 参考

- **原项目**: [Bashfuscator](https://github.com/Bashfuscator/Bashfuscator) by [@capnspacehook](https://github.com/capnspacehook)
- **相关演讲**: [Bsides Charm - Bashfuscator](https://www.youtube.com/watch?v=zef422NDmpo)
- **灵感来源**: [danielbohannon](https://github.com/danielbohannon) 的 Invoke-Obfuscation 和 Invoke-DOSfuscation

## 许可

本 skill 是 Bashfuscator 项目的 Python 再实现，遵循原项目许可。
