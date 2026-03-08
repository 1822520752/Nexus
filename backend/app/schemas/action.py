"""
动作相关 Schema
定义动作 API 的请求和响应模型
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CommandPreviewRequest(BaseModel):
    """
    命令预览请求模型
    """
    
    command: str = Field(..., description="要预览的命令")
    arguments: Optional[List[str]] = Field(default=None, description="命令参数列表")
    working_directory: Optional[str] = Field(default=None, description="工作目录")
    
    class Config:
        json_schema_extra = {
            "example": {
                "command": "dir",
                "arguments": ["C:\\Users"],
                "working_directory": "C:\\",
            }
        }


class RiskAssessmentResponse(BaseModel):
    """
    风险评估响应模型
    """
    
    level: str = Field(..., description="权限级别 (safe/moderate/dangerous)")
    score: int = Field(..., description="风险分数 (0-100)")
    reasons: List[str] = Field(default_factory=list, description="风险原因列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")
    requires_confirmation: bool = Field(..., description="是否需要用户确认")


class CommandPreviewResponse(BaseModel):
    """
    命令预览响应模型
    """
    
    command: str = Field(..., description="原始命令")
    command_name: str = Field(..., description="命令名称")
    arguments: List[str] = Field(default_factory=list, description="参数列表")
    working_directory: str = Field(..., description="工作目录")
    risk_assessment: RiskAssessmentResponse = Field(..., description="风险评估结果")
    safety_tips: List[str] = Field(default_factory=list, description="安全提示")
    estimated_impact: str = Field(..., description="预估影响")
    requires_confirmation: bool = Field(..., description="是否需要确认")
    preview_time: str = Field(..., description="预览时间")


class CommandExecuteRequest(BaseModel):
    """
    命令执行请求模型
    """
    
    command: str = Field(..., description="要执行的命令")
    arguments: Optional[List[str]] = Field(default=None, description="命令参数列表")
    working_directory: Optional[str] = Field(default=None, description="工作目录")
    environment: Optional[Dict[str, str]] = Field(default=None, description="环境变量")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间（秒）")
    input_data: Optional[str] = Field(default=None, description="标准输入数据")
    auto_approve_safe: bool = Field(default=True, description="是否自动批准安全操作")
    conversation_id: Optional[int] = Field(default=None, description="关联对话 ID")
    message_id: Optional[int] = Field(default=None, description="关联消息 ID")
    action_name: Optional[str] = Field(default=None, description="动作名称")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "command": "echo Hello World",
                "timeout": 30,
                "auto_approve_safe": True,
            }
        }


class ExecutionResultResponse(BaseModel):
    """
    执行结果响应模型
    """
    
    success: bool = Field(..., description="是否成功")
    exit_code: int = Field(default=0, description="退出码")
    stdout: str = Field(default="", description="标准输出")
    stderr: str = Field(default="", description="标准错误")
    duration_ms: int = Field(default=0, description="执行耗时（毫秒）")
    timed_out: bool = Field(default=False, description="是否超时")
    memory_used_mb: float = Field(default=0.0, description="内存使用（MB）")
    working_directory: str = Field(default="", description="工作目录")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class CommandExecuteResponse(BaseModel):
    """
    命令执行响应模型
    """
    
    action_id: int = Field(..., description="动作 ID")
    status: str = Field(..., description="执行状态")
    result: Optional[str] = Field(default=None, description="执行结果")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    duration_ms: Optional[int] = Field(default=None, description="执行耗时（毫秒）")
    execution_record: Optional[Dict[str, Any]] = Field(default=None, description="完整执行记录")


class ActionConfirmRequest(BaseModel):
    """
    动作确认请求模型
    """
    
    approved: bool = Field(..., description="是否批准执行")
    confirmed_by: Optional[str] = Field(default=None, description="确认用户")
    
    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "confirmed_by": "user",
            }
        }


class ActionHistoryItem(BaseModel):
    """
    动作历史项模型
    """
    
    id: int = Field(..., description="动作 ID")
    action_type: str = Field(..., description="动作类型")
    action_name: Optional[str] = Field(default=None, description="动作名称")
    command: str = Field(..., description="执行命令")
    status: str = Field(..., description="执行状态")
    result: Optional[str] = Field(default=None, description="执行结果")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    conversation_id: Optional[int] = Field(default=None, description="关联对话 ID")
    duration_ms: Optional[int] = Field(default=None, description="执行耗时（毫秒）")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class ActionHistoryListResponse(BaseModel):
    """
    动作历史列表响应模型
    """
    
    data: List[ActionHistoryItem] = Field(default_factory=list, description="动作历史列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=50, description="每页数量")


class ActionStatusResponse(BaseModel):
    """
    动作状态响应模型
    """
    
    id: int = Field(..., description="动作 ID")
    action_type: str = Field(..., description="动作类型")
    action_name: Optional[str] = Field(default=None, description="动作名称")
    command: str = Field(..., description="执行命令")
    status: str = Field(..., description="执行状态")
    result: Optional[str] = Field(default=None, description="执行结果")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    conversation_id: Optional[int] = Field(default=None, description="关联对话 ID")
    message_id: Optional[int] = Field(default=None, description="关联消息 ID")
    approved_at: Optional[str] = Field(default=None, description="批准时间")
    started_at: Optional[str] = Field(default=None, description="开始时间")
    finished_at: Optional[str] = Field(default=None, description="结束时间")
    duration_ms: Optional[int] = Field(default=None, description="执行耗时（毫秒）")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class FileOperationRequest(BaseModel):
    """
    文件操作请求模型
    """
    
    operation: str = Field(..., description="操作类型 (read/write/delete)")
    file_path: str = Field(..., description="文件路径")
    content: Optional[str] = Field(default=None, description="文件内容（写入时需要）")
    encoding: str = Field(default="utf-8", description="文件编码")
    conversation_id: Optional[int] = Field(default=None, description="关联对话 ID")
    message_id: Optional[int] = Field(default=None, description="关联消息 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation": "read",
                "file_path": "C:\\temp\\test.txt",
            }
        }


class FileOperationResponse(BaseModel):
    """
    文件操作响应模型
    """
    
    action_id: Optional[int] = Field(default=None, description="动作 ID")
    status: str = Field(..., description="执行状态")
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    preview: Optional[Dict[str, Any]] = Field(default=None, description="操作预览")
    message: Optional[str] = Field(default=None, description="提示信息")


class PendingConfirmationsResponse(BaseModel):
    """
    待确认动作列表响应模型
    """
    
    data: List[ActionHistoryItem] = Field(default_factory=list, description="待确认动作列表")
    total: int = Field(default=0, description="总数")


# ==================== 预定义动作相关 Schema ====================


class ActionParameterSchema(BaseModel):
    """
    动作参数模型
    """
    
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(default=True, description="是否必需")
    default: Optional[Any] = Field(default=None, description="默认值")
    choices: Optional[List[str]] = Field(default=None, description="可选值列表")
    min_value: Optional[float] = Field(default=None, description="最小值")
    max_value: Optional[float] = Field(default=None, description="最大值")
    pattern: Optional[str] = Field(default=None, description="正则表达式验证模式")


class ActionMetadataResponse(BaseModel):
    """
    动作元数据响应模型
    """
    
    name: str = Field(..., description="动作名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="动作描述")
    category: str = Field(..., description="动作类别")
    parameters: List[ActionParameterSchema] = Field(default_factory=list, description="参数列表")
    returns: str = Field(default="", description="返回值描述")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="使用示例")
    tags: List[str] = Field(default_factory=list, description="标签")
    version: str = Field(default="1.0.0", description="版本号")
    author: str = Field(default="Nexus", description="作者")
    requires_confirmation: bool = Field(default=False, description="是否需要确认")
    is_dangerous: bool = Field(default=False, description="是否危险操作")
    is_enabled: bool = Field(default=True, description="是否启用")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class ActionListResponse(BaseModel):
    """
    动作列表响应模型
    """
    
    data: List[ActionMetadataResponse] = Field(default_factory=list, description="动作列表")
    total: int = Field(default=0, description="总数")
    category: Optional[str] = Field(default=None, description="分类过滤")


class ActionExecuteRequest(BaseModel):
    """
    预定义动作执行请求模型
    """
    
    action_name: str = Field(..., description="动作名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="动作参数")
    conversation_id: Optional[int] = Field(default=None, description="关联对话 ID")
    message_id: Optional[int] = Field(default=None, description="关联消息 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_name": "file.list_directory",
                "parameters": {
                    "directory": "C:\\Users",
                    "sort_by": "name",
                },
            }
        }


class ActionResultResponse(BaseModel):
    """
    动作执行结果响应模型
    """
    
    success: bool = Field(..., description="是否成功")
    data: Optional[Any] = Field(default=None, description="返回数据")
    message: str = Field(default="", description="结果消息")
    error: Optional[str] = Field(default=None, description="错误信息")
    duration_ms: int = Field(default=0, description="执行耗时（毫秒）")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class ActionStatisticsResponse(BaseModel):
    """
    动作统计信息响应模型
    """
    
    total_actions: int = Field(..., description="总动作数")
    enabled_actions: int = Field(..., description="启用的动作数")
    disabled_actions: int = Field(..., description="禁用的动作数")
    dangerous_actions: int = Field(..., description="危险动作数")
    by_category: Dict[str, int] = Field(default_factory=dict, description="按类别统计")


# ==================== 文件操作动作 Schema ====================


class FileOrganizeRequest(BaseModel):
    """
    文件整理请求模型
    """
    
    directory: str = Field(..., description="要整理的目录路径")
    rules: Optional[Dict[str, List[str]]] = Field(default=None, description="自定义分类规则")
    dry_run: bool = Field(default=False, description="是否仅预览不实际执行")
    
    class Config:
        json_schema_extra = {
            "example": {
                "directory": "C:\\Users\\用户名\\Downloads",
                "dry_run": True,
            }
        }


class FileMoveRequest(BaseModel):
    """
    文件移动请求模型
    """
    
    source: str = Field(..., description="源文件或目录路径")
    destination: str = Field(..., description="目标目录路径")
    pattern: Optional[str] = Field(default=None, description="文件名匹配模式")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的文件")


class FileRenameRequest(BaseModel):
    """
    文件重命名请求模型
    """
    
    directory: str = Field(..., description="目录路径")
    pattern: str = Field(..., description="匹配模式（正则表达式）")
    replacement: str = Field(..., description="替换字符串")
    recursive: bool = Field(default=False, description="是否递归处理子目录")
    preview: bool = Field(default=True, description="是否仅预览")


class FileDeleteRequest(BaseModel):
    """
    文件删除请求模型
    """
    
    paths: List[str] = Field(..., description="要删除的文件路径列表")
    safe_mode: bool = Field(default=True, description="安全模式")
    move_to_trash: bool = Field(default=True, description="是否移动到回收站")


class FileCopyRequest(BaseModel):
    """
    文件复制请求模型
    """
    
    source: str = Field(..., description="源文件或目录路径")
    destination: str = Field(..., description="目标路径")
    pattern: Optional[str] = Field(default=None, description="文件名匹配模式")
    recursive: bool = Field(default=False, description="是否递归复制")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的文件")


class FileListRequest(BaseModel):
    """
    文件列表请求模型
    """
    
    directory: str = Field(..., description="目录路径")
    pattern: Optional[str] = Field(default=None, description="文件名匹配模式")
    recursive: bool = Field(default=False, description="是否递归列出")
    show_hidden: bool = Field(default=False, description="是否显示隐藏文件")
    sort_by: str = Field(default="name", description="排序字段")
    sort_order: str = Field(default="asc", description="排序顺序")


# ==================== 笔记操作动作 Schema ====================


class NoteCreateRequest(BaseModel):
    """
    笔记创建请求模型
    """
    
    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记内容")
    notes_dir: Optional[str] = Field(default=None, description="笔记存储目录")
    format: str = Field(default="md", description="文件格式 (md, txt)")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的文件")


class NoteAppendRequest(BaseModel):
    """
    笔记追加请求模型
    """
    
    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="要追加的内容")
    notes_dir: Optional[str] = Field(default=None, description="笔记存储目录")
    separator: str = Field(default="\n\n---\n\n", description="分隔符")
    timestamp: bool = Field(default=True, description="是否添加时间戳")


class NoteSearchRequest(BaseModel):
    """
    笔记搜索请求模型
    """
    
    query: str = Field(..., description="搜索关键词")
    notes_dir: Optional[str] = Field(default=None, description="笔记存储目录")
    search_in_content: bool = Field(default=True, description="是否在内容中搜索")
    search_in_tags: bool = Field(default=True, description="是否在标签中搜索")
    case_sensitive: bool = Field(default=False, description="是否区分大小写")
    limit: int = Field(default=50, ge=1, le=500, description="返回结果数量限制")


class NoteListRequest(BaseModel):
    """
    笔记列表请求模型
    """
    
    notes_dir: Optional[str] = Field(default=None, description="笔记存储目录")
    tag: Optional[str] = Field(default=None, description="按标签筛选")
    sort_by: str = Field(default="updated", description="排序字段")
    sort_order: str = Field(default="desc", description="排序顺序")
    limit: int = Field(default=100, ge=1, le=500, description="返回数量限制")


class NoteReadRequest(BaseModel):
    """
    笔记读取请求模型
    """
    
    title: str = Field(..., description="笔记标题")
    notes_dir: Optional[str] = Field(default=None, description="笔记存储目录")


class NoteDeleteRequest(BaseModel):
    """
    笔记删除请求模型
    """
    
    title: str = Field(..., description="笔记标题")
    notes_dir: Optional[str] = Field(default=None, description="笔记存储目录")


# ==================== 系统信息动作 Schema ====================


class DiskUsageRequest(BaseModel):
    """
    磁盘使用情况请求模型
    """
    
    drive: Optional[str] = Field(default=None, description="驱动器字母")


class ProcessListRequest(BaseModel):
    """
    进程列表请求模型
    """
    
    filter_name: Optional[str] = Field(default=None, description="按进程名过滤")
    sort_by: str = Field(default="memory", description="排序字段")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")


# ==================== 脚本执行动作 Schema ====================


class ScriptExecuteRequest(BaseModel):
    """
    脚本执行请求模型
    """
    
    code: str = Field(..., description="Python 脚本代码")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="输入数据")
    timeout: int = Field(default=30, ge=1, le=300, description="执行超时时间（秒）")
    validate: bool = Field(default=True, description="是否验证脚本安全性")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code - action.py:514": "result = 1 + 1\nprint(f'结果: {result}')",
                "timeout": 30,
            }
        }


class ScriptTemplateExecuteRequest(BaseModel):
    """
    脚本模板执行请求模型
    """
    
    template_name: str = Field(..., description="模板名称")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="模板参数")
    timeout: int = Field(default=30, ge=1, le=300, description="执行超时时间（秒）")


class ScriptValidateRequest(BaseModel):
    """
    脚本验证请求模型
    """
    
    code: str = Field(..., description="Python 脚本代码")


class ScriptTemplateListRequest(BaseModel):
    """
    脚本模板列表请求模型
    """
    
    category: Optional[str] = Field(default=None, description="按分类过滤")


class ScriptTemplateResponse(BaseModel):
    """
    脚本模板响应模型
    """
    
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    code: str = Field(..., description="模板代码")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="参数定义")
    category: str = Field(default="general", description="模板分类")
    tags: List[str] = Field(default_factory=list, description="标签")


class ScriptTemplateListResponse(BaseModel):
    """
    脚本模板列表响应模型
    """
    
    templates: List[ScriptTemplateResponse] = Field(default_factory=list, description="模板列表")
    count: int = Field(default=0, description="模板数量")
