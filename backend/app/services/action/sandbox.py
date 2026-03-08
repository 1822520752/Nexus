"""
安全沙箱执行环境
提供隔离的命令执行环境，包含资源限制和安全控制
"""
import asyncio
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.logger import logger


@dataclass
class ResourceLimits:
    """
    资源限制配置
    
    定义沙箱执行环境的资源限制
    """
    
    max_cpu_time: int = 30          # 最大 CPU 时间（秒）
    max_memory_mb: int = 512        # 最大内存使用（MB）
    max_output_size: int = 10 * 1024 * 1024  # 最大输出大小（字节）
    max_file_size: int = 100 * 1024 * 1024   # 最大文件大小（字节）
    max_processes: int = 5          # 最大子进程数
    max_open_files: int = 100       # 最大打开文件数


@dataclass
class ExecutionResult:
    """
    执行结果
    
    包含命令执行的完整结果信息
    """
    
    success: bool                           # 是否成功
    exit_code: int = 0                      # 退出码
    stdout: str = ""                        # 标准输出
    stderr: str = ""                        # 标准错误
    duration_ms: int = 0                    # 执行耗时（毫秒）
    timed_out: bool = False                 # 是否超时
    memory_used_mb: float = 0.0             # 内存使用（MB）
    working_directory: str = ""             # 工作目录
    environment: Dict[str, str] = field(default_factory=dict)  # 环境变量
    error_message: Optional[str] = None     # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)     # 额外元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含执行结果的字典
        """
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "memory_used_mb": self.memory_used_mb,
            "working_directory": self.working_directory,
            "environment": self.environment,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class SandboxEnvironment:
    """
    沙箱执行环境
    
    提供隔离的命令执行环境，包含资源限制和安全控制
    """
    
    # 默认安全环境变量
    DEFAULT_SAFE_ENV_VARS: List[str] = [
        "PATH",
        "TEMP",
        "TMP",
        "SYSTEMROOT",
        "COMSPEC",
        "PATHEXT",
        "USERPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
        "HOMEPATH",
        "HOMEDRIVE",
        "LOGONSERVER",
        "COMPUTERNAME",
        "USERNAME",
        "USERDOMAIN",
        "OS",
        "PROCESSOR_ARCHITECTURE",
        "NUMBER_OF_PROCESSORS",
    ]
    
    # 危险环境变量（不应传递）
    DANGEROUS_ENV_VARS: List[str] = [
        "PYTHONPATH",
        "PYTHONHOME",
        "PERL5LIB",
        "PERLLIB",
        "RUBYLIB",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
    ]
    
    def __init__(
        self,
        working_directory: Optional[str] = None,
        resource_limits: Optional[ResourceLimits] = None,
        allowed_env_vars: Optional[List[str]] = None,
        custom_env: Optional[Dict[str, str]] = None,
        isolate_filesystem: bool = False,
    ):
        """
        初始化沙箱环境
        
        Args:
            working_directory: 工作目录，None 则使用临时目录
            resource_limits: 资源限制配置
            allowed_env_vars: 允许的环境变量列表
            custom_env: 自定义环境变量
            isolate_filesystem: 是否隔离文件系统
        """
        self.resource_limits = resource_limits or ResourceLimits()
        self.allowed_env_vars = allowed_env_vars or self.DEFAULT_SAFE_ENV_VARS
        self.custom_env = custom_env or {}
        self.isolate_filesystem = isolate_filesystem
        
        # 设置工作目录
        if working_directory:
            self.working_directory = Path(working_directory).absolute()
            self._temp_dir = None
        else:
            self._temp_dir = tempfile.mkdtemp(prefix="nexus_sandbox_")
            self.working_directory = Path(self._temp_dir)
        
        # 确保工作目录存在
        self.working_directory.mkdir(parents=True, exist_ok=True)
        
        # 构建安全的环境变量
        self.environment = self._build_safe_environment()
        
        logger.info(f"沙箱环境初始化完成: {self.working_directory}")
    
    def _build_safe_environment(self) -> Dict[str, str]:
        """
        构建安全的环境变量
        
        Returns:
            过滤后的安全环境变量字典
        """
        env = {}
        
        # 复制允许的环境变量
        for var_name in self.allowed_env_vars:
            if var_name in os.environ:
                env[var_name] = os.environ[var_name]
        
        # 移除危险的环境变量
        for var_name in self.DANGEROUS_ENV_VARS:
            env.pop(var_name, None)
        
        # 添加自定义环境变量
        env.update(self.custom_env)
        
        return env
    
    async def execute(
        self,
        command: str,
        args: Optional[List[str]] = None,
        input_data: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """
        在沙箱中执行命令
        
        Args:
            command: 要执行的命令
            args: 命令参数列表
            input_data: 标准输入数据
            timeout: 超时时间（秒），None 使用默认值
        
        Returns:
            执行结果
        """
        start_time = time.time()
        timeout = timeout or self.resource_limits.max_cpu_time
        
        # 构建完整命令
        full_command = self._build_command(command, args)
        
        logger.info(f"沙箱执行命令: {full_command}")
        logger.debug(f"工作目录: {self.working_directory}")
        
        try:
            # 使用 asyncio 创建子进程
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                cwd=str(self.working_directory),
                env=self.environment,
            )
            
            # 执行并等待结果
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(input_data.encode() if input_data else None),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # 超时，终止进程
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.warning(f"命令执行超时: {full_command}")
                
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    duration_ms=duration_ms,
                    timed_out=True,
                    working_directory=str(self.working_directory),
                    environment=self.environment,
                    error_message=f"命令执行超时（超过 {timeout} 秒）",
                )
            
            # 解码输出
            stdout = self._decode_output(stdout_bytes)
            stderr = self._decode_output(stderr_bytes)
            
            # 截断过长的输出
            if len(stdout) > self.resource_limits.max_output_size:
                stdout = stdout[:self.resource_limits.max_output_size] + "\n... [输出已截断]"
            if len(stderr) > self.resource_limits.max_output_size:
                stderr = stderr[:self.resource_limits.max_output_size] + "\n... [错误输出已截断]"
            
            duration_ms = int((time.time() - start_time) * 1000)
            exit_code = process.returncode or 0
            
            success = exit_code == 0
            
            logger.info(
                f"命令执行完成: {full_command}, "
                f"退出码: {exit_code}, 耗时: {duration_ms}ms"
            )
            
            return ExecutionResult(
                success=success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                timed_out=False,
                working_directory=str(self.working_directory),
                environment=self.environment,
                metadata={
                    "command": full_command,
                    "args": args or [],
                },
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"命令执行异常: {str(e)}"
            
            logger.error(f"{error_msg}\n命令: {full_command}")
            
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_ms=duration_ms,
                timed_out=False,
                working_directory=str(self.working_directory),
                environment=self.environment,
                error_message=error_msg,
            )
    
    async def execute_with_progress(
        self,
        command: str,
        args: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None,
    ) -> ExecutionResult:
        """
        执行命令并实时报告进度
        
        Args:
            command: 要执行的命令
            args: 命令参数列表
            progress_callback: 进度回调函数
        
        Returns:
            执行结果
        """
        start_time = time.time()
        full_command = self._build_command(command, args)
        
        logger.info(f"沙箱执行命令（带进度）: {full_command}")
        
        stdout_chunks = []
        stderr_chunks = []
        
        try:
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_directory),
                env=self.environment,
            )
            
            async def read_stream(stream, chunks, stream_name):
                """读取流并收集输出"""
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = self._decode_output(line)
                    chunks.append(decoded)
                    
                    if progress_callback:
                        await progress_callback(
                            stream_name,
                            decoded,
                            int((time.time() - start_time) * 1000),
                        )
            
            # 并发读取 stdout 和 stderr
            await asyncio.gather(
                read_stream(process.stdout, stdout_chunks, "stdout"),
                read_stream(process.stderr, stderr_chunks, "stderr"),
            )
            
            await process.wait()
            
            duration_ms = int((time.time() - start_time) * 1000)
            exit_code = process.returncode or 0
            
            return ExecutionResult(
                success=exit_code == 0,
                exit_code=exit_code,
                stdout="".join(stdout_chunks),
                stderr="".join(stderr_chunks),
                duration_ms=duration_ms,
                timed_out=False,
                working_directory=str(self.working_directory),
                environment=self.environment,
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"命令执行异常: {str(e)}"
            
            logger.error(error_msg)
            
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="".join(stdout_chunks),
                stderr="".join(stderr_chunks),
                duration_ms=duration_ms,
                timed_out=False,
                working_directory=str(self.working_directory),
                environment=self.environment,
                error_message=error_msg,
            )
    
    def _build_command(self, command: str, args: Optional[List[str]] = None) -> str:
        """
        构建完整命令
        
        Args:
            command: 基础命令
            args: 参数列表
        
        Returns:
            完整的命令字符串
        """
        if args:
            # 转义参数
            escaped_args = [self._escape_arg(arg) for arg in args]
            return f"{command} {' '.join(escaped_args)}"
        return command
    
    def _escape_arg(self, arg: str) -> str:
        """
        转义命令参数
        
        Args:
            arg: 原始参数
        
        Returns:
            转义后的参数
        """
        # Windows 下使用双引号转义
        if " " in arg or '"' in arg:
            arg = arg.replace('"', '""')
            return f'"{arg}"'
        return arg
    
    def _decode_output(self, data: bytes) -> str:
        """
        解码命令输出
        
        Args:
            data: 字节数据
        
        Returns:
            解码后的字符串
        """
        # 尝试多种编码
        encodings = ["utf-8", "gbk", "gb2312", "cp936", "latin-1"]
        
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，使用替换字符
        return data.decode("utf-8", errors="replace")
    
    def create_file(self, relative_path: str, content: str) -> Path:
        """
        在沙箱中创建文件
        
        Args:
            relative_path: 相对于工作目录的路径
            content: 文件内容
        
        Returns:
            创建的文件路径
        """
        file_path = self.working_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        logger.debug(f"创建沙箱文件: {file_path}")
        return file_path
    
    def read_file(self, relative_path: str) -> str:
        """
        读取沙箱中的文件
        
        Args:
            relative_path: 相对于工作目录的路径
        
        Returns:
            文件内容
        """
        file_path = self.working_directory / relative_path
        return file_path.read_text(encoding="utf-8")
    
    def list_files(self, relative_path: str = "") -> List[str]:
        """
        列出沙箱目录中的文件
        
        Args:
            relative_path: 相对于工作目录的路径
        
        Returns:
            文件列表
        """
        dir_path = self.working_directory / relative_path
        if not dir_path.exists():
            return []
        
        return [str(p.relative_to(self.working_directory)) for p in dir_path.iterdir()]
    
    def cleanup(self) -> None:
        """
        清理沙箱环境
        
        删除临时目录和所有文件
        """
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                logger.info(f"沙箱环境已清理: {self._temp_dir}")
            except Exception as e:
                logger.warning(f"清理沙箱环境失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.cleanup()
        return False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        self.cleanup()
        return False


class SandboxManager:
    """
    沙箱管理器
    
    管理多个沙箱环境的创建和销毁
    """
    
    def __init__(self, base_directory: Optional[str] = None):
        """
        初始化沙箱管理器
        
        Args:
            base_directory: 沙箱基础目录
        """
        self.base_directory = Path(base_directory) if base_directory else Path(tempfile.gettempdir())
        self.base_directory.mkdir(parents=True, exist_ok=True)
        self._sandboxes: Dict[str, SandboxEnvironment] = {}
    
    def create_sandbox(
        self,
        sandbox_id: str,
        resource_limits: Optional[ResourceLimits] = None,
        custom_env: Optional[Dict[str, str]] = None,
    ) -> SandboxEnvironment:
        """
        创建新的沙箱环境
        
        Args:
            sandbox_id: 沙箱 ID
            resource_limits: 资源限制
            custom_env: 自定义环境变量
        
        Returns:
            创建的沙箱环境
        """
        sandbox_dir = self.base_directory / f"sandbox_{sandbox_id}"
        sandbox = SandboxEnvironment(
            working_directory=str(sandbox_dir),
            resource_limits=resource_limits,
            custom_env=custom_env,
        )
        
        self._sandboxes[sandbox_id] = sandbox
        logger.info(f"创建沙箱: {sandbox_id}")
        
        return sandbox
    
    def get_sandbox(self, sandbox_id: str) -> Optional[SandboxEnvironment]:
        """
        获取沙箱环境
        
        Args:
            sandbox_id: 沙箱 ID
        
        Returns:
            沙箱环境，不存在则返回 None
        """
        return self._sandboxes.get(sandbox_id)
    
    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """
        销毁沙箱环境
        
        Args:
            sandbox_id: 沙箱 ID
        
        Returns:
            是否成功销毁
        """
        sandbox = self._sandboxes.pop(sandbox_id, None)
        if sandbox:
            sandbox.cleanup()
            logger.info(f"销毁沙箱: {sandbox_id}")
            return True
        return False
    
    def destroy_all(self) -> None:
        """销毁所有沙箱环境"""
        for sandbox_id in list(self._sandboxes.keys()):
            self.destroy_sandbox(sandbox_id)
    
    def list_sandboxes(self) -> List[str]:
        """
        列出所有沙箱 ID
        
        Returns:
            沙箱 ID 列表
        """
        return list(self._sandboxes.keys())
