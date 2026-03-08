"""
文件操作动作
提供文件整理、移动、重命名、删除、复制和目录列表等操作
"""
import os
import re
import shutil
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


def _validate_path(path: str, base_dir: Optional[str] = None) -> Path:
    """
    验证并规范化路径
    
    Args:
        path: 要验证的路径
        base_dir: 基础目录（可选）
    
    Returns:
        规范化的 Path 对象
    
    Raises:
        ValueError: 路径无效或不在允许范围内
    """
    # 规范化路径
    path_obj = Path(path).resolve()
    
    # 检查路径是否存在（对于读取操作）
    # 对于创建操作，检查父目录是否存在
    
    # 如果指定了基础目录，检查路径是否在基础目录内
    if base_dir:
        base_path = Path(base_dir).resolve()
        try:
            path_obj.relative_to(base_path)
        except ValueError:
            raise ValueError(f"路径不在允许的目录范围内: {path}")
    
    return path_obj


def _get_file_info(path: Path) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        path: 文件路径
    
    Returns:
        文件信息字典
    """
    try:
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "size": stat.st_size,
            "size_formatted": _format_size(stat.st_size),
            "extension": path.suffix.lower(),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
        }
    except Exception as e:
        return {
            "name": path.name,
            "path": str(path),
            "error": str(e),
        }


def _format_size(size: int) -> str:
    """
    格式化文件大小
    
    Args:
        size: 文件大小（字节）
    
    Returns:
        格式化的大小字符串
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def organize_downloads(
    directory: str,
    rules: Optional[Dict[str, List[str]]] = None,
    dry_run: bool = False,
) -> ActionResult:
    """
    整理下载文件夹
    
    根据文件类型自动分类整理文件到不同子目录
    
    Args:
        directory: 要整理的目录路径
        rules: 自定义分类规则，键为目标文件夹名，值为文件扩展名列表
        dry_run: 是否仅预览不实际执行
    
    Returns:
        执行结果
    """
    logger.info(f"整理目录: {directory}, dry_run={dry_run}")
    
    try:
        # 验证目录
        dir_path = _validate_path(directory)
        
        if not dir_path.is_dir():
            return ActionResult(
                success=False,
                error=f"路径不是目录: {directory}",
            )
        
        # 默认分类规则
        default_rules = {
            "文档": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".md"],
            "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
            "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
            "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
            "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "程序": [".exe", ".msi", ".bat", ".cmd", ".ps1"],
            "代码": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".rb"],
        }
        
        # 合并自定义规则
        if rules:
            default_rules.update(rules)
        
        # 统计信息
        stats = {
            "total_files": 0,
            "organized_files": 0,
            "skipped_files": 0,
            "created_folders": [],
            "moved_files": [],
            "errors": [],
        }
        
        # 遍历目录中的文件
        for item in dir_path.iterdir():
            if item.is_file():
                stats["total_files"] += 1
                
                # 查找匹配的分类
                ext = item.suffix.lower()
                target_folder = None
                
                for folder, extensions in default_rules.items():
                    if ext in extensions:
                        target_folder = folder
                        break
                
                # 如果没有匹配的分类，放入"其他"
                if not target_folder:
                    target_folder = "其他"
                
                target_path = dir_path / target_folder
                
                if dry_run:
                    # 仅预览
                    stats["organized_files"] += 1
                    stats["moved_files"].append({
                        "file": item.name,
                        "from": str(item),
                        "to": str(target_path / item.name),
                    })
                    if target_folder not in stats["created_folders"]:
                        stats["created_folders"].append(target_folder)
                else:
                    # 实际执行
                    try:
                        # 创建目标文件夹
                        target_path.mkdir(exist_ok=True)
                        if target_folder not in stats["created_folders"]:
                            stats["created_folders"].append(target_folder)
                        
                        # 移动文件
                        new_path = target_path / item.name
                        
                        # 如果目标文件已存在，添加序号
                        if new_path.exists():
                            counter = 1
                            while True:
                                new_name = f"{item.stem}_{counter}{item.suffix}"
                                new_path = target_path / new_name
                                if not new_path.exists():
                                    break
                                counter += 1
                        
                        shutil.move(str(item), str(new_path))
                        
                        stats["organized_files"] += 1
                        stats["moved_files"].append({
                            "file": item.name,
                            "from": str(item),
                            "to": str(new_path),
                        })
                        
                    except Exception as e:
                        stats["skipped_files"] += 1
                        stats["errors"].append({
                            "file": item.name,
                            "error": str(e),
                        })
                        logger.error(f"移动文件失败: {item}, 错误: {e}")
        
        return ActionResult(
            success=True,
            data=stats,
            message=f"整理完成: 共 {stats['total_files']} 个文件, "
                    f"已整理 {stats['organized_files']} 个, "
                    f"跳过 {stats['skipped_files']} 个",
        )
        
    except Exception as e:
        logger.error(f"整理目录失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def move_files(
    source: str,
    destination: str,
    pattern: Optional[str] = None,
    overwrite: bool = False,
) -> ActionResult:
    """
    移动文件
    
    将文件或匹配模式的文件移动到目标目录
    
    Args:
        source: 源文件或目录路径
        destination: 目标目录路径
        pattern: 文件名匹配模式（支持通配符）
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        执行结果
    """
    logger.info(f"移动文件: {source} -> {destination}")
    
    try:
        source_path = _validate_path(source)
        dest_path = _validate_path(destination)
        
        # 确保目标目录存在
        dest_path.mkdir(parents=True, exist_ok=True)
        
        moved_files = []
        errors = []
        
        if source_path.is_file():
            # 移动单个文件
            files_to_move = [source_path]
        elif source_path.is_dir():
            # 移动目录中的文件
            if pattern:
                files_to_move = list(source_path.glob(pattern))
            else:
                files_to_move = list(source_path.iterdir())
        else:
            return ActionResult(
                success=False,
                error=f"源路径不存在: {source}",
            )
        
        for file_path in files_to_move:
            if not file_path.is_file():
                continue
            
            try:
                target = dest_path / file_path.name
                
                # 检查目标文件是否存在
                if target.exists():
                    if overwrite:
                        target.unlink()
                    else:
                        # 添加序号
                        counter = 1
                        while True:
                            new_name = f"{file_path.stem}_{counter}{file_path.suffix}"
                            target = dest_path / new_name
                            if not target.exists():
                                break
                            counter += 1
                
                shutil.move(str(file_path), str(target))
                moved_files.append({
                    "from": str(file_path),
                    "to": str(target),
                })
                
            except Exception as e:
                errors.append({
                    "file": str(file_path),
                    "error": str(e),
                })
                logger.error(f"移动文件失败: {file_path}, 错误: {e}")
        
        return ActionResult(
            success=len(moved_files) > 0,
            data={
                "moved_count": len(moved_files),
                "error_count": len(errors),
                "moved_files": moved_files,
                "errors": errors,
            },
            message=f"移动完成: 成功 {len(moved_files)} 个, 失败 {len(errors)} 个",
        )
        
    except Exception as e:
        logger.error(f"移动文件失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def rename_files(
    directory: str,
    pattern: str,
    replacement: str,
    recursive: bool = False,
    preview: bool = True,
) -> ActionResult:
    """
    批量重命名文件
    
    使用正则表达式批量重命名文件
    
    Args:
        directory: 目录路径
        pattern: 匹配模式（正则表达式）
        replacement: 替换字符串
        recursive: 是否递归处理子目录
        preview: 是否仅预览
    
    Returns:
        执行结果
    """
    logger.info(f"批量重命名: {directory}, pattern={pattern}")
    
    try:
        dir_path = _validate_path(directory)
        
        if not dir_path.is_dir():
            return ActionResult(
                success=False,
                error=f"路径不是目录: {directory}",
            )
        
        # 编译正则表达式
        regex = re.compile(pattern)
        
        # 收集文件
        if recursive:
            files = list(dir_path.rglob("*"))
        else:
            files = list(dir_path.glob("*"))
        
        renamed_files = []
        errors = []
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            old_name = file_path.name
            
            # 应用正则替换
            new_name = regex.sub(replacement, old_name)
            
            # 如果名称没有变化，跳过
            if new_name == old_name:
                continue
            
            new_path = file_path.parent / new_name
            
            # 检查新名称是否已存在
            if new_path.exists():
                errors.append({
                    "file": str(file_path),
                    "error": f"目标文件已存在: {new_name}",
                })
                continue
            
            if preview:
                renamed_files.append({
                    "old_name": old_name,
                    "new_name": new_name,
                    "path": str(file_path.parent),
                })
            else:
                try:
                    file_path.rename(new_path)
                    renamed_files.append({
                        "old_name": old_name,
                        "new_name": new_name,
                        "path": str(file_path.parent),
                    })
                except Exception as e:
                    errors.append({
                        "file": str(file_path),
                        "error": str(e),
                    })
        
        return ActionResult(
            success=True,
            data={
                "renamed_count": len(renamed_files),
                "error_count": len(errors),
                "renamed_files": renamed_files,
                "errors": errors,
                "preview": preview,
            },
            message=f"重命名{'预览' if preview else '完成'}: {len(renamed_files)} 个文件",
        )
        
    except Exception as e:
        logger.error(f"批量重命名失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def delete_files(
    paths: List[str],
    safe_mode: bool = True,
    move_to_trash: bool = True,
) -> ActionResult:
    """
    安全删除文件
    
    删除指定文件，支持安全模式和回收站
    
    Args:
        paths: 要删除的文件路径列表
        safe_mode: 安全模式，检查敏感文件
        move_to_trash: 是否移动到回收站而非永久删除
    
    Returns:
        执行结果
    """
    logger.info(f"删除文件: {len(paths)} 个文件")
    
    # 敏感文件扩展名
    sensitive_extensions = {".exe", ".bat", ".cmd", ".ps1", ".vbs", ".sys", ".dll"}
    
    # 敏感目录
    sensitive_dirs = {
        "windows", "system32", "program files", "program files (x86)",
        "programdata", "appdata",
    }
    
    deleted_files = []
    skipped_files = []
    errors = []
    
    for path_str in paths:
        try:
            path = _validate_path(path_str)
            
            if not path.exists():
                errors.append({
                    "path": path_str,
                    "error": "文件不存在",
                })
                continue
            
            # 安全模式检查
            if safe_mode:
                # 检查敏感扩展名
                if path.suffix.lower() in sensitive_extensions:
                    skipped_files.append({
                        "path": path_str,
                        "reason": "敏感文件类型",
                    })
                    continue
                
                # 检查敏感目录
                path_lower = str(path).lower()
                if any(sdir in path_lower for sdir in sensitive_dirs):
                    skipped_files.append({
                        "path": path_str,
                        "reason": "敏感目录",
                    })
                    continue
            
            if move_to_trash:
                # Windows 下移动到回收站
                try:
                    import winshell
                    winshell.delete_file(str(path), no_confirm=True)
                    deleted_files.append({
                        "path": path_str,
                        "method": "recycle_bin",
                    })
                except ImportError:
                    # 如果没有 winshell，直接删除
                    if path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(str(path))
                    deleted_files.append({
                        "path": path_str,
                        "method": "permanent",
                    })
            else:
                # 永久删除
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(str(path))
                deleted_files.append({
                    "path": path_str,
                    "method": "permanent",
                })
                
        except Exception as e:
            errors.append({
                "path": path_str,
                "error": str(e),
            })
            logger.error(f"删除文件失败: {path_str}, 错误: {e}")
    
    return ActionResult(
        success=len(deleted_files) > 0,
        data={
            "deleted_count": len(deleted_files),
            "skipped_count": len(skipped_files),
            "error_count": len(errors),
            "deleted_files": deleted_files,
            "skipped_files": skipped_files,
            "errors": errors,
        },
        message=f"删除完成: 成功 {len(deleted_files)} 个, "
                f"跳过 {len(skipped_files)} 个, 失败 {len(errors)} 个",
    )


def copy_files(
    source: str,
    destination: str,
    pattern: Optional[str] = None,
    recursive: bool = False,
    overwrite: bool = False,
) -> ActionResult:
    """
    复制文件
    
    复制文件或目录到目标位置
    
    Args:
        source: 源文件或目录路径
        destination: 目标路径
        pattern: 文件名匹配模式
        recursive: 是否递归复制
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        执行结果
    """
    logger.info(f"复制文件: {source} -> {destination}")
    
    try:
        source_path = _validate_path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            return ActionResult(
                success=False,
                error=f"源路径不存在: {source}",
            )
        
        copied_files = []
        errors = []
        
        if source_path.is_file():
            # 复制单个文件
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if dest_path.exists() and not overwrite:
                # 添加序号
                counter = 1
                while True:
                    new_name = f"{dest_path.stem}_{counter}{dest_path.suffix}"
                    new_path = dest_path.parent / new_name
                    if not new_path.exists():
                        dest_path = new_path
                        break
                    counter += 1
            
            shutil.copy2(str(source_path), str(dest_path))
            copied_files.append({
                "from": str(source_path),
                "to": str(dest_path),
            })
            
        elif source_path.is_dir():
            # 复制目录
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # 收集文件
            if pattern:
                files = source_path.glob(pattern)
            elif recursive:
                files = source_path.rglob("*")
            else:
                files = source_path.glob("*")
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                try:
                    # 计算相对路径
                    rel_path = file_path.relative_to(source_path)
                    target = dest_path / rel_path
                    
                    # 创建目标目录
                    target.parent.mkdir(parents=True, exist_ok=True)
                    
                    if target.exists() and not overwrite:
                        counter = 1
                        while True:
                            new_name = f"{target.stem}_{counter}{target.suffix}"
                            target = target.parent / new_name
                            if not target.exists():
                                break
                            counter += 1
                    
                    shutil.copy2(str(file_path), str(target))
                    copied_files.append({
                        "from": str(file_path),
                        "to": str(target),
                    })
                    
                except Exception as e:
                    errors.append({
                        "file": str(file_path),
                        "error": str(e),
                    })
        
        return ActionResult(
            success=len(copied_files) > 0,
            data={
                "copied_count": len(copied_files),
                "error_count": len(errors),
                "copied_files": copied_files,
                "errors": errors,
            },
            message=f"复制完成: 成功 {len(copied_files)} 个, 失败 {len(errors)} 个",
        )
        
    except Exception as e:
        logger.error(f"复制文件失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def list_directory(
    directory: str,
    pattern: Optional[str] = None,
    recursive: bool = False,
    show_hidden: bool = False,
    sort_by: str = "name",
    sort_order: str = "asc",
) -> ActionResult:
    """
    列出目录内容
    
    列出指定目录中的文件和子目录
    
    Args:
        directory: 目录路径
        pattern: 文件名匹配模式
        recursive: 是否递归列出
        show_hidden: 是否显示隐藏文件
        sort_by: 排序字段 (name, size, modified, type)
        sort_order: 排序顺序 (asc, desc)
    
    Returns:
        执行结果
    """
    logger.info(f"列出目录: {directory}")
    
    try:
        dir_path = _validate_path(directory)
        
        if not dir_path.is_dir():
            return ActionResult(
                success=False,
                error=f"路径不是目录: {directory}",
            )
        
        # 收集文件
        if recursive:
            if pattern:
                items = dir_path.rglob(pattern)
            else:
                items = dir_path.rglob("*")
        else:
            if pattern:
                items = dir_path.glob(pattern)
            else:
                items = dir_path.iterdir()
        
        # 过滤和收集信息
        files = []
        dirs = []
        
        for item in items:
            # 过滤隐藏文件
            if not show_hidden and item.name.startswith("."):
                continue
            
            info = _get_file_info(item)
            
            if item.is_file():
                files.append(info)
            elif item.is_dir():
                dirs.append(info)
        
        # 排序
        reverse = sort_order.lower() == "desc"
        
        if sort_by == "name":
            files.sort(key=lambda x: x["name"].lower(), reverse=reverse)
            dirs.sort(key=lambda x: x["name"].lower(), reverse=reverse)
        elif sort_by == "size":
            files.sort(key=lambda x: x.get("size", 0), reverse=reverse)
        elif sort_by == "modified":
            files.sort(key=lambda x: x.get("modified", ""), reverse=reverse)
            dirs.sort(key=lambda x: x.get("modified", ""), reverse=reverse)
        elif sort_by == "type":
            files.sort(key=lambda x: x.get("extension", ""), reverse=reverse)
        
        return ActionResult(
            success=True,
            data={
                "directory": str(dir_path),
                "files": files,
                "directories": dirs,
                "file_count": len(files),
                "dir_count": len(dirs),
                "total_size": sum(f.get("size", 0) for f in files),
            },
            message=f"找到 {len(files)} 个文件, {len(dirs)} 个目录",
        )
        
    except Exception as e:
        logger.error(f"列出目录失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


# 注册动作到注册表
def _register_actions():
    """
    注册所有文件操作动作
    """
    # 整理下载文件夹
    action_registry.register(
        name="file.organize_downloads",
        display_name="整理文件夹",
        description="根据文件类型自动分类整理文件到不同子目录",
        category=ActionCategory.FILE,
        executor=organize_downloads,
        parameters=[
            ActionParameter(
                name="directory",
                type="str",
                description="要整理的目录路径",
                required=True,
            ),
            ActionParameter(
                name="rules",
                type="dict",
                description="自定义分类规则，键为目标文件夹名，值为文件扩展名列表",
                required=False,
            ),
            ActionParameter(
                name="dry_run",
                type="bool",
                description="是否仅预览不实际执行",
                required=False,
                default=False,
            ),
        ],
        returns="整理统计信息，包括移动的文件列表",
        examples=[
            {
                "directory": "C:\\Users\\用户名\\Downloads",
                "dry_run": True,
            }
        ],
        tags=["file", "organize", "cleanup"],
    )
    
    # 移动文件
    action_registry.register(
        name="file.move",
        display_name="移动文件",
        description="将文件或匹配模式的文件移动到目标目录",
        category=ActionCategory.FILE,
        executor=move_files,
        parameters=[
            ActionParameter(
                name="source",
                type="str",
                description="源文件或目录路径",
                required=True,
            ),
            ActionParameter(
                name="destination",
                type="str",
                description="目标目录路径",
                required=True,
            ),
            ActionParameter(
                name="pattern",
                type="str",
                description="文件名匹配模式（支持通配符）",
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
        returns="移动的文件列表",
        examples=[
            {
                "source": "C:\\temp",
                "destination": "C:\\backup",
                "pattern": "*.txt",
            }
        ],
        tags=["file", "move"],
    )
    
    # 批量重命名
    action_registry.register(
        name="file.rename",
        display_name="批量重命名",
        description="使用正则表达式批量重命名文件",
        category=ActionCategory.FILE,
        executor=rename_files,
        parameters=[
            ActionParameter(
                name="directory",
                type="str",
                description="目录路径",
                required=True,
            ),
            ActionParameter(
                name="pattern",
                type="str",
                description="匹配模式（正则表达式）",
                required=True,
            ),
            ActionParameter(
                name="replacement",
                type="str",
                description="替换字符串",
                required=True,
            ),
            ActionParameter(
                name="recursive",
                type="bool",
                description="是否递归处理子目录",
                required=False,
                default=False,
            ),
            ActionParameter(
                name="preview",
                type="bool",
                description="是否仅预览",
                required=False,
                default=True,
            ),
        ],
        returns="重命名的文件列表",
        examples=[
            {
                "directory": "C:\\photos",
                "pattern": "IMG_(\\d+)",
                "replacement": "Photo_\\1",
                "preview": True,
            }
        ],
        tags=["file", "rename", "batch"],
    )
    
    # 删除文件
    action_registry.register(
        name="file.delete",
        display_name="删除文件",
        description="安全删除指定文件，支持安全模式和回收站",
        category=ActionCategory.FILE,
        executor=delete_files,
        parameters=[
            ActionParameter(
                name="paths",
                type="list",
                description="要删除的文件路径列表",
                required=True,
            ),
            ActionParameter(
                name="safe_mode",
                type="bool",
                description="安全模式，检查敏感文件",
                required=False,
                default=True,
            ),
            ActionParameter(
                name="move_to_trash",
                type="bool",
                description="是否移动到回收站而非永久删除",
                required=False,
                default=True,
            ),
        ],
        returns="删除结果统计",
        examples=[
            {
                "paths": ["C:\\temp\\file1.txt", "C:\\temp\\file2.txt"],
                "safe_mode": True,
                "move_to_trash": True,
            }
        ],
        tags=["file", "delete", "safe"],
        requires_confirmation=True,
        is_dangerous=True,
    )
    
    # 复制文件
    action_registry.register(
        name="file.copy",
        display_name="复制文件",
        description="复制文件或目录到目标位置",
        category=ActionCategory.FILE,
        executor=copy_files,
        parameters=[
            ActionParameter(
                name="source",
                type="str",
                description="源文件或目录路径",
                required=True,
            ),
            ActionParameter(
                name="destination",
                type="str",
                description="目标路径",
                required=True,
            ),
            ActionParameter(
                name="pattern",
                type="str",
                description="文件名匹配模式",
                required=False,
            ),
            ActionParameter(
                name="recursive",
                type="bool",
                description="是否递归复制",
                required=False,
                default=False,
            ),
            ActionParameter(
                name="overwrite",
                type="bool",
                description="是否覆盖已存在的文件",
                required=False,
                default=False,
            ),
        ],
        returns="复制的文件列表",
        examples=[
            {
                "source": "C:\\documents",
                "destination": "D:\\backup\\documents",
                "recursive": True,
            }
        ],
        tags=["file", "copy", "backup"],
    )
    
    # 列出目录
    action_registry.register(
        name="file.list_directory",
        display_name="列出目录",
        description="列出指定目录中的文件和子目录",
        category=ActionCategory.FILE,
        executor=list_directory,
        parameters=[
            ActionParameter(
                name="directory",
                type="str",
                description="目录路径",
                required=True,
            ),
            ActionParameter(
                name="pattern",
                type="str",
                description="文件名匹配模式",
                required=False,
            ),
            ActionParameter(
                name="recursive",
                type="bool",
                description="是否递归列出",
                required=False,
                default=False,
            ),
            ActionParameter(
                name="show_hidden",
                type="bool",
                description="是否显示隐藏文件",
                required=False,
                default=False,
            ),
            ActionParameter(
                name="sort_by",
                type="str",
                description="排序字段 (name, size, modified, type)",
                required=False,
                default="name",
                choices=["name", "size", "modified", "type"],
            ),
            ActionParameter(
                name="sort_order",
                type="str",
                description="排序顺序 (asc, desc)",
                required=False,
                default="asc",
                choices=["asc", "desc"],
            ),
        ],
        returns="文件和目录列表",
        examples=[
            {
                "directory": "C:\\Users",
                "sort_by": "name",
            }
        ],
        tags=["file", "list", "directory"],
    )


# 模块加载时自动注册
_register_actions()
