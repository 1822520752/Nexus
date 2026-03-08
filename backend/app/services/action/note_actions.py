"""
笔记操作动作
提供笔记创建、追加、搜索等功能，支持 Markdown 和 TXT 格式
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import logger
from app.services.action.action_registry import (
    ActionCategory,
    ActionMetadata,
    ActionParameter,
    ActionResult,
    action_registry,
)


# 默认笔记存储目录
DEFAULT_NOTES_DIR = os.path.join(os.path.expanduser("~"), "Nexus", "Notes")


def _ensure_notes_dir(notes_dir: Optional[str] = None) -> Path:
    """
    确保笔记目录存在
    
    Args:
        notes_dir: 笔记目录路径，None 使用默认目录
    
    Returns:
        笔记目录 Path 对象
    """
    directory = Path(notes_dir or DEFAULT_NOTES_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _get_note_path(
    title: str,
    notes_dir: Optional[str] = None,
    format: str = "md",
) -> Path:
    """
    获取笔记文件路径
    
    Args:
        title: 笔记标题
        notes_dir: 笔记目录
        format: 文件格式 (md, txt)
    
    Returns:
        笔记文件路径
    """
    directory = _ensure_notes_dir(notes_dir)
    
    # 清理标题中的非法字符
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title)
    
    # 确定文件扩展名
    ext = ".md" if format.lower() in ["md", "markdown"] else ".txt"
    
    return directory / f"{safe_title}{ext}"


def _generate_frontmatter(metadata: Dict[str, Any]) -> str:
    """
    生成 YAML 前置元数据
    
    Args:
        metadata: 元数据字典
    
    Returns:
        YAML 格式的前置元数据字符串
    """
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, str):
            lines.append(f'{key}: "{value}"')
        elif isinstance(value, (int, float, bool)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def _parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """
    解析 YAML 前置元数据
    
    Args:
        content: 文件内容
    
    Returns:
        (元数据字典, 正文内容)
    """
    if not content.startswith("---"):
        return {}, content
    
    # 查找前置元数据结束位置
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return {}, content
    
    frontmatter_str = content[3:end_match.start() + 3]
    body = content[end_match.end() + 3:]
    
    # 简单解析 YAML（不使用 PyYAML）
    metadata = {}
    for line in frontmatter_str.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # 移除引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # 转换类型
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            elif re.match(r'^-?\d+\.?\d*$', value):
                value = float(value)
            
            metadata[key] = value
    
    return metadata, body


def create_note(
    title: str,
    content: str,
    notes_dir: Optional[str] = None,
    format: str = "md",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    overwrite: bool = False,
) -> ActionResult:
    """
    创建笔记
    
    创建新的笔记文件，支持 Markdown 和 TXT 格式
    
    Args:
        title: 笔记标题
        content: 笔记内容
        notes_dir: 笔记存储目录，None 使用默认目录
        format: 文件格式 (md, txt)
        tags: 标签列表
        metadata: 额外元数据
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        执行结果
    """
    logger.info(f"创建笔记: {title}")
    
    try:
        # 获取笔记路径
        note_path = _get_note_path(title, notes_dir, format)
        
        # 检查文件是否存在
        if note_path.exists() and not overwrite:
            return ActionResult(
                success=False,
                error=f"笔记已存在: {note_path}",
                data={"path": str(note_path)},
            )
        
        # 准备元数据
        now = datetime.now()
        note_metadata = {
            "title": title,
            "created": now.isoformat(),
            "updated": now.isoformat(),
            "tags": tags or [],
        }
        if metadata:
            note_metadata.update(metadata)
        
        # 构建文件内容
        if format.lower() in ["md", "markdown"]:
            # Markdown 格式，添加前置元数据
            frontmatter = _generate_frontmatter(note_metadata)
            full_content = f"{frontmatter}\n\n# {title}\n\n{content}"
        else:
            # TXT 格式，添加简单头部
            header = f"Title: {title}\nCreated: {now.strftime('%Y-%m-%d %H:%M:%S')}\nTags: {', '.join(tags or [])}\n{'=' * 50}\n\n"
            full_content = header + content
        
        # 写入文件
        note_path.write_text(full_content, encoding="utf-8")
        
        logger.info(f"笔记创建成功: {note_path}")
        
        return ActionResult(
            success=True,
            data={
                "path": str(note_path),
                "title": title,
                "format": format,
                "size": len(full_content),
                "created": now.isoformat(),
            },
            message=f"笔记创建成功: {title}",
        )
        
    except Exception as e:
        logger.error(f"创建笔记失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def append_note(
    title: str,
    content: str,
    notes_dir: Optional[str] = None,
    separator: str = "\n\n---\n\n",
    timestamp: bool = True,
) -> ActionResult:
    """
    追加笔记内容
    
    在现有笔记末尾追加新内容
    
    Args:
        title: 笔记标题
        content: 要追加的内容
        notes_dir: 笔记存储目录
        separator: 分隔符
        timestamp: 是否添加时间戳
    
    Returns:
        执行结果
    """
    logger.info(f"追加笔记: {title}")
    
    try:
        # 查找笔记文件
        directory = _ensure_notes_dir(notes_dir)
        
        # 尝试查找笔记文件（支持 md 和 txt）
        note_path = None
        for ext in [".md", ".txt"]:
            potential_path = _get_note_path(title, notes_dir, ext[1:])
            if potential_path.exists():
                note_path = potential_path
                break
        
        if not note_path:
            return ActionResult(
                success=False,
                error=f"笔记不存在: {title}",
            )
        
        # 读取现有内容
        existing_content = note_path.read_text(encoding="utf-8")
        
        # 准备追加内容
        append_content = content
        if timestamp:
            now = datetime.now()
            append_content = f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}]\n{content}"
        
        # 追加内容
        new_content = existing_content + separator + append_content
        
        # 如果是 Markdown，更新元数据中的更新时间
        if note_path.suffix == ".md":
            metadata, body = _parse_frontmatter(existing_content)
            if metadata:
                metadata["updated"] = datetime.now().isoformat()
                frontmatter = _generate_frontmatter(metadata)
                new_content = f"{frontmatter}\n\n{body}{separator}{append_content}"
        
        # 写入文件
        note_path.write_text(new_content, encoding="utf-8")
        
        logger.info(f"笔记追加成功: {note_path}")
        
        return ActionResult(
            success=True,
            data={
                "path": str(note_path),
                "title": title,
                "appended_size": len(append_content),
                "total_size": len(new_content),
            },
            message=f"笔记追加成功: {title}",
        )
        
    except Exception as e:
        logger.error(f"追加笔记失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def search_notes(
    query: str,
    notes_dir: Optional[str] = None,
    search_in_content: bool = True,
    search_in_tags: bool = True,
    case_sensitive: bool = False,
    limit: int = 50,
) -> ActionResult:
    """
    搜索笔记
    
    在笔记中搜索指定内容
    
    Args:
        query: 搜索关键词
        notes_dir: 笔记存储目录
        search_in_content: 是否在内容中搜索
        search_in_tags: 是否在标签中搜索
        case_sensitive: 是否区分大小写
        limit: 返回结果数量限制
    
    Returns:
        执行结果
    """
    logger.info(f"搜索笔记: {query}")
    
    try:
        directory = _ensure_notes_dir(notes_dir)
        
        # 准备搜索模式
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(query), flags)
        
        results = []
        
        # 遍历笔记文件
        for note_file in directory.glob("*.md"):
            try:
                content = note_file.read_text(encoding="utf-8")
                metadata, body = _parse_frontmatter(content)
                
                title = metadata.get("title", note_file.stem)
                tags = metadata.get("tags", [])
                
                # 搜索匹配
                matches = {
                    "title": False,
                    "content": False,
                    "tags": False,
                }
                
                # 标题匹配
                if pattern.search(title):
                    matches["title"] = True
                
                # 内容匹配
                if search_in_content and pattern.search(body):
                    matches["content"] = True
                
                # 标签匹配
                if search_in_tags and any(pattern.search(tag) for tag in tags):
                    matches["tags"] = True
                
                # 如果有任何匹配
                if any(matches.values()):
                    # 提取匹配上下文
                    context = ""
                    if matches["content"]:
                        # 查找匹配位置并提取上下文
                        match = pattern.search(body)
                        if match:
                            start = max(0, match.start() - 50)
                            end = min(len(body), match.end() + 50)
                            context = body[start:end]
                            if start > 0:
                                context = "..." + context
                            if end < len(body):
                                context = context + "..."
                    
                    results.append({
                        "path": str(note_file),
                        "title": title,
                        "tags": tags,
                        "matches": matches,
                        "context": context,
                        "created": metadata.get("created"),
                        "updated": metadata.get("updated"),
                    })
                    
                    if len(results) >= limit:
                        break
                        
            except Exception as e:
                logger.warning(f"读取笔记失败: {note_file}, 错误: {e}")
                continue
        
        # 同时搜索 TXT 文件
        for note_file in directory.glob("*.txt"):
            try:
                content = note_file.read_text(encoding="utf-8")
                
                # 简单解析 TXT 头部
                lines = content.split("\n")
                title = note_file.stem
                for line in lines[:5]:
                    if line.startswith("Title:"):
                        title = line[6:].strip()
                        break
                
                matches = {
                    "title": bool(pattern.search(title)),
                    "content": search_in_content and bool(pattern.search(content)),
                    "tags": False,
                }
                
                if any(matches.values()):
                    # 提取匹配上下文
                    context = ""
                    if matches["content"]:
                        match = pattern.search(content)
                        if match:
                            start = max(0, match.start() - 50)
                            end = min(len(content), match.end() + 50)
                            context = content[start:end]
                    
                    results.append({
                        "path": str(note_file),
                        "title": title,
                        "tags": [],
                        "matches": matches,
                        "context": context,
                    })
                    
                    if len(results) >= limit:
                        break
                        
            except Exception as e:
                logger.warning(f"读取笔记失败: {note_file}, 错误: {e}")
                continue
        
        return ActionResult(
            success=True,
            data={
                "query": query,
                "results": results,
                "count": len(results),
            },
            message=f"找到 {len(results)} 个匹配的笔记",
        )
        
    except Exception as e:
        logger.error(f"搜索笔记失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def list_notes(
    notes_dir: Optional[str] = None,
    tag: Optional[str] = None,
    sort_by: str = "updated",
    sort_order: str = "desc",
    limit: int = 100,
) -> ActionResult:
    """
    列出笔记
    
    列出所有笔记或按标签筛选
    
    Args:
        notes_dir: 笔记存储目录
        tag: 按标签筛选
        sort_by: 排序字段 (title, created, updated)
        sort_order: 排序顺序 (asc, desc)
        limit: 返回数量限制
    
    Returns:
        执行结果
    """
    logger.info(f"列出笔记, tag={tag}")
    
    try:
        directory = _ensure_notes_dir(notes_dir)
        
        notes = []
        
        # 遍历 Markdown 文件
        for note_file in directory.glob("*.md"):
            try:
                content = note_file.read_text(encoding="utf-8")
                metadata, body = _parse_frontmatter(content)
                
                title = metadata.get("title", note_file.stem)
                tags = metadata.get("tags", [])
                
                # 标签过滤
                if tag and tag not in tags:
                    continue
                
                # 统计字数
                word_count = len(body.split())
                
                notes.append({
                    "path": str(note_file),
                    "title": title,
                    "tags": tags,
                    "created": metadata.get("created"),
                    "updated": metadata.get("updated"),
                    "word_count": word_count,
                    "format": "markdown",
                })
                
            except Exception as e:
                logger.warning(f"读取笔记失败: {note_file}, 错误: {e}")
                continue
        
        # 遍历 TXT 文件
        for note_file in directory.glob("*.txt"):
            try:
                content = note_file.read_text(encoding="utf-8")
                
                # 简单解析
                lines = content.split("\n")
                title = note_file.stem
                for line in lines[:5]:
                    if line.startswith("Title:"):
                        title = line[6:].strip()
                        break
                
                notes.append({
                    "path": str(note_file),
                    "title": title,
                    "tags": [],
                    "word_count": len(content.split()),
                    "format": "text",
                })
                
            except Exception as e:
                logger.warning(f"读取笔记失败: {note_file}, 错误: {e}")
                continue
        
        # 排序
        reverse = sort_order.lower() == "desc"
        
        def sort_key(note):
            if sort_by == "title":
                return note.get("title", "").lower()
            elif sort_by == "created":
                return note.get("created") or ""
            elif sort_by == "updated":
                return note.get("updated") or note.get("created") or ""
            return ""
        
        notes.sort(key=sort_key, reverse=reverse)
        
        # 限制数量
        notes = notes[:limit]
        
        return ActionResult(
            success=True,
            data={
                "notes": notes,
                "count": len(notes),
                "directory": str(directory),
            },
            message=f"找到 {len(notes)} 个笔记",
        )
        
    except Exception as e:
        logger.error(f"列出笔记失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def read_note(
    title: str,
    notes_dir: Optional[str] = None,
) -> ActionResult:
    """
    读取笔记
    
    读取指定笔记的内容
    
    Args:
        title: 笔记标题
        notes_dir: 笔记存储目录
    
    Returns:
        执行结果
    """
    logger.info(f"读取笔记: {title}")
    
    try:
        directory = _ensure_notes_dir(notes_dir)
        
        # 查找笔记文件
        note_path = None
        for ext in [".md", ".txt"]:
            potential_path = _get_note_path(title, notes_dir, ext[1:])
            if potential_path.exists():
                note_path = potential_path
                break
        
        if not note_path:
            return ActionResult(
                success=False,
                error=f"笔记不存在: {title}",
            )
        
        # 读取内容
        content = note_path.read_text(encoding="utf-8")
        
        # 解析
        metadata = {}
        body = content
        
        if note_path.suffix == ".md":
            metadata, body = _parse_frontmatter(content)
        
        return ActionResult(
            success=True,
            data={
                "path": str(note_path),
                "title": metadata.get("title", title),
                "content": body,
                "metadata": metadata,
                "size": len(content),
            },
            message=f"读取笔记成功: {title}",
        )
        
    except Exception as e:
        logger.error(f"读取笔记失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def delete_note(
    title: str,
    notes_dir: Optional[str] = None,
) -> ActionResult:
    """
    删除笔记
    
    删除指定的笔记文件
    
    Args:
        title: 笔记标题
        notes_dir: 笔记存储目录
    
    Returns:
        执行结果
    """
    logger.info(f"删除笔记: {title}")
    
    try:
        # 查找笔记文件
        note_path = None
        for ext in [".md", ".txt"]:
            potential_path = _get_note_path(title, notes_dir, ext[1:])
            if potential_path.exists():
                note_path = potential_path
                break
        
        if not note_path:
            return ActionResult(
                success=False,
                error=f"笔记不存在: {title}",
            )
        
        # 删除文件
        note_path.unlink()
        
        logger.info(f"笔记删除成功: {note_path}")
        
        return ActionResult(
            success=True,
            data={
                "path": str(note_path),
                "title": title,
            },
            message=f"笔记删除成功: {title}",
        )
        
    except Exception as e:
        logger.error(f"删除笔记失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


# 注册动作到注册表
def _register_actions():
    """
    注册所有笔记操作动作
    """
    # 创建笔记
    action_registry.register(
        name="note.create",
        display_name="创建笔记",
        description="创建新的笔记文件，支持 Markdown 和 TXT 格式",
        category=ActionCategory.NOTE,
        executor=create_note,
        parameters=[
            ActionParameter(
                name="title",
                type="str",
                description="笔记标题",
                required=True,
            ),
            ActionParameter(
                name="content",
                type="str",
                description="笔记内容",
                required=True,
            ),
            ActionParameter(
                name="notes_dir",
                type="str",
                description="笔记存储目录，None 使用默认目录",
                required=False,
            ),
            ActionParameter(
                name="format",
                type="str",
                description="文件格式 (md, txt)",
                required=False,
                default="md",
                choices=["md", "txt"],
            ),
            ActionParameter(
                name="tags",
                type="list",
                description="标签列表",
                required=False,
            ),
            ActionParameter(
                name="metadata",
                type="dict",
                description="额外元数据",
                required=False,
            ),
            ActionParameter(
                name="overwrite",
                type="bool",
                description="是否覆盖已存在的文件",
                required=False,
                default=False,
            ),
        ],
        returns="创建的笔记信息",
        examples=[
            {
                "title": "会议记录",
                "content": "今天讨论了项目进度...",
                "format": "md",
                "tags": ["会议", "项目"],
            }
        ],
        tags=["note", "create", "markdown"],
    )
    
    # 追加笔记
    action_registry.register(
        name="note.append",
        display_name="追加笔记",
        description="在现有笔记末尾追加新内容",
        category=ActionCategory.NOTE,
        executor=append_note,
        parameters=[
            ActionParameter(
                name="title",
                type="str",
                description="笔记标题",
                required=True,
            ),
            ActionParameter(
                name="content",
                type="str",
                description="要追加的内容",
                required=True,
            ),
            ActionParameter(
                name="notes_dir",
                type="str",
                description="笔记存储目录",
                required=False,
            ),
            ActionParameter(
                name="separator",
                type="str",
                description="分隔符",
                required=False,
                default="\n\n---\n\n",
            ),
            ActionParameter(
                name="timestamp",
                type="bool",
                description="是否添加时间戳",
                required=False,
                default=True,
            ),
        ],
        returns="追加结果信息",
        examples=[
            {
                "title": "会议记录",
                "content": "新增讨论内容...",
                "timestamp": True,
            }
        ],
        tags=["note", "append"],
    )
    
    # 搜索笔记
    action_registry.register(
        name="note.search",
        display_name="搜索笔记",
        description="在笔记中搜索指定内容",
        category=ActionCategory.NOTE,
        executor=search_notes,
        parameters=[
            ActionParameter(
                name="query",
                type="str",
                description="搜索关键词",
                required=True,
            ),
            ActionParameter(
                name="notes_dir",
                type="str",
                description="笔记存储目录",
                required=False,
            ),
            ActionParameter(
                name="search_in_content",
                type="bool",
                description="是否在内容中搜索",
                required=False,
                default=True,
            ),
            ActionParameter(
                name="search_in_tags",
                type="bool",
                description="是否在标签中搜索",
                required=False,
                default=True,
            ),
            ActionParameter(
                name="case_sensitive",
                type="bool",
                description="是否区分大小写",
                required=False,
                default=False,
            ),
            ActionParameter(
                name="limit",
                type="int",
                description="返回结果数量限制",
                required=False,
                default=50,
                min_value=1,
                max_value=500,
            ),
        ],
        returns="搜索结果列表",
        examples=[
            {
                "query": "项目进度",
                "search_in_content": True,
            }
        ],
        tags=["note", "search"],
    )
    
    # 列出笔记
    action_registry.register(
        name="note.list",
        display_name="列出笔记",
        description="列出所有笔记或按标签筛选",
        category=ActionCategory.NOTE,
        executor=list_notes,
        parameters=[
            ActionParameter(
                name="notes_dir",
                type="str",
                description="笔记存储目录",
                required=False,
            ),
            ActionParameter(
                name="tag",
                type="str",
                description="按标签筛选",
                required=False,
            ),
            ActionParameter(
                name="sort_by",
                type="str",
                description="排序字段 (title, created, updated)",
                required=False,
                default="updated",
                choices=["title", "created", "updated"],
            ),
            ActionParameter(
                name="sort_order",
                type="str",
                description="排序顺序 (asc, desc)",
                required=False,
                default="desc",
                choices=["asc", "desc"],
            ),
            ActionParameter(
                name="limit",
                type="int",
                description="返回数量限制",
                required=False,
                default=100,
            ),
        ],
        returns="笔记列表",
        examples=[
            {
                "tag": "会议",
                "sort_by": "updated",
            }
        ],
        tags=["note", "list"],
    )
    
    # 读取笔记
    action_registry.register(
        name="note.read",
        display_name="读取笔记",
        description="读取指定笔记的内容",
        category=ActionCategory.NOTE,
        executor=read_note,
        parameters=[
            ActionParameter(
                name="title",
                type="str",
                description="笔记标题",
                required=True,
            ),
            ActionParameter(
                name="notes_dir",
                type="str",
                description="笔记存储目录",
                required=False,
            ),
        ],
        returns="笔记内容和元数据",
        examples=[
            {
                "title": "会议记录",
            }
        ],
        tags=["note", "read"],
    )
    
    # 删除笔记
    action_registry.register(
        name="note.delete",
        display_name="删除笔记",
        description="删除指定的笔记文件",
        category=ActionCategory.NOTE,
        executor=delete_note,
        parameters=[
            ActionParameter(
                name="title",
                type="str",
                description="笔记标题",
                required=True,
            ),
            ActionParameter(
                name="notes_dir",
                type="str",
                description="笔记存储目录",
                required=False,
            ),
        ],
        returns="删除结果",
        examples=[
            {
                "title": "旧笔记",
            }
        ],
        tags=["note", "delete"],
        requires_confirmation=True,
    )


# 模块加载时自动注册
_register_actions()
