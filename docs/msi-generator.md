# msi-generator

MSI 安装包生成工具，用于创建测试检测规则的样本安装包。

## 来源

基于 Python 内置 `msilib` 库。`msilib` 是 Python 标准库的一部分，仅在 Windows 上可用。

对于 Linux 环境，可使用 `msitools`：
```bash
apt-get install msitools
```

## 核心功能

### MSI 生成

MSI（Microsoft Windows Installer）是一种 Windows 安装包格式。本工具可以：

- 生成基本的 MSI 安装包
- 包含自定义的可执行文件
- 添加安装/卸载脚本
- 生成可疑样本用于测试检测规则

### MSI 结构

```
MSI Database
├── Directory      # 安装目录结构
├── Component     # 组件（文件/注册表）
├── File          # 要安装的文件
├── Feature       # 功能模块
├── CustomAction  # 自定义操作（脚本）
└── ...
```

## 使用方法

### 命令行

```bash
# 生成基本 MSI
python3 msi-generator/msi_generator.py generate output.msi -n MyApp -f myapp.exe

# 生成可疑 MSI（用于检测测试）
python3 msi-generator/msi_generator.py generate-suspicious fake_update.msi "calc.exe"

# 分析 MSI
python3 msi-generator/msi_generator.py analyze suspicious.msi
```

### Python 模块

```python
from msi_generator import generate_msi, generate_suspicious_msi, analyze_msi

# 基本 MSI
result = generate_msi(
    output_path="test.msi",
    name="MyApp",
    version="1.0.0",
    manufacturer="TestVendor",
    source_file="myapp.exe"
)

# 可疑 MSI（模拟恶意安装包）
result = generate_suspicious_msi(
    output_path="fake_update.msi",
    name="CriticalUpdate",  # 听起来合法的名字
    payload_command="powershell -enc ..."  # 要执行的命令
)

# 分析 MSI
analysis = analyze_msi("suspicious.msi")
print(analysis['suspicious'])  # True/False
```

## 参数说明

### generate

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `output.msi` | 输出路径 | - |
| `-n, --name` | 产品名称 | `App` |
| `-v, --version` | 版本号 | `1.0.0` |
| `-m, --manufacturer` | 制造商 | `TestVendor` |
| `-f, --file` | 要包含的可执行文件 | - |
| `-d, --dir` | 安装目录 | 产品名称 |

### generate-suspicious

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `output.msi` | 输出路径 | - |
| `payload_command` | 要执行的 Payload | `calc.exe` |

## 检测模式

内置的检测规则：

| 模式 | 严重性 | 说明 |
|------|--------|------|
| `MSI_CUSTOM_ACTION` | medium | MSI 中的自定义操作 |
| `MSI_HIDDEN_EXEC` | high | 隐藏执行模式 |
| `MSI_REGISTRY_WRITE` | medium | 注册表写入 |
| `MSI_SCHEDULE_TASK` | high | 计划任务创建 |
| `MSI_SERVICE_INSTALL` | high | Windows 服务安装 |
| `MSI_FILE_OVERWRITE` | medium | 文件覆盖/修改 |

## 示例

### 示例 1: 基本 MSI

```bash
$ python3 msi-generator/msi_generator.py generate App.msi -n "MyApp" -v "1.0.0" -m "MyCompany" -f myapp.exe

MSI created: App.msi
{
    "name": "MyApp",
    "version": "1.0.0",
    "manufacturer": "MyCompany",
    "install_dir": "MyApp",
    "executable": "myapp.exe"
}
```

### 示例 2: 可疑 MSI

```bash
$ python3 msi-generator/msi_generator.py generate-suspicious "Critical Update.msi" "powershell -enc SQBFAFgAKAA="

Suspicious MSI created: Critical Update.msi
Detection hints:
  - Suspicious product name: Critical Update
  - Suspicious manufacturer: Microsoft Update
  - Hidden payload execution
  - Version number pattern: 1.0.4321.1234
```

### 示例 3: 分析 MSI

```bash
$ python3 msi-generator/msi_generator.py analyze suspicious.msi

MSI: suspicious.msi
Suspicious: True

Info:
  title: Critical System Update
  manufacturer: Microsoft Update

Patterns found:
  [high] Hidden execution (WindowStyle Hidden)
  [high] MSI_CUSTOM_ACTION (powershell.exe)
```

## 恶意 MSI 常见特征

| 特征 | 描述 |
|------|------|
| 伪装成系统更新 | "Windows Update", "Critical Update" |
| 伪装制造商 | "Microsoft", "Windows" |
| 隐藏执行 | `WindowStyle Hidden`, `NoVisible` |
| 自定义操作 | PowerShell/VBScript 脚本 |
| 持久化 | 注册表、计划任务、服务 |

## 注意事项

1. **msilib 仅限 Windows**：该模块是 Python Windows 版专属。Linux 下无法直接使用。

2. **Linux 替代方案**：使用 `msitools` 的 `msi` 命令：
   ```bash
   msi make test.msi  # 需要正确的 MSI 结构
   ```

3. **仅用于测试**：生成的 MSI 仅为检测测试目的，不要用于实际恶意活动。

## 参考

- [Python msilib 文档](https://docs.python.org/3/library/msilib.html)
- [Windows Installer SDK](https://docs.microsoft.com/en-us/windows/win32/msi/)
- [MSI 表格参考](https://docs.microsoft.com/en-us/windows/win32/msi/database-tables-reference)

## 许可

本 skill 仅用于防御性安全研究和检测规则开发。
