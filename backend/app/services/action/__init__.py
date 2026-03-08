"""
动作服务模块
提供安全沙箱执行环境的核心功能
"""
from app.services.action.permission import (
    OperationCategory,
    PermissionChecker,
    PermissionLevel,
    RiskAssessment,
    default_permission_checker,
)
from app.services.action.sandbox import (
    ExecutionResult,
    ResourceLimits,
    SandboxEnvironment,
    SandboxManager,
)
from app.services.action.executor import (
    CommandExecutor,
    CommandPreview,
    ExecutionRecord,
    ExecutionRequest,
    ExecutionStatus,
    FileOperationExecutor,
    default_executor,
    default_file_executor,
)
from app.services.action.action_service import (
    ActionService,
    ActionServiceFactory,
)
from app.services.action.action_registry import (
    ActionCategory,
    ActionMetadata,
    ActionParameter,
    ActionResult,
    ActionRegistry,
    action_registry,
    action_decorator,
)
from app.services.action.file_actions import (
    organize_downloads,
    move_files,
    rename_files,
    delete_files,
    copy_files,
    list_directory,
)
from app.services.action.note_actions import (
    create_note,
    append_note,
    search_notes,
    list_notes,
    read_note,
    delete_note,
)
from app.services.action.system_actions import (
    get_system_info,
    get_disk_usage,
    get_memory_info,
    get_running_processes,
    get_network_info,
    get_cpu_info,
)
from app.services.action.script_executor import (
    ScriptSandbox,
    ScriptTemplate,
    ScriptTemplateManager,
    script_sandbox,
    template_manager,
    execute_script,
    execute_template,
    list_templates,
    validate_script,
)

__all__ = [
    # 权限相关
    "PermissionLevel",
    "OperationCategory",
    "RiskAssessment",
    "PermissionChecker",
    "default_permission_checker",
    # 沙箱相关
    "ResourceLimits",
    "ExecutionResult",
    "SandboxEnvironment",
    "SandboxManager",
    # 执行器相关
    "ExecutionStatus",
    "CommandPreview",
    "ExecutionRequest",
    "ExecutionRecord",
    "CommandExecutor",
    "FileOperationExecutor",
    "default_executor",
    "default_file_executor",
    # 服务相关
    "ActionService",
    "ActionServiceFactory",
    # 动作注册表
    "ActionCategory",
    "ActionMetadata",
    "ActionParameter",
    "ActionResult",
    "ActionRegistry",
    "action_registry",
    "action_decorator",
    # 文件操作动作
    "organize_downloads",
    "move_files",
    "rename_files",
    "delete_files",
    "copy_files",
    "list_directory",
    # 笔记操作动作
    "create_note",
    "append_note",
    "search_notes",
    "list_notes",
    "read_note",
    "delete_note",
    # 系统信息动作
    "get_system_info",
    "get_disk_usage",
    "get_memory_info",
    "get_running_processes",
    "get_network_info",
    "get_cpu_info",
    # 脚本执行器
    "ScriptSandbox",
    "ScriptTemplate",
    "ScriptTemplateManager",
    "script_sandbox",
    "template_manager",
    "execute_script",
    "execute_template",
    "list_templates",
    "validate_script",
]
