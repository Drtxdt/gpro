# gpro ：g++报错信息翻译器

## 这是什么

本项目是基于python开发的g++报错信息翻译器，可以通过正则表达式捕获g++编译器生成的错误然后翻译为中文，并且加上修改建议，代替英语输出在终端上。另外，报错中的原始代码我们予以保留。

## 如何使用

要运行本项目，首先您的电脑上应该安装了3.10版本及以上的Python解释器

请在您想要克隆项目的目录下打开中端，执行：

```bash
git clone https://github.com/Drtxdt/gpro.git
```

然后，执行以下命令来切换到项目目录：

```bash
cd gpro
```

目前只支持windows系统（以后会支持mac和Linux），继续在终端中运行：

```bash
.\install.ps1
```

这样一来，我们将本项目添加到了您的环境变量中，并将`python "$projectPath\cpp_translator.py" g++`配置了别名`gpro`

> 如果您在这一步中遇到了终端无法关闭的情况，请另行在任意位置打开终端，运行：
>
> ```powershell
> taskkill /F /IM powershell.exe
> ```
>
> 来强制关闭终端（请放心，我们不是病毒）

下一步，请您运行以下代码以自动安装依赖：

```cpp
pip install -r requirements.txt
```

恭喜，您已经完成了环境配置！！

以后您编译C++文件时，只需在输入命令中把`g++`替换为`gpro`，其余部分正常执行即可

不明白？看看这个例子：

```bash
# 本来应该执行的编译指令
g++ .\test_errors.cpp

# 现在可以使用的翻译项目
gpro .\test_errors.cpp
```

## 如何快速测试

本人明白看到这个项目的都是编程大佬~~不会写错误~~，所以本人在项目中特地搞了一个~~充满错误~~的cpp文件，名称是`test_errors.cpp`，大佬们不妨运行上面的例子来快速测试一下

## 有关那个json文件

注意，`cpp_translator.py`一定要和`cpp_translator_glossary.json`放在同一目录下。以防万一，我在程序中做了处理，如果没有找到`json`文件可以直接在程序中查找现有的错误类型

这个`json`文件可以识别大致50种常见的报错。如果诸位大佬在使用的过程中发现了没有收集到的错误，欢迎来提issue或者PR~