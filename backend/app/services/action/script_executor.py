"""
自定义 Python 脚本执行器
提供安全的脚本执行环境、模板管理和输入输出处理
"""
import ast
import asyncio
import builtins
import io
import sys
import textwrap
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union

from app.core.logger import logger
from app.services.action.action_registry import (
    ActionCategory,
    ActionMetadata,
    ActionParameter,
    ActionResult,
    action_registry,
)


@dataclass
class ScriptTemplate:
    """
    脚本模板
    
    预定义的脚本模板，包含名称、描述和代码
    """
    
    name: str                                   # 模板名称
    description: str                            # 模板描述
    code: str                                   # 模板代码
    parameters: List[Dict[str, Any]] = field(default_factory=list)  # 参数定义
    category: str = "general"                   # 分类
    tags: List[str] = field(default_factory=list)  # 标签
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含模板信息的字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "parameters": self.parameters,
            "category": self.category,
            "tags": self.tags,
        }


class ScriptSandbox:
    """
    脚本沙箱
    
    提供安全的 Python 脚本执行环境
    """
    
    # 允许的安全内置函数
    SAFE_BUILTINS: Set[str] = {
        # 基础类型
        "int", "float", "str", "bool", "list", "dict", "set", "tuple",
        "bytes", "bytearray", "complex", "frozenset",
        # 类型检查
        "type", "isinstance", "issubclass", "hasattr", "callable",
        # 数学和逻辑
        "abs", "all", "any", "bin", "chr", "divmod", "enumerate",
        "filter", "format", "hex", "len", "map", "max", "min",
        "oct", "ord", "pow", "range", "repr", "reversed", "round",
        "sorted", "sum", "zip",
        # 迭代器
        "iter", "next", "slice",
        # 字符串处理
        "ascii", "capitalize", "center", "count", "encode", "decode",
        "endswith", "find", "format", "index", "isalnum", "isalpha",
        "isdigit", "islower", "isspace", "istitle", "isupper",
        "join", "lower", "lstrip", "replace", "rfind", "rindex",
        "rsplit", "rstrip", "split", "splitlines", "startswith",
        "strip", "swapcase", "title", "upper",
        # 其他安全函数
        "print", "input", "open",  # open 将被限制
        "help", "id", "locals", "globals", "vars",
    }
    
    # 禁止的模块
    BLOCKED_MODULES: Set[str] = {
        "os", "subprocess", "sys", "importlib", "ctypes",
        "multiprocessing", "threading", "socket", "socketserver",
        "asyncio", "concurrent", "pickle", "shelve", "marshal",
        "shutil", "tempfile", "glob", "fnmatch", "linecache",
        "code", "codeop", "compile", "exec", "eval",
    }
    
    # 允许的安全模块
    ALLOWED_MODULES: Set[str] = {
        "math", "random", "statistics", "decimal", "fractions",
        "datetime", "time", "calendar",
        "re", "string", "textwrap", "unicodedata",
        "json", "csv", "configparser",
        "collections", "itertools", "functools", "operator",
        "copy", "pprint", "reprlib",
        "typing", "dataclasses", "enum",
        "pathlib",  # 受限使用
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_memory_mb: int = 256,
        max_output_size: int = 1024 * 1024,  # 1MB
        allowed_modules: Optional[Set[str]] = None,
        blocked_modules: Optional[Set[str]] = None,
        extra_builtins: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化脚本沙箱
        
        Args:
            timeout: 执行超时时间（秒）
            max_memory_mb: 最大内存使用（MB）
            max_output_size: 最大输出大小（字节）
            allowed_modules: 允许的模块列表
            blocked_modules: 禁止的模块列表
            extra_builtins: 额外的内置函数
        """
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.max_output_size = max_output_size
        self.allowed_modules = allowed_modules or self.ALLOWED_MODULES
        self.blocked_modules = blocked_modules or self.BLOCKED_MODULES
        self.extra_builtins = extra_builtins or {}
        
        # 构建安全的内置函数字典
        self._safe_builtins = self._build_safe_builtins()
    
    def _build_safe_builtins(self) -> Dict[str, Any]:
        """
        构建安全的内置函数字典
        
        Returns:
            安全的内置函数字典
        """
        safe = {}
        
        for name in self.SAFE_BUILTINS:
            if hasattr(builtins, name):
                safe[name] = getattr(builtins, name)
        
        # 添加受限的 open 函数
        safe["open"] = self._restricted_open
        
        # 添加额外的内置函数
        safe.update(self.extra_builtins)
        
        return safe
    
    def _restricted_open(self, file, mode="r", *args, **kwargs):
        """
        受限的 open 函数
        
        只允许读取当前工作目录下的文件
        
        Args:
            file: 文件路径
            mode: 打开模式
        
        Returns:
            文件对象
        
        Raises:
            PermissionError: 权限错误
        """
        import os
        from pathlib import Path
        
        # 只允许读取模式
        if "w" in mode or "a" in mode or "x" in mode:
            raise PermissionError("沙箱环境不允许写入文件")
        
        # 解析路径
        file_path = Path(file)
        
        # 检查是否为绝对路径
        if file_path.is_absolute():
            # 只允许访问临时目录
            temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMP", ".")))
            try:
                file_path.relative_to(temp_dir)
            except ValueError:
                raise PermissionError(f"沙箱环境不允许访问路径: {file}")
        
        return builtins.open(file, mode, *args, **kwargs)
    
    def _create_restricted_globals(
        self,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建受限的全局命名空间
        
        Args:
            input_data: 输入数据
        
        Returns:
            受限的全局命名空间
        """
        # 创建受限的导入函数
        def restricted_import(name, *args, **kwargs):
            # 检查模块是否被禁止
            module_name = name.split(".")[0]
            if module_name in self.blocked_modules:
                raise ImportError(f"模块 '{name}' 在沙箱环境中被禁止")
            
            # 检查模块是否被允许
            if module_name not in self.allowed_modules:
                raise ImportError(f"模块 '{name}' 不在允许列表中")
            
            return __import__(name, *args, **kwargs)
        
        # 构建全局命名空间
        globals_dict = {
            "__builtins__": self._safe_builtins,
            "__import__": restricted_import,
            "__name__": "__main__",
            "__doc__": None,
        }
        
        # 添加输入数据
        if input_data:
            globals_dict.update(input_data)
        
        return globals_dict
    
    def validate_script(self, code: str) -> List[str]:
        """
        验证脚本安全性
        
        检查脚本是否包含不安全的代码
        
        Args:
            code: 脚本代码
        
        Returns:
            警告信息列表
        """
        warnings = []
        
        try:
            # 解析 AST
            tree = ast.parse(code)
            
            # 遍历 AST 检查不安全操作
            for node in ast.walk(tree):
                # 检查导入
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        if module_name in self.blocked_modules:
                            warnings.append(f"禁止导入模块: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                        if module_name in self.blocked_modules:
                            warnings.append(f"禁止从模块导入: {node.module}")
                
                # 检查 exec 和 eval
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ("exec", "eval", "compile"):
                            warnings.append(f"禁止使用函数: {node.func.id}")
                
                # 检查属性访问
                elif isinstance(node, ast.Attribute):
                    if node.attr.startswith("_"):
                        warnings.append(f"禁止访问私有属性: {node.attr}")
            
        except SyntaxError as e:
            warnings.append(f"语法错误: {e}")
        
        return warnings
    
    def execute(
        self,
        code: str,
        input_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> ActionResult:
        """
        执行脚本
        
        在沙箱环境中执行 Python 脚本
        
        Args:
            code: 脚本代码
            input_data: 输入数据（将作为全局变量传入）
            timeout: 执行超时时间（秒）
        
        Returns:
            执行结果
        """
        import time
        
        start_time = time.time()
        timeout = timeout or self.timeout
        
        logger.info(f"执行脚本, 超时: {timeout}s")
        
        # 验证脚本
        warnings = self.validate_script(code)
        if warnings:
            logger.warning(f"脚本验证警告: {warnings}")
        
        # 创建输出缓冲区
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        # 创建受限的全局命名空间
        globals_dict = self._create_restricted_globals(input_data)
        
        # 添加结果变量
        result_var = "__result__"
        globals_dict[result_var] = None
        
        # 包装代码以捕获结果
        wrapped_code = textwrap.dedent(f"""
{code}

# 尝试获取结果
if 'result' in dir():
    __result__ = result
elif 'output' in dir():
    __result__ = output
""")
        
        try:
            # 重定向输出
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # 执行代码
                exec(wrapped_code, globals_dict)
            
            # 获取执行结果
            result = globals_dict.get(result_var)
            
            # 获取输出
            stdout = stdout_buffer.getvalue()
            stderr = stderr_buffer.getvalue()
            
            # 截断过长的输出
            if len(stdout) > self.max_output_size:
                stdout = stdout[:self.max_output_size] + "\n... [输出已截断]"
            if len(stderr) > self.max_output_size:
                stderr = stderr[:self.max_output_size] + "\n... [错误输出已截断]"
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"脚本执行完成, 耗时: {duration_ms}ms")
            
            return ActionResult(
                success=True,
                data={
                    "result": result,
                    "stdout": stdout,
                    "stderr": stderr,
                    "variables": {
                        k: str(v)[:1000]  # 限制变量值长度
                        for k, v in globals_dict.items()
                        if not k.startswith("_") and k not in ("__builtins__", "__import__")
                    },
                },
                message="脚本执行成功",
                duration_ms=duration_ms,
                metadata={
                    "warnings": warnings,
                },
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 获取错误信息
            error_type = type(e).__name__
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            
            # 获取输出
            stdout = stdout_buffer.getvalue()
            stderr = stderr_buffer.getvalue()
            
            logger.error(f"脚本执行失败: {error_type}: {error_msg}")
            
            return ActionResult(
                success=False,
                error=f"{error_type}: {error_msg}",
                data={
                    "stdout": stdout,
                    "stderr": stderr,
                    "traceback": traceback_str,
                },
                duration_ms=duration_ms,
                metadata={
                    "warnings": warnings,
                    "error_type": error_type,
                },
            )


class ScriptTemplateManager:
    """
    脚本模板管理器
    
    管理预定义的脚本模板
    """
    
    def __init__(self):
        """
        初始化模板管理器
        """
        self._templates: Dict[str, ScriptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """
        加载默认模板
        """
        # 数学计算模板
        self.register_template(ScriptTemplate(
            name="math_calculation",
            description="数学计算模板",
            code=textwrap.dedent("""
                # 数学计算
                import math
                
                # 输入参数
                expression = expression  # 数学表达式
                
                # 计算
                try:
                    result = eval(expression, {"math": math, "__builtins__": {}})
                    print(f"结果: {result} - script_executor.py:447")
                except Exception as e:
                    print(f"计算错误: {e} - script_executor.py:449")
                    result = None
            """),
            parameters=[
                {"name": "expression", "type": "str", "description": "数学表达式", "required": True},
            ],
            category="math",
            tags=["math", "calculation"],
        ))
        
        # 数据处理模板
        self.register_template(ScriptTemplate(
            name="data_processing",
            description="数据处理模板",
            code=textwrap.dedent("""
                # 数据处理
                import json
                from collections import Counter
                
                # 输入数据
                data = data
                
                # 处理数据
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        pass
                
                # 统计
                if isinstance(data, (list, tuple)):
                    counter = Counter(data)
                    result = {
                        "count": len(data),
                        "unique": len(counter),
                        "most_common": counter.most_common(10),
                    }
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                elif isinstance(data, dict):
                    result = {
                        "keys": list(data.keys()),
                        "values_count": len(data),
                    }
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    result = {"type": type(data).__name__, "value": str(data)}
                    print(json.dumps(result, indent=2, ensure_ascii=False))
            """),
            parameters=[
                {"name": "data", "type": "any", "description": "输入数据", "required": True},
            ],
            category="data",
            tags=["data", "processing", "json"],
        ))
        
        # 文本处理模板
        self.register_template(ScriptTemplate(
            name="text_processing",
            description="文本处理模板",
            code=textwrap.dedent("""
                # 文本处理
                import re
                from collections import Counter
                
                # 输入文本
                text = text
                
                # 分析文本
                words = re.findall(r'\\w+', text.lower())
                chars = len(text)
                lines = text.count('\\n') + 1
                
                # 词频统计
                word_freq = Counter(words)
                
                result = {
                    "characters": chars,
                    "words": len(words),
                    "lines": lines,
                    "unique_words": len(word_freq),
                    "top_words": word_freq.most_common(10),
                }
                
                print(f"字符数: {chars} - script_executor.py:532")
                print(f"单词数: {len(words)} - script_executor.py:533")
                print(f"行数: {lines} - script_executor.py:534")
                print(f"不重复单词: {len(word_freq)} - script_executor.py:535")
            """),
            parameters=[
                {"name": "text", "type": "str", "description": "输入文本", "required": True},
            ],
            category="text",
            tags=["text", "analysis", "nlp"],
        ))
        
        # JSON 处理模板
        self.register_template(ScriptTemplate(
            name="json_processing",
            description="JSON 数据处理模板",
            code=textwrap.dedent("""
                # JSON 处理
                import json
                
                # 输入 JSON 字符串
                json_str = json_str
                
                # 解析 JSON
                try:
                    data = json.loads(json_str)
                    
                    # 格式化输出
                    formatted = json.dumps(data, indent=2, ensure_ascii=False)
                    print(formatted)
                    
                    result = data
                except json.JSONDecodeError as e:
                    print(f"JSON 解析错误: {e} - script_executor.py:565")
                    result = None
            """),
            parameters=[
                {"name": "json_str", "type": "str", "description": "JSON 字符串", "required": True},
            ],
            category="data",
            tags=["json", "parsing"],
        ))
        
        # 日期时间模板
        self.register_template(ScriptTemplate(
            name="datetime_processing",
            description="日期时间处理模板",
            code=textwrap.dedent("""
                # 日期时间处理
                from datetime import datetime, timedelta
                
                # 输入参数
                operation = operation  # 操作类型: add, subtract, format, parse
                date_str = date_str    # 日期字符串
                days = days            # 天数
                
                now = datetime.now()
                
                if operation == "add":
                    result = now + timedelta(days=days)
                    print(f"当前时间: {now} - script_executor.py:592")
                    print(f"加 {days} 天后: {result} - script_executor.py:593")
                elif operation == "subtract":
                    result = now - timedelta(days=days)
                    print(f"当前时间: {now} - script_executor.py:596")
                    print(f"减 {days} 天后: {result} - script_executor.py:597")
                elif operation == "format":
                    if date_str:
                        dt = datetime.fromisoformat(date_str)
                    else:
                        dt = now
                    result = dt.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"格式化结果: {result} - script_executor.py:604")
                elif operation == "parse":
                    dt = datetime.fromisoformat(date_str)
                    result = dt
                    print(f"解析结果: {dt} - script_executor.py:608")
                else:
                    print(f"当前时间: {now} - script_executor.py:610")
                    result = now.isoformat()
            """),
            parameters=[
                {"name": "operation", "type": "str", "description": "操作类型", "required": True, "choices": ["add", "subtract", "format", "parse"]},
                {"name": "date_str", "type": "str", "description": "日期字符串", "required": False},
                {"name": "days", "type": "int", "description": "天数", "required": False, "default": 0},
            ],
            category="datetime",
            tags=["datetime", "date", "time"],
        ))
    
    def register_template(self, template: ScriptTemplate) -> None:
        """
        注册模板
        
        Args:
            template: 脚本模板
        """
        self._templates[template.name] = template
        logger.info(f"注册脚本模板: {template.name}")
    
    def get_template(self, name: str) -> Optional[ScriptTemplate]:
        """
        获取模板
        
        Args:
            name: 模板名称
        
        Returns:
            脚本模板，不存在则返回 None
        """
        return self._templates.get(name)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ScriptTemplate]:
        """
        列出模板
        
        Args:
            category: 按分类过滤
            tags: 按标签过滤
        
        Returns:
            模板列表
        """
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def delete_template(self, name: str) -> bool:
        """
        删除模板
        
        Args:
            name: 模板名称
        
        Returns:
            是否成功删除
        """
        if name in self._templates:
            del self._templates[name]
            logger.info(f"删除脚本模板: {name}")
            return True
        return False


# 创建全局实例
script_sandbox = ScriptSandbox()
template_manager = ScriptTemplateManager()


def execute_script(
    code: str,
    input_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    validate: bool = True,
) -> ActionResult:
    """
    执行 Python 脚本
    
    在安全沙箱中执行 Python 脚本
    
    Args:
        code: 脚本代码
        input_data: 输入数据
        timeout: 执行超时时间（秒）
        validate: 是否验证脚本安全性
    
    Returns:
        执行结果
    """
    logger.info("执行自定义脚本")
    
    # 创建沙箱
    sandbox = ScriptSandbox(timeout=timeout)
    
    # 验证脚本
    if validate:
        warnings = sandbox.validate_script(code)
        # 检查是否有严重警告
        blocked_warnings = [w for w in warnings if "禁止" in w]
        if blocked_warnings:
            return ActionResult(
                success=False,
                error="脚本包含不安全代码",
                data={"warnings": warnings},
            )
    
    # 执行脚本
    return sandbox.execute(code, input_data, timeout)


def execute_template(
    template_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> ActionResult:
    """
    执行脚本模板
    
    使用预定义模板执行脚本
    
    Args:
        template_name: 模板名称
        parameters: 模板参数
        timeout: 执行超时时间（秒）
    
    Returns:
        执行结果
    """
    logger.info(f"执行脚本模板: {template_name}")
    
    # 获取模板
    template = template_manager.get_template(template_name)
    if not template:
        return ActionResult(
            success=False,
            error=f"模板不存在: {template_name}",
        )
    
    # 准备输入数据
    input_data = parameters or {}
    
    # 执行脚本
    return execute_script(
        code=template.code,
        input_data=input_data,
        timeout=timeout,
        validate=False,  # 模板已预验证
    )


def list_templates(
    category: Optional[str] = None,
) -> ActionResult:
    """
    列出脚本模板
    
    列出所有可用的脚本模板
    
    Args:
        category: 按分类过滤
    
    Returns:
        模板列表
    """
    templates = template_manager.list_templates(category=category)
    
    return ActionResult(
        success=True,
        data={
            "templates": [t.to_dict() for t in templates],
            "count": len(templates),
        },
        message=f"找到 {len(templates)} 个模板",
    )


def validate_script(code: str) -> ActionResult:
    """
    验证脚本安全性
    
    检查脚本是否包含不安全的代码
    
    Args:
        code: 脚本代码
    
    Returns:
        验证结果
    """
    sandbox = ScriptSandbox()
    warnings = sandbox.validate_script(code)
    
    # 检查语法
    try:
        ast.parse(code)
        syntax_valid = True
    except SyntaxError as e:
        syntax_valid = False
        warnings.append(f"语法错误: {e}")
    
    # 判断是否安全
    is_safe = not any("禁止" in w for w in warnings)
    
    return ActionResult(
        success=syntax_valid and is_safe,
        data={
            "is_safe": is_safe,
            "syntax_valid": syntax_valid,
            "warnings": warnings,
        },
        message="脚本验证通过" if is_safe else "脚本包含不安全代码",
    )


# 注册动作到注册表
def _register_actions():
    """
    注册所有脚本执行动作
    """
    # 执行脚本
    action_registry.register(
        name="script.execute",
        display_name="执行脚本",
        description="在安全沙箱中执行 Python 脚本",
        category=ActionCategory.SCRIPT,
        executor=execute_script,
        parameters=[
            ActionParameter(
                name="code",
                type="str",
                description="Python 脚本代码",
                required=True,
            ),
            ActionParameter(
                name="input_data",
                type="dict",
                description="输入数据（将作为全局变量传入）",
                required=False,
            ),
            ActionParameter(
                name="timeout",
                type="int",
                description="执行超时时间（秒）",
                required=False,
                default=30,
                min_value=1,
                max_value=300,
            ),
            ActionParameter(
                name="validate",
                type="bool",
                description="是否验证脚本安全性",
                required=False,
                default=True,
            ),
        ],
        returns="执行结果，包含输出和返回值",
        examples=[
            {
                "code": "print('Hello, World!')\nresult = 1 + 1",
            },
            {
                "code": "import math\nresult = math.sqrt(16)\nprint(f'平方根: {result}')",
            },
        ],
        tags=["script", "python", "execute"],
    )
    
    # 执行模板
    action_registry.register(
        name="script.execute_template",
        display_name="执行脚本模板",
        description="使用预定义模板执行脚本",
        category=ActionCategory.SCRIPT,
        executor=execute_template,
        parameters=[
            ActionParameter(
                name="template_name",
                type="str",
                description="模板名称",
                required=True,
            ),
            ActionParameter(
                name="parameters",
                type="dict",
                description="模板参数",
                required=False,
            ),
            ActionParameter(
                name="timeout",
                type="int",
                description="执行超时时间（秒）",
                required=False,
                default=30,
            ),
        ],
        returns="执行结果",
        examples=[
            {
                "template_name": "math_calculation",
                "parameters": {"expression": "2 ** 10"},
            },
            {
                "template_name": "text_processing",
                "parameters": {"text": "Hello World! This is a test."},
            },
        ],
        tags=["script", "template", "execute"],
    )
    
    # 列出模板
    action_registry.register(
        name="script.list_templates",
        display_name="列出脚本模板",
        description="列出所有可用的脚本模板",
        category=ActionCategory.SCRIPT,
        executor=list_templates,
        parameters=[
            ActionParameter(
                name="category",
                type="str",
                description="按分类过滤",
                required=False,
            ),
        ],
        returns="模板列表",
        examples=[{}],
        tags=["script", "template", "list"],
    )
    
    # 验证脚本
    action_registry.register(
        name="script.validate",
        display_name="验证脚本",
        description="检查脚本是否包含不安全的代码",
        category=ActionCategory.SCRIPT,
        executor=validate_script,
        parameters=[
            ActionParameter(
                name="code",
                type="str",
                description="Python 脚本代码",
                required=True,
            ),
        ],
        returns="验证结果",
        examples=[
            {"code": "import os\nos.system('ls')"},
        ],
        tags=["script", "validate", "security"],
    )


# 模块加载时自动注册
_register_actions()
