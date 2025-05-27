import re
import subprocess
import sys
import json
import codecs
from pathlib import Path

class CppErrorTranslator:
    def __init__(self):
        self.glossary = self._load_glossary()
        self.patterns = {
            'missing_semicolon': r"expected ';' (before|at end of)",
            'undefined_reference': r"undefined reference to '(.*?)'",
            'template_args': r"no matching (function|constructor) for call to"
        }
        # Windows编码防范设置
        self.encoding = 'utf-8'  # 强制使用UTF-8编码
        self.error_encodings = ['utf-8', 'gbk', 'iso-8859-1']  # 备选编码列表

    def _load_glossary(self):
        current_dir = Path(__file__).parent
        user_glossary = current_dir / 'cpp_translator_glossary.json'
        try:
            # 强制用UTF-8打开术语库文件
            with open(user_glossary, 'r', encoding='utf-8') as f:
                print("配置加载成功……")
                return json.load(f)
        except FileNotFoundError:
            print("配置加载失败，启用默认配置")
            return {
                "error: expected ';' before '}' token": {
                    "translation": "语法错误：在 '}' 前缺少分号",
                    "severity": "error",
                    "suggestion": "检查结构体/类定义结尾是否添加分号"
                },
                "expected ';' after class definition": {
                    "translation": "语法错误：类定义后缺少分号",
                    "severity": "error",
                    "suggestion": "在类定义结束的右花括号后添加分号，例如：class MyClass { };"
                },
                "'(.*)' in namespace 'std' does not name a type": {
                    "translation": "命名空间std中找不到指定的类型 → $1",
                    "severity": "error",
                    "suggestion": "检查是否包含了正确的头文件，例如string需要包含<string>，vector需要包含<vector>"
                },
                "note: '(.*)' is defined in header '<(.*)>'; this is probably fixable by adding '#include <(.*)>'": {
                    "translation": "提示：'$1'定义在头文件'<$2>'中；可能通过添加'#include <$3>'来修复",
                    "severity": "note",
                    "suggestion": "按照提示添加相应的头文件包含语句"
                },
                "note: suggested alternative: '.*'": {
                    "translation": "提示：建议的替代方案：'$1'",
                    "severity": "note",
                    "suggestion": "尝试使用编译器建议的替代名称"
                },
                "note: in expansion of macro '.*'": {
                    "translation": "提示：在宏'$1'的展开中",
                    "severity": "note",
                    "suggestion": "检查宏定义和使用方式"
                },
                "note: previous declaration of '.*' was here": {
                    "translation": "提示：'$1'的前一个声明在此处",
                    "severity": "note",
                    "suggestion": "检查多重声明的一致性"
                },
                "note: candidate: '.*'": {
                    "translation": "提示：候选函数：'$1'",
                    "severity": "note",
                    "suggestion": "检查函数重载的参数类型是否匹配"
                },
                "undefined reference to '.*'": {
                    "translation": "链接错误：未定义的符号引用 → ",
                    "severity": "error",
                    "suggestion": "确认函数已实现，检查链接库路径和-l参数"
                },
                "no matching function for call to '.*'": {
                    "translation": "函数调用不匹配（参数类型或数量错误）⇨ ",
                    "severity": "error",
                    "suggestion": "检查函数重载版本或使用static_cast明确类型"
                },
                "template argument deduction failed": {
                    "translation": "模板参数推导失败（无法推断模板类型）",
                    "severity": "error",
                    "suggestion": "尝试显式指定模板参数，如func<int>(...)"
                },
                "use of deleted function '.*'": {
                    "translation": "错误：尝试使用被删除的函数",
                    "severity": "error",
                    "suggestion": "检查是否对移动构造函数使用了=delete"
                },
                "invalid conversion from '.*' to '.*'": {
                    "translation": "类型转换错误：从 [类型A] 到 [类型B] 的转换无效",
                    "severity": "error",
                    "suggestion": "检查static_cast/dynamic_cast的使用场景"
                },
                "control reaches end of non-void function": {
                    "translation": "警告：非void函数可能没有返回值",
                    "severity": "warning",
                    "suggestion": "检查所有代码路径是否都有return语句"
                },
                "implicit declaration of function '.*'": {
                    "translation": "隐式函数声明错误：使用了未声明的函数 → ",
                    "severity": "error",
                    "suggestion": "添加适当的头文件或在使用前声明函数"
                },
                "variable '.*' set but not used": {
                    "translation": "变量被设置但未使用 → ",
                    "severity": "warning",
                    "suggestion": "删除未使用的变量或将其标记为[[maybe_unused]]"
                },
                "comparison between signed and unsigned": {
                    "translation": "有符号与无符号整数比较警告",
                    "severity": "warning",
                    "suggestion": "确保比较操作数类型一致，使用适当的类型转换"
                },
                "unused variable '.*'": {
                    "translation": "未使用的变量 → ",
                    "severity": "warning",
                    "suggestion": "删除未使用的变量或将其标记为[[maybe_unused]]"
                },
                "expected '\\)' before '.*'": {
                    "translation": "语法错误：缺少右括号')'",
                    "severity": "error",
                    "suggestion": "检查括号是否配对，特别是在复杂表达式中"
                },
                "expected identifier or '\\(' before '.*'": {
                    "translation": "语法错误：预期标识符或'('",
                    "severity": "error",
                    "suggestion": "检查语法结构，可能是关键字拼写错误或缺少标识符"
                },
                "'.*' was not declared in this scope": {
                    "translation": "未声明的标识符：在当前作用域中找不到 → ",
                    "severity": "error",
                    "suggestion": "检查变量名拼写或添加适当的命名空间(如std::)"
                },
                "redefinition of '.*'": {
                    "translation": "重复定义错误 → ",
                    "severity": "error",
                    "suggestion": "检查是否在多个地方定义了同名变量或函数"
                },
                "expected initializer before '.*'": {
                    "translation": "语法错误：预期初始化器",
                    "severity": "error",
                    "suggestion": "检查变量声明语法，确保正确初始化"
                },
                "cannot convert '.*' to '.*' in initialization": {
                    "translation": "初始化时类型转换错误",
                    "severity": "error",
                    "suggestion": "使用兼容类型或显式类型转换"
                },
                "taking address of temporary": {
                    "translation": "错误：获取临时对象的地址",
                    "severity": "error",
                    "suggestion": "临时对象生命周期有限，避免获取其地址"
                },
                "narrowing conversion of '.*' from '.*' to '.*'": {
                    "translation": "窄化转换警告：可能丢失数据精度",
                    "severity": "warning",
                    "suggestion": "使用static_cast显式转换或修改变量类型"
                },
                "division by zero": {
                    "translation": "错误：除以零",
                    "severity": "error",
                    "suggestion": "检查除法操作，确保除数不为零"
                },
                "array subscript is not an integer": {
                    "translation": "数组下标不是整数",
                    "severity": "error",
                    "suggestion": "确保数组索引是整数类型"
                },
                "array subscript out of bounds": {
                    "translation": "数组下标越界",
                    "severity": "error",
                    "suggestion": "检查数组访问，确保索引在有效范围内"
                },
                "invalid operands of types '.*' and '.*' to binary '.*'": {
                    "translation": "二元运算符操作数类型无效",
                    "severity": "error",
                    "suggestion": "检查操作数类型是否支持该运算符，或使用适当的类型转换"
                },
                "expected constructor, destructor, or type conversion before '.*'": {
                    "translation": "语法错误：预期构造函数、析构函数或类型转换",
                    "severity": "error",
                    "suggestion": "检查类定义语法，特别是构造函数和析构函数的声明"
                },
                "'.*' is not a member of '.*'": {
                    "translation": "成员访问错误：指定的成员不存在 → ",
                    "severity": "error",
                    "suggestion": "检查类/结构体定义，确认成员名称拼写正确"
                },
                "'.*' in '.*' does not name a type": {
                    "translation": "类型名称错误：指定的名称不是类型 → ",
                    "severity": "error",
                    "suggestion": "检查类型名称拼写或添加适当的命名空间"
                },
                "'.*' is not a class, namespace, or enumeration": {
                    "translation": "作用域解析错误：指定的名称不是类、命名空间或枚举 → ",
                    "severity": "error",
                    "suggestion": "检查名称拼写或确认该标识符的正确类型"
                },
                "expected unqualified-id before '.*'": {
                    "translation": "语法错误：预期标识符",
                    "severity": "error",
                    "suggestion": "检查语法结构，可能是缺少标识符或语法错误"
                },
                "conflicting declaration '.*'": {
                    "translation": "冲突声明 → ",
                    "severity": "error",
                    "suggestion": "检查变量或函数的多处声明是否一致"
                },
                "ISO C\\+\\+ forbids declaration of '.*' with no type": {
                    "translation": "C++标准禁止无类型声明 → ",
                    "severity": "error",
                    "suggestion": "添加适当的类型说明符"
                },
                "expected '=', ',', ';', 'asm' or '__attribute__' before '.*'": {
                    "translation": "语法错误：预期 =, ,, ;, asm 或 __attribute__",
                    "severity": "error",
                    "suggestion": "检查语法结构，可能是缺少分隔符或语法错误"
                },
                "invalid use of incomplete type '.*'": {
                    "translation": "使用不完整类型错误 → ",
                    "severity": "error",
                    "suggestion": "确保在使用前完整定义类型，而仅仅是前向声明"
                },
                "no matching function for call to '.*::.*'": {
                    "translation": "类成员函数调用不匹配 → ",
                    "severity": "error",
                    "suggestion": "检查成员函数参数类型和数量是否正确"
                },
                "cannot bind non-const lvalue reference of type '.*' to an rvalue of type '.*'": {
                    "translation": "非const左值引用无法绑定到右值",
                    "severity": "error",
                    "suggestion": "使用const引用或值传递，或确保传递左值"
                },
                "expected primary-expression before '.*'": {
                    "translation": "语法错误：预期基本表达式",
                    "severity": "error",
                    "suggestion": "检查表达式语法，可能是缺少操作数或语法错误"
                },
                "expected '}' before end of line": {
                    "translation": "语法错误：预期右花括号'}'",
                    "severity": "error",
                    "suggestion": "检查花括号是否配对，特别是在复杂代码块中"
                },
                "'.*' has incomplete type and cannot be defined": {
                    "translation": "不完整类型定义错误 → ",
                    "severity": "error",
                    "suggestion": "确保在定义前完整声明类型"
                },
                "'.*' was not declared in this scope; did you mean '.*'?": {
                    "translation": "未声明的标识符（可能是拼写错误）→ ",
                    "severity": "error",
                    "suggestion": "使用编译器建议的替代名称或检查拼写"
                },
                "missing terminating \" character": {
                    "translation": "字符串缺少结束引号",
                    "severity": "error",
                    "suggestion": "检查字符串是否正确闭合，特别是多行字符串"
                },
                "stray '\\' in program": {
                    "translation": "程序中有游离的反斜杠字符",
                    "severity": "error",
                    "suggestion": "检查字符串或字符常量中的转义序列是否正确"
                },
                "unknown escape sequence": {
                    "translation": "未知的转义序列",
                    "severity": "warning",
                    "suggestion": "检查字符串中的转义序列，确保使用有效的转义字符"
                },
                "format '.*' expects argument of type '.*', but argument .* has type '.*'": {
                    "translation": "格式化字符串类型不匹配",
                    "severity": "warning",
                    "suggestion": "确保printf/scanf等函数的格式说明符与参数类型匹配"
                },
                "too few arguments for format": {
                    "translation": "格式化字符串参数过少",
                    "severity": "warning",
                    "suggestion": "检查printf/scanf等函数的格式说明符数量是否与提供的参数数量一致"
                },
                "too many arguments for format": {
                    "translation": "格式化字符串参数过多",
                    "severity": "warning",
                    "suggestion": "检查printf/scanf等函数的格式说明符数量是否与提供的参数数量一致"
                },
                "statement has no effect": {
                    "translation": "语句没有效果",
                    "severity": "warning",
                    "suggestion": "检查是否误用了;或写了无效的表达式语句"
                },
                "suggest parentheses around assignment used as truth value": {
                    "translation": "建议在用作条件的赋值表达式外加括号",
                    "severity": "warning",
                    "suggestion": "使用if (x = y)容易与if (x == y)混淆，建议使用if ((x = y))明确意图"
                },
                "suggest braces around empty body in an 'if' statement": {
                    "translation": "建议在空的if语句体周围加上花括号",
                    "severity": "warning",
                    "suggestion": "使用{}明确表示空语句块，如if (condition) {}"
                },
                "enumeration value '.*' not handled in switch": {
                    "translation": "switch语句中未处理枚举值 → ",
                    "severity": "warning",
                    "suggestion": "添加缺失的case分支或使用default分支处理"
                },
                "no return statement in function returning non-void": {
                    "translation": "非void函数缺少return语句",
                    "severity": "error",
                    "suggestion": "在所有执行路径上添加适当的return语句"
                },
                "address of local variable '.*' returned": {
                    "translation": "返回局部变量的地址",
                    "severity": "warning",
                    "suggestion": "局部变量在函数返回后被销毁，返回其地址可能导致悬垂指针"
                },
                "comparison of unsigned expression .* is always (true|false)": {
                    "translation": "无符号表达式比较总是为真/假",
                    "severity": "warning",
                    "suggestion": "检查逻辑错误，无符号数与0比较时可能导致意外结果"
                },
                "passing '.*' chooses '.*' over '.*'": {
                    "translation": "参数传递选择了意外的重载函数",
                    "severity": "warning",
                    "suggestion": "使用显式类型转换或修改参数类型以选择正确的重载版本"
                },
                "unused parameter '.*'": {
                    "translation": "未使用的参数 → ",
                    "severity": "warning",
                    "suggestion": "删除未使用的参数或将其标记为[[maybe_unused]]"
                }
                # ... 其他默认术语保持不变
            }
        except json.JSONDecodeError as e:
            print(f"术语库格式错误：{e}")
            return {}

    def _decoder(self, byte_data):
        """多重编码尝试解码"""
        for encoding in self.error_encodings:
            try:
                return byte_data.decode(encoding)
            except UnicodeDecodeError:
                continue
        # 全部失败时替换非法字符
        return byte_data.decode(self.encoding, errors='replace')

    def _enhance_translation(self, raw_error, translated, suggestion=None):
        """新增错误高亮匹配和建议输出"""
        line = raw_error.strip()
        result = translated
        
        if any(k in line for k in ['error:', 'warning:']):
            result = f"🚨 {translated}"
        
        # 如果有建议，添加到翻译后的文本中
        if suggestion:
            result += f"\n💡 建议: {suggestion}"
            
        return result

    def translate_line(self, line):
        """支持正则表达式键名匹配，并返回翻译和建议"""
        for pattern, details in self.glossary.items():
            try:
                if re.search(pattern, line, re.IGNORECASE):
                    translation = details['translation']
                    suggestion = details.get('suggestion', None)
                    
                    # 动态提取变量（如函数名）
                    if '(.*?)' in pattern:
                        match = re.search(pattern.replace('.*?', '(.*?)'), line)
                        if match:
                            translation += f" » {match.group(1)}"
                            
                    # 处理正则表达式捕获组替换
                    if '$' in translation and re.search(pattern, line):
                        match = re.search(pattern, line)
                        if match:
                            for i in range(1, len(match.groups()) + 1):
                                translation = translation.replace(f'${i}', match.group(i))
                    
                    # 同样处理建议中的捕获组
                    if suggestion and '$' in suggestion and re.search(pattern, line):
                        match = re.search(pattern, line)
                        if match:
                            for i in range(1, len(match.groups()) + 1):
                                suggestion = suggestion.replace(f'${i}', match.group(i))
                                
                    return translation, suggestion
            except re.error:
                if pattern in line:
                    return details['translation'], details.get('suggestion', None)
        return line, None

    def run_compiler(self, args):
        """改进的解码处理流程"""
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=False  # 禁用自动解码
        )

        # 实时捕获并处理字节流
        while True:
            raw_byte = proc.stdout.readline()
            if not raw_byte and proc.poll() is not None:
                break
            try:
                # 尝试多重解码
                decoded_line = self._decoder(raw_byte).strip()
            except Exception as e:
                decoded_line = f"解码失败：{str(e)} | 原始数据: {raw_byte.hex()}"

            if decoded_line:
                translated, suggestion = self.translate_line(decoded_line)
                enhanced = self._enhance_translation(decoded_line, translated, suggestion)
                
                # Windows兼容颜色输出
                if sys.platform == 'win32':
                    from colorama import init, Fore
                    init()
                    print(Fore.RED + enhanced + Fore.RESET)
                else:
                    print(f"\033[31m{enhanced}\033[0m")

        return proc.returncode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python cpp_translator.py [编译命令]")
        print("示例: python cpp_translator.py 'g++ -std=c++11 test.cpp'")
        sys.exit(1)

    # Windows命令行参数特殊处理
    if sys.platform == 'win32':
        import sys
        from subprocess import list2cmdline
        args = list2cmdline(sys.argv[1:])
    else:
        args = sys.argv[1:]

    translator = CppErrorTranslator()
    sys.exit(translator.run_compiler(args))