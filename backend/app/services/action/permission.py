"""
安全沙箱权限模型
定义命令执行的权限级别和检查机制
"""
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.core.logger import logger


class PermissionLevel(str, Enum):
    """
    权限级别枚举
    
    定义不同风险等级的操作权限
    """
    
    SAFE = "safe"           # 安全操作：读取文件、查看信息
    MODERATE = "moderate"   # 中等风险：创建文件、修改配置
    DANGEROUS = "dangerous" # 高风险：删除文件、执行命令、系统操作


class OperationCategory(str, Enum):
    """
    操作类别枚举
    
    定义不同类型的操作分类
    """
    
    FILE_READ = "file_read"               # 文件读取
    FILE_WRITE = "file_write"             # 文件写入
    FILE_DELETE = "file_delete"           # 文件删除
    SHELL_EXECUTE = "shell_execute"       # Shell 命令执行
    NETWORK_ACCESS = "network_access"     # 网络访问
    SYSTEM_CONFIG = "system_config"       # 系统配置
    PROCESS_MANAGE = "process_manage"     # 进程管理
    PACKAGE_INSTALL = "package_install"   # 包安装


class RiskAssessment:
    """
    风险评估结果
    
    包含操作的风险评估详情
    """
    
    def __init__(
        self,
        level: PermissionLevel,
        score: int,
        reasons: List[str],
        warnings: List[str],
        requires_confirmation: bool,
    ):
        """
        初始化风险评估结果
        
        Args:
            level: 权限级别
            score: 风险分数 (0-100)
            reasons: 风险原因列表
            warnings: 警告信息列表
            requires_confirmation: 是否需要用户确认
        """
        self.level = level
        self.score = score
        self.reasons = reasons
        self.warnings = warnings
        self.requires_confirmation = requires_confirmation
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            包含风险评估信息的字典
        """
        return {
            "level": self.level.value,
            "score": self.score,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "requires_confirmation": self.requires_confirmation,
        }


class PermissionChecker:
    """
    权限检查器
    
    负责评估操作风险和权限检查
    """
    
    # Windows 危险命令黑名单
    WINDOWS_DANGEROUS_COMMANDS: Set[str] = {
        # 系统操作
        "format", "diskpart", "fdisk", "chkdsk",
        # 用户管理
        "net user", "net localgroup", "net group",
        # 注册表
        "reg delete", "reg add",
        # 服务管理
        "sc delete", "sc config", "net stop", "net start",
        # 系统关机
        "shutdown", "restart", "logoff",
        # 网络配置
        "ipconfig /release", "ipconfig /renew", "route delete",
        # 防火墙
        "netsh advfirewall",
        # 权限提升
        "runas", "psexec", "powershell -exec bypass",
        # 系统文件
        "sfc", "dism",
    }
    
    # Windows 中等风险命令
    WINDOWS_MODERATE_COMMANDS: Set[str] = {
        "copy", "move", "xcopy", "robocopy",
        "mkdir", "rmdir", "del", "erase",
        "attrib", "icacls", "takeown",
        "taskkill", "tasklist",
        "reg query", "reg export",
        "netstat", "tasklist",
        "winget install", "choco install", "scoop install",
    }
    
    # Windows 安全命令
    WINDOWS_SAFE_COMMANDS: Set[str] = {
        "dir", "cd", "type", "find", "findstr",
        "echo", "set", "ver", "vol",
        "tree", "more", "sort",
        "where", "whoami", "hostname",
        "ipconfig", "systeminfo", "tasklist",
        "get-help", "get-command", "get-childitem",
    }
    
    # 危险文件扩展名（删除时高风险）
    DANGEROUS_EXTENSIONS: Set[str] = {
        ".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js",
        ".sys", ".dll", ".drv",
    }
    
    # 敏感目录（访问需要额外确认）
    SENSITIVE_DIRECTORIES: Set[str] = {
        # Windows 系统目录
        "C:\\Windows",
        "C:\\Windows\\System32",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\ProgramData",
        # 用户目录
        "\\AppData",
        "\\Desktop",
        "\\Documents",
    }
    
    # 敏感文件模式
    SENSITIVE_FILE_PATTERNS: List[str] = [
        r".*\.env$",
        r".*\.pem$",
        r".*\.key$",
        r".*password.*",
        r".*secret.*",
        r".*credential.*",
        r".*token.*",
        r".*\.gitconfig$",
        r".*\.ssh\\.*",
    ]
    
    def __init__(
        self,
        allowed_directories: Optional[List[str]] = None,
        blocked_directories: Optional[List[str]] = None,
        auto_approve_safe: bool = True,
    ):
        """
        初始化权限检查器
        
        Args:
            allowed_directories: 允许操作的目录列表
            blocked_directories: 禁止操作的目录列表
            auto_approve_safe: 是否自动批准安全操作
        """
        self.allowed_directories = set(allowed_directories or [])
        self.blocked_directories = set(blocked_directories or [])
        self.auto_approve_safe = auto_approve_safe
        
        # 编译敏感文件模式
        self._sensitive_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.SENSITIVE_FILE_PATTERNS
        ]
    
    def assess_command(self, command: str) -> RiskAssessment:
        """
        评估命令风险
        
        Args:
            command: 要执行的命令
        
        Returns:
            风险评估结果
        """
        command_lower = command.lower().strip()
        reasons: List[str] = []
        warnings: List[str] = []
        score = 0
        
        # 检查是否为空命令
        if not command_lower:
            return RiskAssessment(
                level=PermissionLevel.SAFE,
                score=0,
                reasons=["空命令"],
                warnings=[],
                requires_confirmation=False,
            )
        
        # 检查危险命令
        for dangerous_cmd in self.WINDOWS_DANGEROUS_COMMANDS:
            if dangerous_cmd in command_lower:
                score += 80
                reasons.append(f"包含危险命令: {dangerous_cmd}")
        
        # 检查中等风险命令
        for moderate_cmd in self.WINDOWS_MODERATE_COMMANDS:
            if moderate_cmd in command_lower:
                score += 40
                reasons.append(f"包含中等风险命令: {moderate_cmd}")
        
        # 检查安全命令
        is_safe_command = False
        for safe_cmd in self.WINDOWS_SAFE_COMMANDS:
            if command_lower.startswith(safe_cmd):
                is_safe_command = True
                break
        
        # 检查管道和重定向
        if "|" in command or ">" in command or ">>" in command:
            score += 10
            warnings.append("命令包含管道或重定向操作")
        
        # 检查通配符
        if "*" in command or "?" in command:
            score += 5
            warnings.append("命令包含通配符")
        
        # 检查 PowerShell 特征
        if "powershell" in command_lower:
            score += 30
            reasons.append("使用 PowerShell")
            
            # 检查危险的 PowerShell 参数
            if "-exec" in command_lower and "bypass" in command_lower:
                score += 50
                reasons.append("PowerShell 执行策略绕过")
            
            if "invoke-expression" in command_lower or "iex" in command_lower:
                score += 40
                reasons.append("PowerShell 动态代码执行")
        
        # 检查管理员权限相关
        if "runas" in command_lower or "sudo" in command_lower:
            score += 50
            reasons.append("尝试提升权限")
        
        # 检查网络相关
        if any(net_cmd in command_lower for net_cmd in ["curl", "wget", "invoke-webrequest", "download"]):
            score += 30
            reasons.append("涉及网络下载操作")
        
        # 确定权限级别
        if score >= 60:
            level = PermissionLevel.DANGEROUS
        elif score >= 30:
            level = PermissionLevel.MODERATE
        else:
            level = PermissionLevel.SAFE
        
        # 确定是否需要确认
        requires_confirmation = not (level == PermissionLevel.SAFE and self.auto_approve_safe)
        
        # 如果是安全命令且没有其他风险因素，降低分数
        if is_safe_command and score < 30:
            score = max(0, score - 20)
            if score < 20:
                level = PermissionLevel.SAFE
                requires_confirmation = not self.auto_approve_safe
        
        logger.debug(f"命令风险评估: {command[:50]}... -> {level.value}, 分数: {score}")
        
        return RiskAssessment(
            level=level,
            score=min(score, 100),
            reasons=reasons,
            warnings=warnings,
            requires_confirmation=requires_confirmation,
        )
    
    def assess_file_operation(
        self,
        operation: OperationCategory,
        file_path: str,
    ) -> RiskAssessment:
        """
        评估文件操作风险
        
        Args:
            operation: 操作类型
            file_path: 文件路径
        
        Returns:
            风险评估结果
        """
        reasons: List[str] = []
        warnings: List[str] = []
        score = 0
        
        path = Path(file_path)
        path_str = str(path.absolute())
        
        # 检查是否在禁止目录中
        for blocked_dir in self.blocked_directories:
            if path_str.lower().startswith(blocked_dir.lower()):
                score += 100
                reasons.append(f"操作禁止目录: {blocked_dir}")
        
        # 检查是否在允许目录外（如果设置了允许目录）
        if self.allowed_directories:
            in_allowed = False
            for allowed_dir in self.allowed_directories:
                if path_str.lower().startswith(allowed_dir.lower()):
                    in_allowed = True
                    break
            if not in_allowed:
                score += 30
                warnings.append("操作目录不在允许范围内")
        
        # 检查敏感目录
        for sensitive_dir in self.SENSITIVE_DIRECTORIES:
            if sensitive_dir.lower() in path_str.lower():
                score += 40
                warnings.append(f"操作敏感目录: {sensitive_dir}")
        
        # 检查敏感文件
        for pattern in self._sensitive_patterns:
            if pattern.match(path_str):
                score += 30
                warnings.append("操作敏感文件")
                break
        
        # 根据操作类型评估
        if operation == OperationCategory.FILE_DELETE:
            score += 50
            reasons.append("文件删除操作")
            
            # 检查危险扩展名
            if path.suffix.lower() in self.DANGEROUS_EXTENSIONS:
                score += 30
                reasons.append(f"删除可执行文件: {path.suffix}")
        
        elif operation == OperationCategory.FILE_WRITE:
            score += 20
            reasons.append("文件写入操作")
            
            # 检查是否创建可执行文件
            if path.suffix.lower() in self.DANGEROUS_EXTENSIONS:
                score += 30
                reasons.append(f"创建可执行文件: {path.suffix}")
        
        elif operation == OperationCategory.FILE_READ:
            score += 5
            reasons.append("文件读取操作")
        
        # 确定权限级别
        if score >= 60:
            level = PermissionLevel.DANGEROUS
        elif score >= 30:
            level = PermissionLevel.MODERATE
        else:
            level = PermissionLevel.SAFE
        
        requires_confirmation = not (level == PermissionLevel.SAFE and self.auto_approve_safe)
        
        logger.debug(f"文件操作风险评估: {operation.value} {file_path} -> {level.value}, 分数: {score}")
        
        return RiskAssessment(
            level=level,
            score=min(score, 100),
            reasons=reasons,
            warnings=warnings,
            requires_confirmation=requires_confirmation,
        )
    
    def check_permission(
        self,
        operation: OperationCategory,
        target: str,
        user_permission: PermissionLevel = PermissionLevel.SAFE,
    ) -> Tuple[bool, str]:
        """
        检查是否有权限执行操作
        
        Args:
            operation: 操作类型
            target: 操作目标（命令或文件路径）
            user_permission: 用户当前权限级别
        
        Returns:
            (是否有权限, 原因说明)
        """
        # 根据操作类型获取风险评估
        if operation in (OperationCategory.SHELL_EXECUTE, OperationCategory.PACKAGE_INSTALL):
            assessment = self.assess_command(target)
        else:
            assessment = self.assess_file_operation(operation, target)
        
        # 权限级别比较
        permission_order = {
            PermissionLevel.SAFE: 0,
            PermissionLevel.MODERATE: 1,
            PermissionLevel.DANGEROUS: 2,
        }
        
        required_level = permission_order[assessment.level]
        user_level = permission_order[user_permission]
        
        if user_level >= required_level:
            return True, f"权限足够，操作级别: {assessment.level.value}"
        else:
            return False, f"权限不足，需要 {assessment.level.value} 级别权限"
    
    def get_command_preview(self, command: str) -> Dict:
        """
        获取命令预览信息
        
        Args:
            command: 要预览的命令
        
        Returns:
            包含命令解析和风险评估的字典
        """
        assessment = self.assess_command(command)
        
        # 解析命令组件
        parts = command.split()
        command_name = parts[0] if parts else ""
        arguments = parts[1:] if len(parts) > 1 else []
        
        return {
            "command": command,
            "command_name": command_name,
            "arguments": arguments,
            "risk_assessment": assessment.to_dict(),
            "safety_tips": self._get_safety_tips(assessment),
        }
    
    def _get_safety_tips(self, assessment: RiskAssessment) -> List[str]:
        """
        获取安全提示
        
        Args:
            assessment: 风险评估结果
        
        Returns:
            安全提示列表
        """
        tips = []
        
        if assessment.level == PermissionLevel.DANGEROUS:
            tips.append("此操作具有高风险，请仔细确认")
            tips.append("建议在执行前备份重要数据")
        elif assessment.level == PermissionLevel.MODERATE:
            tips.append("此操作具有一定风险，请确认操作内容")
        
        if assessment.warnings:
            tips.extend(assessment.warnings)
        
        return tips


# 创建默认权限检查器实例
default_permission_checker = PermissionChecker()
